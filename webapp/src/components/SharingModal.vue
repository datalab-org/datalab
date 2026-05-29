<template>
  <Modal :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <template #header>
      <font-awesome-icon icon="share-alt" class="me-2" />
      Share
      <FormattedItemName
        v-if="headerName"
        class="ms-2"
        :item_id="headerName"
        :item-type="itemType"
      />
    </template>
    <template #body>
      <ul class="nav nav-tabs mb-4">
        <li class="nav-item">
          <a
            class="nav-link"
            :class="{ active: activeTab === 'direct' }"
            href="#"
            @click.prevent="activeTab = 'direct'"
          >
            <font-awesome-icon icon="user-friends" class="me-2" />
            Direct access
          </a>
        </li>
        <li class="nav-item">
          <a
            class="nav-link"
            :class="{ active: activeTab === 'links' }"
            href="#"
            @click.prevent="activeTab = 'links'"
          >
            <font-awesome-icon icon="link" class="me-2" />
            Sharing links &amp; labels
          </a>
        </li>
      </ul>

      <!-- Direct access tab -->
      <div v-if="activeTab === 'direct'">
        <!-- People with access -->
        <div class="mb-4">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <h6 class="fw-bold mb-0">People with access</h6>
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary"
              @click="editingPeople = !editingPeople"
            >
              <font-awesome-icon :icon="editingPeople ? 'check' : 'pen'" class="me-1" />
              {{ editingPeople ? "Done" : "Manage" }}
            </button>
          </div>
          <OnClickOutside v-if="editingPeople" @trigger="editingPeople = false">
            <UserSelect
              v-model="creatorsShadow"
              aria-label="Manage people with access"
              multiple
              @click.stop
            />
          </OnClickOutside>
          <ul v-else-if="creators && creators.length" class="list-unstyled mb-0">
            <li
              v-for="person in creators"
              :key="person.immutable_id"
              class="share-row d-flex align-items-center py-2"
            >
              <Creators :creators="[person]" :size="36" class="flex-grow-1" />
              <div class="role-control text-muted" title="Creators currently have edit access">
                <span class="me-3">Editor</span>
                <font-awesome-icon icon="lock" />
              </div>
            </li>
          </ul>
          <p v-else class="text-muted small mb-0">No users have direct access yet.</p>
        </div>

        <!-- Groups with access -->
        <div class="mb-4">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <h6 class="fw-bold mb-0">Groups with access</h6>
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary"
              @click="editingGroups = !editingGroups"
            >
              <font-awesome-icon :icon="editingGroups ? 'check' : 'pen'" class="me-1" />
              {{ editingGroups ? "Done" : "Manage" }}
            </button>
          </div>
          <OnClickOutside v-if="editingGroups" @trigger="editingGroups = false">
            <GroupSelect v-model="groupsShadow" multiple @click.stop />
          </OnClickOutside>
          <ul v-else-if="groups && groups.length" class="list-unstyled mb-0">
            <li
              v-for="group in groups"
              :key="group.immutable_id"
              class="share-row d-flex align-items-center py-2"
            >
              <div class="flex-grow-1">
                <FormattedGroupName :group="group" :size="36" />
              </div>
              <div class="role-control text-muted" title="Groups currently have read-only access">
                <span class="me-3">Viewer</span>
                <font-awesome-icon icon="lock" />
              </div>
            </li>
          </ul>
          <p v-else class="text-muted small mb-0">No groups have access yet.</p>
        </div>
      </div>

      <!-- Sharing links & labels tab -->
      <div v-else-if="activeTab === 'links'">
        <p class="text-muted small">
          Share this item with a printable QR code or copyable link. Public links bypass
          authentication and can be revoked at any time.
        </p>
        <QRCode :refcode="refcode" />
      </div>
    </template>
    <template #footer>
      <button type="button" class="btn btn-primary" @click="$emit('update:modelValue', false)">
        Done
      </button>
    </template>
  </Modal>
</template>

<script>
import { toRaw } from "vue";
import { OnClickOutside } from "@vueuse/components";
import Modal from "@/components/Modal.vue";
import QRCode from "@/components/QRCode.vue";
import UserSelect from "@/components/UserSelect.vue";
import GroupSelect from "@/components/GroupSelect.vue";
import FormattedItemName from "@/components/FormattedItemName.vue";
import Creators from "@/components/Creators.vue";
import FormattedGroupName from "@/components/FormattedGroupName.vue";
import { DialogService } from "@/services/DialogService";
import { updateItemPermissions, updateCollectionPermissions } from "@/server_fetch_utils.js";

export default {
  name: "SharingModal",
  components: {
    Modal,
    QRCode,
    UserSelect,
    GroupSelect,
    FormattedItemName,
    Creators,
    FormattedGroupName,
    OnClickOutside,
  },
  props: {
    modelValue: Boolean,
    refcode: { type: String, default: null },
    itemId: { type: String, default: null },
    collectionId: { type: String, default: null },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      activeTab: "direct",
      editingPeople: false,
      editingGroups: false,
      creatorsShadow: [],
      groupsShadow: [],
    };
  },
  computed: {
    isCollection() {
      return !!this.collectionId;
    },
    sourceData() {
      if (this.isCollection) {
        return this.$store.state.all_collection_data[this.collectionId] || {};
      }
      return this.$store.state.all_item_data[this.itemId] || {};
    },
    itemType() {
      return this.isCollection ? "collections" : this.sourceData.type;
    },
    headerName() {
      return this.isCollection ? this.collectionId : this.itemId;
    },
    creators() {
      return this.sourceData.creators || [];
    },
    groups() {
      return this.sourceData.groups || [];
    },
  },
  watch: {
    creators: {
      immediate: true,
      handler(newVal) {
        this.creatorsShadow = Array.isArray(newVal) ? [...newVal] : [];
      },
    },
    groups: {
      immediate: true,
      handler(newVal) {
        this.groupsShadow = Array.isArray(newVal) ? [...newVal] : [];
      },
    },
    editingPeople(now, was) {
      if (was && !now) this.persistCreators();
    },
    editingGroups(now, was) {
      if (was && !now) this.persistGroups();
    },
  },
  methods: {
    async persistCreators() {
      if (JSON.stringify(toRaw(this.creators)) === JSON.stringify(toRaw(this.creatorsShadow))) {
        return;
      }
      if (!this.creatorsShadow.length) {
        DialogService.error({
          title: "Permission Update Failed",
          message: "You must have at least one creator.",
        });
        this.creatorsShadow = [...this.creators];
        return;
      }
      const confirmed = await DialogService.confirm({
        title: "Update Permissions",
        message: "Update the people with access to this item?",
        type: "warning",
      });
      if (!confirmed) {
        this.creatorsShadow = [...this.creators];
        return;
      }
      try {
        if (this.isCollection) {
          await updateCollectionPermissions(this.collectionId, this.creatorsShadow);
          this.$store.commit("updateCollectionData", {
            collection_id: this.collectionId,
            block_data: { creators: [...this.creatorsShadow] },
          });
        } else {
          await updateItemPermissions(this.refcode, this.creatorsShadow);
          this.$store.commit("updateItemData", {
            item_id: this.itemId,
            item_data: { creators: [...this.creatorsShadow] },
          });
        }
      } catch (err) {
        DialogService.error({
          title: "Permission Update Failed",
          message: "Error updating permissions: " + err,
        });
        this.creatorsShadow = [...this.creators];
      }
    },
    async persistGroups() {
      if (JSON.stringify(toRaw(this.groups)) === JSON.stringify(toRaw(this.groupsShadow))) {
        return;
      }
      const confirmed = await DialogService.confirm({
        title: "Update Permissions",
        message: "Update the groups with access to this item?",
        type: "warning",
      });
      if (!confirmed) {
        this.groupsShadow = [...this.groups];
        return;
      }
      try {
        if (this.isCollection) {
          await updateCollectionPermissions(this.collectionId, null, this.groupsShadow);
          this.$store.commit("updateCollectionData", {
            collection_id: this.collectionId,
            block_data: { groups: [...this.groupsShadow] },
          });
        } else {
          await updateItemPermissions(this.refcode, null, this.groupsShadow);
          this.$store.commit("updateItemData", {
            item_id: this.itemId,
            item_data: { groups: [...this.groupsShadow] },
          });
        }
      } catch (err) {
        DialogService.error({
          title: "Permission Update Failed",
          message: "Error updating group permissions: " + err,
        });
        this.groupsShadow = [...this.groups];
      }
    },
  },
};
</script>

<style scoped>
.nav-tabs .nav-link {
  color: #0056b3;
  font-weight: 600;
}
.nav-tabs .nav-link.active {
  color: #003d82;
}

.share-row {
  border-bottom: 1px solid #f1f3f5;
}
.share-row:last-child {
  border-bottom: none;
}

.role-control {
  cursor: not-allowed;
  user-select: none;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}
.role-control:hover {
  background-color: #f1f3f5;
}
</style>
