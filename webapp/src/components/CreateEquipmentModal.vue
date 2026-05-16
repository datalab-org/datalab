<template>
  <form class="modal-enclosure" data-testid="create-equipment-form" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="Boolean(isValidEntryID) || !Boolean(item_id)"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <template #header> Add equipment </template>

      <template #body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="equipment-id" class="col-form-label">ID:</label>
            <input id="equipment-id" v-model="item_id" type="text" class="form-control" required />
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div class="form-error" v-html="isValidEntryID"></div>
          </div>
          <div class="form-group col-md-6">
            <label for="create-equipment-modal-item-type-select" class="col-form-label"
              >Type:</label
            >
            <select
              id="create-equipment-modal-item-type-select"
              v-model="item_type"
              class="form-control"
              required
              disabled
            >
              <option v-for="(obj, type) in availableTypes" :key="type" :value="type">
                {{ obj.display }}
              </option>
            </select>
          </div>
          <div class="form-group col-md-6">
            <label for="create-equipment-modal-date" class="col-form-label">Date Created:</label>
            <input
              id="create-equipment-modal-date"
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
            <label for="create-equipment-modal-name">Name:</label>
            <input
              id="create-equipment-modal-name"
              v-model="name"
              type="text"
              class="form-control"
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
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="shareWithGroupsLabel">(Optional) Share with groups:</label>
            <GroupSelect
              v-model="shareWithGroups"
              aria-labelledby="shareWithGroupsLabel"
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
import { createNewItem } from "@/server_fetch_utils.js";
import { validateEntryID } from "@/field_utils.js";
import { itemTypes } from "@/resources.js";

export default {
  name: "CreateEquipmentModal",
  components: {
    Modal,
    ItemSelect,
    GroupSelect,
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  data() {
    return {
      item_id: null,
      item_type: "equipment",
      date: this.now(),
      name: "",
      startingDataCallback: null,
      takenItemIds: [], // this holds ids that have been tried, whereas the computed takenEquipmentIds holds ids in the equipment table
      selectedItemToCopy: null,
      shareWithGroups: [],
      agesAgo: new Date("1970-01-01").toISOString().slice(0, -8), // a datetime for the unix epoch start
      //this is all just to filter an object in javascript:
      availableTypes: { equipment: itemTypes["equipment"] },
    };
  },
  computed: {
    itemTypeDisplayName() {
      return itemTypes[this.item_type].display;
    },
    itemCreateModalAddonComponent() {
      return itemTypes[this.item_type].itemCreateModalAddon;
    },
    takenEquipmentIds() {
      return this.$store.state.equipment_list
        ? this.$store.state.equipment_list.map((x) => x.item_id)
        : [];
    },
    isValidEntryID() {
      return validateEntryID(this.item_id, this.takenItemIds, this.takenEquipmentIds);
    },
  },
  methods: {
    async submitForm() {
      console.log("new equipment form submit triggered");

      const groupsData = this.shareWithGroups.length > 0 ? this.shareWithGroups : null;

      await createNewItem(
        this.item_id,
        this.item_type,
        this.date,
        this.name,
        null, // no startingCollection
        {}, // no extra data
        this.selectedItemToCopy && this.selectedItemToCopy.item_id,
        false,
        groupsData,
        null,
      )
        .then(() => {
          this.$emit("update:modelValue", false); // close this modal
          if (document.getElementById(this.item_id)) {
            document.getElementById(this.item_id).scrollIntoView({ behavior: "smooth" });
          }
          this.item_id = null;
          this.date = this.now(); // reset date to the new current time
          this.shareWithGroups = [];
        })
        .catch((error) => {
          console.log("THERE WAS AN ERROR");
          console.log(error);
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
                message: "Error with creating new equipment: " + error,
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
      } else {
        this.name = `COPY OF ${this.selectedItemToCopy.name}`;
      }
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

.modal-enclosure :deep(.modal-content) {
  max-height: 90vh;
  overflow: auto;
  scroll-behavior: smooth;
}
</style>
