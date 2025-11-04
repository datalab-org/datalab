<template>
  <!-- render the chat with the LLM bot as a green chat bubble on the left, and the user's messages as a grey chat bubble on the right -->
  <div
    class="bubble-enclosure"
    :class="{
      'flex-left': role === 'assistant',
      'flex-right': role === 'user' || role === 'system',
    }"
  >
    <div
      class="bubble"
      :class="{
        'bubble-assistant': role === 'assistant',
        'bubble-user': role === 'user',
        'bubble-system': role === 'system',
      }"
    >
      <span v-if="role === 'system'" class="system-prompt-label">system prompt:</span>
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div v-show="!showRaw" ref="markdownDiv" class="markdown-content" v-html="markdownContent" />
      <div v-show="showRaw" class="raw-content">{{ message.content }}</div>
      <div class="float-right raw-toggle clickable" @click="showRaw = !showRaw">
        <span :class="{ 'font-weight-bold': showRaw }"> raw </span> |
        <span :class="{ 'font-weight-bold': !showRaw }">formatted</span>
      </div>
    </div>
  </div>
</template>

<script>
import MarkdownIt from "markdown-it";
import "markdown-it";
import hljs from "highlight.js";
import "highlight.js/styles/a11y-light.css";
import mermaid from "mermaid";

export default {
  name: "MessageBubble",
  props: {
    message: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      md: null,
      showRaw: false,
    };
  },
  computed: {
    role() {
      return this.message.role;
    },
    isUserMessage() {
      return this.message.role === "user";
    },
    isSystemMessage() {
      return this.message.role === "system";
    },
    markdownContent() {
      return this.md?.render(this.message.content);
    },
  },
  watch: {
    markdownContent: {
      flush: "post",
      async handler() {
        // if any mermaid code blocks are present, convert them to mermaid plots:
        const elements = this.$refs.markdownDiv.querySelectorAll("pre.mermaid-code");
        elements.forEach(async (el) => {
          const { svg } = await mermaid.render(
            "mermaid_" + Math.floor(Math.random() * 1000000),
            el.textContent,
            el,
          );
          el.innerHTML = svg;
        });
      },
    },
  },
  mounted() {
    console.log("mounted called");
    this.md = new MarkdownIt({
      typographer: true,
      highlight: function (str, lang) {
        if (lang && lang.toLowerCase() == "mermaid") {
          try {
            return `<pre class="mermaid-code">${str}</pre>`;
          } catch (__) {
            //pass
          }
        }
        if (lang && lang.toLowerCase() == "svg") {
          return `<pre class="svg-drawing">${str}</pre>`;
        } else if (lang && hljs.getLanguage(lang)) {
          try {
            return hljs.highlight(str, { language: lang }).value;
          } catch (__) {
            //pass
          }
        }
      },
    });

    this.md.renderer.rules.table_open = function () {
      return '<table class="table table-sm">';
    };
  },
  methods: {},
};
</script>

<style scoped>
.bubble-enclosure {
  display: flex;
  flex-direction: column;
  margin: 0.5rem 0;
  margin-bottom: 2rem;
}

.flex-left {
  align-items: flex-start;
}

.flex-right {
  align-items: flex-end;
}

.bubble-user {
  background-color: rgba(25, 150, 25, 0.3);
  max-width: 90%;
}

.bubble-assistant {
  background-color: rgba(25, 25, 25, 0.05);
  width: 90%;
}

.bubble-system {
  border: 1px solid #dee2e6;
  background-color: rgba(24, 132, 185, 0.05);
  border-radius: 0.1rem !important;
  width: 90%;
}

.system-prompt-label {
  font-family: var(--font-monospace);
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(100, 100, 100);
}

.raw-content {
  font-family: var(--font-monospace);
  font-size: 0.875rem;
  white-space: pre-wrap;
  overflow-x: auto;
  scrollbar-width: thin;
}

.bubble {
  border-radius: 0.5rem;
  padding: 1rem;
  color: black;
}

.raw-toggle {
  font-size: 0.875rem;
  color: rgb(100, 100, 100);
  opacity: 0.5;
}

.raw-toggle:hover {
  opacity: 1;
}
</style>

<style>
/* seem to need unscoped styles in order for these to stick */
.markdown-content pre code {
  background-color: transparent;
  text-shadow: none; /* overrighting an annoying shadow from tinymce styles */
}

.markdown-content pre {
  background-color: rgba(255, 255, 255, 0.6);
  border-radius: 0.25rem;
  padding: 0.5rem;
}

.markdown-content table {
  font-size: 0.875rem;
  background-color: rgba(255, 255, 255, 0.6);
  border-radius: 0.25rem;
}

.markdown-content p:last-child {
  margin-bottom: 0px;
}
</style>
