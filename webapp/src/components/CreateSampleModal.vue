<template>
  <form @submit.prevent="submitForm">
    <Modal
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :disableSubmit="Boolean(sampleIDValidationMessage) || !Boolean(item_id)"
    >
      <template v-slot:header> Add new sample </template>

      <template v-slot:body>
        <div class="form-row">
          <div class="form-group col-md-8">
            <label for="sample-id" class="col-form-label">Sample ID:</label>
            <input v-model="item_id" type="text" class="form-control" id="sample-id" required />
            <div class="form-error" v-html="sampleIDValidationMessage"></div>
          </div>
          <div class="form-group col-md-4">
            <label for="date" class="col-form-label">Date Created:</label>
            <input type="date" v-model="date" class="form-control" id="date" required />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="name">Sample Name:</label>
            <input id="name" type="text" v-model="name" class="form-control" />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import { createNewSample } from "@/server_fetch_utils.js";
export default {
  name: "CreateSampleModal",
  data() {
    return {
      item_id: null,
      date: new Date().toISOString().split("T")[0], // todo: add time zone support...			}
      name: "",
      takenItemIds: [],
    };
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  computed: {
    sampleIDValidationMessage() {
      if (this.item_id == null) {
        return "";
      } // Don't throw an error before the user starts typing

      if (this.takenItemIds.includes(this.item_id)) {
        return `<a href='edit/${this.item_id}'>${this.item_id}</a> already in use.`;
      }
      if (/\s/.test(this.item_id)) {
        return "ID cannot have any spaces";
      }
      if (this.item_id.length < 1 || this.item_id.length > 40) {
        return "ID must be between 1 and 40 characters in length";
      }
      return "";
    },
  },
  methods: {
    async submitForm() {
      console.log("new sample form submit triggered");

      await createNewSample(this.item_id, this.date, this.name)
        .then(() => {
          this.$emit("update:modelValue", false);
          document.getElementById(this.item_id).scrollIntoView({ behavior: "smooth" });
        })
        .catch((error) => {
          if (error.includes("item_id_validation_error")) {
            this.takenItemIds.push(this.item_id);
          } else {
            alert("Error with creating new sample: " + error);
          }
        });
    },
  },
  components: {
    Modal,
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
