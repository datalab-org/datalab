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

For custom item types, use the
[`Matgenix/datalab-item-plugin-template`](https://github.com/Matgenix/datalab-item-plugin-template).
Its generated repositories retain `.copier-answers.yml`, so template improvements can be applied
later with `uvx copier update`. Two worked repositories demonstrate the supported rendering paths:

- [`datalab-item-plugin-example`](https://github.com/Matgenix/datalab-item-plugin-example)
  uses schema annotations and requires no plugin JavaScript.
- [`datalab-item-plugin-example-custom-vue`](https://github.com/Matgenix/datalab-item-plugin-example-custom-vue)
  provides a custom Vue panel and references the first example's `solutions` items.

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
4. Collects any custom Vue panels into the webapp when run from a complete source checkout.

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

### Rendering a custom type in the web UI

The web UI renders a custom type's extra fields automatically. On startup the frontend reads `/info/types`, registers every custom type,
and on the edit page shows:

- the **base item component** — the same name / refcode / relationships block used by the
  built-in type the model inherits from; and
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
| `datalab_ui_hidden_fields` | base-component sections to hide (`status`, `collections`, `description`, `substance_information`, `synthesis_information`) |
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
    type: Literal["solutions"] = "solutions"

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

Thus, entering `1000 mmol/L` above stores `concentration: 1.0`. The optional companion field keeps
the user's display choice, so the item reopens as `1000 mmol/L`; without it, the UI uses the default
display unit.

Plugin authors choose the canonical unit and provide correct conversions; Datalab validates and
applies them. Changing the canonical unit requires a data migration. Conversions that are not a
fixed scale and offset require a custom panel.

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
repository provides a complete `MixedSolutionPanel.vue`: it references `solutions` items from the
companion schema-only example, pulls their concentrations via `getItemData`, and computes the
resulting mixture live — none of which the core panel can do on its own.

!!! warning "Custom panels are trusted, compiled code"
    Panel `.vue` files are compiled into the webapp bundle and run in every user's browser, so
    installing or updating a UI plugin means rebuilding the frontend. The Docker commands above
    perform collection before the development or production frontend is compiled. Only install
    panels from sources you trust.

## Plugin installation

The same `invoke dev.install` task is used by both Docker API images (`.docker/server/Dockerfile`): a `plugins.toml` at the repository root is picked up automatically at build time, and both frontend profiles collect panels from the corresponding plugin-enabled API image. Plugins can therefore be baked into a complete deployment without modifying either Dockerfile.
It will also be invoked from the [*datalab* Ansible role](https://github.com/datalab-org/datalab-ansible-terraform) to provision plugins on a deployed server when a `plugins.toml` is provided; see the role documentation for details.
