import TiptapInline from "@/components/TiptapInline.vue";
import { createStore } from "vuex";

describe("TiptapInline - TinyMCE HTML Compatibility", () => {
  let store;

  beforeEach(() => {
    store = createStore({
      state: {},
      mutations: {},
      getters: {},
    });
  });

  it("renders basic formatting from TinyMCE HTML", () => {
    const tinyMCEHtml = `<p><strong>Bold text</strong> and <em>italic text</em> and <u>underlined text</u> and <s>strikethrough</s></p>`;

    cy.mount(TiptapInline, {
      props: {
        modelValue: tinyMCEHtml,
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror").should("contain.html", "<strong>Bold text</strong>");
    cy.get(".ProseMirror").should("contain.html", "<em>italic text</em>");
    cy.get(".ProseMirror").should("contain.html", "<u>underlined text</u>");
    cy.get(".ProseMirror").should("contain.html", "<s>strikethrough</s>");
  });

  it("renders headings from TinyMCE HTML", () => {
    const tinyMCEHtml = `<h1>Heading 1</h1><h2>Heading 2</h2><h3>Heading 3</h3>`;

    cy.mount(TiptapInline, {
      props: {
        modelValue: tinyMCEHtml,
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror h1").should("contain.text", "Heading 1");
    cy.get(".ProseMirror h2").should("contain.text", "Heading 2");
    cy.get(".ProseMirror h3").should("contain.text", "Heading 3");
  });

  it("renders lists from TinyMCE HTML", () => {
    const tinyMCEHtml = `<ul><li>Item 1</li><li>Item 2</li></ul><ol><li>First</li><li>Second</li></ol>`;

    cy.mount(TiptapInline, {
      props: {
        modelValue: tinyMCEHtml,
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror ul li").should("have.length", 2);
    cy.get(".ProseMirror ul li").first().should("contain.text", "Item 1");
    cy.get(".ProseMirror ol li").should("have.length", 2);
    cy.get(".ProseMirror ol li").first().should("contain.text", "First");
  });

  it("renders links from TinyMCE HTML", () => {
    const tinyMCEHtml = `<p>Visit <a href="https://example.com" target="_blank">this link</a></p>`;

    cy.mount(TiptapInline, {
      props: {
        modelValue: tinyMCEHtml,
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror a")
      .should("have.attr", "href", "https://example.com")
      .and("have.attr", "target", "_blank")
      .and("contain.text", "this link");
  });

  it("renders images from TinyMCE HTML", () => {
    const tinyMCEHtml = `<p><img src="https://example.com/image.png" alt="Test image" /></p>`;

    cy.mount(TiptapInline, {
      props: {
        modelValue: tinyMCEHtml,
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror img")
      .should("have.attr", "src", "https://example.com/image.png")
      .and("have.attr", "alt", "Test image");
  });

  it("renders tables from TinyMCE HTML", () => {
    const tinyMCEHtml = `
      <table>
        <thead>
          <tr>
            <th>Header 1</th>
            <th>Header 2</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Cell 1</td>
            <td>Cell 2</td>
          </tr>
        </tbody>
      </table>
    `;

    cy.mount(TiptapInline, {
      props: {
        modelValue: tinyMCEHtml,
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror table").should("exist");
    cy.get(".ProseMirror th").should("have.length", 2);
    cy.get(".ProseMirror th").first().should("contain.text", "Header 1");
    cy.get(".ProseMirror td").should("have.length", 2);
    cy.get(".ProseMirror td").first().should("contain.text", "Cell 1");
  });

  it("renders colored text from TinyMCE HTML", () => {
    const tinyMCEHtml = `<p><span style="color: rgb(255, 0, 0);">Red text</span></p>`;

    cy.mount(TiptapInline, {
      props: {
        modelValue: tinyMCEHtml,
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror span").should("have.attr", "style").and("include", "color");
  });

  it("renders horizontal rules from TinyMCE HTML", () => {
    const tinyMCEHtml = `<p>Before</p><hr /><p>After</p>`;

    cy.mount(TiptapInline, {
      props: {
        modelValue: tinyMCEHtml,
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror hr").should("exist");
  });

  it("renders cross-references from datalab HTML", () => {
    const datalabHtml = `<p>See sample <span data-type="crossreference" data-item-id="sample1" data-item-type="samples" data-name="Test Sample" data-chemform="H2O"></span> for details</p>`;

    cy.mount(TiptapInline, {
      props: {
        modelValue: datalabHtml,
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror .cross-reference-wrapper").should("exist");
    cy.get(".formatted-item-name").should("contain.text", "sample1");
  });

  it("renders complex nested formatting from TinyMCE HTML", () => {
    const tinyMCEHtml = `
      <h2>Complex Document</h2>
      <p>This is a <strong>bold and <em>italic</em></strong> text with <a href="https://example.com">a link</a>.</p>
      <ul>
        <li><strong>Bold list item</strong></li>
        <li><em>Italic list item</em></li>
      </ul>
      <table>
        <tr>
          <td><strong>Bold cell</strong></td>
          <td><span style="color: rgb(0, 0, 255);">Blue cell</span></td>
        </tr>
      </table>
    `;

    cy.mount(TiptapInline, {
      props: {
        modelValue: tinyMCEHtml,
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror h2").should("contain.text", "Complex Document");
    cy.get(".ProseMirror strong").should("exist");
    cy.get(".ProseMirror em").should("exist");
    cy.get(".ProseMirror a").should("have.attr", "href");
    cy.get(".ProseMirror ul li").should("have.length", 2);
    cy.get(".ProseMirror table td").should("have.length", 2);
  });

  it("handles empty content gracefully", () => {
    cy.mount(TiptapInline, {
      props: {
        modelValue: "",
      },
      global: {
        plugins: [store],
      },
    });

    cy.get(".ProseMirror").should("exist");
  });
});
