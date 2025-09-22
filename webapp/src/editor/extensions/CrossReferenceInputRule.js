import { Extension } from "@tiptap/core";
import { Plugin, PluginKey } from "@tiptap/pm/state";
import { createApp } from "vue";
import ItemSelect from "@/components/ItemSelect.vue";

let suggestionApp = null;
let suggestionEl = null;

export const CrossReferenceInputRule = Extension.create({
  name: "crossReferenceInputRule",

  addOptions() {
    return {
      suggestion: {
        char: "@",
        pluginKey: new PluginKey("crossReferenceSuggestion"),
        allowSpaces: false,
        startOfLine: false,
        command: ({ editor, range, props }) => {
          editor
            .chain()
            .focus()
            .insertContentAt(range, [
              {
                type: "crossreference",
                attrs: {
                  itemId: props.item_id,
                  itemType: props.type || "samples",
                  name: props.name || "",
                  chemform: props.chemform || "",
                },
              },
              { type: "text", text: " " },
            ])
            .run();
        },
      },
    };
  },

  addProseMirrorPlugins() {
    const { suggestion } = this.options;
    const editor = this.editor;
    return [createSuggestionPlugin(suggestion, editor)];
  },
});

function createSuggestionPlugin(options, editor) {
  const pluginKey = options.pluginKey;

  return new Plugin({
    key: pluginKey,

    state: {
      init() {
        return { active: false, query: null, range: null };
      },

      apply(tr, prev, oldState, newState) {
        const { selection } = newState;
        const { empty, from } = selection;
        if (!empty) return { ...prev, active: false };
        const $pos = selection.$from;
        const textBefore = $pos.parent.textContent.slice(0, $pos.parentOffset);
        const match = textBefore.match(/@(\w*)$/);
        if (!match) {
          hideSuggestions();
          return { ...prev, active: false };
        }
        const query = match[1];
        const range = { from: from - match[0].length, to: from };
        return { active: true, query, range };
      },
    },

    view() {
      return {
        update(view) {
          const state = pluginKey.getState(view.state);
          if (state?.active && state.query !== null) {
            showSuggestions(view, state, options, editor);
          } else {
            hideSuggestions();
          }
        },
        destroy() {
          hideSuggestions(true);
        },
      };
    },
  });
}

function showSuggestions(view, state, options, editor) {
  if (!suggestionEl) {
    suggestionEl = document.createElement("div");
    suggestionEl.className = "dropdown-menu show p-2 tiptap-suggestions";
    document.body.appendChild(suggestionEl);
  }

  if (!suggestionApp) {
    suggestionApp = createApp(ItemSelect, {
      modelValue: null,
      placeholder: "Search items...",
      typesToQuery: ["samples", "cells", "starting_materials"],
      "onUpdate:modelValue": (item) => {
        if (!item) return;
        options.command({ editor, range: state.range, props: item });
        hideSuggestions();
      },
    });
    suggestionApp.mount(suggestionEl);
    window.addEventListener("scroll", () => hideSuggestions(), true);
    window.addEventListener("resize", () => hideSuggestions(), true);
  }

  reposition(view, state);
  suggestionEl.style.display = "block";
  suggestionEl.querySelector("input")?.focus();
}

function reposition(view, state) {
  if (!suggestionEl) return;
  const coords = view.coordsAtPos(state.range.from);

  suggestionEl.style.position = "absolute";
  suggestionEl.style.left = `${coords.left}px`;
  suggestionEl.style.top = `${coords.bottom - 20}px`;
  suggestionEl.style.zIndex = 1050;

  suggestionEl.style.minWidth = "350px";
  suggestionEl.style.maxWidth = "600px";
}

function hideSuggestions(destroy = false) {
  if (suggestionEl) {
    suggestionEl.style.display = "none";
    if (destroy) {
      suggestionEl.remove();
      suggestionEl = null;
      suggestionApp = null;
    }
  }
}
