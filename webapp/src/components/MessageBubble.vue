<template>
  <!-- render the chat with the LLM bot as a green chat bubble on the left, and the user's messages as a grey chat bubble on the right -->
  <div
    class="bubble-enclosure"
    :class="{ 'flex-left': !isUserMessage, 'flex-right': isUserMessage }"
  >
    <div class="bubble" :class="{ 'bubble-system': !isUserMessage, 'bubble-user': isUserMessage }">
      <div ref="markdownDiv" v-show="!showRaw" class="markdown-content" v-html="markdownContent" />
      <div class="raw-content" v-show="showRaw">{{ message.content }}</div>
      <div class="float-right raw-toggle" @click="showRaw = !showRaw">
        <span :class="{ 'font-weight-bold': showRaw }"> raw </span> |
        <span :class="{ 'font-weight-bold': !showRaw }">formatted</span>
      </div>
    </div>
  </div>
</template>

<script>
import MarkdownIt from "markdown-it";
import "markdown-it";
// import hljs from "highlight.js";
// import "highlight.js/styles/a11y-light.css";
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
    isUserMessage() {
      return this.message.role === "user";
    },
    markdownContent() {
      return this.md?.render(this.message.content);
    },
  },
  methods: {},
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
            el
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
        if (lang && lang == "mermaid") {
          try {
            return `<pre class="mermaid-code">${str}</pre>`;
          } catch (__) {
            //pass
          }
        }
        if (lang && lang == "svg") {
          return `<pre class="svg-drawing">${str}</pre>`;
        }
        // else if (lang && hljs.getLanguage(lang)) {
        //   try {
        //     return hljs.highlight(str, { language: lang }).value;
        //   } catch (__) {
        //     //pass
        //   }
        // }
      },
    });

    this.md.renderer.rules.table_open = function () {
      return '<table class="table table-sm">';
    };
  },
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

.bubble-system {
  background-color: rgba(25, 25, 25, 0.05);
  width: 90%;
}

.raw-content {
  font-family: "Roboto Mono", monospace;
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
  cursor: pointer;
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
