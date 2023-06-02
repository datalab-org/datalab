<template>
  <form data-testid="batch-modal-container" class="modal-enclosure" @submit.prevent="submitForm">
    <Modal
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :disableSubmit="
        sampleIDValidationMessages.some((e) => e) || samples.some((s) => !Boolean(s.item_id))
      "
    >
      <template v-slot:header>
        <template v-if="beforeSubmit">Add new samples</template>
        <template v-else>
          <a role="button" id="back-arrow" @click="beforeSubmit = true">←</a>
          Samples added
        </template>
      </template>
      <template v-slot:body>
        <div id="screens-container">
          <transition name="slide-content-left">
            <div id="left-screen" v-show="beforeSubmit">
              <div class="row">
                <div class="col-md-8 mt-2" @click="templateIsOpen = !templateIsOpen">
                  <font-awesome-icon
                    :icon="['fas', 'chevron-right']"
                    fixed-width
                    class="collapse-arrow"
                    :class="{ expanded: templateIsOpen }"
                  />
                  <label class="blue-label collapse-clickable ml-2"> Template: </label>
                </div>
                <label
                  for="batchSampleNRows"
                  class="blue-label col-md-2 col-3 col-form-label text-left mb-2"
                >
                  Number of rows:
                </label>
                <input
                  id="batchSampleNRows"
                  v-model="nSamples"
                  class="form-control col-md-1 col-2"
                  type="number"
                  min="0"
                  max="100"
                />
              </div>

              <div
                v-show="templateIsOpen"
                class="card bg-light mt-2 mx-auto mb-4"
                style="width: 95%"
              >
                <table data-testid="batch-add-table-template" class="table table-sm mb-2">
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
                        type="datetime-local"
                        v-model="sampleTemplate.date"
                        @input="applyDateTemplate"
                        :min="epochStart"
                        :max="oneYearOn"
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
                  <label
                    for="start-counting"
                    id="start-counting-label"
                    class="px-3 col-form-label-sm"
                  >
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

              <table data-testid="batch-add-table" class="table mb-2">
                <thead>
                  <tr class="subheading">
                    <th style="width: calc(12%)">ID</th>
                    <th>Name</th>
                    <th style="width: calc(15%)">Date</th>
                    <th style="width: calc(22%)">Copy from</th>
                    <th style="width: calc(22%) - 2rem">Components</th>
                    <th style="width: 2rem"></th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="(sample, index) in samples" :key="index">
                    <tr>
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
                      <td>
                        <input
                          class="form-control"
                          type="datetime-local"
                          v-model="sample.date"
                          :min="epochStart"
                          :max="oneYearOn"
                        />
                      </td>
                      <td>
                        <ItemSelect v-model="sample.copyFrom" :formattedItemNameMaxLength="8" />
                      </td>
                      <td>
                        <ItemSelect
                          v-model="sample.components"
                          multiple
                          :formattedItemNameMaxLength="8"
                        />
                      </td>
                      <td>
                        <button
                          type="button"
                          class="close"
                          @click.stop="removeRow(index)"
                          aria-label="delete"
                        >
                          <span aria-hidden="true">&times;</span>
                        </button>
                      </td>
                    </tr>
                    <td colspan="3">
                      <span class="form-error" v-html="sampleIDValidationMessages[index]" />
                    </td>
                  </template>
                </tbody>
              </table>
            </div>
          </transition>
          <transition name="slide-content-right">
            <div id="right-screen" v-show="!beforeSubmit">
              <div v-for="(response, index) in serverResponses" :key="index">
                <div class="callout callout-info" v-if="response.status == 'success'">
                  <a class="item-id-link" :href="`edit/${response.item_id}`">
                    {{ response.item_id }}
                  </a>
                  Successfully created.
                </div>
                <div
                  class="callout callout-danger form-error"
                  v-if="
                    response.status == 'error' &&
                    response.message.includes('item_id_validation_error')
                  "
                >
                  <a :href="`edit/${response.item_id}`">
                    {{ response.item_id }}
                  </a>
                  was not added as it already exists in the database.
                </div>
                <div class="callout callout-danger" v-else-if="response.status == 'error'">
                  {{ response.message }}
                </div>
              </div>
            </div>
          </transition>
        </div>
      </template>
      <template v-if="!beforeSubmit" v-slot:footer>
        <button type="button" class="btn btn-info" @click="openEditPagesInNewTabs">Open all</button>
        <button
          type="button"
          class="btn btn-secondary"
          data-dismiss="modal"
          @click="$emit('update:modelValue', false)"
        >
          Close
        </button>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import ItemSelect from "@/components/ItemSelect.vue";
import { createNewSamples } from "@/server_fetch_utils.js";
export default {
  name: "BatchCreateSampleModal",
  data() {
    return {
      beforeSubmit: true,
      epochStart: new Date("1970-01-01").toISOString().slice(0, -8),
      oneYearOn: this.determineOneYearOn(),
      nSamples: 3,
      samples: [
        {
          item_id: null,
          name: "",
          copyFrom: null,
          components: [],
          date: this.now(),
        },
        {
          item_id: null,
          name: "",
          copyFrom: null,
          components: [],
          date: this.now(),
        },
        {
          item_id: null,
          name: "",
          copyFrom: null,
          components: [],
          date: this.now(),
        },
      ],
      takenItemIds: [], // this holds ids that have been tried, whereas the computed takenSampleIds holds ids in the sample table

      templateIsOpen: true,
      templateStartNumber: 1,
      sampleTemplate: {
        item_id: null,
        name: "",
        copyFrom: null,
        components: null,
        date: this.now(),
      },

      serverResponses: {}, // after the server responds, store error messages if any
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
    someValidationMessagePresent() {
      return this.sampleIDValidationMessages.some();
    },
    sampleIDValidationMessages() {
      return this.samples.map((sample, index, samples) => {
        if (sample.item_id == null) {
          return "";
        } // Don't throw an error before the user starts typing

        // check that sample id isn't repeated in this table
        if (
          samples
            .slice(0, index)
            .map((el) => el.item_id)
            .includes(sample.item_id)
        ) {
          return "ID is repeated from an above row.";
        }

        if (
          this.takenItemIds.includes(sample.item_id) ||
          this.takenSampleIds.includes(sample.item_id)
        ) {
          return `<a href='edit/${sample.item_id}'>${sample.item_id}</a> already in use.`;
        }
        if (!/^[a-zA-Z0-9._-]+$/.test(sample.item_id)) {
          return "ID can only contain alphanumeric characters, dashes ('-') and underscores ('_') and periods ('.')";
        }
        if (/^[._-]/.test(sample.item_id) | /[._-]$/.test(sample.item_id)) {
          return "ID cannot start or end with puncutation";
        }
        if (/\s/.test(sample.item_id)) {
          return "ID cannot have any spaces";
        }
        if (sample.item_id.length < 1 || sample.item_id.length > 40) {
          return "ID must be between 1 and 40 characters in length";
        }
        return "";
      });
    },
  },
  methods: {
    now() {
      return new Date().toISOString().slice(0, -8);
    },
    determineOneYearOn() {
      // returns a timestamp 1 year from now
      let d = new Date();
      d.setFullYear(d.getFullYear() + 1);
      return d.toISOString().slice(0, -8);
    },
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
      console.log("batch sample create form submit triggered");

      const newSampleDatas = this.samples.map((sample) => {
        return {
          item_id: sample.item_id,
          date: sample.date,
          name: sample.name,
          type: "samples",
          synthesis_constituents: sample.components
            ? sample.components.map((x) => ({ item: x, quantity: null }))
            : [],
        };
      });

      const copyFromItemIds = this.samples.map((sample) => sample.copyFrom?.item_id);

      await createNewSamples(newSampleDatas, copyFromItemIds)
        .then((responses) => {
          console.log("samples added");
          this.serverResponses = responses;

          document
            .querySelector(".modal-enclosure .modal-content")
            .scrollTo({ top: 0, behavior: "smooth" });
          this.beforeSubmit = false;
        })
        .catch((error) => {
          console.log("Error with creating new samples: " + error);
        });
    },
    openEditPagesInNewTabs() {
      this.serverResponses
        .slice()
        .reverse()
        .forEach((response) => {
          window.open(`/edit/${response.item_id}`, "_blank");
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
          this.samples.push({ ...this.sampleTemplate });
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
#screens-container {
  width: 200%;
}

#left-screen {
  width: 50%;
  padding-right: 1em;
  padding-left: 1em;
  display: inline-block;
  float: left;
}

#right-screen {
  width: 50%;
  padding-left: 1em;
  display: inline-block;
  float: left;
}

.slide-content-left-leave-active,
.slide-content-left-enter-active {
  transition: all 0.8s ease;
}

.slide-content-left-leave-to,
.slide-content-left-enter-from {
  transform: translateX(-100%);
}

.slide-content-right-leave-active,
.slide-content-right-enter-active {
  transition: all 0.8s ease;
}

.slide-content-left-leave-active .form-error {
  display: none;
}

.slide-content-right-leave-from,
.slide-content-right-enter-to {
  transform: translateX(-100%);
}

.close {
  margin-top: 0.2em;
  color: grey;
}

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

.collapse-clickable {
  cursor: pointer;
}

.expanded {
  -webkit-transform: rotate(90deg);
  -moz-transform: rotate(90deg);
  transform: rotate(90deg);
}

.item-id-link {
  color: #0b6093;
  font-weight: 600;
}

.form-error {
  color: red;
}

:deep(.form-error a) {
  color: #820000;
  font-weight: 600;
}

.modal-enclosure :deep(.modal-header) {
  padding: 0.5rem 1rem;
}

.modal-enclosure :deep(.modal-dialog) {
  max-width: 95vw;
  min-height: 90vh;
  margin-top: 2.5vh;
  margin-bottom: 2.5vh;
}

.modal-enclosure :deep(.modal-content) {
  height: 90vh;
  overflow: scroll;
  scroll-behavior: smooth;
}
</style>
