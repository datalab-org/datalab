<template>
  <form class="modal-enclosure" data-testid="create-item-form" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="Boolean(isValidEntryID) || (!generateIDAutomatically && !Boolean(item_id))"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <template #header> Add new item </template>

      <template #body>
        <div class="row">
          <div class="col-md-6 mb-3">
            <label for="create-item-item_id" class="form-label">ID:</label>
            <input
              id="create-item-item_id"
              v-model="item_id"
              type="text"
              class="form-control"
              :disabled="generateIDAutomatically"
              :required="!generateIDAutomatically"
            />
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div class="form-error" v-html="isValidEntryID"></div>
            <div class="form-check mt-1">
              <input
                id="create-item-auto-id-checkbox"
                v-model="generateIDAutomatically"
                type="checkbox"
                class="form-check-input"
                @input="item_id = null"
              />
              <label
                id="create-item-automatic-id-label"
                class="form-check-label"
                for="create-item-auto-id-checkbox"
              >
                Generate automatically
              </label>
            </div>
          </div>
          <div class="col-md-6 mb-3">
            <label for="item-type-select" class="form-label">Type:</label>
            <select id="item-type-select" v-model="item_type" class="form-select" required>
              <option v-for="type in allowedTypes" :key="type" :value="type">
                {{ itemTypes[type].display }}
              </option>
            </select>
          </div>
          <div class="col-md-6 mb-3">
            <label for="create-item-date" class="form-label">Date Created:</label>
            <input
              id="create-item-date"
              v-model="date"
              type="datetime-local"
              class="form-control"
              :min="agesAgo"
              :max="oneYearOn()"
              required
            />
          </div>
        </div>
        <div class="row">
          <div class="col-md-12 mb-3">
            <label for="create-item-name" class="form-label">Name:</label>
            <input id="create-item-name" v-model="name" type="text" class="form-control" />
          </div>
        </div>
        <div class="row">
          <div class="col-md-12 mb-3">
            <label id="startInCollection" class="form-label"
              >(Optional) Insert into collection:</label
            >
            <CollectionSelect
              v-model="startInCollection"
              data-testid="start-in-collection"
              aria-labelledby="startInCollection"
              multiple
            />
          </div>
        </div>
        <div class="row">
          <div class="col-md-12 mb-3">
            <label id="copyFromSelectLabel" class="form-label">
              (Optional) Copy from existing {{ itemTypeDisplayName }}:
            </label>
            <ItemSelect
              data-testid="copy-from-select"
              aria-labelledby="copyFromSelectLabel"
              :model-value="selectedItemToCopy"
              :types-to-query="[item_type]"
              @update:model-value="
                selectedItemToCopy = $event;
                setCopiedName();
              "
            />
          </div>
        </div>
        <component
          :is="itemCreateModalAddonComponent"
          @starting-data-callback="(callback) => (startingDataCallback = callback)"
        />
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import ItemSelect from "@/components/ItemSelect.vue";
import { createNewItem } from "@/server_fetch_utils.js";
import { validateEntryID } from "@/field_utils.js";
import { itemTypes, SAMPLE_TABLE_TYPES, AUTOMATICALLY_GENERATE_ID_DEFAULT } from "@/resources.js";
import CollectionSelect from "@/components/CollectionSelect.vue";
export default {
  name: "CreateItemModal",
  components: {
    Modal,
    ItemSelect,
    CollectionSelect,
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
      item_id: null,
      item_type: "",
      date: this.now(),
      name: "",
      startingDataCallback: null,
      startInCollection: null,
      takenItemIds: [],
      selectedItemToCopy: null,
      startingConstituents: [],
      generateIDAutomatically: AUTOMATICALLY_GENERATE_ID_DEFAULT,
      agesAgo: new Date("1970-01-01").toISOString().slice(0, -8),
    };
  },
  computed: {
    itemTypes() {
      return itemTypes;
    },
    itemTypeDisplayName() {
      return itemTypes[this.item_type].display;
    },
    itemCreateModalAddonComponent() {
      return itemTypes[this.item_type].itemCreateModalAddon;
    },
    takenSampleIds() {
      return this.$store.state.sample_list
        ? this.$store.state.sample_list.map((x) => x.item_id)
        : [];
    },
    isValidEntryID() {
      return validateEntryID(this.item_id, this.takenItemIds, this.takenSampleIds);
    },
  },
  created() {
    this.item_type = this.allowedTypes[0];
  },
  methods: {
    async submitForm() {
      console.log("new item form submit triggered");

      const extraData = this.startingDataCallback && this.startingDataCallback();
      let startingCollection = [];
      if (this.startInCollection != null) {
        startingCollection = this.startInCollection.map((x) => ({
          collection_id: x.collection_id,
          immutable_id: x.immutable_id,
          type: "collections",
        }));
      }

      await createNewItem(
        this.item_id,
        this.item_type,
        this.date,
        this.name,
        startingCollection,
        extraData,
        this.selectedItemToCopy && this.selectedItemToCopy.item_id,
        this.generateIDAutomatically,
      )
        .then(() => {
          this.$emit("update:modelValue", false);
          this.item_id = null;
          this.name = null;
          this.date = this.now();
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
              alert("Error with creating new item: " + error);
            }
          }
        });
    },
    oneYearOn() {
      let d = new Date();
      d.setFullYear(d.getFullYear() + 1);
      return d.toISOString().slice(0, -8);
    },
    now() {
      return new Date().toISOString().slice(0, -8);
    },

    setCopiedName() {
      if (!this.selectedItemToCopy) {
        this.name = "";
      }
      this.name = `COPY OF ${this.selectedItemToCopy.name}`;
    },
  },
};
</script>

<style scoped>
#create-item-automatic-id-label {
  color: #555;
}

.form-error {
  color: red;
}

:deep(.form-error a) {
  color: #820000;
  font-weight: 600;
}

.modal-enclosure :deep(.modal-content) {
  max-height: 90vh;
  overflow: auto;
  scroll-behavior: smooth;
}
</style>
