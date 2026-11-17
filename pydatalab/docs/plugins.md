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
Plugins (and deployments) can also register **custom item types**, new top-level item models served through the generic item endpoints (see [below](#custom-item-types)).
Plugins can ship Vue components for their blocks and item types (see [below](#webapp-components)).
Tool plugins add in-app or standalone tools through the dedicated framework
described in [Developing tool plugins](plugin-development/tool-plugin.md).
Further plugin types, e.g., ingestion hooks, are planned in the future (see [roadmap.md](roadmap.md)); please reach out if you have a specific use case.
*datalab* discovers them at server startup by enumerating the relevant entry point group, with no changes required to the core code.

## Installing and maintaining plugins

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

Use the exact distribution name and any required extras from the plugin's own
installation guide. Preserve existing entries when adding another plugin. Pin
production Git sources to a reviewed tag or commit; use editable path sources
only for local development.

Before installation or upgrade, review the plugin's source, dependencies,
frontend assets, release provenance, configuration, and any companion service
artifacts. Then install *datalab* together with the declared plugins:

```shell
cd pydatalab
uv run invoke dev.install
```

This task:

1. Merges `plugins.toml` into a copy of `pyproject.toml` under `./build/` (as a `plugins` optional-dependency group, plus any `[tool.uv.sources]` entries).
2. Regenerates `./build/uv.lock` so plugin versions are locked alongside the core deps.
3. Runs `uv sync --all-extras --active --project ./build` to install everything into the currently active *datalab* virtual environment.
4. Collects any custom Vue panels into the webapp when run from a complete source checkout.

Pass `--no-dev` to skip dev dependencies (used by the production Docker build).

If no `plugins.toml` is present, the task falls back to installing the base `pyproject.toml` — so it is safe to run unconditionally.

For a native installation, restart the datalab API after installation so it
discovers the plugin entry points. For Docker Compose, rebuild and recreate the
API and webapp images using the normal deployment profile; the Docker builds run
the same installation task and collect plugin frontend assets automatically.
The [datalab Ansible role](https://github.com/datalab-org/datalab-ansible-terraform)
also uses this task when a `plugins.toml` is provided.
If a standalone tool owns a separate service, deploy that service explicitly as
described in [Plugin-provided standalone services](deployment.md#plugin-provided-standalone-services).

After the restart, confirm that the tool or other plugin feature appears and
test it as a non-administrator user. Tool plugins are enabled by default;
[server configuration](config.md#tools) is the single reference for disabling
or ordering them. Plugin-specific settings remain in the plugin repository.

To upgrade a plugin, review the new release, change its pinned source or version,
rerun the installation or image build, restart the API, and repeat the check.
Keep the previous pin so the deployment can be rolled back by restoring it and
rebuilding.

To remove a plugin, delete its dependency and source entry from `plugins.toml`,
rerun the same installation or image build, and restart. Check the plugin's own
guide first: removing a provider stops its code from loading, but does not
necessarily remove plugin-owned stored data or a separately deployed service.

To revert to the locked core dependencies without any plugins, run:

```shell
uv sync --all-extras --dev
```

## Developing plugins

Use the template for the extension type rather than adding domain-specific code
to datalab core:

- For a data block, start from
  [`datalab-app-plugin-template`](https://github.com/datalab-org/datalab-app-plugin-template)
  and read the [Data Blocks documentation](blocks/index.md).
- For a custom item type, start from
  [`datalab-item-plugin-template`](https://github.com/Matgenix/datalab-item-plugin-template).
  The [schema-driven example](https://github.com/Matgenix/datalab-item-plugin-example)
  and [custom-Vue example](https://github.com/Matgenix/datalab-item-plugin-example-custom-vue)
  demonstrate the two supported rendering paths.
- For an in-app or standalone tool, follow
  [Developing tool plugins](plugin-development/tool-plugin.md). That guide owns
  the provider contract, selected-items actions, testing, packaging, and release
  workflow; the UI-specific tutorials build complete minimal examples.

## Custom item types

Beyond data blocks, a deployment can register **custom item types**: new top-level item models that are served through the same generic endpoints as the built-in `samples`, `cells`, `starting_materials` and `equipment` types, and advertised at `/info/types`.

A custom item type is a subclass either of an existing item model (to extend it) or of the base `Item` model (for a wholly new type).
At a minimum, it **must** declare its own `type` literal, which must not collide with a built-in type.
Its identifier must have the form `<namespace>:<type-name>`, for example `battery:electrode` and `battery_lab:coin-cell`.
Both parts must use lowercase letters and numbers, with hyphens or underscores allowed between words.
Exactly one colon separates the namespace from the type name.
The complete value is the canonical type identifier. It must be used wherever the type is referenced, including Python models,
REST payloads and URLs, database documents, relationships, constituents, schemas and the web UI.
The namespace and type name are only components of the naming convention; they are not stored or queried separately.

Existing core identifiers such as `samples` and `cells` remain bare and are exempt from this
custom-type rule. All built-in item types use bare identifiers. Choose a stable namespace owned by
the plugin or domain, because changing a type identifier changes stored data and API references.
Each model declares its complete identifier; a package may reuse one namespace for all of its
models or publish models under different namespaces.

```python
from typing import Literal

from pydantic import Field

from pydatalab.models.samples import Sample


class MySample(Sample):
    type: Literal["example:samples"] = "example:samples"

    drying_time: float | None = Field(
        None,
        # opt this field into item list/summary views:
        json_schema_extra={"datalab_include_field_in_summary": True},
    )
```

For now, all custom item types are created and listed from the Samples page, regardless of their
Python base model.

There are two ways to register a custom item type, both of which run at server startup and require no changes to the core code:

1. **From a plugin package**, via the `pydatalab.item_types` entry point group
   (mirrors the data block mechanism):

    ```toml
    # pyproject.toml of the plugin package
    [project.entry-points."pydatalab.item_types"]
    example-samples = "my_plugin.models:MySample"
    ```

   The entry-point key is a packaging-safe discovery name. The model's `type` literal is the
   canonical item type identifier.

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

Deployments using `ITEM_TYPE_ALLOW_LIST` must refer to a custom type by its complete `<namespace>:<type-name>` identifier.
A string entry permits every globally available block, while an object entry can provide a narrower `block_type_allow_list`.
See [Item and block availability](config.md#item-and-block-availability) for the complete
configuration semantics.

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

### Rendering a custom type in the web UI

The web UI renders a custom type's extra fields automatically. On startup the frontend reads `/info/types`, registers every custom type,
and on the edit page shows:

- the **base item component** — either the component used by the built-in type the model inherits
  from, or the generic name / refcode / relationships component for a direct `Item` subclass; and
- a **custom-fields panel** that diffs the type's schema against its base type and renders only
  the fields the model *adds*.

Each added field is rendered from its JSON-Schema type plus a small set of `json_schema_extra`
annotations on the field:

| `Field(json_schema_extra=…)` key | Effect in the UI |
|---|---|
| `datalab_include_field_in_summary` | also show the field as a column in list / summary views |
| `datalab_hidden` | store the field but don't render it directly |
| `datalab_quantity` | declare canonical storage plus plugin-defined display-unit conversions for a floating-point field |
| `datalab_ref_types` | render as an item-search selector restricted to these item types — i.e. a link to another item (built-in *or* custom) |
| `datalab_section` | group this field into its own titled card |
| `datalab_multiline` | render a string as a multi-line text area |

A few keys on the model's `model_config` control the type as a whole:

| `ConfigDict(json_schema_extra=…)` / config key | Effect in the UI |
|---|---|
| `title` | display name of the type (navbar, create dialog) |
| `datalab_ui_color` | accent colour for the navbar, field labels and the item's reference badge |
| `datalab_ui_hidden_fields` | base-component sections to hide (`status`, `collections`, `description`, `substance_information`, `synthesis_information`, `tags`, `location`) |
| `datalab_section_title` | title of the default custom-fields card |

Only **scalar-like** fields are rendered automatically: strings, numbers, enums, booleans, unit
quantities, and single item references. Lists, nested objects, computed values or charts need a
custom panel (see below).

```python
from typing import Literal
from pydantic import ConfigDict, Field
from pydatalab.models.samples import Sample
from pydatalab.models.utils import EntryReference


class Solution(Sample):
    model_config = ConfigDict(
        title="Solution",
        json_schema_extra={
            "datalab_ui_hidden_fields": ["synthesis_information"],
            "datalab_section_title": "Solution",
            "datalab_ui_color": "#3a7ca5",
        },
    )
    type: Literal["chemistry:solutions"] = "chemistry:solutions"

    # Fields linking to a built-in `starting_materials` or another `samples` item:
    solute: EntryReference | None = Field(
        None, json_schema_extra={"datalab_ref_types": ["starting_materials", "samples"]}
    )
    solvent: EntryReference | None = Field(
        None, json_schema_extra={"datalab_ref_types": ["starting_materials", "samples"]}
    )

    concentration: float | None = Field(
        None,
        ge=0,
        json_schema_extra={
            "datalab_include_field_in_summary": True,
            "datalab_quantity": {
                "canonical_unit": "mol/L",
                "display_units": {
                    "mol/L": {"scale": 1.0},
                    "mmol/L": {"scale": 0.001},
                },
                "default_display_unit": "mol/L",
                "display_unit_field": "concentration_display_unit",
            },
        },
    )
    concentration_display_unit: Literal["mol/L", "mmol/L"] | None = None
```

The numeric field always uses `canonical_unit` in Python, REST payloads and the database. The UI
converts other display units using:

```text
canonical = displayed * scale + offset
```

The optional `display_unit_field` stores only the user's display-unit preference. It must name a
companion string `Literal` whose possible values exactly match the keys in `display_units`.

### Custom panels (full control)

When annotations aren't enough (structured tables, values computed in the browser, plots, or
actions that pull data from a linked item), a plugin can ship its own Vue component, which takes
over rendering of the custom area entirely (the base item component is still shown above it).

Place a `<ClassName>Panel.vue` in a `webapp/` directory beside the models, where `<ClassName>` is
the model's class name (`MixedSolution` → `MixedSolutionPanel.vue`):

```
my_plugin/
├── pyproject.toml
└── my_plugin/
    ├── models.py
    └── webapp/
        └── MixedSolutionPanel.vue
```

Panel collection is part of plugin installation. For a native checkout, the complete installation
command is:

```bash
cd pydatalab
uv run invoke dev.install
```

The equivalent Docker workflows install the plugins, collect their panels, and build the matching
frontend image as one operation:

```bash
docker compose --profile dev up --build
docker compose --profile prod up --build
```

After editing a panel in a local plugin, rebuild the development frontend and its panel artifact:

```bash
docker compose --profile dev up --build app-dev
```

The collector remains available as a troubleshooting command when the installed environment has
not changed:

```bash
uv run invoke dev.collect-plugin-panels
```

The generated panel registry uses the model's exact type identifier. Because colon-separated names
are not JavaScript identifiers, these keys are quoted, for example:

```js
"chemistry:mixed-solutions": () => import("./my_plugin/MixedSolutionPanel.vue"),
```

The panel receives two props, `item_id` and `itemType`, and reads/writes the item through the
Vuex store — exactly like the built-in information components:

```js
computed: {
  itemData() {
    return this.$store.state.all_item_data[this.item_id] || {};
  },
},
methods: {
  updateField(name, value) {
    this.$store.commit("updateItemData", { item_id: this.item_id, item_data: { [name]: value } });
  },
},
```

Reuse datalab's building blocks rather than rebuilding them, imported via the `@/components/…`
alias: `ItemSelect` (item search), `FormattedItemName` (the type-coloured item badge + link),
`TooltipIcon`, and so on. The separate
[`datalab-item-plugin-example-custom-vue`](https://github.com/Matgenix/datalab-item-plugin-example-custom-vue)
repository provides a complete `MixedSolutionPanel.vue`: it references solution items from the
companion schema-only example, pulls their concentrations via `getItemData`, and computes the
resulting mixture live — none of which the core panel can do on its own.

!!! warning "Custom panels are trusted, compiled code"
    Panel `.vue` files are compiled into the webapp bundle and run in every user's browser, so
    installing or updating a UI plugin means rebuilding the frontend. The Docker commands above
    perform collection before the development or production frontend is compiled. Only install
    panels from sources you trust.

## Webapp components

A plugin can ship Vue components by placing a `webapp/` folder containing an `index.js` manifest
inside its Python package. The manifest declares components for two extension points: `blocks`,
keyed by blocktype, and `itemPanels`, keyed by the complete canonical item type identifier, e.g.
`example:mixed-solutions`:

```js
// my_plugin/webapp/index.js
export default {
  apiVersion: 1,
  blocks: {
    my_block: () => import("./MyBlock.vue"),
  },
  itemPanels: {},
};
```

The whole folder is collected into the webapp by `invoke dev.install` (as for custom panels above),
so components can import each other relatively and datalab's own components via `@/…`. A block
component receives `item_id` and `block_id` props and typically wraps `DataBlockBase`. Plugin
blocks cannot replace built-in block components, and a manifest takes precedence over the
`<ClassName>Panel.vue` convention for its package.
The plugin's `pyproject.toml` must include the folder as package data.

A plugin can declare npm dependencies with a `package.json` (requiring `name` and `version`)
in the same folder. Each collected plugin becomes a [yarn workspace](https://classic.yarnpkg.com/en/docs/workspaces/)
of the webapp, and `invoke dev.install` runs `yarn install --pure-lockfile`, which keeps the
webapp's locked versions without writing the plugin's dependencies into `yarn.lock`. Versions
that conflict with the webapp's are installed alongside it for the plugin alone. Packages that
must be shared with the webapp (`vue`, `vuex`, `vue-router`, `primevue`, `@primeuix/themes`,
`@bokeh/bokehjs` and `@fortawesome/*`) may only be listed under `peerDependencies`:

```json
{
  "name": "my-plugin-webapp",
  "version": "0.1.0",
  "private": true,
  "dependencies": { "markdown-it": "^14.1.0" },
  "peerDependencies": { "vue": "^3.5.0" }
}
```
