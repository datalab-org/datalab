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
data the user can access. A standalone tool token retains the user's identity,
ownership, and group-based access, but never delegates role-based administrator
elevation.

Tool plugins are trusted extensions. In particular, an in-app tool runs
administrator-approved JavaScript inside the signed-in datalab application.
Deployment administrators must review a plugin and its dependencies before
installing it.

## Opening a tool

Tools can provide one or both of these entry points:

- **Tools menu:** click **Tools** in the main navigation for a quick list, or
  choose **All tools** for the complete catalog. This is useful for tools that
  start without a particular item selection.
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
external JupyterHub. It supports normal launches and an **Open in notebook**
selected-items action. Its repository documents installation, notebook
behavior, deployment, and security; the generic tool ordering and disabling
settings remain in [server configuration](config.md#tools).
