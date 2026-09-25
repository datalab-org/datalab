<template>
  <Navbar />

  <main data-testid="tool-host">
    <div v-if="isLoading" class="container py-5 text-center" role="status">
      <span class="spinner-border text-primary mb-3" aria-hidden="true"></span>
      <p class="mb-0">Loading tool...</p>
    </div>

    <div v-else-if="loadError" class="container py-4">
      <div class="alert alert-danger" role="alert">
        <p class="mb-2">Unable to load this tool: {{ loadError }}</p>
        <router-link to="/tools" class="alert-link">Return to Tools</router-link>
      </div>
    </div>

    <component :is="toolComponent" v-else-if="toolComponent" />
  </main>
</template>

<script>
import { markRaw } from "vue";

import Navbar from "@/components/Navbar.vue";
import { getTools, launchTool } from "@/server_fetch_utils.js";
import { isSupportedTool, selectionFromRouteQuery } from "@/tool_launch_utils.js";
import { loadInAppTool } from "@/tool_sdk.js";

export default {
  name: "ToolHost",
  components: {
    Navbar,
  },
  data() {
    return {
      isLoading: true,
      loadError: null,
      toolComponent: null,
      loadSequence: 0,
    };
  },
  watch: {
    "$route.params.toolId": {
      immediate: true,
      handler() {
        this.loadTool();
      },
    },
  },
  errorCaptured(error) {
    this.toolComponent = null;
    this.loadError = `The tool encountered an error: ${
      error instanceof Error ? error.message : String(error)
    }`;
    return false;
  },
  methods: {
    async loadTool() {
      const sequence = ++this.loadSequence;
      this.isLoading = true;
      this.loadError = null;
      this.toolComponent = null;

      try {
        const tools = await getTools();
        const tool = tools.find((candidate) => candidate.id === this.$route.params.toolId);
        if (!tool) {
          throw new Error("The tool is disabled, unavailable, or not installed.");
        }
        if (!isSupportedTool(tool) || tool.ui.kind !== "in_app") {
          throw new Error("The requested tool is not an in-app tool.");
        }

        const selection = selectionFromRouteQuery(this.$route.query);
        await launchTool(
          tool.id,
          selection
            ? {
                action: selection.actionId,
                items: selection.itemRefcodes,
              }
            : {},
        );

        const component = await loadInAppTool(tool);
        if (sequence !== this.loadSequence) {
          return;
        }
        this.toolComponent = markRaw(component);
        const websiteTitle = process.env.VUE_APP_WEBSITE_TITLE || "datalab";
        document.title = `${websiteTitle} - ${tool.name}`;
      } catch (error) {
        if (sequence === this.loadSequence) {
          this.loadError = error instanceof Error ? error.message : String(error);
        }
      } finally {
        if (sequence === this.loadSequence) {
          this.isLoading = false;
        }
      }
    },
  },
};
</script>
