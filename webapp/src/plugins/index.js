// Stable entry point for plugin-contributed panel components.
// The actual registry is written to `panels.generated.js` (gitignored) by
// `datalab-collect-plugin-panels`; this shim tolerates its absence so the
// webapp builds from a fresh clone with no plugins installed.
let panels = {};
const generated = require.context(".", false, /panels\.generated\.js$/);
if (generated.keys().includes("./panels.generated.js")) {
  panels = generated("./panels.generated.js").PLUGIN_PANELS || {};
}
export const PLUGIN_PANELS = panels;
