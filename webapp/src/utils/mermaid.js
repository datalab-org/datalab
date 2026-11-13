// Mermaid is large and only needed to render diagrams, so it is loaded (and initialised) on first
// use, in its own chunk.
let mermaidPromise = null;

export function loadMermaid() {
  if (!mermaidPromise) {
    mermaidPromise = import("mermaid")
      .then(({ default: mermaid }) => {
        mermaid.initialize({
          startOnLoad: false,
          theme: "default",
          securityLevel: "sandbox",
        });
        return mermaid;
      })
      .catch((error) => {
        // Allow a retry, e.g., after a network error
        mermaidPromise = null;
        throw error;
      });
  }
  return mermaidPromise;
}
