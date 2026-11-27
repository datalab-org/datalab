// BokehJS is large and only needed to render plots, so it is loaded on first use, in its own chunk.
// The package's default entry point additionally pulls in the WebGL, API and MathJax modules
// (~10 MB of `mathjax-full` alone), none of which are used by our plots, so the three modules
// matching the old CDN bundles are imported directly instead. The widget and table modules
// register their models with the Bokeh model registry when loaded.
let bokehPromise = null;

export function loadBokeh() {
  if (!bokehPromise) {
    bokehPromise = Promise.all([
      import("@bokeh/bokehjs/build/js/lib/main"),
      import("@bokeh/bokehjs/build/js/lib/models/widgets/main"),
      import("@bokeh/bokehjs/build/js/lib/models/widgets/tables/main"),
    ])
      .then(([Bokeh]) => Bokeh)
      .catch((error) => {
        // Allow a retry, e.g., after a network error
        bokehPromise = null;
        throw error;
      });
  }
  return bokehPromise;
}
