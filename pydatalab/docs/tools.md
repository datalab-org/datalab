# Using tools

Tools are optional applications for analysing, comparing, or otherwise working
with data in datalab. Unlike a [data block](blocks/index.md), which displays data
attached to one item, a tool can work across several items or provide a complete
working environment.

This page explains how signed-in users open and use tools. Deployment
administrators should start with [Installing and maintaining plugins](plugins.md#installing-and-maintaining-plugins),
and developers with [Developing tool plugins](plugin-development/tool-plugin.md).

## Open a tool

An installed tool can provide either or both of these entry points:

1. To start without a selection, click **Tools** in the main navigation. Choose
   a tool from the quick list, or choose **All tools** to open the complete
   catalog.
2. To start with existing items, select rows in a supported table and choose the
   tool's action from the selected-items menu. Tools decide which tables and
   selection sizes they support, so an action may not appear for every table or
   selection.

If a tool is missing, first clear the current selection and check **All tools**.
The tool may also be unavailable to your account, disabled for this deployment,
or not installed; ask the deployment administrator if it is still absent.

Selected-items actions pass only the items' immutable refcodes. The tool then
loads the current data through permission-aware datalab interfaces. Items you
cannot access are not exposed to the tool.

## Tool types

| Type | Where it opens | What to expect |
|---|---|---|
| **In-app tool** | Below the normal datalab navigation | A focused interface that behaves like part of datalab |
| **Standalone tool** | A separate application, usually in a new tab | A complete application or working environment with its own interface |

Both types use your current datalab identity and normal data permissions. A
standalone tool receives temporary, non-administrator access. Its session can
expire or be replaced when you relaunch the same tool. A trusted provider may
instead reuse an eligible existing session or create independent concurrent
sessions; those sessions still have the same user-level authority and expiry
limits. With an explicit trusted confirmation, a provider may also extend an
eligible reused session within datalab's rolling and absolute lifetime limits.
If a tool reports an expired session or HTTP 401, return to datalab and launch
it again.

Do not share a standalone tool's launch URL. It can contain a short-lived,
single-use code intended only for the application you opened. Long-lived item
access, such as a QR code for a physical sample, must be created in datalab
rather than through a tool.

Tool plugins are trusted extensions selected by the deployment administrator.
In particular, an in-app tool runs administrator-approved JavaScript inside the
signed-in datalab application.

## Available tool documentation

The tools installed on an instance vary. The following companion tools document
their own behavior:

- [Item comparison](https://matgenix.github.io/datalab-item-comparison-tool/)
  compares metadata and data blocks for selected items in datalab.
- [datalab-jupyter](https://github.com/Matgenix/datalab-jupyter#using-jupyterlab)
  opens JupyterLab as a standalone tool and can create a notebook for selected
  items.

For another tool, follow the documentation linked by its maintainers or contact
the administrator who installed it.
