# Tools

Tools are optional applications for analysing, comparing, or otherwise working
with data in datalab. Unlike a [data block](blocks/index.md), which displays
data attached to one item, a tool can work across several items or provide a
complete working environment.

Possible tools include:

- comparing measurements from several samples;
- summarising the items visible to a user;
- checking data quality or producing a report; and
- exploring data programmatically in a notebook.

## Tool types

datalab supports two kinds of tool user interface:

| Tool type | Where it appears | Typical use |
|---|---|---|
| **In-app tool** | Inside the datalab web application, below the normal navigation bar | A focused interface that should feel like part of datalab |
| **Standalone tool** | In a separate page or application, normally opened in a new browser tab | A complete application or working environment with its own interface |

An in-app tool can use datalab's frontend integration to request data as the
signed-in user. A standalone tool can receive temporary access to the datalab
API for that user. In both cases, normal datalab permissions determine which
data the user can access.

Tool plugins are trusted extensions. In particular, an in-app tool runs
administrator-approved JavaScript inside the signed-in datalab application.
Deployment administrators must review a plugin and its dependencies before
installing it.

## Opening a tool

Tools can provide one or both of these entry points:

- **Tools menu:** open a tool directly from the main navigation. This is useful
  for tools that start without a particular item selection.
- **Selected-items action:** select one or more rows in a supported table, then
  choose the tool's action from the selected-items menu. The tool receives the
  selected items' immutable refcodes and loads the current data through
  permission-aware API routes.

Selected-items actions use the same ordered list of immutable refcodes for
in-app and standalone tools. A tool chooses which tables and selection sizes it
supports; it does not appear in tables for which it has not opted in.

Deployment administrators can configure one consistent tool order for the
navigation menu, Tools page, and selected-items actions with `TOOLS.ORDER`.
Tools omitted from that list follow alphabetically by stable tool ID. See
[server configuration](config.md#tools) for the configuration syntax.

## Tool plugins

A tool is installed as a [tool plugin](plugins.md#writing-a-tool-plugin).
Installed plugins use the same Tools menu and selected-items integration.

**JupyterLab** is provided by the companion
[`datalab-jupyter`](https://github.com/Matgenix/datalab-jupyter) plugin. It is a
standalone tool that can use the Compose-managed JupyterHub image or a compatible
external JupyterHub.

When JupyterLab is opened from the Tools menu, it opens normally. When it is
opened with **Open in notebook** after selecting 1–20 rows in Samples,
Inventory, Equipment, or a collection's item table, it creates a new notebook
for that selection. The notebook contains a visible initialization cell that:

- stores the selected refcodes in `selected_item_refcodes`;
- loads accessible item dictionaries into `selected_items`; and
- records inaccessible or deleted refcodes in `selected_item_errors`.

The cell runs automatically once when the notebook is created. It remains
editable and can be rerun after restarting its kernel or reopening the notebook
with a fresh kernel. Other notebooks and consoles continue to preload only
`datalab` and `current_user`.

See [server configuration](config.md#tools) for installation settings and
[JupyterHub deployment](deployment.md#optional-jupyterhub-tool) for deployment
and security details.
