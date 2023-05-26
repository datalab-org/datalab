<template>
  <form @submit.prevent="submitForm">
    <Modal
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :disableSubmit="Boolean(IDValidationMessage) || !Boolean(collection_id)"
    >
      <template v-slot:header> Create new collection </template>

      <template v-slot:body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="collection-id" class="col-form-label">Collection ID:</label>
            <input
              v-model="collection_id"
              type="text"
              class="form-control"
              id="collection-id"
              required
            />
            <div class="form-error" v-html="IDValidationMessage"></div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="title">Full title:</label>
            <input id="title" type="text" v-model="title" class="form-control" />
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="startWithMembers">(Optional) Start with members:</label>
            <ItemSelect
              aria-labelledby="startWithMembersLabel"
              multiple
              v-model="startingMembers"
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
  data() {
    return {
      collection_id: null,
      title: "",
      selectedCollectionToCopy: null,
      startingMembers: [],
    };
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
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
  components: {
    Modal,
    ItemSelect,
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
