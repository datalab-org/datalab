<template>
  <form class="modal-enclosure" data-testid="create-item-form" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="Boolean(isValidEntryID) || (!generateIDAutomatically && !Boolean(item_id))"
      @update:model-value="$emit('update:modelValue', $event)"
      @submit="submitForm"
    >
      <template #header> Add new item </template>

      <template #body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="create-item-item_id" class="col-form-label">ID:</label>
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
            <div class="form-check mt-1 ml-1">
              <input
                id="create-item-auto-id-checkbox"
                v-model="generateIDAutomatically"
                type="checkbox"
                class="form-check-input clickable"
                @input="item_id = null"
              />
              <label
                id="create-item-automatic-id-label"
                class="form-check-label clickable"
                for="create-item-auto-id-checkbox"
                >generate automatically</label
              >
            </div>
          </div>
          <div class="form-group col-md-6">
            <label for="item-type-select" class="col-form-label">Type:</label>
            <select id="item-type-select" v-model="item_type" class="form-control" required>
              <option v-for="type in allowedTypes" :key="type" :value="type">
                {{ itemTypes[type].display }}
              </option>
            </select>
          </div>
          <div class="form-group col-md-6 pt-0">
            <label for="create-item-date" class="col-form-label">Date Created:</label>
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
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="create-item-name">Name:</label>
            <input id="create-item-name" v-model="name" type="text" class="form-control" />
          </div>
        </div>
        <!-- All item types can be added to a collection, so this is always available -->
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="startInCollection">(Optional) Insert into collection:</label>
            <CollectionSelect
              v-model="startInCollection"
              aria-labelledby="startInCollection"
              multiple
            />
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="copyFromSelectLabel"
              >(Optional) Copy from existing {{ itemTypeDisplayName }}:</label
            >
            <ItemSelect
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
        <!-- dynamically insert addons to this modal for each item type. On mount, the component
        should emit a callback that can be called to get properly formatted
        data to provide to the server -->
        <component
          :is="itemCreateModalAddonComponent"
          @starting-data-callback="(callback) => (startingDataCallback = callback)"
        />
        <div class="form-row">
          <div class="col-md-6 form-group">
            <label id="shareWithGroupsLabel">(Optional) Share with groups:</label>
            <GroupSelect
              v-model="shareWithGroups"
              aria-labelledby="shareWithGroupsLabel"
              multiple
            />
          </div>
          <div class="col-md-6 form-group">
            <label id="additionalCreatorsLabel">(Optional) Additional creators:</label>
            <UserSelect
              v-model="additionalCreators"
              aria-labelledby="additionalCreatorsLabel"
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
import GroupSelect from "@/components/GroupSelect.vue";
import UserSelect from "@/components/UserSelect.vue";
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
    GroupSelect,
    UserSelect,
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
      takenItemIds: [], // this holds ids that have been tried, whereas the computed takenSampleIds holds ids in the sample table
      selectedItemToCopy: null,
      startingConstituents: [],
      generateIDAutomatically: AUTOMATICALLY_GENERATE_ID_DEFAULT,
      agesAgo: new Date("1970-01-01").toISOString().slice(0, -8), // a datetime for the unix epoch start
      shareWithGroups: [],
      additionalCreators: [],
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

      // get any extra data by calling the optional callback from the type-specific addon component
      const extraData = this.startingDataCallback && this.startingDataCallback();
      let startingCollection = [];
      if (this.startInCollection != null) {
        startingCollection = this.startInCollection.map((x) => ({
          collection_id: x.collection_id,
          immutable_id: x.immutable_id,
          type: "collections",
        }));
      }
      const groupsData = this.shareWithGroups.length > 0 ? this.shareWithGroups : null;
      const creatorsData = this.additionalCreators.length > 0 ? this.additionalCreators : null;

      await createNewItem(
        this.item_id,
        this.item_type,
        this.date,
        this.name,
        startingCollection,
        extraData,
        this.selectedItemToCopy && this.selectedItemToCopy.item_id,
        this.generateIDAutomatically,
        groupsData,
        creatorsData,
      )
        .then(() => {
          this.$emit("update:modelValue", false); // close this modal
          // can enable the following line to get smooth scrolling into view, but will fail
          // if generateIDAutomatically. It's currently not necessary because
          // new items always show up at the top of the sample table
          // // document.getElementById(this.item_id).scrollIntoView({ behavior: "smooth" });
          this.item_id = null;
          this.date = this.now(); // reset date to the new current time
          this.shareWithGroups = [];
          this.additionalCreators = [];
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
              DialogService.error({
                title: "Creation Error",
                message: "Error with creating new item: " + error,
              });
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
