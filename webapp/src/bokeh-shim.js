// Bokeh is loaded as a global (`window.Bokeh`) by the CDN <script> tags in
// index.html. Under webpack this was wired up via `externals: { bokeh: "Bokeh" }`;
// under Vite we alias the bare `bokeh` import (see vite.config.js) to this shim
// so that `import Bokeh from "bokeh"` resolves to the CDN global in both the dev
// server and production builds. The CDN scripts are render-blocking and live in
// <head>, so `window.Bokeh` is defined before the (module/deferred) app runs.
export default window.Bokeh;
