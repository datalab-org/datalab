<!-- This file was edited with the assistance of an AI model and requires human review from the contributor. -->
# datalab-chat-plugin

An example plugin that ships a block's Vue component via a webapp manifest
(`datalab_chat_plugin/webapp/index.js`). See `pydatalab/docs/plugins.md`.

Install it by adding the following to `plugins.toml` at the repository root,
then running `uv run invoke dev.install` from `pydatalab/`:

```toml
dependencies = ["datalab-chat-plugin"]

[tool.uv.sources]
datalab-chat-plugin = { path = "examples/datalab-chat-plugin" }
```

The server-side `ChatBlock` still lives in core datalab, and the npm packages
used by `MessageBubble.vue` (`markdown-it`, `highlight.js`, `mermaid`)
remain in the core webapp's `package.json` until plugins can declare their
own webapp dependencies.
