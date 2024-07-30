<template>
  <form data-testid="batch-modal-container" class="modal-enclosure" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="
        itemIDValidationMessages.some((e) => e) ||
        (!generateIDsAutomatically && items.some((s) => !Boolean(s.item_id)))
      "
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <template #header>
        <template v-if="beforeSubmit">Add new items</template>
        <template v-else>
          <a id="back-arrow" role="button" @click="beforeSubmit = true">←</a>
          Items added
        </template>
      </template>
      <template #body>
        <div id="screens-container">
          <transition name="slide-content-left">
            <div v-show="beforeSubmit" id="left-screen">
              <div class="row">
                <div class="input-group col-lg-3 col-6">
                  <label for="batch-item-type-select" class="blue-label col-form-label mr-3">
                    Type:
                  </label>
                  <select
                    id="batch-item-type-select"
                    v-model="item_type"
                    class="form-control"
                    required
                  >
                    <option v-for="type in allowedTypes" :key="type" :value="type">
                      {{ itemTypes[type].display }}
                    </option>
                  </select>
                </div>
                <div class="input-group col-lg-3 col-6">
                  <label for="batchItemNRows" class="blue-label col-form-label text-left mb-2 mr-3">
                    Number of rows:
                  </label>
                  <input
                    id="batchItemNRows"
                    v-model="nSamples"
                    class="form-control"
                    type="number"
                    min="0"
                    max="100"
                  />
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mt-2" @click="templateIsOpen = !templateIsOpen">
                  <font-awesome-icon
                    :icon="['fas', 'chevron-right']"
                    fixed-width
                    class="collapse-arrow clickable"
                    :class="{ expanded: templateIsOpen }"
                  />
                  <label class="blue-label clickable pl-2"> Template: </label>
                </div>
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
                        v-model="itemTemplate.item_id"
                        class="form-control"
                        :placeholder="generateIDsAutomatically ? null : 'ex_{#}'"
                        :disabled="generateIDsAutomatically"
                        @input="applyIdTemplate"
                      />
                      <div class="form-check mt-1 ml-1">
                        <input
                          id="automatic-batch-id-label"
                          v-model="generateIDsAutomatically"
                          type="checkbox"
                          class="form-check-input clickable"
                          @input="setIDsNull"
                        />
                        <label
                          id="automatic-id-label"
                          class="form-check-label clickable"
                          for="automatic-batch-id-label"
                        >
                          auto IDs
                        </label>
                      </div>
                    </td>
                    <td>
                      <input
                        v-model="itemTemplate.name"
                        class="form-control"
                        placeholder="Example name {#}"
                        @input="applyNameTemplate"
                      />
                    </td>
                    <td>
                      <input
                        v-model="itemTemplate.date"
                        class="form-control"
                        type="datetime-local"
                        :min="epochStart"
                        :max="oneYearOn"
                        @input="applyDateTemplate"
                      />
                    </td>
                    <td>
                      <ItemSelect
                        v-model="itemTemplate.copyFrom"
                        :formatted-item-name-max-length="8"
                        @update:model-value="applyCopyFromTemplate"
                      />
                    </td>
                    <td>
                      <div v-if="item_type == 'samples'">
                        <ItemSelect
                          v-model="itemTemplate.components"
                          multiple
                          :formatted-item-name-max-length="8"
                          taggable
                          @update:model-value="applyComponentsTemplate"
                        />
                      </div>
                      <div v-if="item_type == 'cells'">
                        <ItemSelect
                          v-model="itemTemplate.positiveElectrode"
                          multiple
                          :formatted-item-name-max-length="8"
                          taggable
                          placeholder="positive electrode"
                          @update:model-value="applyPositiveElectrodeTemplate"
                        />
                        <ItemSelect
                          v-model="itemTemplate.electrolyte"
                          multiple
                          :formatted-item-name-max-length="8"
                          class="pt-1"
                          taggable
                          placeholder="electrolyte"
                          @update:model-value="applyElectrolyteTemplate"
                        />
                        <ItemSelect
                          v-model="itemTemplate.negativeElectrode"
                          multiple
                          :formatted-item-name-max-length="8"
                          class="pt-1"
                          taggable
                          placeholder="negative electrode"
                          @update:model-value="applyNegativeElectrodeTemplate"
                        />
                      </div>
                    </td>
                  </tbody>
                </table>

                <div class="form-group mt-2 mb-1" style="display: flex">
                  <label
                    id="start-counting-label"
                    for="start-counting"
                    class="px-3 col-form-label-sm"
                  >
                    start counting {#} at:
                  </label>
                  <input
                    id="start-counting"
                    v-model="templateStartNumber"
                    type="number"
                    class="form-control form-control-sm"
                    style="width: 5em"
                    @input="applyIdAndNameTemplates"
                  />
                </div>
              </div>

              <table data-testid="batch-add-table" class="table mb-2">
                <thead>
                  <tr class="subheading">
                    <th style="width: calc(12%)">ID</th>
                    <th style="width: calc(25%)">Name</th>
                    <th style="width: calc(15%)">Date</th>
                    <th style="width: calc(22%)">Copy from</th>
                    <th style="width: calc(22%) - 2rem">Components</th>
                    <th style="width: 2rem"></th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="(item, index) in items" :key="index">
                    <tr>
                      <td>
                        <input
                          v-model="item.item_id"
                          class="form-control"
                          :disabled="generateIDsAutomatically"
                          @input="itemTemplate.item_id = ''"
                        />
                      </td>
                      <td>
                        <input
                          v-model="item.name"
                          class="form-control"
                          @input="itemTemplate.name = ''"
                        />
                      </td>
                      <td>
                        <input
                          v-model="item.date"
                          class="form-control"
                          type="datetime-local"
                          :min="epochStart"
                          :max="oneYearOn"
                        />
                      </td>
                      <td>
                        <ItemSelect v-model="item.copyFrom" :formatted-item-name-max-length="8" />
                      </td>
                      <td>
                        <div v-if="item_type == 'samples'">
                          <ItemSelect
                            v-model="item.components"
                            multiple
                            :formatted-item-name-max-length="8"
                            taggable
                          />
                        </div>
                        <div v-if="item_type == 'cells'">
                          <ItemSelect
                            v-model="item.positiveElectrode"
                            multiple
                            :formatted-item-name-max-length="8"
                            taggable
                            placeholder="positive electrode"
                          />
                          <ItemSelect
                            v-model="item.electrolyte"
                            multiple
                            :formatted-item-name-max-length="8"
                            class="pt-1"
                            taggable
                            placeholder="electrolyte"
                          />
                          <ItemSelect
                            v-model="item.negativeElectrode"
                            multiple
                            :formatted-item-name-max-length="8"
                            class="pt-1"
                            taggable
                            placeholder="negative electrode"
                          />
                        </div>
                      </td>
                      <td>
                        <button
                          type="button"
                          class="close"
                          aria-label="delete"
                          @click.stop="removeRow(index)"
                        >
                          <span aria-hidden="true">&times;</span>
                        </button>
                      </td>
                    </tr>
                    <td colspan="3">
                      <!-- eslint-disable-next-line vue/no-v-html -->
                      <span class="form-error" v-html="itemIDValidationMessages[index]" />
                    </td>
                  </template>
                </tbody>
              </table>
            </div>
          </transition>
          <transition name="slide-content-right">
            <div v-show="!beforeSubmit" id="right-screen">
              <div v-for="(response, index) in serverResponses" :key="index">
                <div v-if="response.status == 'success'" class="callout callout-info">
                  <a class="item-id-link" :href="`edit/${response.item_id}`">
                    {{ response.item_id }}
                  </a>
                  Successfully created.
                </div>
                <div
                  v-if="
                    response.status == 'error' &&
                    response.message.includes('item_id_validation_error')
                  "
                  class="callout callout-danger form-error"
                >
                  <a :href="`edit/${response.item_id}`">
                    {{ response.item_id }}
                  </a>
                  was not added as it already exists in the database.
                </div>
                <div v-else-if="response.status == 'error'" class="callout callout-danger">
                  {{ response.message }}
                </div>
              </div>
            </div>
          </transition>
        </div>
      </template>
      <template v-if="!beforeSubmit" #footer>
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
import { itemTypes, SAMPLE_TABLE_TYPES } from "@/resources.js";
export default {
  name: "BatchCreateItemModal",
  components: {
    Modal,
    ItemSelect,
  },
  props: {
    modelValue: Boolean,
    allowedTypes: {
      type: Array,
      default: () => SAMPLE_TABLE_TYPES,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      beforeSubmit: true,
      epochStart: new Date("1970-01-01").toISOString().slice(0, -8),
      oneYearOn: this.determineOneYearOn(),
      nSamples: 3,
      generateIDsAutomatically: false,
      item_type: "samples",
      items: [
        {
          item_id: null,
          name: "",
          copyFrom: null,
          components: [],
          positiveElectrode: [],
          electrolyte: [],
          negativeElectrode: [],
          date: this.now(),
        },
        {
          item_id: null,
          name: "",
          copyFrom: null,
          components: [],
          positiveElectrode: [],
          electrolyte: [],
          negativeElectrode: [],
          date: this.now(),
        },
        {
          item_id: null,
          name: "",
          copyFrom: null,
          components: [],
          positiveElectrode: [],
          electrolyte: [],
          negativeElectrode: [],
          date: this.now(),
        },
      ],
      takenItemIds: [], // this holds ids that have been tried, whereas the computed takenSampleIds holds ids in the item table

      templateIsOpen: true,
      templateStartNumber: 1,
      itemTemplate: {
        item_id: null,
        name: "",
        copyFrom: null,
        components: null,
        positiveElectrode: null,
        electrolyte: null,
        negativeElectrode: null,
        date: this.now(),
      },

      serverResponses: {}, // after the server responds, store error messages if any
    };
  },
  computed: {
    itemTypes() {
      return itemTypes;
    },
    takenSampleIds() {
      return this.$store.state.sample_list
        ? this.$store.state.sample_list.map((x) => x.item_id)
        : [];
    },
    someValidationMessagePresent() {
      return this.itemIDValidationMessages.some();
    },
    itemIDValidationMessages() {
      return this.items.map((item, index, items) => {
        if (item.item_id == null) {
          return "";
        } // Don't throw an error before the user starts typing

        // check that item id isn't repeated in this table
        if (
          items
            .slice(0, index)
            .map((el) => el.item_id)
            .includes(item.item_id)
        ) {
          return "ID is repeated from an above row.";
        }

        if (
          this.takenItemIds.includes(item.item_id) ||
          this.takenSampleIds.includes(item.item_id)
        ) {
          return `<a href='edit/${item.item_id}'>${item.item_id}</a> already in use.`;
        }
        if (!/^[a-zA-Z0-9._-]+$/.test(item.item_id)) {
          return "ID can only contain alphanumeric characters, dashes ('-') and underscores ('_') and periods ('.')";
        }
        if (/^[._-]/.test(item.item_id) | /[._-]$/.test(item.item_id)) {
          return "ID cannot start or end with puncutation";
        }
        if (/\s/.test(item.item_id)) {
          return "ID cannot have any spaces";
        }
        if (item.item_id.length < 1 || item.item_id.length > 40) {
          return "ID must be between 1 and 40 characters in length";
        }
        return "";
      });
    },
  },

  watch: {
    nSamples(newValue, oldValue) {
      if (newValue < oldValue) {
        this.items = this.items.slice(0, newValue);
      }
      if (newValue > oldValue) {
        for (let i = 0; i < newValue - oldValue; i++) {
          this.items.push({ ...this.itemTemplate });
        }
        if (this.itemTemplate.item_id) {
          this.applyIdTemplate();
        }
        if (this.itemTemplate.name) {
          this.applyNameTemplate();
        }
      }
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
      this.items.forEach((item, i) => {
        item.item_id = this.itemTemplate.item_id.replace("{#}", i + this.templateStartNumber);
      });
    },
    applyNameTemplate() {
      this.items.forEach((item, i) => {
        item.name = this.itemTemplate.name.replace("{#}", i + this.templateStartNumber);
      });
    },
    applyIdAndNameTemplates() {
      this.itemTemplate.name && this.applyNameTemplate();
      this.itemTemplate.item_id && this.applyIdTemplate();
    },
    applyDateTemplate() {
      this.items.forEach((item) => {
        item.date = this.itemTemplate.date;
      });
    },
    applyCopyFromTemplate() {
      this.items.forEach((item) => {
        item.copyFrom = this.itemTemplate.copyFrom;
      });
    },
    applyComponentsTemplate() {
      this.items.forEach((item) => {
        item.components = this.itemTemplate.components;
      });
    },
    applyPositiveElectrodeTemplate() {
      this.items.forEach((item) => {
        item.positiveElectrode = this.itemTemplate.positiveElectrode;
      });
    },
    applyElectrolyteTemplate() {
      this.items.forEach((item) => {
        item.electrolyte = this.itemTemplate.electrolyte;
      });
    },
    applyNegativeElectrodeTemplate() {
      this.items.forEach((item) => {
        item.negativeElectrode = this.itemTemplate.negativeElectrode;
      });
    },
    removeRow(index) {
      this.items.splice(index, 1);
      this.nSamples = this.nSamples - 1;
      // unless the removed row is the last one, reset the template and name id
      if (index != this.items.length) {
        this.itemTemplate.item_id = "";
        this.itemTemplate.name = "";
      }
    },
    setIDsNull() {
      this.itemTemplate["item_id"] = null;
      this.items.forEach((entry) => {
        entry["item_id"] = null;
      });
    },
    async submitForm() {
      console.log("batch item create form submit triggered");

      let newSampleDatas;

      if (this.item_type == "samples") {
        newSampleDatas = this.items.map((item) => {
          return {
            item_id: item.item_id,
            date: item.date,
            name: item.name,
            type: "samples",
            synthesis_constituents: item.components
              ? item.components.map((x) => ({ item: x, quantity: null }))
              : [],
          };
        });
      } else {
        newSampleDatas = this.items.map((item) => {
          return {
            item_id: item.item_id,
            date: item.date,
            name: item.name,
            type: "cells",
            positive_electrode: item.positiveElectrode
              ? item.positiveElectrode.map((x) => ({ item: x, quantity: null }))
              : [],
            electrolyte: item.electrolyte
              ? item.electrolyte.map((x) => ({ item: x, quantity: null }))
              : [],
            negative_electrode: item.negativeElectrode
              ? item.negativeElectrode.map((x) => ({ item: x, quantity: null }))
              : [],
          };
        });
      }

      const copyFromItemIds = this.items.map((item) => item.copyFrom?.item_id);

      await createNewSamples(newSampleDatas, copyFromItemIds, this.generateIDsAutomatically)
        .then((responses) => {
          console.log("items added");
          this.serverResponses = responses;

          document
            .querySelector(".modal-enclosure .modal-content")
            .scrollTo({ top: 0, behavior: "smooth" });
          this.beforeSubmit = false;
        })
        .catch((error) => {
          console.log("Error with creating new items: " + error);
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

#automatic-batch-id-label {
  color: #555;
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
}

.collapse-arrow:hover {
  color: #7ca7ca;
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
