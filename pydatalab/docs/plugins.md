# Plugins

*datalab*'s plugin system is under active development, as is this documentation
page.
The most mature plugin type are custom application data blocks, a template repository for which can be found at [datalab-org/datalab-app-plugin-template](https://github.com/datalab-org/datalab-app-plugin-template).

## Installing plugins

Plugins are declared in a `plugins.toml` file at the root of `pydatalab/`. The format mirrors the relevant fragments of `pyproject.toml`:

```toml
# pydatalab/plugins.toml
dependencies = [
    "datalab-app-plugin-insitu",
    "my-local-plugin",
]

[tool.uv.sources]
# Pin to a specific git ref:
datalab-app-plugin-insitu = { git = "https://github.com/datalab-org/datalab-app-plugin-insitu.git", rev = "v0.4.1" }
# Or point at a local checkout (paths are resolved relative to pydatalab/):
my-local-plugin = { path = "../../my-local-plugin", editable = true }
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

The same `invoke dev.install` task is used by the production Docker image (`.docker/server/Dockerfile`): a `plugins.toml` at `pydatalab/plugins.toml` is picked up automatically at build time, so plugins can be baked into a custom image without modifying the Dockerfile itself. It can also be invoked from the [*datalab* Ansible role](https://github.com/datalab-org/datalab-ansible-terraform) to provision plugins on a deployed server — drop a `plugins.toml` next to the checked-out `pydatalab/` directory and run the install task as part of the deployment playbook.
