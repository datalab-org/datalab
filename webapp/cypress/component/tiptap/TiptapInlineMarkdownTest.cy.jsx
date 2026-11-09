import TiptapInline from "@/components/TiptapInline.vue";
import { createStore } from "vuex";

/**
 * Regression tests for the Markdown/Preview toggle.
 *
 * The component and the MarkdownToggle extension each track whether the editor
 * is in Markdown mode. They used to drift apart: nothing told the extension
 * about the trip back to Preview, so its flag stuck on and every later toggle
 * re-used the Markdown cached by the first conversion.
 *
 * These drive the real switch rather than the commands underneath it, because
 * the bug lived in the handshake between the two and not in either half.
 */
describe("TiptapInline - Markdown/Preview toggle", () => {
  let store;

  beforeEach(() => {
    store = createStore({ state: {}, mutations: {}, getters: {} });
  });

  const mountEditor = (modelValue) =>
    cy.mount(TiptapInline, {
      props: { modelValue },
      global: { plugins: [store] },
    });

  // The toolbar only appears once the editor has focus.
  const showToolbar = () => cy.get(".ProseMirror").click();

  // Bootstrap's custom switch hides the real checkbox, so click its label.
  const toggleMarkdown = () => cy.get('label[for="markdownToggleSwitch"]').click();

  // Scoped by placeholder: MermaidModal also renders a (hidden) textarea.
  const markdownInput = () => cy.get('textarea[placeholder="Edit in Markdown..."]');

  it("shows the current document each time Markdown is opened", () => {
    mountEditor("<p>First version</p>");
    showToolbar();

    toggleMarkdown();
    markdownInput().should("have.value", "First version");

    // Back to Preview, then change the document.
    toggleMarkdown();
    cy.get(".ProseMirror p").type("{selectall}{del}Second version");

    // Re-opening Markdown must re-serialise rather than replay the first
    // conversion, which is what the original bug did.
    toggleMarkdown();
    markdownInput().should("have.value", "Second version");
  });

  it("applies Markdown edits when switching back to Preview", () => {
    mountEditor("<p>Original</p>");
    showToolbar();

    toggleMarkdown();
    markdownInput().clear().type("## Edited in Markdown");

    toggleMarkdown();
    cy.get(".ProseMirror h2").should("contain.text", "Edited in Markdown");
  });

  it("survives repeated toggling without losing content", () => {
    mountEditor("<p>Durable content</p>");
    showToolbar();

    for (let i = 0; i < 3; i += 1) {
      toggleMarkdown();
      markdownInput().should("have.value", "Durable content");
      toggleMarkdown();
      cy.get(".ProseMirror p").should("contain.text", "Durable content");
    }
  });

  it("leaves the document untouched when Markdown is only viewed", () => {
    // Alignment is deliberately not serialised to Markdown, so it stands in for
    // anything the converter cannot represent. Merely looking at the Markdown
    // must not push the document through the converter and drop it.
    mountEditor('<p style="text-align: center">Centred paragraph</p>');
    showToolbar();

    cy.get(".ProseMirror p").should("have.attr", "style").and("include", "text-align: center");

    toggleMarkdown();
    toggleMarkdown();

    cy.get(".ProseMirror p").should("have.attr", "style").and("include", "text-align: center");
  });
});
