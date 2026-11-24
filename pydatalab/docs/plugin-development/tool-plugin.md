# Developing tool plugins

A tool plugin is an independently packaged, trusted extension that registers an
application in datalab's Tools catalog. This guide is the shared development
path for both supported UI types. Follow it first, then use the
[in-app](in-app-tool-plugin.md) or [standalone](standalone-tool-plugin.md)
tutorial for a complete minimal implementation.

For other audiences, see [Using tools](../tools.md) or
[Installing and maintaining plugins](../plugins.md#installing-and-maintaining-plugins).

## Choose the UI type

| | In-app | Standalone |
|---|---|---|
| UI location | Inside datalab, below its navigation | A separate page or service |
| Data access | Frontend SDK and the browser session | Temporary tool access token |
| Best for | Focused interfaces that should feel native to datalab | Complete applications and working environments |
| Additional deployment | None beyond the plugin package | Required when `launch()` targets a separate service |

Choose in-app unless the tool needs to own its full page, runtime, or service.
Both types execute trusted Python in the datalab API process. In-app tools also
execute their reviewed JavaScript bundle in the signed-in datalab page.

## Create the project

Generate a repository from the Copier template rather than forking it:

```shell
uvx copier copy --trust \
  https://github.com/Matgenix/datalab-tool-plugin-template \
  ../my-datalab-tool
cd ../my-datalab-tool
```

Copier asks for the display name, stable tool ID, Python distribution name, UI
type, browser open mode, and optional selected-items action. Treat the tool ID
as permanent once released: it is used by entry points, configuration, URLs,
and delegated credentials.

Install the generated development environment and run its initial checks:

```shell
uv sync --locked --all-extras --dev
uv run pytest
uv run pre-commit run --all-files
```

For an in-app tool, build the generated frontend after each frontend change:

```shell
cd frontend
corepack yarn install --frozen-lockfile
corepack yarn build
cd ..
```

Commit both `frontend/yarn.lock` and the generated
`src/<package>/static/frontend/tool.js`; they are reviewed and shipped as part
of the trusted plugin.

The generated project keeps its answers in `.copier-answers.yml`. To incorporate
a later template release, run `uvx copier update`, review and resolve the diff,
rebuild the frontend if present, and rerun all checks.

## Implement the provider

The Python distribution exposes a zero-argument `ToolProvider` subclass through
an entry point:

```toml
[project.entry-points."pydatalab.tools"]
example-tool = "example_tool.provider:ExampleToolProvider"
```

The entry-point name must equal the provider's lowercase, hyphenated `id` class
attribute. The provider declares immutable `ToolMetadata` and can define:

- `launch(context, grants)`: return `None` for an in-app tool, or the HTTP(S)
  launch URL for a standalone tool;
- `is_available(context)`: decide whether the current user can see and launch
  the tool and access its browser-authenticated provider routes; and
- `blueprint`: expose provider-owned Flask routes.

datalab discovers providers once when the API starts. A provider that fails to
load is logged and skipped; duplicate IDs are rejected. Restart the API after
installing, removing, or changing a plugin package.

Keep `is_available()` small and reliable. It is evaluated for catalog
visibility, launch permission, and every browser-authenticated provider route;
an exception denies access. It is not evaluated for service-authenticated
routes because those requests have no browser `ToolContext`.

### Provider routes and data permissions

Add routes only through the provider blueprint. datalab mounts it below
`/tools/plugins/<tool-id>/` for each supported API alias and applies the route's
declared authentication policy:

- The default browser policy requires an active browser session, verifies
  provider availability, and validates the origin of non-safe requests.
- `ToolRouteAuth.SERVICE` is for machine-to-machine calls. The provider must
  implement `authenticate_service_request()` and authorize the client again as
  required by each handler.

Automatic route authentication decides who may enter a route; it does not add
object-level permission filters to arbitrary database queries. Load data through
the normal datalab API or explicitly use permission-aware server services.

| Interface | Authentication owner | Data-permission owner |
|---|---|---|
| Core catalog and launch endpoints | datalab | datalab and provider availability |
| `launch()` and `is_available()` callbacks | Protected core route | Restricted provider context |
| Provider blueprint route | datalab browser policy or provider service policy | Plugin, using permission-aware interfaces |
| Separately hosted service | External service | Normal datalab API called with the temporary token |

Direct Flask app registration and changes to core blueprints are unsupported.
The canonical endpoints are `GET /v0.1/info/tools`,
`POST /v0.1/tools/<tool-id>/launch`, and provider routes below
`/v0.1/tools/plugins/<tool-id>/...`.

## Add a selected-items action

Either UI type can contribute an action to item tables:

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

Supported table IDs are `samples`, `inventory`, `equipment`, and
`collection-items`. Limits must satisfy
`1 <= min_items <= max_items <= 100`.

datalab passes an ordered, deduplicated list of immutable refcodes, never item
names, database IDs, blocks, or complete table rows. Treat the selection as
untrusted input and reload each item through a permission-aware interface.

An in-app tool reads the action and refcodes from the SDK:

```javascript
const { actionId, itemRefcodes } = sdk.selection.current();
```

A standalone tool receives the validated action and refcodes in its launch
exchange result. A Tools-menu launch has no selection. The
[item comparison tool](https://github.com/Matgenix/datalab-item-comparison-tool)
is a production-sized in-app example;
[`datalab-jupyter`](https://github.com/Matgenix/datalab-jupyter) demonstrates a
standalone **Open in notebook** action.

## Complete the UI-specific implementation

For an in-app tool, the provider serves one compiled frontend entry point. The
bundle synchronously registers its component with
`window.datalabToolSdk.register(ToolView)`. Use the versioned SDK for
authenticated API calls, navigation, host components, dialogs, and selection;
do not import private webapp stores or source paths. Continue with the
[in-app tutorial](in-app-tool-plugin.md).

For a standalone tool, `launch()` issues a single-use launch code and returns a
URL. The external page exchanges the code for a temporary, tool-bound credential
and calls normal datalab API endpoints. The exchange, token handling,
relaunch behavior, and browser-versus-service authentication rules are security
critical; implement them exactly as shown in the
[standalone tutorial](standalone-tool-plugin.md).

Trusted provider code can bind a delegated-session policy to each launch grant.
The default policy replaces other sessions for the same user and provider;
exchange clients cannot choose the policy. See the standalone tutorial for
canonical reuse, independent-session semantics, and optional explicit renewal.
Renewal requires both grant-bound provider permission and a trusted exchange
request; retaining a candidate token and presenting any user confirmation are
responsibilities of the standalone service.

## Test and run locally

Keep provider tests independent of a running datalab instance where possible.
At minimum, test metadata and UI kind, entry-point/provider construction,
availability decisions, launch behavior, selection constraints, and every
provider route's authentication and permission behavior. In-app projects should
also build the frontend in CI.

To exercise the tool in datalab, add the generated distribution as an editable
path in the datalab checkout's root `plugins.toml`, following the generated
`INSTALL.md`, then run:

```shell
cd pydatalab
uv run invoke dev.install
```

Restart the native API, or rebuild the development Compose stack with
`docker compose --profile dev up --build`. Sign in as a normal user, confirm the
Tools-menu launch, and test every declared table action at its minimum and
maximum selection sizes. The UI-specific tutorials provide concrete
`plugins.toml` examples and troubleshooting tables.

## Package and distribute

Before publishing a release:

1. Write user instructions for the tool's normal workflow and a plugin-specific
   deployment guide containing the exact distribution name, extras, settings,
   and any companion services.
2. Run the Python tests, frontend build if present, and pre-commit checks.
3. Run `uv build` and inspect the wheel to ensure package data, including the
   in-app bundle or standalone static page, is present.
4. Tag a semantic version and publish an immutable release artifact. State the
   compatible datalab versions and preserve upgrade notes in the changelog.

For a separately hosted standalone application, version its service artifact
alongside the provider and document health checks, storage and retention,
resource limits, credentials, and any privileged host resources. Administrators
must opt into that service explicitly; installing the provider never starts it.
The production boundary is defined in
[Plugin-provided standalone services](../deployment.md#plugin-provided-standalone-services).

Never place secrets, launch codes, tool access tokens, or user data in examples,
logs, release artifacts, or committed configuration.
