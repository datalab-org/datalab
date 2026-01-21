<template>
  <Modal v-model="isOpen" :is-large="true">
    <template #header>
      <span v-if="!isPreviewMode">Version History for {{ refcode }}</span>
      <span v-else>
        <font-awesome-icon icon="eye" fixed-width />
        Preview: Version {{ previewVersion }} of {{ refcode }}
      </span>
    </template>

    <template #body>
      <!-- Loading State -->
      <div v-if="isLoadingVersions" class="text-center py-5">
        <font-awesome-icon icon="spinner" class="fa-spin" size="2x" style="color: gray" />
        <p class="mt-3">Loading version history...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!isLoadingVersions && versions.length === 0" class="text-center py-5">
        <p class="text-muted">No version history available for this item.</p>
      </div>

      <!-- Version List View -->
      <div v-else-if="!isPreviewMode" class="version-list-container">
        <p class="text-muted mb-3">
          Click on a version to preview it, or use the restore button to revert to that version.
        </p>
        <div class="table-responsive">
          <table class="table table-hover">
            <thead>
              <tr>
                <th>Version</th>
                <th>Saved</th>
                <th>Action</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="version in sortedVersions"
                :key="version._id"
                class="version-row"
                :class="{ 'table-active': version.version === currentVersion }"
                @click="previewVersionData(version._id, version.version)"
              >
                <td>
                  <strong>{{ version.version }}</strong>
                  <span v-if="version.version === currentVersion" class="badge badge-primary ml-2">
                    Current
                  </span>
                </td>
                <td>
                  <span :title="formatDate(version.timestamp)">
                    {{ formatDistanceToNow(new Date(version.timestamp), { addSuffix: true }) }}
                  </span>
                </td>
                <td>
                  <span class="text-muted">{{
                    formatAction(version.action, version.restored_from_version)
                  }}</span>
                </td>
                <td class="text-right">
                  <button
                    v-if="version.version !== currentVersion"
                    class="btn btn-sm btn-outline-primary"
                    @click.stop="confirmRestore(version._id, version.version)"
                  >
                    <font-awesome-icon icon="undo" fixed-width />
                    Restore
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Preview Mode -->
      <div v-else class="preview-container">
        <div class="alert alert-info mb-3">
          <font-awesome-icon icon="info-circle" fixed-width />
          You are viewing a read-only preview of version {{ previewVersion }}. Changes made in this
          version are highlighted below.
        </div>

        <!-- Loading preview -->
        <div v-if="isLoadingPreview" class="text-center py-5">
          <font-awesome-icon icon="spinner" class="fa-spin" size="2x" style="color: gray" />
          <p class="mt-3">Loading version data...</p>
        </div>

        <!-- Preview content -->
        <div v-else-if="previewData" class="preview-content">
          <!-- Debug: Show raw data structure -->
          <details class="mb-3">
            <summary style="cursor: pointer; color: #666">
              <small>Debug: View raw data</small>
            </summary>
            <pre style="max-height: 200px; overflow-y: auto; font-size: 0.8em">{{
              JSON.stringify(previewData, null, 2)
            }}</pre>
          </details>

          <h5>Item Information</h5>
          <div class="row mb-3">
            <div class="col-md-6">
              <strong>Name:</strong>
              <p>{{ previewData.name || "N/A" }}</p>
            </div>
            <div class="col-md-6">
              <strong>Date:</strong>
              <p>{{ previewData.date || "N/A" }}</p>
            </div>
          </div>

          <div class="row mb-3">
            <div class="col-12">
              <strong>Description:</strong>
              <p>{{ previewData.description || "N/A" }}</p>
            </div>
          </div>

          <div v-if="previewData.synthesis_description" class="row mb-3">
            <div class="col-12">
              <strong>Synthesis Description:</strong>
              <p>{{ previewData.synthesis_description }}</p>
            </div>
          </div>

          <div v-if="previewData.chemical_formula" class="row mb-3">
            <div class="col-md-6">
              <strong>Chemical Formula:</strong>
              <p>{{ previewData.chemical_formula }}</p>
            </div>
          </div>

          <div v-if="previewData.location" class="row mb-3">
            <div class="col-md-6">
              <strong>Location:</strong>
              <p>{{ previewData.location }}</p>
            </div>
          </div>

          <div v-if="previewData.manufacturer" class="row mb-3">
            <div class="col-md-6">
              <strong>Manufacturer:</strong>
              <p>{{ previewData.manufacturer }}</p>
            </div>
          </div>

          <div
            v-if="previewData.display_order && previewData.display_order.length > 0"
            class="mt-4"
          >
            <h5>Data Blocks ({{ previewData.display_order.length }})</h5>
            <ul class="list-group">
              <li
                v-for="blockId in previewData.display_order"
                :key="blockId"
                class="list-group-item"
              >
                <strong>{{ getBlockTitle(blockId) }}</strong>
                <span class="text-muted ml-2">({{ getBlockType(blockId) }})</span>
              </li>
            </ul>
          </div>

          <div v-if="previewData.files && previewData.files.length > 0" class="mt-4">
            <h5>Files ({{ previewData.files.length }})</h5>
            <ul class="list-group">
              <li
                v-for="file in previewData.files"
                :key="file.immutable_id"
                class="list-group-item"
              >
                {{ file.name }}
              </li>
            </ul>
          </div>
        </div>

        <!-- Preview actions -->
        <div class="mt-4 d-flex justify-content-between">
          <button class="btn btn-secondary" @click="exitPreview">
            <font-awesome-icon icon="arrow-left" fixed-width />
            Back to List
          </button>
          <button class="btn btn-primary" @click="confirmRestore(previewVersionId, previewVersion)">
            <font-awesome-icon icon="undo" fixed-width />
            Restore This Version
          </button>
        </div>
      </div>
    </template>

    <template #footer>
      <button type="button" class="btn btn-secondary" @click="closeModal">Close</button>
    </template>
  </Modal>
</template>

<script>
import Modal from "@/components/Modal.vue";
import { getItemVersions, getItemVersion, restoreItemVersion } from "@/server_fetch_utils";
import { formatDistanceToNow } from "date-fns";
import { DialogService } from "@/services/DialogService";

export default {
  components: {
    Modal,
  },
  props: {
    modelValue: Boolean,
    refcode: {
      type: String,
      required: true,
    },
    itemId: {
      type: String,
      required: true,
    },
    currentVersion: {
      type: Number,
      default: 1,
    },
  },
  emits: ["update:modelValue", "version-restored"],
  data() {
    return {
      isOpen: false,
      versions: [],
      isLoadingVersions: false,
      isPreviewMode: false,
      previewVersion: null,
      previewVersionId: null,
      previewData: null,
      isLoadingPreview: false,
    };
  },
  computed: {
    sortedVersions() {
      return [...this.versions].sort((a, b) => b.version - a.version);
    },
  },
  watch: {
    modelValue(newValue) {
      this.isOpen = newValue;
      if (newValue) {
        this.loadVersions();
      } else {
        this.resetState();
      }
    },
    isOpen(newValue) {
      this.$emit("update:modelValue", newValue);
    },
  },
  methods: {
    formatDistanceToNow,
    formatDate(timestamp) {
      return new Date(timestamp).toLocaleString();
    },
    formatAction(action, restoredFromVersion) {
      const actionLabels = {
        manual_save: "Manual Save",
        auto_save: "Auto Save",
        restored: restoredFromVersion
          ? `Restored from v${this.getVersionNumberById(restoredFromVersion)}`
          : "Restored",
      };
      return actionLabels[action] || action || "Saved";
    },
    getVersionNumberById(versionId) {
      const version = this.versions.find((v) => v._id === versionId);
      return version ? version.version : "?";
    },
    async loadVersions() {
      this.isLoadingVersions = true;
      try {
        this.versions = await getItemVersions(this.refcode);
      } catch (error) {
        console.error("Failed to load versions:", error);
        this.versions = [];
      } finally {
        this.isLoadingVersions = false;
      }
    },
    async previewVersionData(versionId, versionNumber) {
      this.isPreviewMode = true;
      this.previewVersion = versionNumber;
      this.previewVersionId = versionId;
      this.isLoadingPreview = true;

      try {
        this.previewData = await getItemVersion(this.refcode, versionId);
      } catch (error) {
        console.error("Failed to load version preview:", error);
        this.previewData = null;
      } finally {
        this.isLoadingPreview = false;
      }
    },
    exitPreview() {
      this.isPreviewMode = false;
      this.previewVersion = null;
      this.previewData = null;
    },
    async confirmRestore(versionId, versionNumber) {
      const confirmed = await DialogService.confirm({
        title: "Restore Version",
        message: `Are you sure you want to restore to version ${versionNumber}? This will create a new version with the restored data. Your current changes will be preserved in the version history.`,
        type: "warning",
      });

      if (confirmed) {
        await this.restoreVersion(versionId, versionNumber);
      }
    },
    async restoreVersion(versionId, versionNumber) {
      try {
        const result = await restoreItemVersion(this.refcode, versionId);

        if (result.status === "success") {
          // Exit preview mode first
          this.exitPreview();

          // Reload the version list to show the new version
          await this.loadVersions();

          // Emit event to parent so it can reload the item data
          this.$emit("version-restored", {
            refcode: this.refcode,
            restoredVersionId: versionId,
            restoredVersionNumber: versionNumber,
            newVersionNumber: result.new_version_number,
          });

          // Show success message
          DialogService.info({
            title: "Version Restored",
            message: `Successfully restored to version ${versionNumber}. A new version ${result.new_version_number} has been created with the restored data.`,
          });
        }
      } catch (error) {
        console.error("Failed to restore version:", error);
        // Error dialog already shown by API function
      }
    },
    getBlockTitle(blockId) {
      if (!this.previewData.blocks_obj || !this.previewData.blocks_obj[blockId]) {
        return blockId;
      }
      return this.previewData.blocks_obj[blockId].title || blockId;
    },
    getBlockType(blockId) {
      if (!this.previewData.blocks_obj || !this.previewData.blocks_obj[blockId]) {
        return "unknown";
      }
      return this.previewData.blocks_obj[blockId].blocktype || "unknown";
    },
    closeModal() {
      this.isOpen = false;
      this.resetState();
    },
    resetState() {
      this.isPreviewMode = false;
      this.previewVersion = null;
      this.previewData = null;
      this.versions = [];
    },
  },
};
</script>

<style scoped>
.version-list-container {
  max-height: 500px;
  overflow-y: auto;
}

.version-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.version-row:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.preview-container {
  max-height: 600px;
  overflow-y: auto;
}

.preview-content {
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
}

.preview-content h5 {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.preview-content h5:first-child {
  margin-top: 0;
}

.preview-content strong {
  color: #495057;
  display: block;
  margin-bottom: 0.25rem;
}

.preview-content p {
  margin-bottom: 0;
  white-space: pre-wrap;
}

.badge {
  font-size: 0.75rem;
  vertical-align: middle;
}
</style>
