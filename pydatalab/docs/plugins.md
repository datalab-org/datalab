# Plugins

*datalab* supports plugins that extend the server with new functionality, in
particular:

- New data block types, which render interactive views of attached files in item
  detail pages.
- Custom item types, which are served through the same generic endpoints as the built-in `samples`, `cells`, `starting_materials` and `equipment` types.
- Tool plugins, which add [in-app or standalone tools](tools.md).

Some self-declared plugins can be found via the [`datalab-plugin` topic on GitHub](https://github.com/topics/datalab-plugin), in lieu of a formal registry at this time.
Plugins can also be kept private and installed from e.g., a private git repository, or a local path on the host, using the same installation described below.

!!! warning "Only install plugins you trust"
    A plugin runs inside the datalab API process with the same privileges as
    the server. An in-app tool plugin also runs JavaScript inside each signed-in
    user's datalab page.

    The deployment administrator is responsible for reviewing and trusting the
    plugin's source, dependencies, compiled frontend assets, maintainers, and
    update process. Framework validation catches accidental incompatibilities;
    it does not isolate deliberately malicious installed code.

## What a plugin is

At present, a *datalab* plugin is a Python package that registers one or more [data block](blocks/index.md) classes, item types, or tool providers via a Python entry point.
Data blocks ingest a file (or set of files) attached to an item and render an interactive view of the parsed data, e.g. an NMR spectrum, an electrochemistry cycler trace, or an XRD pattern.
Plugins (and deployments) can also register **custom item types**, new top-level item models served through the generic item endpoints (see [below](#custom-item-types)). Further plugin types, e.g., ingestion hooks and webapp components, are planned in the future (see [roadmap.md](roadmap.md)); please reach out if you have a specific use case.
Tool plugins add in-app or standalone tools through the dedicated tool framework described below.
*datalab* discovers them at server startup by enumerating the relevant entry point group, with no changes required to the core code.

## Writing a plugin

The recommended starting point is the [Copier](https://copier.readthedocs.io/) template at [datalab-org/datalab-app-plugin-template](https://github.com/datalab-org/datalab-app-plugin-template), which scaffolds a minimal data block plugin together with the packaging boilerplate (entry point declaration, test scaffolding, and a working `pyproject.toml`).
Rather than forking the repository, you should use it directly with Copier to
generate a new plugin repository; see the README in the [datalab-org/datalab-app-plugin-template](https://github.com/datalab-org/datalab-app-plugin-template) repository for full instructions.

The [Data Blocks documentation](blocks/index.md) explains the block lifecycle,
events, rendering, and asynchronous processing in more detail.

## Writing a Tool plugin

A Tool plugin registers a provider through the `pydatalab.tools` entry-point
group. Start from the Copier template:

```shell
uvx copier copy https://github.com/Matgenix/datalab-tool-plugin-template \
  ../my-datalab-tool
```

The template repository is hosted at
[Matgenix/datalab-tool-plugin-template](https://github.com/Matgenix/datalab-tool-plugin-template).

The template asks for the tool name, its stable ID, its Python distribution
name, the UI type, and whether it opens in the same browser tab or a new one.
For an in-app tool it can also generate an optional selected-items table
action. It derives the Python package and provider class names automatically.

### Provider contract and discovery

The package exposes a zero-argument `ToolProvider` subclass:

```toml
[project.entry-points."pydatalab.tools"]
example-tool = "example_tool.provider:ExampleToolProvider"
```

The entry-point name must match the provider's lowercase, hyphenated `id`. The
provider declares immutable `ToolMetadata` and may implement:

- `launch(context, grants)`, which returns `None` for an in-app tool or an
  HTTP(S) URL for a standalone tool;
- `is_available(context)`, which controls whether the current user can see and
  launch the tool; and
- a Flask `Blueprint` containing provider-owned routes.

datalab discovers providers once at API startup. A provider that fails to load
is logged and skipped without preventing the server from starting. Duplicate
IDs are rejected. Installing or removing a plugin therefore requires an API
restart. An administrator can disable an installed provider by adding its ID to
`TOOLS.DISABLED`.

Provider blueprints are the only supported way for a plugin to add routes to
datalab. The framework mounts them below
`/tools/plugins/<tool-id>/` for every supported API alias and automatically
authenticates every route:

- the default browser policy requires an active datalab browser session and
  validates the origin of non-safe requests;
- the service policy is for machine-to-machine integrations and requires the
  provider to implement `authenticate_service_request()`.

Automatic route authentication determines who may enter a route. It does not
automatically filter arbitrary database queries. Plugins should retrieve data
through the normal datalab API or explicitly use permission-aware datalab
services for server-side processing.

The route ownership boundary is:

| Interface | Authentication | Data permissions |
|---|---|---|
| Core catalog and launch endpoints | datalab | Current user and provider availability |
| Provider callbacks such as `launch()` and `is_available()` | Called by protected core routes; they are not routes themselves | Restricted provider context |
| Routes in `ToolProvider.blueprint` | Provider's browser or service policy, applied by datalab | Normal API calls or explicit permission-aware server queries |
| Routes on an external tool service | External service | Calls to the datalab API with a temporary tool access token |

Directly registering routes on the Flask app or modifying core blueprints is
unsupported and bypasses the tool framework's guarantees.

The canonical API endpoints are:

- `GET /v0.1/info/tools` for the current-user catalog;
- `POST /v0.1/tools/<tool-id>/launch` to launch either UI type; and
- `/v0.1/tools/plugins/<tool-id>/...` for provider-owned routes.

### In-app tools

An in-app tool renders below the normal datalab navigation:

```python
metadata = ToolMetadata(
    name="Example analysis",
    description="Analyse data without leaving datalab.",
    ui=InAppToolUI(),
)
```

The provider serves one compiled frontend entrypoint from its blueprint. The
bundle registers its component synchronously:

```javascript
window.datalabToolSdk.register(ToolView);
```

The versioned frontend SDK supplies the host runtime, authenticated API helpers,
navigation helpers, selected datalab components, and the standard dialog
service. An in-app tool should use these supported interfaces rather than the
webapp's private store or internal source paths.

The template's Vite project builds one classic JavaScript bundle, externalising
the frontend runtime supplied by datalab. Build it before packaging the Python
distribution:

```shell
cd frontend
yarn install
yarn build
```

Commit and review the dependency lockfile and compiled bundle. Loading a bundle
into the webapp is an administrator trust decision, not a browser sandbox.

### Selected-items table actions

A tool may add an action to selected-items menus:

```python
metadata = ToolMetadata(
    name="Example comparison",
    description="Compare selected items.",
    ui=InAppToolUI(),
    launch_actions=(
        ItemTableSelectionAction(
            id="compare-selected",
            label="Compare selected",
            tables=("samples", "inventory", "collection-items"),
            min_items=2,
            max_items=20,
        ),
    ),
)
```

The supported table identifiers are `samples`, `inventory`, `equipment`, and
`collection-items`. Selection limits must satisfy
`1 <= min_items <= max_items <= 100`.

When the user chooses an in-app action, datalab opens the normal tool host with
ordered, deduplicated item refcodes:

```text
/tools/example-comparison?action=compare-selected&items=test%3AABC&items=test%3ADEF
```

The frontend reads them through the SDK:

```javascript
const { actionId, itemRefcodes } = sdk.selection.current();
```

Only immutable refcodes are passed—not item names, blocks, database IDs, or
complete table rows. Query parameters are untrusted input, so the plugin must
load current item data through permission-aware API routes.

A standalone tool can declare the same action metadata. datalab validates the
selection and sends it through the normal launch request:

```json
{
  "action": "open-in-notebook",
  "items": ["test:ABC", "test:DEF"]
}
```

The ordered selection is bound to the provider's single-use launch grant and is
returned by `exchange_launch_code`. A provider that declares several actions
uses `selection.action_id` to distinguish them. A launch from the Tools menu
has no selection.

The
[datalab item comparison tool](https://github.com/Matgenix/datalab-item-comparison-tool)
demonstrates this integration for Samples, Inventory, and items within a
collection.

### Standalone tools

A standalone tool owns its user interface and normally opens separately:

```python
metadata = ToolMetadata(
    name="Example tool",
    description="A separate application.",
    ui=StandaloneToolUI(),
)

def launch(self, context, grants):
    code = grants.issue("example-tool")
    return f"https://tool.example/#datalab_launch_code={code}"
```

The launch code is short-lived, single-use, and bound to the user, tool, and
client. A successful exchange atomically consumes it and returns a temporary
tool access token. The standalone application uses that token only with normal
datalab API endpoints, which apply the current user's permissions.

Keep launch codes in URL fragments rather than query parameters where possible,
remove them from the address bar immediately, and never put the resulting tool
access token in URLs, persistent browser storage, notebooks, files, analytics,
or logs. Tool access tokens must not be confused with users' permanent datalab
API keys.

A separately hosted application is outside datalab's automatic route
protection. Its administrator owns its authentication, isolation, storage, and
data-retention policy. If it requires a callback hosted by datalab, the
installed provider must expose that callback through a service-authenticated
provider blueprint.

### Tool plugin development tutorials

The tutorials build two deliberately small plugins:

- [Developing a standalone Tool plugin](plugin-development/standalone-tool-plugin.md),
  accompanied by the
  [standalone example repository](https://github.com/Matgenix/datalab-standalone-tool-plugin-example),
  opens in a new tab and displays the signed-in user's accessible sample count.
- [Developing an in-app Tool plugin](plugin-development/in-app-tool-plugin.md),
  accompanied by the
  [in-app example repository](https://github.com/Matgenix/datalab-in-app-tool-plugin-example),
  renders inside datalab and displays the same small piece of API-backed data.

Start with the
[plugin development tutorial overview](plugin-development/index.md) for a
side-by-side explanation of discovery and current-user access.

## Installing plugins

Plugins are declared in a `plugins.toml` file at the root of the repository (alongside `pydatalab/` and `webapp/`).
The format mirrors the relevant fragments of `pyproject.toml`, and a generated JSON Schema describing the expected structure is checked in at `pydatalab/schemas/plugin_config.json`:

```toml
# plugins.toml (at the repository root)
dependencies = [
    "datalab-app-plugin-insitu",
    "my-local-plugin",
]

[tool.uv.sources]
# Pin to a specific git ref:
datalab-app-plugin-insitu = { git = "https://github.com/datalab-org/datalab-app-plugin-insitu.git", rev = "v0.4.1" }
# Or point at a local checkout (paths are resolved relative to plugins.toml itself):
my-local-plugin = { path = "../my-local-plugin", editable = true }
```

To install *datalab* together with the declared plugins:

```shell
cd pydatalab
uv run invoke dev.install
```

This task:

1. Merges `plugins.toml` into a copy of `pyproject.toml` under `./build/` (as a `plugins` optional-dependency group, plus any `[tool.uv.sources]` entries).
2. Regenerates `./build/uv.lock` so plugin versions are locked alongside the core deps.
3. Runs `uv sync --all-extras --active --project ./build` to install everything into the currently active *datalab* virtual environment.

Pass `--no-dev` to skip dev dependencies (used by the production Docker build).

If no `plugins.toml` is present, the task falls back to installing the base `pyproject.toml` — so it is safe to run unconditionally.

To revert to the locked core dependencies without any plugins, run:

```shell
uv sync --all-extras --dev
```

## Custom item types

Beyond data blocks, a deployment can register **custom item types**: new top-level item models that are served through the same generic endpoints as the built-in `samples`, `cells`, `starting_materials` and `equipment` types, and advertised at `/info/types`.

A custom item type is a subclass either of an existing item model (to extend it) or of the base `Item` model (for a wholly new type).
At a minimum, it **must** declare its own `type` literal, which must not collide with a built-in type.
Custom types are namespaced with a leading underscore, reserving the un-prefixed namespace for built-in types; a type that does not already have one has it added at registration (so `my_samples` is served as `_my_samples`):

```python
from typing import Literal

from pydantic import Field

from pydatalab.models.samples import Sample


class MySample(Sample):
    type: Literal["my_samples"] = "my_samples"

    drying_time: float | None = Field(
        None,
        # opt this field into item list/summary views:
        json_schema_extra={"datalab_include_field_in_summary": True},
    )
```

There are two ways to register a custom item type, both of which run at server startup and require no changes to the core code:

1. **From a plugin package**, via the `pydatalab.item_types` entry point group
   (mirrors the data block mechanism):

    ```toml
    # pyproject.toml of the plugin package
    [project.entry-points."pydatalab.item_types"]
    my_samples = "my_plugin.models:MySample"
    ```

2. **From the server config**, by listing dotted import paths
   (`package.module:ClassName`) in `CUSTOM_ITEM_MODELS` — convenient for models
   that are already importable by the server:

    ```json
    {
      "CUSTOM_ITEM_MODELS": [
        "my_package.models:MySample",
        "my_package.models:MyItem"
      ]
    }
    ```

Fields tagged with `json_schema_extra={"datalab_include_field_in_summary": True}` are additionally included in item list/summary responses.
A worked example of both a `Sample` subclass and a standalone `Item` subclass lives at `pydatalab/src/pydatalab/models/_example_custom.py`.

### What belongs in a custom item type

Custom item types are for metadata that describes the item itself, and in particular for values recorded for *every* item of that type:

- **Intrinsic properties of the thing**: dimensions, a supplier batch number, an electrode loading.
- **Input parameters of how it was made**: the settings of a synthesis or fabrication step (temperature, duration, atmosphere).
- **High-level results that are always measured**: a single summary number per item — a capacity, a purity, a yield.

Data with one value per file, per scan or per cycle belongs in a [data block](blocks/index.md) instead: a block can be attached many times, whereas a field exists exactly once per item.
Similarly, anything with its own identity or provenance (a precursor batch, a piece of equipment) is better modelled as its own item and linked via a relationship.
As a rule of thumb, if you would want to *filter* the item list by it, it is a field on the item type; if you would want to *plot* it, it is probably block data.

!!! note "Extending nested fields is future work"
    Custom types can add new fields, including nested models of their own, but
    extending the structured fields that built-in models already define (e.g.
    adding a field to the entries of `synthesis_constituents`) is not yet
    supported.

!!! warning "Backend-only for now"
    The web UI does not yet render bespoke fields or provide tailored
    create/edit forms for custom types, so custom fields are readable and
    writable through the API but do not appear in item detail pages.

Eventually, such item types will allow for rich descriptions of unitful quantites, semantic annotations and URIs for fields, and cross-linking between items via custom relationships.

## Plugin installation

The same `invoke dev.install` task is used by the production Docker image (`.docker/server/Dockerfile`): a `plugins.toml` at the repository root is picked up automatically at build time, so plugins can be baked into a custom image without modifying the Dockerfile itself.
It will also be invoked from the [*datalab* Ansible role](https://github.com/datalab-org/datalab-ansible-terraform) to provision plugins on a deployed server when a `plugins.toml` is provided; see the role documentation for details.
