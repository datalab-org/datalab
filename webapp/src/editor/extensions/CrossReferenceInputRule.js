import { Extension } from "@tiptap/core";
import { Plugin, PluginKey } from "@tiptap/pm/state";
import { createApp } from "vue";
import ItemSelect from "@/components/ItemSelect.vue";

let suggestionApp = null;
let suggestionEl = null;
let cleanupListeners = null;

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
        return { active: false, range: null, query: null };
      },
      apply(tr, prev, oldState, newState) {
        const { selection } = newState;
        const { empty, from } = selection;
        if (!empty) return { active: false, range: null, query: null };

        const $pos = selection.$from;
        const textBefore = $pos.parent.textContent.slice(0, $pos.parentOffset);
        const match = textBefore.match(/@(\w*)$/);

        if (!match) {
          hideSuggestions();
          return { active: false, range: null, query: null };
        }

        const query = match[1];
        const range = { from: from - match[0].length, to: from };
        return { active: true, range, query };
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
    suggestionEl.style.position = "fixed";
    suggestionEl.style.minWidth = "350px";
    suggestionEl.style.maxWidth = "600px";
    suggestionEl.style.zIndex = 2000;
    document.body.appendChild(suggestionEl);
  }

  if (!suggestionApp) {
    suggestionApp = createApp(ItemSelect, {
      modelValue: null,
      placeholder: "Search items...",
      typesToQuery: ["samples", "cells", "starting_materials", "equipment"],
      "onUpdate:modelValue": (item) => {
        const state = options.pluginKey.getState(editor.state);
        if (!item || !state?.range) return;

        options.command({ editor, range: state.range, props: item });
        hideSuggestions();
      },
    });
    suggestionApp.mount(suggestionEl);
    cleanupListeners = setupGlobalListeners();
  }

  reposition(view, state.range);
  suggestionEl.style.display = "block";

  const input = suggestionEl.querySelector("input");
  if (input) {
    requestAnimationFrame(() => {
      input.focus({ preventScroll: true });
    });
  }
}

function reposition(view, range) {
  if (!suggestionEl || !range) return;

  const coords = view.coordsAtPos(range.from);

  suggestionEl.style.left = `${coords.left}px`;
  suggestionEl.style.top = `${coords.bottom}px`;
}

function hideSuggestions(destroy = false) {
  if (suggestionEl) {
    suggestionEl.style.display = "none";
    if (destroy) {
      try {
        if (suggestionApp) {
          suggestionApp.unmount();
        }
      } catch (e) {
        console.error("Error unmounting suggestionApp", e);
      }
      suggestionEl.remove();
      suggestionEl = null;
      suggestionApp = null;
      if (cleanupListeners) {
        cleanupListeners();
        cleanupListeners = null;
      }
    }
  }
}

function setupGlobalListeners() {
  const onClickOutside = (event) => {
    if (suggestionEl && !suggestionEl.contains(event.target)) {
      hideSuggestions();
    }
  };

  const onScrollOrResize = () => {
    if (suggestionEl) hideSuggestions();
  };

  window.addEventListener("mousedown", onClickOutside);
  window.addEventListener("scroll", onScrollOrResize, true);
  window.addEventListener("resize", onScrollOrResize, true);

  return () => {
    window.removeEventListener("mousedown", onClickOutside);
    window.removeEventListener("scroll", onScrollOrResize, true);
    window.removeEventListener("resize", onScrollOrResize, true);
  };
}
