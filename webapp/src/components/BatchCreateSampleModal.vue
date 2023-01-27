<template>
  <form class="modal-enclosure" @submit.prevent="submitForm">
    <Modal
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :disableSubmit="Boolean(sampleIDValidationMessage) || !Boolean(item_id)"
    >
      <template v-slot:header> Add new samples </template>

      <template v-slot:body>
        <div class="row">
          <div class="col-md-8 mt-2">
            <font-awesome-icon
              :icon="['fas', 'chevron-right']"
              fixed-width
              class="collapse-arrow"
              :class="{ expanded: templateIsOpen }"
              @click="templateIsOpen = !templateIsOpen"
            />
            <label class="blue-label ml-2" @click="templateIsOpen = !templateIsOpen">
              Template:
            </label>
          </div>
          <label for="batchSampleNRows" class="blue-label col-md-2 col-3 col-form-label text-left">
            Number of rows:
          </label>
          <input
            id="batchSampleNRows"
            v-model="nSamples"
            class="form-control col-md-1 col-2"
            type="number"
            min="0"
          />
        </div>

        <div v-show="templateIsOpen" class="card bg-light mt-4 mx-auto mb-4" style="width: 95%">
          <table class="table table-sm mb-2">
            <thead>
              <tr class="subheading template-subheading">
                <th style="width: calc(12%)">ID</th>
                <th>Name</th>
                <th style="width: calc(15%)">Date</th>
                <th style="width: calc(22%)">Copy from</th>
                <th style="width: calc(22%)">Components</th>
              </tr>
            </thead>
            <tbody>
              <td>
                <input
                  class="form-control"
                  v-model="sampleTemplate.item_id"
                  @input="applyIdTemplate"
                  placeholder="ex_{#}"
                />
              </td>
              <td>
                <input
                  class="form-control"
                  @input="applyNameTemplate"
                  v-model="sampleTemplate.name"
                  placeholder="Example name {#}"
                />
              </td>
              <td>
                <input
                  class="form-control"
                  type="date"
                  v-model="sampleTemplate.date"
                  @input="applyDateTemplate"
                />
              </td>
              <td>
                <ItemSelect
                  v-model="sampleTemplate.copyFrom"
                  @update:modelValue="applyCopyFromTemplate"
                  :formattedItemNameMaxLength="8"
                />
              </td>
              <td>
                <ItemSelect
                  v-model="sampleTemplate.components"
                  multiple
                  @update:modelValue="applyComponentsTemplate"
                  :formattedItemNameMaxLength="8"
                />
              </td>
            </tbody>
          </table>

          <div class="form-group mt-2 mb-1" style="display: flex">
            <label for="start-counting" id="start-counting-label" class="px-3 col-form-label-sm">
              start counting {#} at:
            </label>
            <input
              type="number"
              id="start-counting"
              v-model="templateStartNumber"
              class="form-control form-control-sm"
              @input="applyIdAndNameTemplates"
              style="width: 5em"
            />
          </div>
        </div>

        <table class="table mb-2">
          <thead>
            <tr class="subheading">
              <th style="width: calc(12%)">ID</th>
              <th>Name</th>
              <th style="width: calc(15%)">Date</th>
              <th style="width: calc(22%)">Copy from</th>
              <th style="width: calc(22%)">Components</th>
            </tr>
          </thead>
          <tr v-for="(sample, index) in samples" :key="index">
            <td>
              <input
                class="form-control"
                v-model="sample.item_id"
                @input="this.sampleTemplate.item_id = ''"
              />
            </td>
            <td>
              <input
                class="form-control"
                v-model="sample.name"
                @input="this.sampleTemplate.name = ''"
              />
            </td>
            <td><input class="form-control" type="date" v-model="sample.date" /></td>
            <td><ItemSelect v-model="sample.copyFrom" :formattedItemNameMaxLength="8" /></td>
            <td>
              <ItemSelect v-model="sample.components" multiple :formattedItemNameMaxLength="8" />
            </td>
            <button type="button" class="close" @click.stop="removeRow(index)" aria-label="delete">
              <span aria-hidden="true">&times;</span>
            </button>
          </tr>
        </table>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import ItemSelect from "@/components/ItemSelect.vue";
import { createNewSample } from "@/server_fetch_utils.js";
export default {
  name: "BatchCreateSampleModal",
  data() {
    return {
      item_id: null,
      date: new Date().toISOString().split("T")[0], // todo: add time zone support...     }
      // name: "",
      nSamples: 2,
      samples: [
        {
          item_id: "",
          name: "",
          copyFrom: null,
          components: null,
          date: new Date().toISOString().split("T")[0],
        },
        {
          item_id: "",
          name: "",
          copyFrom: null,
          components: null,
          date: new Date().toISOString().split("T")[0],
        },
      ],
      takenItemIds: [], // this holds ids that have been tried, whereas the computed takenSampleIds holds ids in the sample table
      selectedItemToCopy: null,
      startingConstituents: [],
      idTemplate: "",
      templateStartNumber: 1,
      templateIsOpen: true,
      sampleTemplate: {
        item_id: "",
        name: "",
        copyFrom: null,
        components: null,
        date: new Date().toISOString().split("T")[0],
      },
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
    applyIdTemplate() {
      this.samples.forEach((sample, i) => {
        sample.item_id = this.sampleTemplate.item_id.replace("{#}", i + this.templateStartNumber);
      });
    },
    applyNameTemplate() {
      this.samples.forEach((sample, i) => {
        sample.name = this.sampleTemplate.name.replace("{#}", i + this.templateStartNumber);
      });
    },
    applyIdAndNameTemplates() {
      this.sampleTemplate.name && this.applyNameTemplate();
      this.sampleTemplate.item_id && this.applyIdTemplate();
    },
    applyDateTemplate() {
      this.samples.forEach((sample) => {
        sample.date = this.sampleTemplate.date;
      });
    },
    applyCopyFromTemplate() {
      this.samples.forEach((sample) => {
        sample.copyFrom = this.sampleTemplate.copyFrom;
      });
    },
    applyComponentsTemplate() {
      this.samples.forEach((sample) => {
        sample.components = this.sampleTemplate.components;
      });
    },
    removeRow(index) {
      this.samples.splice(index, 1);
      this.nSamples = this.nSamples - 1;
      // unless the removed row is the last one, reset the template and name id
      if (index != this.samples.length) {
        this.sampleTemplate.item_id = "";
        this.sampleTemplate.name = "";
      }
    },
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
          this.item_id = null;
          this.name = null;
          this.date = new Date().toISOString().split("T")[0]; // reset the date (is this the most user-friendly behavior?)

          this.$emit("update:modelValue", false); // close this modal
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
  watch: {
    nSamples(newValue, oldValue) {
      if (newValue < oldValue) {
        this.samples = this.samples.slice(0, newValue);
      }
      if (newValue > oldValue) {
        for (let i = 0; i < newValue - oldValue; i++) {
          this.samples.push({
            item_id: "",
            name: "",
            copyFrom: null,
            components: null,
            date: new Date().toISOString().split("T")[0],
          });
        }
        if (this.sampleTemplate.item_id) {
          this.applyIdTemplate();
        }
        if (this.sampleTemplate.name) {
          this.applyNameTemplate();
        }
      }
    },
  },
  components: {
    Modal,
    ItemSelect,
  },
};
</script>

<style scoped>
.blue-label {
  font-weight: 600;
  color: #0b6093;
}

#start-counting-label {
  font-size: 1em;
  font-style: italic;
}

.template-subheading > th {
  font-style: italic;
  font-weight: 500;
}

.form-error {
  color: red;
}

:deep(.form-error a) {
  color: #820000;
  font-weight: 600;
}

.collapse-arrow {
  transition: all 0.4s;
  cursor: pointer;
}

.collapse-arrow:hover {
  color: #7ca7ca;
}

.expanded {
  -webkit-transform: rotate(90deg);
  -moz-transform: rotate(90deg);
  transform: rotate(90deg);
}

.modal-enclosure >>> .modal-header {
  padding: 0.5rem 1rem;
}

.modal-enclosure >>> .modal-dialog {
  max-width: 95vw;
  min-height: 75vh;
  margin-top: 2.5vh;
  margin-bottom: 2.5vh;
}

.modal-enclosure >>> .modal-content {
  height: 75vh;
  overflow: scroll;
}
</style>
