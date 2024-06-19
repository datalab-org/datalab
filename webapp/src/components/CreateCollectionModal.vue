<template>
  <form @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="Boolean(IDValidationMessage) || !Boolean(collection_id)"
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
            <div class="form-error" v-html="IDValidationMessage"></div>
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
import Modal from "@/components/Modal.vue";
import ItemSelect from "@/components/ItemSelect.vue";
import { createNewCollection } from "@/server_fetch_utils.js";

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
    IDValidationMessage() {
      if (this.collection_id == null) {
        return "";
      } // Don't throw an error before the user starts typing

      if (this.takenCollectionIds.includes(this.collection_id)) {
        return `<a href='edit/${this.collection_id}'>${this.collection_id}</a> already in use.`;
      }
      if (!/^[a-zA-Z0-9_-]+$/.test(this.collection_id)) {
        return "ID can only contain alphanumeric characters, dashes ('-') and underscores ('_')";
      }
      if (this.collection_id.length < 1 || this.collection_id.length > 40) {
        return "ID must be between 1 and 40 characters in length";
      }
      return "";
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
              alert("Error with creating new sample: " + error);
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
