<template>
  <form class="modal-enclosure" data-testid="batch-tag-form" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="selectedTags.length === 0 || isSubmitting"
      @update:model-value="handleClose"
    >
      <template #header> Add tags </template>
      <template #body>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="batch-tag-items-selected" class="col-form-label"> Items Selected: </label>
            <div id="batch-tag-items-selected" class="dynamic-input">
              <FormattedItemName
                v-for="item in itemsSelected"
                :key="item.refcode"
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
            Existing tags will be preserved.
          </small>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="batchTagsLabel">Tags to add:</label>
            <TagSelect
              id="batch-tag-select"
              v-model="selectedTags"
              aria-labelledby="batchTagsLabel"
            />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import FormattedItemName from "@/components/FormattedItemName";
import TagSelect from "@/components/TagSelect.vue";
import { DialogService } from "@/services/DialogService";

import {
  addTagsToItems,
  getEquipmentList,
  getSampleList,
  getStartingMaterialList,
} from "@/server_fetch_utils";

export default {
  name: "BatchTagModal",
  components: {
    Modal,
    FormattedItemName,
    TagSelect,
  },
  props: {
    modelValue: Boolean,
    itemsSelected: {
      type: Array,
      required: true,
    },
    dataType: {
      type: String,
      required: true,
    },
  },
  emits: ["update:modelValue", "itemsUpdated"],
  data() {
    return {
      selectedTags: [],
      isSubmitting: false,
    };
  },
  methods: {
    async submitForm() {
      if (this.selectedTags.length === 0 || this.isSubmitting) {
        return;
      }

      this.isSubmitting = true;
      try {
        const response = await addTagsToItems(
          this.itemsSelected.map((item) => item.refcode),
          this.selectedTags.map((tag) => tag.immutable_id),
        );

        if (this.dataType === "samples") {
          await getSampleList();
        } else if (this.dataType === "startingMaterials") {
          await getStartingMaterialList();
        } else if (this.dataType === "equipment") {
          await getEquipmentList();
        }

        const failedCount = response.failed_refcodes.length;
        const parts = [
          `${response.updated_count} item(s) updated.`,
          `${response.unchanged_count} item(s) already had all selected tags.`,
        ];
        if (failedCount > 0) {
          parts.push(`${failedCount} item(s) could not be updated.`);
        }

        DialogService.alert({
          title:
            failedCount > 0
              ? "Tags Partially Added"
              : response.updated_count === 0
                ? "No Changes Made"
                : "Tags Added",
          message: parts.join(" "),
          type: failedCount > 0 ? "warning" : "success",
        });

        this.$emit("itemsUpdated");
        this.handleClose();
      } catch (error) {
        DialogService.error({
          title: "Unable to Add Tags",
          message: error.message || error,
        });
      } finally {
        this.isSubmitting = false;
      }
    },
    handleClose() {
      this.selectedTags = [];
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
  max-height: 10rem;
  overflow-y: auto;
  box-sizing: border-box;
  gap: 0.2em;
}
</style>
