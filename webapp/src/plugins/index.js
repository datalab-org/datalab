// Stable entry point for plugin-contributed components.
// The actual registry is written to `panels.generated.js` (gitignored) by
// `invoke dev.collect-plugin-panels`; this shim tolerates its absence so the
// webapp builds from a fresh clone with no plugins installed.
//
// The registry exports `PLUGINS`, a list of plugin manifests (each a plugin's
// `webapp/index.js`), and `PLUGIN_PANELS`, item panels found via the legacy
// `<ClassName>Panel.vue` naming convention. Both are merged into the two
// extension points below, keyed by item type and blocktype respectively.
const PLUGIN_API_VERSION = 1;

let generatedModule = {};
const generated = require.context(".", false, /panels\.generated\.js$/);
if (generated.keys().includes("./panels.generated.js")) {
  generatedModule = generated("./panels.generated.js");
}

const manifests = [
  ...(generatedModule.PLUGINS || []),
  { apiVersion: PLUGIN_API_VERSION, itemPanels: generatedModule.PLUGIN_PANELS || {} },
];

export const PLUGIN_PANELS = {};
export const PLUGIN_BLOCKS = {};

for (const manifest of manifests) {
  if (manifest.apiVersion !== PLUGIN_API_VERSION) {
    console.warn(
      `Ignoring plugin manifest with apiVersion ${manifest.apiVersion}; expected ${PLUGIN_API_VERSION}.`,
    );
    continue;
  }
  Object.assign(PLUGIN_PANELS, manifest.itemPanels || {});
  Object.assign(PLUGIN_BLOCKS, manifest.blocks || {});
}
