# Plugins

*datalab* supports plugins that extend the server with new functionality, in
particular:

- New data block types, which render interactive views of attached files in item
  detail pages.
- Custom item types, which are served through the same generic endpoints as the built-in `samples`, `cells`, `starting_materials` and `equipment` types.

Some self-declared plugins can be found via the [`datalab-plugin` topic on GitHub](https://github.com/topics/datalab-plugin), in lieu of a formal registry at this time.
Plugins can also be kept private and installed from e.g., a private git repository, or a local path on the host, using the same installation described below.

!!! warning "Only install plugins you trust"
    Plugins are installed into the same Python environment as the *datalab* server and run with full server privileges. Only install plugins from sources you trust.

## What a plugin is

At present, a *datalab* plugin is a Python package that registers one or more [data block](blocks/index.md) classes or item types via a Python entry point.
Data blocks ingest a file (or set of files) attached to an item and render an interactive view of the parsed data, e.g. an NMR spectrum, an electrochemistry cycler trace, or an XRD pattern.
Plugins (and deployments) can also register **custom item types**, new top-level item models served through the generic item endpoints (see [below](#custom-item-types)). Further plugin types, e.g., ingestion hooks and webapp components, are planned in the future (see [roadmap.md](roadmap.md)); please reach out if you have a specific use case.
*datalab* discovers them at server startup by enumerating the relevant entry point group, with no changes required to the core code.

## Writing a plugin

The recommended starting point is the [Copier](https://copier.readthedocs.io/) template at [datalab-org/datalab-app-plugin-template](https://github.com/datalab-org/datalab-app-plugin-template), which scaffolds a minimal data block plugin together with the packaging boilerplate (entry point declaration, test scaffolding, and a working `pyproject.toml`).
Rather than forking the repository, you should use it directly with Copier to
generate a new plugin repository; see the README in the [datalab-org/datalab-app-plugin-template](https://github.com/datalab-org/datalab-app-plugin-template) repository for full instructions.

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
