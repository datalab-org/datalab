<template>
  <!-- Teleport to <body> so the fixed-position modal is not clipped or hidden by a
       transformed/overflow ancestor of wherever the trigger button is mounted (e.g.
       the collection page header). -->
  <Teleport to="body">
    <Modal v-model="isOpen" :is-large="true">
      <template #header>
        <i class="fa fa-download mr-1"></i>
        {{ headerText }}
      </template>

      <template #body>
        <div ref="logContainer" class="export-log" data-testid="export-log">
          <div
            v-for="(stage, index) in stages"
            :key="index"
            class="export-log-line"
            :class="`level-${stage.level || 'info'}`"
          >
            <span class="export-log-time">{{ formatTime(stage.timestamp) }}</span>
            <span class="export-log-message">{{ stage.message }}</span>
          </div>
          <div v-if="stages.length === 0 && status === 'processing'" class="text-muted">
            <i class="fa fa-spinner fa-spin"></i> Starting export&hellip;
          </div>
        </div>

        <div v-if="status === 'error'" class="alert alert-danger mt-3 mb-0">
          <i class="fa fa-exclamation-triangle mr-1"></i>
          {{ errorMessage || "An error occurred during export." }}
        </div>
        <div v-else-if="status === 'ready'" class="alert alert-success mt-3 mb-0">
          <i class="fa fa-check-circle mr-1"></i>
          Export complete &mdash; your file is ready to download.
        </div>
        <div v-else class="mt-3 text-muted d-flex align-items-center">
          <i class="fa fa-spinner fa-spin mr-2"></i>
          Generating&nbsp;<code>.eln</code>&nbsp;file&hellip;
        </div>
      </template>

      <template #footer>
        <!-- No `download` attribute: the server sets `Content-Disposition: attachment`
             with the intended `<collection_id|item_id>.eln` filename, and a `download`
             attribute here would override it (e.g. to `collection.eln`) for same-origin
             deployments. -->
        <a
          v-if="status === 'ready'"
          :href="downloadUrl"
          class="btn btn-primary"
          data-testid="export-download-link"
        >
          <i class="fa fa-download mr-1"></i> Download .eln
        </a>
        <button type="button" class="btn btn-secondary" @click="close">
          {{ isFinished ? "Close" : "Cancel" }}
        </button>
      </template>
    </Modal>
  </Teleport>
</template>

<script>
import Modal from "@/components/Modal";
import { getExportStatus, getExportDownloadUrl } from "@/server_fetch_utils";

const POLL_INTERVAL_MS = 2000;

export default {
  name: "ExportProgressModal",
  components: {
    Modal,
  },
  props: {
    exportType: {
      type: String,
      default: "export",
    },
  },
  emits: ["close"],
  data() {
    return {
      isOpen: false,
      taskId: null,
      status: "processing",
      stages: [],
      errorMessage: null,
      pollInterval: null,
    };
  },
  computed: {
    isFinished() {
      return this.status === "ready" || this.status === "error";
    },
    headerText() {
      if (this.status === "ready") {
        return "Export complete";
      }
      if (this.status === "error") {
        return "Export failed";
      }
      return `Exporting ${this.exportType}…`;
    },
    downloadUrl() {
      return this.taskId ? getExportDownloadUrl(this.taskId) : "#";
    },
  },
  watch: {
    isOpen(open) {
      if (!open) {
        this.stopPolling();
        this.$emit("close");
      }
    },
    stages() {
      this.$nextTick(this.scrollLogToBottom);
    },
  },
  beforeUnmount() {
    this.stopPolling();
  },
  methods: {
    // Open the modal for a freshly-started export task and begin streaming its stages.
    start(taskId) {
      this.taskId = taskId;
      this.status = "processing";
      this.stages = [];
      this.errorMessage = null;
      this.isOpen = true;
      this.poll();
      this.pollInterval = setInterval(this.poll, POLL_INTERVAL_MS);
    },
    async poll() {
      if (!this.taskId) {
        return;
      }
      try {
        const status = await getExportStatus(this.taskId);
        this.stages = status.stages || [];
        this.status = status.status;

        if (status.status === "ready") {
          this.stopPolling();
        } else if (status.status === "error") {
          this.errorMessage = status.error_message;
          this.stopPolling();
        }
      } catch (error) {
        console.error("Error polling export status:", error);
        this.status = "error";
        this.errorMessage = "Lost connection while checking export status.";
        this.stopPolling();
      }
    },
    stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;
      }
    },
    close() {
      this.isOpen = false;
    },
    scrollLogToBottom() {
      const el = this.$refs.logContainer;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    },
    formatTime(timestamp) {
      if (!timestamp) {
        return "";
      }
      const date = new Date(timestamp);
      if (Number.isNaN(date.getTime())) {
        return "";
      }
      return date.toLocaleTimeString();
    },
  },
};
</script>

<style scoped>
.export-log {
  max-height: 40vh;
  overflow-y: auto;
  background-color: #1e1e1e;
  color: #d4d4d4;
  border-radius: 5px;
  padding: 0.75rem 1rem;
  font-family: var(--bs-font-monospace, monospace);
  font-size: 0.85rem;
  line-height: 1.5;
}

.export-log-line {
  white-space: pre-wrap;
  word-break: break-word;
}

.export-log-time {
  color: #6a9955;
  margin-right: 0.75rem;
  user-select: none;
}

.export-log-line.level-warning .export-log-message {
  color: #dcdcaa;
}

.export-log-line.level-error .export-log-message {
  color: #f48771;
}
</style>
