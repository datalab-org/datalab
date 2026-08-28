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
                <th>Saved by</th>
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
                @click="previewVersionData(version)"
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
                  <Creators v-if="version.creator" :creators="[version.creator]" :size="24" />
                  <span v-else class="text-muted">Unknown</span>
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
      <div v-else class="preview-container container-fluid">
        <dl v-if="previewVersionRecord" class="row mb-3">
          <dt class="col-sm-3">Saved by</dt>
          <dd class="col-sm-9">
            <Creators
              v-if="previewVersionRecord.creator"
              :creators="[previewVersionRecord.creator]"
              :size="24"
            />
            <span v-else class="text-muted">Unknown</span>
          </dd>

          <dt class="col-sm-3">Saved</dt>
          <dd class="col-sm-9">
            {{ formatDate(previewVersionRecord.timestamp) }}
            <span class="text-muted">
              ({{
                formatDistanceToNow(new Date(previewVersionRecord.timestamp), { addSuffix: true })
              }})
            </span>
          </dd>

          <dt class="col-sm-3">Action</dt>
          <dd class="col-sm-9">
            {{
              formatAction(previewVersionRecord.action, previewVersionRecord.restored_from_version)
            }}
          </dd>

          <dt class="col-sm-3">Saved via</dt>
          <dd class="col-sm-9">
            <span v-if="previewVersionRecord.user_agent">{{
              previewVersionRecord.user_agent
            }}</span>
            <span v-else class="text-muted">Not recorded</span>
          </dd>
        </dl>

        <div class="alert alert-info mb-3">
          <font-awesome-icon icon="info-circle" fixed-width />
          <span v-if="isPermissionsUpdate">
            Version {{ previewVersion }} records a change to who can access this item. The item's
            content was not edited.
          </span>
          <span v-else-if="previousVersionNumber">
            What changed in version {{ previewVersion }}, compared with version
            {{ previousVersionNumber }}.
          </span>
          <span v-else> Version {{ previewVersion }} is the first recorded version. </span>
        </div>

        <!-- Loading preview -->
        <div v-if="isLoadingPreview" class="text-center py-5">
          <font-awesome-icon icon="spinner" class="fa-spin" size="2x" style="color: gray" />
          <p class="mt-3">Loading changes...</p>
        </div>

        <div v-else-if="isPermissionsUpdate" />

        <div v-else-if="!previousVersionNumber" class="text-muted py-3">
          There is no earlier version to compare it against.
        </div>

        <div v-else-if="changes.length === 0" class="text-muted py-3">
          No changes to the item's content were recorded in this version.
        </div>

        <div v-else class="table-responsive">
          <table class="table table-sm changes-table">
            <thead>
              <tr>
                <th>Field</th>
                <th>Before</th>
                <th>After</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="change in changes" :key="change.field">
                <td>
                  <code>{{ change.field }}</code>
                </td>
                <td class="change-value change-before">{{ change.before }}</td>
                <td class="change-value change-after">{{ change.after }}</td>
              </tr>
            </tbody>
          </table>
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
import { getItemVersions, compareItemVersions, restoreItemVersion } from "@/server_fetch_utils";
import { formatDistanceToNow } from "date-fns";
import { DialogService } from "@/services/DialogService";
import Creators from "@/components/Creators.vue";

// Fields that are bookkeeping rather than item content: they change on every save, or
// are inlined by the server for display, so listing them as changes is just noise.
const IGNORED_FIELDS = [
  "last_modified",
  "version",
  "_id",
  "immutable_id",
  "refcode",
  "creators",
  "groups",
  "creator_ids",
  "group_ids",
];

export default {
  components: {
    Modal,
    Creators,
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
      previewVersionRecord: null,
      previousVersionNumber: null,
      changes: [],
      isLoadingPreview: false,
      // Incremented whenever the active preview changes, so responses from an
      // earlier (slower) comparison can be discarded instead of overwriting it.
      previewRequestId: 0,
    };
  },
  computed: {
    sortedVersions() {
      return [...this.versions].sort((a, b) => b.version - a.version);
    },
    isPermissionsUpdate() {
      return this.previewVersionRecord?.action === "permissions_update";
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
        created: "Created",
        manual_save: "Manual Save",
        auto_save: "Auto Save",
        agent_save: "Agent Save",
        permissions_update: "Permissions Update",
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
    async previewVersionData(version) {
      const versionId = version._id;
      const versionNumber = version.version;
      const requestId = ++this.previewRequestId;

      this.isPreviewMode = true;
      this.previewVersion = versionNumber;
      this.previewVersionId = versionId;
      this.previewVersionRecord = version;
      this.changes = [];
      this.previousVersionNumber = null;

      // A permissions update never touches the item's content, so a field-level diff
      // has nothing useful to say about it.
      if (this.isPermissionsUpdate) {
        return;
      }

      // Compare against the closest earlier version rather than `versionNumber - 1`,
      // since numbering can skip where a snapshot was deleted.
      let previous = this.findPreviousVersion(versionNumber);
      if (!previous) {
        // The list may predate versions minted since the modal was opened, so confirm
        // against the server before concluding this is the earliest version.
        await this.loadVersions();
        if (requestId !== this.previewRequestId) {
          return;
        }
        previous = this.findPreviousVersion(versionNumber);
        // `loadVersions` replaces the records, so re-point at the refreshed one.
        this.previewVersionRecord =
          this.versions.find((v) => v.version === versionNumber) || this.previewVersionRecord;
      }
      this.previousVersionNumber = previous ? previous.version : null;

      if (!previous) {
        return;
      }

      this.isLoadingPreview = true;
      try {
        const diff = await compareItemVersions(this.refcode, previous._id, versionId);
        if (requestId !== this.previewRequestId) {
          return;
        }
        this.changes = this.summariseDiff(diff);
      } catch (error) {
        if (requestId !== this.previewRequestId) {
          return;
        }
        console.error("Failed to load version changes:", error);
        this.changes = [];
      } finally {
        if (requestId === this.previewRequestId) {
          this.isLoadingPreview = false;
        }
      }
    },
    findPreviousVersion(versionNumber) {
      // `sortedVersions` is descending, so the first entry below this one is its
      // immediate predecessor.
      return this.sortedVersions.find((v) => v.version < versionNumber) || null;
    },
    summariseDiff(diff) {
      // The server returns raw DeepDiff output, keyed by the kind of change, each
      // mapping a path like `root['blocks_obj']['abc']['title']` to its values.
      const changes = [];
      const push = (path, before, after) => {
        const field = this.formatFieldPath(path);
        if (!field || IGNORED_FIELDS.includes(field.split(/[.[]/)[0])) {
          return;
        }
        changes.push({
          field,
          before: this.formatValue(before),
          after: this.formatValue(after),
        });
      };

      for (const [path, change] of Object.entries(diff?.values_changed || {})) {
        push(path, change.old_value, change.new_value);
      }
      for (const [path, change] of Object.entries(diff?.type_changes || {})) {
        push(path, change.old_value, change.new_value);
      }
      for (const key of ["dictionary_item_added", "iterable_item_added"]) {
        for (const [path, value] of Object.entries(diff?.[key] || {})) {
          push(path, undefined, value);
        }
      }
      for (const key of ["dictionary_item_removed", "iterable_item_removed"]) {
        for (const [path, value] of Object.entries(diff?.[key] || {})) {
          push(path, value, undefined);
        }
      }

      return changes.sort((a, b) => a.field.localeCompare(b.field));
    },
    formatFieldPath(path) {
      // `root['blocks_obj']['abc'][0]` -> `blocks_obj.abc[0]`
      const parts = [...String(path).matchAll(/\['([^']*)'\]|\[(\d+)\]/g)];
      return parts
        .map(([, key, index], i) => {
          if (index !== undefined) return `[${index}]`;
          return i === 0 ? key : `.${key}`;
        })
        .join("");
    },
    formatValue(value) {
      if (value === undefined) return "-";
      if (value === null) return "null";
      if (typeof value === "string") {
        return value.length > 200 ? `${value.slice(0, 200)}...` : value || '""';
      }
      if (typeof value === "object") {
        const serialised = JSON.stringify(value);
        return serialised.length > 200 ? `${serialised.slice(0, 200)}...` : serialised;
      }
      return String(value);
    },
    exitPreview() {
      // Invalidate any comparison still in flight for the version being left.
      this.previewRequestId++;
      this.isPreviewMode = false;
      this.previewVersion = null;
      this.previewVersionRecord = null;
      this.previousVersionNumber = null;
      this.changes = [];
      this.isLoadingPreview = false;
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
    closeModal() {
      this.isOpen = false;
      this.resetState();
    },
    resetState() {
      this.previewRequestId++;
      this.isPreviewMode = false;
      this.previewVersion = null;
      this.previewVersionRecord = null;
      this.previousVersionNumber = null;
      this.changes = [];
      this.isLoadingPreview = false;
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

.changes-table code {
  color: #495057;
  word-break: break-all;
}

.change-value {
  white-space: pre-wrap;
  word-break: break-word;
  max-width: 20rem;
}

.change-before {
  color: #842029;
  background-color: rgba(220, 53, 69, 0.05);
}

.change-after {
  color: #0f5132;
  background-color: rgba(25, 135, 84, 0.05);
}

.badge {
  font-size: 0.75rem;
  vertical-align: middle;
}
</style>
