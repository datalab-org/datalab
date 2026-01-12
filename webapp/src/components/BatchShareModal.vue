<template>
  <form class="modal-enclosure" data-testid="batch-share-form" @submit.prevent="submitForm">
    <Modal :model-value="modelValue" @update:model-value="handleClose">
      <template #header> Share Items</template>
      <template #body>
        <div v-if="modelValue">
          <div class="form-row">
            <div class="form-group col-md-12">
              <label for="items-selected" class="col-form-label">Items Selected:</label>
              <div id="items-selected" class="dynamic-input">
                <FormattedItemName
                  v-for="(item, index) in itemsSelected"
                  :key="index"
                  :item_id="item.item_id"
                  :item-type="item.type"
                  enable-click
                />
              </div>
            </div>
          </div>

          <div class="alert alert-info">
            <small>
              <font-awesome-icon icon="info-circle" class="mr-1" />
              Select people and/or groups to add to these items. Existing permissions will be
              preserved.
            </small>
          </div>

          <div class="form-row">
            <div class="col-md-6 form-group">
              <label id="creatorsLabel">Add creators (read/write access):</label>
              <UserSelect v-model="newCreators" aria-labelledby="creatorsLabel" multiple />
            </div>
            <div class="col-md-6 form-group">
              <label id="groupsLabel">Add groups (read-only access):</label>
              <GroupSelect v-model="newGroups" aria-labelledby="groupsLabel" multiple />
            </div>
          </div>

          <div
            v-if="newCreators.length === 0 && newGroups.length === 0"
            class="alert alert-warning"
          >
            <small>
              <font-awesome-icon icon="exclamation-triangle" class="mr-1" />
              Please select at least one person or group to add.
            </small>
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import FormattedItemName from "@/components/FormattedItemName";
import UserSelect from "@/components/UserSelect.vue";
import GroupSelect from "@/components/GroupSelect.vue";

import {
  fetchItemPermissions,
  updateItemPermissions,
  getSampleList,
  getStartingMaterialList,
  getEquipmentList,
} from "@/server_fetch_utils";

export default {
  name: "BatchShareModal",
  components: {
    Modal,
    FormattedItemName,
    UserSelect,
    GroupSelect,
  },
  props: {
    modelValue: Boolean,
    itemsSelected: {
      type: Array,
      required: true,
    },
  },
  emits: ["update:modelValue", "itemsUpdated"],
  data() {
    return {
      newCreators: [],
      newGroups: [],
    };
  },
  methods: {
    async submitForm() {
      if (this.newCreators.length === 0 && this.newGroups.length === 0) {
        return;
      }

      try {
        const refcodes = this.itemsSelected.map((item) => item.refcode);

        for (const refcode of refcodes) {
          const { creators: currentCreators, groups: currentGroups } =
            await fetchItemPermissions(refcode);

          const currentCreatorIds = currentCreators.map((c) => c.immutable_id || c._id);
          const creatorsToAdd = this.newCreators.filter(
            (c) => !currentCreatorIds.includes(c.immutable_id),
          );

          const currentGroupIds = currentGroups.map((g) => g.immutable_id || g._id);
          const groupsToAdd = this.newGroups.filter(
            (g) => !currentGroupIds.includes(g.immutable_id),
          );

          if (creatorsToAdd.length > 0 || groupsToAdd.length > 0) {
            const mergedCreators = [...currentCreators, ...creatorsToAdd];
            const mergedGroups = [...currentGroups, ...groupsToAdd];

            await updateItemPermissions(refcode, mergedCreators, mergedGroups);
          }
        }

        this.$emit("itemsUpdated");

        if (this.itemsSelected.some((item) => item.type === "samples" || item.type === "cells")) {
          getSampleList();
        } else if (this.itemsSelected.some((item) => item.type === "starting_materials")) {
          getStartingMaterialList();
        } else if (this.itemsSelected.some((item) => item.type === "equipment")) {
          getEquipmentList();
        }

        console.log("Items shared successfully.");

        this.handleClose();
      } catch (error) {
        console.error("Error sharing items:", error);
      }
    },

    handleClose() {
      this.newCreators = [];
      this.newGroups = [];
      this.$emit("update:modelValue", false);
    },
  },
};
</script>

<style scoped>
.dynamic-input {
  display: flex;
  flex-wrap: wrap;
  border: 1px solid #ced4da;
  padding: 0.375rem 0.75rem;
  border-radius: 0.25rem;
  max-width: 100%;
  box-sizing: border-box;
  gap: 0.2em;
}
</style>
