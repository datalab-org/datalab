<template>
  <Navbar />

  <main class="container py-4" data-testid="tools-page">
    <header class="mb-4">
      <h1 class="h2">Tools</h1>
      <p class="text-muted mb-0">Open tools that work with the data available to your account.</p>
    </header>

    <div v-if="isLoading" class="text-center py-5" role="status" data-testid="tools-loading">
      <span class="spinner-border text-primary mb-3" aria-hidden="true"></span>
      <p class="mb-0">Loading tools...</p>
    </div>

    <div
      v-else-if="loadError"
      class="alert alert-danger d-flex flex-wrap align-items-center justify-content-between"
      role="alert"
      data-testid="tools-error"
    >
      <span>Unable to load tools: {{ loadError }}</span>
      <button class="btn btn-outline-danger btn-sm ml-3" type="button" @click="loadTools">
        Try again
      </button>
    </div>

    <div
      v-else-if="tools.length === 0"
      class="alert alert-secondary"
      role="status"
      data-testid="tools-empty"
    >
      No tools are currently available.
    </div>

    <div v-else class="row">
      <div v-for="tool in tools" :key="tool.id" class="col-md-6 col-xl-4 mb-4">
        <article class="card h-100 shadow-sm" :data-testid="`tool-card-${tool.id}`">
          <div class="card-body d-flex flex-column">
            <div class="d-flex align-items-start mb-3">
              <font-awesome-icon
                :icon="tool.icon || 'laptop-code'"
                class="fa-2x text-primary mr-3"
                aria-hidden="true"
              />
              <div>
                <h2 class="h4 card-title mb-1">{{ tool.name }}</h2>
                <span v-if="tool.version" class="small text-muted">Version {{ tool.version }}</span>
              </div>
            </div>

            <p class="card-text flex-grow-1">
              {{ tool.description || "No description is available for this tool." }}
            </p>

            <p
              v-if="!isSupportedTool(tool)"
              class="small text-danger"
              :data-testid="`tool-unsupported-${tool.id}`"
            >
              This tool has an unsupported frontend configuration.
            </p>

            <button
              class="btn btn-primary align-self-start"
              type="button"
              :disabled="launchingToolId !== null || !isSupportedTool(tool)"
              :data-testid="`tool-launch-${tool.id}`"
              @click="openTool(tool)"
            >
              <template v-if="launchingToolId === tool.id">
                <span class="spinner-border spinner-border-sm mr-2" aria-hidden="true"></span>
                Opening...
              </template>
              <template v-else>Open {{ tool.name }}</template>
            </button>
          </div>
        </article>
      </div>
    </div>

    <div v-if="launchError" class="alert alert-danger mt-2" role="alert">
      {{ launchError }}
    </div>
  </main>
</template>

<script>
import Navbar from "@/components/Navbar.vue";
import { getTools } from "@/server_fetch_utils.js";
import { isSupportedTool, openTool } from "@/tool_launch_utils.js";

export default {
  name: "Tools",
  components: {
    Navbar,
  },
  data() {
    return {
      tools: [],
      isLoading: true,
      loadError: null,
      launchError: null,
      launchingToolId: null,
    };
  },
  mounted() {
    this.loadTools();
  },
  methods: {
    async loadTools() {
      this.isLoading = true;
      this.loadError = null;

      try {
        this.tools = await getTools();
      } catch (error) {
        this.tools = [];
        this.loadError = error instanceof Error ? error.message : String(error);
      } finally {
        this.isLoading = false;
      }
    },
    isSupportedTool(tool) {
      return isSupportedTool(tool);
    },
    async openTool(tool) {
      this.launchError = null;
      this.launchingToolId = tool.id;

      try {
        await openTool(tool, this.$router);
      } catch (error) {
        this.launchError = `Unable to open ${tool.name}: ${
          error instanceof Error ? error.message : String(error)
        }`;
      } finally {
        if (this.launchingToolId === tool.id) {
          this.launchingToolId = null;
        }
      }
    },
  },
};
</script>
