<template>
  <form @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="Boolean(isValidEntryID) || !Boolean(collection_id)"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <template #header> Create new collection </template>

      <template #body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="collection-id" class="col-form-label">Collection ID:</label>
            <input
              id="collection-id"
              v-model="collection_id"
              type="text"
              class="form-control"
              required
            />
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div class="form-error" v-html="isValidEntryID"></div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="title">Full title:</label>
            <input id="title" v-model="title" type="text" class="form-control" />
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="startWithMembers">(Optional) Start with members:</label>
            <ItemSelect
              v-model="startingMembers"
              aria-labelledby="startWithMembersLabel"
              multiple
            />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import { DialogService } from "@/services/DialogService";

import Modal from "@/components/Modal.vue";
import ItemSelect from "@/components/ItemSelect.vue";
import { createNewCollection } from "@/server_fetch_utils.js";
import { validateEntryID } from "@/field_utils.js";

export default {
  name: "CreateCollectionModal",
  components: {
    Modal,
    ItemSelect,
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  data() {
    return {
      collection_id: null,
      title: "",
      selectedCollectionToCopy: null,
      startingMembers: [],
    };
  },
  computed: {
    takenCollectionIds() {
      return this.$store.state.collection_list
        ? this.$store.state.collection_list.map((x) => x.collection_id)
        : [];
    },
    isValidEntryID() {
      return validateEntryID(this.collection_id, this.takenCollectionIds);
    },
  },
  methods: {
    async submitForm() {
      await createNewCollection(this.collection_id, this.title, {
        starting_members: this.startingMembers,
      })
        .then(() => {
          this.$emit("update:modelValue", false); // close this modal
          // Disable scroll now that items are added to the top by default
          // document.getElementById(this.item_id).scrollIntoView({ behavior: "smooth" });
          this.collection_id = null;
          this.title = null;
        })
        .catch((error) => {
          let id_error = false;
          try {
            if (error.includes("collection_id_validation_error")) {
              this.takenCollectionIds.push(this.collection_id);
              id_error = true;
            }
          } catch (e) {
            console.log("error parsing error message", e);
          } finally {
            if (!id_error) {
              DialogService.error({
                title: "Collection Creation Failed",
                message: "Error with creating new collection: " + error,
              });
            }
          }
        });
    },
    setCopiedName() {
      if (!this.selectedCollectionToCopy) {
        this.name = "";
      }
      this.name = `COPY OF ${this.selectedCollectionToCopy.name}`;
    },
  },
};
</script>

<style scoped>
.form-error {
  color: red;
}

:deep(.form-error a) {
  color: #820000;
  font-weight: 600;
}
</style>
