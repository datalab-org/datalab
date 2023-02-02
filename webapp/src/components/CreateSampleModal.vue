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
          <div class="form-group col-md-6">
            <label for="sample-id" class="col-form-label">Sample ID:</label>
            <input v-model="item_id" type="text" class="form-control" id="sample-id" required />
            <div class="form-error" v-html="sampleIDValidationMessage"></div>
          </div>
          <div class="form-group col-md-6">
            <label for="date" class="col-form-label">Date Created:</label>
            <input
              type="datetime-local"
              v-model="date"
              class="form-control"
              id="date"
              :min="agesAgo"
              :max="oneYearOn()"
              required
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="name">Sample Name:</label>
            <input id="name" type="text" v-model="name" class="form-control" />
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="copyFromSelectLabel">(Optional) Copy from:</label>
            <ItemSelect
              aria-labelledby="copyFromSelectLabel"
              :modelValue="selectedItemToCopy"
              @update:modelValue="
                selectedItemToCopy = $event;
                setCopiedName();
              "
            />
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="startWithConstituentsLabel">(Optional) Start with constituents:</label>
            <ItemSelect
              aria-labelledby="startWithConstituentsLabel"
              multiple
              v-model="startingConstituents"
            />
            <!-- <ItemSelect v-model="selectedNewConstituent" @option:selected="addConstituent" /> -->
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import ItemSelect from "@/components/ItemSelect.vue";
import { createNewSample } from "@/server_fetch_utils.js";
export default {
  name: "CreateSampleModal",
  data() {
    return {
      item_id: null,
      date: this.now(),
      name: "",
      takenItemIds: [], // this holds ids that have been tried, whereas the computed takenSampleIds holds ids in the sample table
      selectedItemToCopy: null,
      startingConstituents: [],
      agesAgo: new Date("1970-01-01").toISOString().slice(0, -8), // a datetime for the unix epoch start
    };
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  computed: {
    takenSampleIds() {
      return this.$store.state.sample_list
        ? this.$store.state.sample_list.map((x) => x.item_id)
        : [];
    },
    sampleIDValidationMessage() {
      if (this.item_id == null) {
        return "";
      } // Don't throw an error before the user starts typing

      if (this.takenItemIds.includes(this.item_id) || this.takenSampleIds.includes(this.item_id)) {
        return `<a href='edit/${this.item_id}'>${this.item_id}</a> already in use.`;
      }
      if (!/^[a-zA-Z0-9_-]+$/.test(this.item_id)) {
        return "ID can only contain alphanumeric characters, dashes ('-') and underscores ('_')";
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

      const startingSynthesisBlock = this.startingConstituents.map((x) => ({
        item: x,
        quantity: null,
      }));

      await createNewSample(
        this.item_id,
        this.date,
        this.name,
        {
          synthesis_constituents: startingSynthesisBlock,
        },
        this.selectedItemToCopy && this.selectedItemToCopy.item_id
      )
        .then(() => {
          this.$emit("update:modelValue", false); // close this modal
          // Disable scroll now that items are added to the top by default
          // document.getElementById(this.item_id).scrollIntoView({ behavior: "smooth" });
          this.item_id = null;
          this.name = null;
          this.date = this.now(); // reset date to the new current time
        })
        .catch((error) => {
          let is_item_id_error = false;
          try {
            if (error.includes("item_id_validation_error")) {
              this.takenItemIds.push(this.item_id);
              is_item_id_error = true;
            }
          } catch (e) {
            console.log("error parsing error message", e);
          } finally {
            if (!is_item_id_error) {
              alert("Error with creating new sample: " + error);
            }
          }
        });
    },
    oneYearOn() {
      // returns a timestamp 1 year from now
      let d = new Date();
      d.setFullYear(d.getFullYear() + 1);
      return d.toISOString().slice(0, -8);
    },
    now() {
      // returns a timestamp for right now
      return new Date().toISOString().slice(0, -8);
    },

    setCopiedName() {
      if (!this.selectedItemToCopy) {
        this.name = "";
      }
      this.name = `COPY OF ${this.selectedItemToCopy.name}`;
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
