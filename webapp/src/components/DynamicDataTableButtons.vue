<template>
  <div v-if="showButtons" class="d-flex flex-column w-100">
    <div
      v-if="isDeletingItems"
      class="position-fixed d-flex justify-content-center align-items-center"
      style="background-color: rgba(255, 255, 255, 0.7); z-index: 1050; inset: 0"
    >
      <div class="card p-3 shadow-sm">
        <div class="text-center">
          <font-awesome-icon
            :icon="['fa', 'sync']"
            class="fa-2x text-primary mb-2"
            :spin="true"
            aria-label="loading"
          />
          <p class="mb-0 mt-1">Deleting {{ itemCount }} items...</p>
        </div>
      </div>
    </div>

    <div class="button-bar row mx-n1 align-items-center">
      <div
        v-if="hasActionButtons"
        class="btn-action-group d-flex flex-column flex-sm-row align-items-stretch align-items-sm-center px-1"
        :class="
          dataType === 'samples'
            ? 'col-12 col-xl-auto mb-2 mb-xl-0'
            : 'col-12 col-lg-auto mb-2 mb-lg-0'
        "
      >
        <template v-if="dataType === 'samples'">
          <button
            data-testid="add-item-button"
            class="btn btn-default btn-action"
            :disabled="!isLoggedIn || adminSuperUserMode"
            :title="
              !isLoggedIn
                ? 'Log in to add items'
                : adminSuperUserMode
                  ? 'Disabled in super-user mode'
                  : ''
            "
            @click="$emit('open-create-item-modal')"
          >
            Add an item
          </button>
          <button
            data-testid="batch-item-button"
            class="btn btn-default btn-action"
            :disabled="!isLoggedIn || adminSuperUserMode"
            :title="
              !isLoggedIn
                ? 'Log in to add items'
                : adminSuperUserMode
                  ? 'Disabled in super-user mode'
                  : ''
            "
            @click="$emit('open-batch-create-item-modal')"
          >
            Add batch of items
          </button>
          <button
            data-testid="scan-qr-button"
            class="btn btn-default btn-action"
            aria-label="Scan QR code"
            title="Scan QR code"
            @click="$emit('open-qr-scanner-modal')"
          >
            <font-awesome-icon icon="qrcode" /> Scan QR code
          </button>
        </template>
        <button
          v-if="dataType === 'collections'"
          data-testid="add-collection-button"
          class="btn btn-default btn-action"
          @click="$emit('open-create-collection-modal')"
        >
          Create new collection
        </button>
        <button
          v-if="dataType === 'startingMaterials' && editableInventory"
          data-testid="add-starting-material-button"
          class="btn btn-default btn-action"
          @click="$emit('open-create-item-modal')"
        >
          Add a starting material
        </button>
        <button
          v-if="dataType === 'equipment'"
          data-testid="add-equipment-button"
          class="btn btn-default btn-action"
          @click="$emit('open-create-equipment-modal')"
        >
          Add equipment
        </button>
        <button
          v-if="dataType === 'tags' && isLoggedIn"
          data-testid="add-tag-button"
          class="btn btn-default btn-action"
          @click="$emit('open-create-tag-modal')"
        >
          Create new tag
        </button>
      </div>

      <div
        class="table-tools d-flex align-items-stretch px-1"
        :class="
          dataType === 'samples'
            ? 'col-12 col-xl flex-column flex-lg-row align-items-lg-center ml-lg-auto'
            : hasActionButtons
              ? 'col-12 col-lg flex-column flex-lg-row align-items-lg-center ml-lg-auto'
              : 'col-12 col-md flex-column flex-md-row align-items-md-center ml-md-auto'
        "
      >
        <div
          class="selection-controls d-flex flex-nowrap align-items-center justify-content-between"
          :class="
            hasActionButtons
              ? 'justify-content-lg-start ml-lg-auto'
              : 'justify-content-md-start ml-md-auto'
          "
        >
          <div
            data-testid="selection-summary"
            class="selection-summary form-control-plaintext w-auto"
          >
            <font-awesome-icon
              :icon="itemsSelected.length > 0 ? 'check-square' : 'stream'"
              class="mr-1"
            />
            <span v-if="itemsSelected.length > 0">
              {{ itemsSelected.length }} {{ itemLabel(itemsSelected.length) }} selected
            </span>
            <span v-else>Number of {{ itemLabel(2) }}: {{ displayedItemCount }}</span>
          </div>

          <div
            v-if="itemsSelected.length > 0"
            v-on-click-outside="() => (isSelectedDropdownVisible = false)"
            class="dropdown"
          >
            <button
              id="selected-actions-dropdown"
              data-testid="selected-dropdown"
              class="btn btn-default dropdown-toggle"
              type="button"
              aria-label="Actions"
              title="Actions"
              data-toggle="dropdown"
              aria-haspopup="true"
              :aria-expanded="isSelectedDropdownVisible"
              @click="isSelectedDropdownVisible = !isSelectedDropdownVisible"
            >
              Actions
            </button>
            <div
              v-show="isSelectedDropdownVisible"
              class="dropdown-menu dropdown-menu-right"
              style="display: block"
              aria-labelledby="selected-actions-dropdown"
            >
              <a
                v-if="
                  !['collections', 'collectionItems', 'users', 'tokens', 'groups', 'tags'].includes(
                    dataType,
                  )
                "
                data-testid="add-to-collection-button"
                class="dropdown-item"
                @click="handleAddToCollection"
              >
                Add to collection
              </a>
              <a
                v-if="dataType === 'collectionItems'"
                data-testid="remove-from-collection-dropdown"
                class="dropdown-item"
                @click="confirmRemoveFromCollection"
              >
                Remove from collection
              </a>
              <a
                v-if="
                  !['collections', 'collectionItems', 'users', 'tokens', 'groups', 'tags'].includes(
                    dataType,
                  )
                "
                data-testid="batch-share-button"
                class="dropdown-item"
                @click="handleBatchShare"
              >
                Batch share
              </a>
              <a
                v-if="!['collectionItems', 'users', 'tokens', 'groups'].includes(dataType)"
                data-testid="delete-selected-button"
                class="dropdown-item"
                @click="confirmDeletion"
              >
                Delete items
              </a>
              <a
                v-if="dataType === 'users'"
                data-testid="bulk-change-role-button"
                class="dropdown-item"
                @click="
                  showBulkChangeRoleModal = true;
                  isSelectedDropdownVisible = false;
                "
              >
                Change role
              </a>
              <a
                v-if="dataType === 'users'"
                data-testid="bulk-add-to-group-button"
                class="dropdown-item"
                @click="
                  showBulkAddToGroupModal = true;
                  isSelectedDropdownVisible = false;
                "
              >
                Add to group
              </a>
              <a
                v-if="dataType === 'users'"
                data-testid="bulk-change-managers-button"
                class="dropdown-item"
                @click="
                  showBulkChangeManagersModal = true;
                  isSelectedDropdownVisible = false;
                "
              >
                Add manager(s)
              </a>
              <a
                v-if="dataType === 'users'"
                data-testid="bulk-activate-users-button"
                class="dropdown-item"
                @click="handleBulkActivateUsers"
              >
                Activate selected users
              </a>
              <a
                v-if="dataType === 'users'"
                data-testid="bulk-deactivate-users-button"
                class="dropdown-item"
                @click="handleBulkDeactivateUsers"
              >
                Deactivate selected users
              </a>
              <a
                v-if="dataType === 'tokens'"
                data-testid="bulk-invalidate-tokens-button"
                class="dropdown-item"
                @click="handleBulkInvalidateTokens"
              >
                Invalidate selected tokens
              </a>
              <a
                v-if="dataType === 'groups'"
                data-testid="bulk-delete-groups-button"
                class="dropdown-item"
                @click="handleBulkDeleteGroups"
              >
                Delete selected groups
              </a>
            </div>
          </div>
        </div>

        <div class="search-settings-group d-flex flex-nowrap">
          <div
            v-if="advancedQueryConfig && advancedQueryConfig.isEnabled"
            v-on-click-outside="() => (isAdvSearchDropdownVisible = false)"
            class="dropdown search-field"
          >
            <div class="input-group">
              <div class="input-group-prepend">
                <span class="input-group-text"><font-awesome-icon icon="search" /></span>
                <span v-if="activeSearchChips.length" class="input-group-text py-0">
                  <!-- Only the label is truncated, so the remove button stays visible. -->
                  <span
                    v-for="chip in activeSearchChips"
                    :key="chip.key"
                    class="badge badge-primary d-inline-flex align-items-center mr-1"
                    style="max-width: 12rem"
                    :title="chip.label"
                  >
                    <span class="text-truncate" style="min-width: 0">{{ chip.label }}</span>
                    <button
                      type="button"
                      class="btn btn-link p-0 ml-1 text-white flex-shrink-0"
                      aria-label="Remove"
                      title="Remove"
                      @click.stop="chip.clear"
                    >
                      &times;
                    </button>
                  </span>
                </span>
              </div>
              <input
                v-model="localFilters.global.value"
                data-testid="search-input"
                class="form-control"
                placeholder="Search"
              />
              <div class="input-group-append">
                <button
                  data-testid="advanced-search-chevron"
                  type="button"
                  class="btn btn-outline-secondary dropdown-toggle"
                  aria-label="Search options"
                  title="Search options"
                  aria-haspopup="true"
                  :aria-expanded="isAdvSearchDropdownVisible"
                  @click="isAdvSearchDropdownVisible = !isAdvSearchDropdownVisible"
                ></button>
              </div>
            </div>

            <AdvancedSearchDropdown
              v-if="isAdvSearchDropdownVisible"
              :active-filters="activeQuickFilters"
              :group-by-fields="groupByFields"
              :available-columns="availableColumns"
              :advanced-query-config="advancedQueryConfig"
              @update:active-filters="onUpdateQuickFilters"
              @update:group-by-fields="onUpdateGroupByFields"
              @open-advanced-query="openAdvancedQuery"
            />
          </div>

          <IconField v-else class="search-field">
            <InputIcon>
              <font-awesome-icon icon="search" />
            </InputIcon>
            <InputText
              v-model="localFilters.global.value"
              data-testid="search-input"
              class="search-input"
              placeholder="Search"
            />
          </IconField>

          <div v-on-click-outside="() => (isSettingsDropdownVisible = false)" class="dropdown">
            <button
              data-testid="table-settings-button"
              class="btn btn-default"
              type="button"
              aria-label="Table settings"
              title="Table settings"
              aria-haspopup="true"
              :aria-expanded="isSettingsDropdownVisible"
              @click="isSettingsDropdownVisible = !isSettingsDropdownVisible"
            >
              <font-awesome-icon icon="cog" />
            </button>
            <div
              v-show="isSettingsDropdownVisible"
              data-testid="table-settings-menu"
              class="dropdown-menu dropdown-menu-right settings-dropdown"
              style="display: block"
            >
              <div class="dropdown-item-text">
                <label class="mb-1 font-weight-bold">Columns</label>
                <!-- Compare columns by field: the default deep comparison can fail on column
                     definitions holding components. -->
                <MultiSelect
                  :model-value="selectedColumns"
                  :options="availableColumns"
                  :option-label="columnLabel"
                  append-to="self"
                  data-key="field"
                  placeholder="Select column(s) to display"
                  display="chip"
                  class="column-select-dropdown"
                  @update:model-value="$emit('update:selected-columns', $event)"
                >
                  <template #value="{ value }">
                    <span v-if="value && value.length == availableColumns.length" class="text-muted"
                      >All columns</span
                    >
                    <span v-else>{{ value.length }} columns</span>
                  </template>
                </MultiSelect>
              </div>
              <div class="dropdown-divider"></div>
              <a data-testid="reset-table-button" class="dropdown-item" @click="resetTable">
                <font-awesome-icon icon="redo" class="mr-2" /> Reset table settings
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <AdvancedQueryBuilder
      v-if="advancedQueryConfig && advancedQueryConfig.isEnabled"
      ref="advancedQueryBuilder"
      :types="advancedQueryConfig.types"
      @query-results="$emit('advanced-query-results', $event)"
      @update:applied-summary="appliedQuerySummary = $event"
    />
    <BulkChangeRoleModal
      v-model="showBulkChangeRoleModal"
      :selected-users="itemsSelected"
      @role-selected="handleBulkChangeRole"
    />
    <BulkAddToGroupModal
      v-model="showBulkAddToGroupModal"
      :selected-users="itemsSelected"
      @group-selected="handleBulkAddToGroup"
    />
    <BulkChangeManagersModal
      v-model="showBulkChangeManagersModal"
      :selected-users="itemsSelected"
      :all-users="allUsers"
      @managers-selected="handleBulkChangeManagers"
    />
  </div>
</template>

<script>
import { DialogService } from "@/services/DialogService";

import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import MultiSelect from "primevue/multiselect";
import "primeicons/primeicons.css";
import { vOnClickOutside } from "@vueuse/components";

import BulkChangeRoleModal from "@/components/BulkChangeRoleModal.vue";
import BulkAddToGroupModal from "@/components/BulkAddToGroupModal.vue";
import BulkChangeManagersModal from "@/components/BulkChangeManagersModal.vue";
import AdvancedQueryBuilder from "@/components/AdvancedQueryBuilder.vue";
import AdvancedSearchDropdown from "@/components/AdvancedSearchDropdown.vue";
import { QUICK_FILTERS } from "@/quickSearchOptions.js";

import {
  deleteSample,
  deleteCollection,
  deleteStartingMaterial,
  deleteEquipment,
  removeItemsFromCollection,
  saveUser,
  saveRole,
  addUserToGroup,
  saveUserManagers,
  invalidateToken,
  deleteGroup,
  deleteTag,
} from "@/server_fetch_utils.js";

export default {
  directives: {
    onClickOutside: vOnClickOutside,
  },
  components: {
    IconField,
    InputIcon,
    InputText,
    MultiSelect,
    BulkChangeRoleModal,
    BulkAddToGroupModal,
    BulkChangeManagersModal,
    AdvancedQueryBuilder,
    AdvancedSearchDropdown,
  },
  props: {
    dataType: {
      type: String,
      required: true,
    },
    itemsSelected: {
      type: Array,
      required: true,
    },
    displayedItemCount: {
      type: Number,
      required: false,
      default: 0,
    },
    filters: {
      type: Object,
      required: true,
    },
    editableInventory: {
      type: Boolean,
      required: false,
      default: false,
    },
    // Global toggle for all buttons and search bar
    showButtons: {
      type: Boolean,
      required: false,
      default: true,
    },
    availableColumns: {
      type: Array,
      required: true,
    },
    selectedColumns: {
      type: Array,
      required: true,
    },
    collectionId: {
      type: String,
      required: false,
      default: null,
    },
    allUsers: {
      type: Array,
      required: false,
      default: () => [],
    },
    advancedQueryConfig: {
      type: Object,
      required: false,
      default: null,
    },
    activeQuickFilters: {
      type: Array,
      required: false,
      default: () => [],
    },
    groupByFields: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  emits: [
    "open-create-item-modal",
    "open-batch-create-item-modal",
    "open-qr-scanner-modal",
    "open-create-collection-modal",
    "open-create-equipment-modal",
    "open-create-tag-modal",
    "open-add-to-collection-modal",
    "open-batch-share-modal",
    "delete-selected-items",
    "update:filters",
    "update:selected-columns",
    "reset-table",
    "remove-selected-items-from-collection",
    "bulk-activate-users",
    "bulk-deactivate-users",
    "users-data-changed",
    "bulk-invalidate-tokens",
    "bulk-delete-groups",
    "advanced-query-results",
    "update:active-quick-filters",
    "update:group-by-fields",
  ],
  data() {
    return {
      localFilters: { ...this.filters },
      isSelectedDropdownVisible: false,
      isSettingsDropdownVisible: false,
      isAdvSearchDropdownVisible: false,
      isDeletingItems: false,
      itemCount: 0,
      showBulkChangeRoleModal: false,
      showBulkAddToGroupModal: false,
      showBulkChangeManagersModal: false,
      appliedQuerySummary: null,
    };
  },
  computed: {
    hasActionButtons() {
      return (
        ["samples", "collections", "equipment"].includes(this.dataType) ||
        (this.dataType === "startingMaterials" && this.editableInventory) ||
        (this.dataType === "tags" && this.isLoggedIn)
      );
    },
    adminSuperUserMode() {
      return this.$store.getters.isAdminSuperUserModeActive;
    },
    isLoggedIn() {
      return this.$store.state.currentUserID !== null;
    },
    activeSearchChips() {
      const chips = [];
      if (this.appliedQuerySummary) {
        chips.push({
          key: "query",
          label: this.appliedQuerySummary,
          clear: this.clearAppliedQuery,
        });
      }
      if (this.activeQuickFilters.length) {
        chips.push({
          key: "quick-filters",
          label: this.activeQuickFilters
            .map((id) => QUICK_FILTERS.find((f) => f.id === id)?.label || id)
            .join(", "),
          clear: () => this.onUpdateQuickFilters([]),
        });
      }
      if (this.groupByFields.length) {
        chips.push({
          key: "group-by",
          label: `Group: ${this.groupByFields.map((g) => g.label).join(" → ")}`,
          clear: () => this.onUpdateGroupByFields([]),
        });
      }
      return chips;
    },
  },
  watch: {
    itemsSelected(newVal) {
      if (newVal.length === 0) {
        this.isSelectedDropdownVisible = false;
      }
    },
    "localFilters.global.value"(newValue) {
      this.$emit("update:filters", { ...this.filters, global: { value: newValue } });
    },
    dataType() {
      // activeQuickFilters/groupByFields are reset by DynamicDataTable itself (it owns them);
      // this only clears this component's own local UI state.
      this.isAdvSearchDropdownVisible = false;
      this.appliedQuerySummary = null;
    },
  },
  methods: {
    itemLabel(count) {
      const labels = {
        samples: ["item", "items"],
        collections: ["collection", "collections"],
        equipment: ["equipment item", "equipment items"],
        startingMaterials: ["starting material", "starting materials"],
        collectionItems: ["item", "items"],
        users: ["user", "users"],
        tokens: ["token", "tokens"],
        groups: ["group", "groups"],
        tags: ["tag", "tags"],
      };
      const [singular, plural] = labels[this.dataType] || ["item", "items"];
      return count === 1 ? singular : plural;
    },
    openAdvancedQuery() {
      this.isAdvSearchDropdownVisible = false;
      this.$refs.advancedQueryBuilder?.open();
    },
    // activeQuickFilters/groupByFields are props owned by DynamicDataTable (the single
    // source of truth); these just forward the change upward instead of keeping a local copy.
    onUpdateQuickFilters(next) {
      this.$emit("update:active-quick-filters", next);
    },
    onUpdateGroupByFields(next) {
      this.$emit("update:group-by-fields", next);
    },
    clearAppliedQuery() {
      this.$refs.advancedQueryBuilder?.clearFilters();
    },
    async confirmDeletion() {
      const isTags = this.dataType === "tags";
      const idsSelected = this.itemsSelected.map(
        (x) => x.item_id || x.collection_id || x.immutable_id,
      );
      // Tags have no human id; label them by name instead of immutable_id.
      const labels = isTags ? this.itemsSelected.map((x) => x.name) : idsSelected;
      let labelText = labels;
      if (labels.length > 10) {
        labelText = labels.slice(0, 10).join(", ") + ", ...";
      }
      const confirmed = await DialogService.confirm({
        title: "Confirm Deletion",
        message: isTags
          ? `Are you sure you want to delete ${this.itemsSelected.length} selected tag(s)? They will be removed from any items using them. (${labelText})`
          : `Are you sure you want to delete ${this.itemsSelected.length} selected items? (${labelText})`,
        type: "warning",
      });
      if (confirmed) {
        this.deleteItems(idsSelected);
        this.$emit("delete-selected-items");
      }
      this.isSelectedDropdownVisible = false;
    },
    async deleteItems(ids) {
      try {
        this.itemCount = ids.length;
        this.isDeletingItems = true;

        let deletePromises = [];

        if (this.dataType === "samples") {
          deletePromises = ids.map((id) => deleteSample(id));
        } else if (this.dataType === "collections") {
          deletePromises = ids.map((id) => deleteCollection(id, { collection_id: id }));
        } else if (this.dataType === "startingMaterials") {
          deletePromises = ids.map((id) => deleteStartingMaterial(id));
        } else if (this.dataType === "equipment") {
          deletePromises = ids.map((id) => deleteEquipment(id));
        } else if (this.dataType === "tags") {
          deletePromises = ids.map((id) => deleteTag(id));
        }

        await Promise.all(deletePromises);
      } catch (error) {
        console.error("Error during batch deletion:", error);
      } finally {
        this.isDeletingItems = false;
      }
    },
    async confirmRemoveFromCollection() {
      const refcodesSelected = this.itemsSelected.map((item) => item.refcode);

      if (
        confirm(
          `Are you sure you want to remove ${refcodesSelected.length} item(s) from ${this.collectionId} ? (${refcodesSelected})`,
        )
      ) {
        await this.removeItemsFromCollection(refcodesSelected);
        this.$emit("remove-selected-items-from-collection");
      }
      this.isSelectedDropdownVisible = false;
    },
    async removeItemsFromCollection(refcodes) {
      try {
        this.itemCount = refcodes.length;
        this.isDeletingItems = true;

        await removeItemsFromCollection(this.collectionId, refcodes);
      } catch (error) {
        console.error("Error during removal from collection:", error);
      } finally {
        this.isDeletingItems = false;
      }
    },
    handleAddToCollection() {
      this.$emit("open-add-to-collection-modal");
      this.isSelectedDropdownVisible = false;
    },
    columnLabel(option) {
      return option.label || option.header || option.field;
    },
    async resetTable() {
      this.isSettingsDropdownVisible = false;
      const confirmed = await DialogService.confirm({
        title: "Confirm reset",
        message:
          "Are you sure you want to reset your preferences (visible columns, widths) for this table?",
        type: "info",
      });
      if (confirmed) {
        this.$emit("reset-table");
      }
    },
    handleBatchShare() {
      this.$emit("open-batch-share-modal");
      this.isSelectedDropdownVisible = false;
    },
    async handleBulkActivateUsers() {
      const userIds = this.itemsSelected.map((u) => u.immutable_id);

      const confirmed = await DialogService.confirm({
        title: "Activate Users",
        message: `Are you sure you want to activate ${userIds.length} user(s)?`,
        type: "info",
      });

      if (!confirmed) {
        this.isSelectedDropdownVisible = false;
        return;
      }

      try {
        this.itemCount = userIds.length;
        this.isDeletingItems = true;

        const promises = userIds.map((userId) => saveUser(userId, { account_status: "active" }));
        await Promise.all(promises);

        this.itemsSelected.forEach((user) => {
          if (user.allUsers) {
            const userInArray = user.allUsers.find((u) => u.immutable_id === user.immutable_id);
            if (userInArray) {
              userInArray.account_status = "active";
            }
          }
        });

        DialogService.alert({
          title: "Success",
          message: `${userIds.length} user(s) activated successfully.`,
          type: "info",
        });
      } catch (error) {
        console.error("Error activating users:", error);
        DialogService.error({
          title: "Error",
          message: "Failed to activate some users.",
        });
      } finally {
        this.isDeletingItems = false;
        this.isSelectedDropdownVisible = false;
        this.$emit("users-data-changed");
        this.$emit("delete-selected-items");
      }
    },

    async handleBulkDeactivateUsers() {
      const userIds = this.itemsSelected.map((u) => u.immutable_id);

      const confirmed = await DialogService.confirm({
        title: "Deactivate Users",
        message: `Are you sure you want to deactivate ${userIds.length} user(s)?`,
        type: "warning",
      });

      if (!confirmed) {
        this.isSelectedDropdownVisible = false;
        return;
      }

      try {
        this.itemCount = userIds.length;
        this.isDeletingItems = true;

        const promises = userIds.map((userId) =>
          saveUser(userId, { account_status: "deactivated" }),
        );
        await Promise.all(promises);

        this.itemsSelected.forEach((user) => {
          if (user.allUsers) {
            const userInArray = user.allUsers.find((u) => u.immutable_id === user.immutable_id);
            if (userInArray) {
              userInArray.account_status = "deactivated";
            }
          }
        });

        DialogService.alert({
          title: "Success",
          message: `${userIds.length} user(s) deactivated successfully.`,
          type: "info",
        });
      } catch (error) {
        console.error("Error deactivating users:", error);
        DialogService.error({
          title: "Error",
          message: "Failed to deactivate some users.",
        });
      } finally {
        this.isDeletingItems = false;
        this.isSelectedDropdownVisible = false;
        this.$emit("users-data-changed");
        this.$emit("delete-selected-items");
      }
    },
    async handleBulkChangeRole(newRole) {
      const adminUsers = this.itemsSelected.filter((u) => u.role === "admin");

      if (adminUsers.length > 0 && newRole !== "admin") {
        const confirmed = await DialogService.confirm({
          title: "Remove Admin Privileges",
          message: `You are about to remove admin privileges from ${adminUsers.length} admin user(s). This action will revoke their full system access. Are you sure?`,
          type: "warning",
        });
        if (!confirmed) {
          return;
        }
      }

      const confirmed = await DialogService.confirm({
        title: "Change User Roles",
        message: `Are you sure you want to change the role of ${this.itemsSelected.length} user(s) to "${newRole}"?`,
        type: "warning",
      });

      if (!confirmed) {
        return;
      }

      try {
        this.itemCount = this.itemsSelected.length;
        this.isDeletingItems = true;

        const results = await Promise.allSettled(
          this.itemsSelected.map((user) => saveRole(user.immutable_id, { role: newRole })),
        );

        const successCount = results.filter((r) => r.status === "fulfilled").length;
        const failureCount = results.filter((r) => r.status === "rejected").length;

        results.forEach((result, index) => {
          if (result.status === "fulfilled") {
            const user = this.itemsSelected[index];
            if (user.allUsers) {
              const userInArray = user.allUsers.find((u) => u.immutable_id === user.immutable_id);
              if (userInArray) {
                userInArray.role = newRole;
              }
            }
          }
        });

        let message = `${successCount} user(s) successfully updated to "${newRole}".`;
        if (failureCount > 0) {
          message += ` ${failureCount} user(s) failed to update.`;
        }
        if (adminUsers.length > 0 && newRole !== "admin") {
          message += ` ${adminUsers.length} admin(s) had their privileges revoked.`;
        }

        DialogService.alert({
          title: failureCount > 0 ? "Partially Successful" : "Success",
          message: message,
          type: failureCount > 0 ? "warning" : "info",
        });
      } catch (error) {
        console.error("Error changing user roles:", error);
        DialogService.error({
          title: "Error",
          message: "Failed to change roles for some users.",
        });
      } finally {
        this.isDeletingItems = false;
        this.isSelectedDropdownVisible = false;
        this.$emit("users-data-changed");
        this.$emit("delete-selected-items");
      }
    },
    async handleBulkAddToGroup(selectedGroups) {
      const groupNames = selectedGroups.map((g) => g.display_name).join(", ");
      const confirmed = await DialogService.confirm({
        title: "Add Users to Groups",
        message: `Are you sure you want to add ${this.itemsSelected.length} user(s) to: ${groupNames}?`,
        type: "info",
      });

      if (!confirmed) {
        return;
      }

      try {
        this.itemCount = this.itemsSelected.length;
        this.isDeletingItems = true;

        const promises = [];
        for (const group of selectedGroups) {
          for (const user of this.itemsSelected) {
            promises.push(addUserToGroup(group.immutable_id, user.immutable_id));
          }
        }

        const results = await Promise.allSettled(promises);

        const successCount = results.filter((r) => r.status === "fulfilled").length;
        const failureCount = results.filter((r) => r.status === "rejected").length;

        results.forEach((result, index) => {
          if (result.status === "fulfilled") {
            const groupIndex = Math.floor(index / this.itemsSelected.length);
            const userIndex = index % this.itemsSelected.length;
            const group = selectedGroups[groupIndex];
            const user = this.itemsSelected[userIndex];

            if (user.allUsers) {
              const userInArray = user.allUsers.find((u) => u.immutable_id === user.immutable_id);
              if (userInArray) {
                if (!userInArray.groups) {
                  userInArray.groups = [];
                }
                const groupExists = userInArray.groups.some(
                  (g) => g.immutable_id === group.immutable_id,
                );
                if (!groupExists) {
                  userInArray.groups.push({
                    immutable_id: group.immutable_id,
                    display_name: group.display_name,
                  });
                }
              }
            }
          }
        });

        let message = `Successfully processed ${successCount} operation(s).`;
        if (failureCount > 0) {
          message += ` ${failureCount} operation(s) failed (users may already be in groups).`;
        }

        DialogService.alert({
          title: failureCount > 0 ? "Partially Successful" : "Success",
          message: message,
          type: failureCount > 0 ? "warning" : "info",
        });
      } catch (error) {
        console.error("Error adding users to groups:", error);
        DialogService.error({
          title: "Error",
          message: "Failed to add users to groups.",
        });
      } finally {
        this.isDeletingItems = false;
        this.isSelectedDropdownVisible = false;
        console.log("Emitting users-data-changed");
        this.$emit("users-data-changed");
        this.$emit("delete-selected-items");
      }
    },
    async handleBulkChangeManagers(newManagers) {
      const confirmed = await DialogService.confirm({
        title: "Add Managers",
        message: `Are you sure you want to add these managers to ${this.itemsSelected.length} user(s)? Existing managers will be kept.`,
        type: "warning",
      });

      if (!confirmed) {
        return;
      }

      try {
        this.itemCount = this.itemsSelected.length;
        this.isDeletingItems = true;

        const newManagerIds = newManagers.map((m) => m.immutable_id);

        const results = await Promise.allSettled(
          this.itemsSelected.map((user) => {
            const existingManagerIds = (user.managers || []).map((m) => m.immutable_id);
            const mergedManagerIds = [...new Set([...existingManagerIds, ...newManagerIds])];
            return saveUserManagers(user.immutable_id, mergedManagerIds);
          }),
        );

        const successCount = results.filter((r) => r.status === "fulfilled").length;
        const failureCount = results.filter((r) => r.status === "rejected").length;

        results.forEach((result, index) => {
          if (result.status === "fulfilled") {
            const user = this.itemsSelected[index];
            if (user.allUsers) {
              const userInArray = user.allUsers.find((u) => u.immutable_id === user.immutable_id);
              if (userInArray) {
                const existingManagers = userInArray.managers || [];
                const allManagerIds = [
                  ...new Set([...existingManagers.map((m) => m.immutable_id), ...newManagerIds]),
                ];
                userInArray.managers = this.allUsers.filter((u) =>
                  allManagerIds.includes(u.immutable_id),
                );
              }
            }
          }
        });

        let message = `${successCount} user(s) successfully updated.`;
        if (failureCount > 0) {
          message += ` ${failureCount} user(s) failed to update.`;
        }

        DialogService.alert({
          title: failureCount > 0 ? "Partially Successful" : "Success",
          message: message,
          type: failureCount > 0 ? "warning" : "info",
        });
      } catch (error) {
        console.error("Error changing user managers:", error);
        DialogService.error({
          title: "Error",
          message: "Failed to change managers for some users.",
        });
      } finally {
        this.isDeletingItems = false;
        this.isSelectedDropdownVisible = false;
        this.$emit("users-data-changed");
        this.$emit("delete-selected-items");
      }
    },
    async handleBulkInvalidateTokens() {
      const activeTokens = this.itemsSelected.filter((token) => token.active);

      if (activeTokens.length === 0) {
        await DialogService.alert({
          title: "No Active Tokens",
          message: "All selected tokens are already invalidated.",
          type: "info",
        });
        return;
      }

      const confirmed = await DialogService.confirm({
        title: "Invalidate Access Tokens",
        message: `Are you sure you want to invalidate ${activeTokens.length} active token(s)?<br><br>This action cannot be undone and will immediately block access for anyone using these tokens.`,
        type: "error",
        confirmButtonText: "Invalidate Tokens",
        cancelButtonText: "Cancel",
      });

      if (!confirmed) {
        return;
      }

      this.isDeletingItems = true;
      this.itemCount = activeTokens.length;

      try {
        const results = await Promise.allSettled(
          activeTokens.map((token) => invalidateToken(token.refcode)),
        );

        const successCount = results.filter((r) => r.status === "fulfilled").length;
        const failureCount = results.filter((r) => r.status === "rejected").length;

        results.forEach((result, index) => {
          if (result.status === "fulfilled") {
            const token = activeTokens[index];
            if (token.allTokens) {
              const tokenInArray = token.allTokens.find((t) => t._id === token._id);
              if (tokenInArray) {
                tokenInArray.active = false;
                tokenInArray.invalidated_at = new Date().toISOString();
              }
            }
          }
        });

        let message = `${successCount} token(s) successfully invalidated.`;
        if (failureCount > 0) {
          message += ` ${failureCount} token(s) failed to invalidate.`;
        }

        await DialogService.alert({
          title: failureCount > 0 ? "Partially Successful" : "Success",
          message: message,
          type: failureCount > 0 ? "warning" : "info",
        });

        this.$emit("bulk-invalidate-tokens");
      } catch (error) {
        console.error("Error invalidating tokens:", error);
        await DialogService.error({
          title: "Error",
          message: "Failed to invalidate some tokens.",
        });
      } finally {
        this.isDeletingItems = false;
      }
    },
    async handleBulkDeleteGroups() {
      const confirmed = await DialogService.confirm({
        title: "Delete Groups",
        message: `Are you sure you want to delete ${this.itemsSelected.length} group(s)?<br><br>This action cannot be undone.`,
        type: "error",
        confirmButtonText: "Delete Groups",
        cancelButtonText: "Cancel",
      });

      if (!confirmed) {
        return;
      }

      this.isDeletingItems = true;
      this.itemCount = this.itemsSelected.length;

      try {
        const results = await Promise.allSettled(
          this.itemsSelected.map((group) => deleteGroup(group.immutable_id || group._id)),
        );

        const successCount = results.filter((r) => r.status === "fulfilled").length;
        const failureCount = results.filter((r) => r.status === "rejected").length;

        let message = `${successCount} group(s) successfully deleted.`;
        if (failureCount > 0) {
          message += ` ${failureCount} group(s) failed to delete.`;
        }

        await DialogService.alert({
          title: failureCount > 0 ? "Partially Successful" : "Success",
          message: message,
          type: failureCount > 0 ? "warning" : "info",
        });

        this.$emit("bulk-delete-groups");
      } catch (error) {
        console.error("Error deleting groups:", error);
        await DialogService.error({
          title: "Error",
          message: "Failed to delete some groups.",
        });
      } finally {
        this.isDeletingItems = false;
      }
    },
  },
};
</script>

<style scoped>
.button-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.btn-action-group {
  display: flex;
  gap: 0.5rem;
}

.btn-action {
  flex: 1;
  text-align: center;
  white-space: nowrap;
}

.table-tools {
  gap: 0.5rem;
  min-width: 0;
}

.selection-controls {
  gap: 0.5rem;
  min-width: 0;
}

.selection-summary {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-settings-group {
  display: flex;
  gap: 0.5rem;
  flex: 0 1 auto;
  min-width: 0;
}

.search-field {
  flex: 1 1 200px;
  min-width: 80px;
}

.search-field :deep(.p-inputtext) {
  height: calc(1.5em + 0.75rem + 2px);
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
}

.search-input {
  height: calc(1.5em + 0.75rem + 2px);
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
  border-radius: 0.25rem;
  width: 100%;
}

.settings-dropdown {
  min-width: 220px;
  padding: 0.5rem 0;
}

.dropdown-item-text {
  padding: 0.5rem 1rem;
}

.column-select-dropdown {
  width: 100%;
}
</style>
