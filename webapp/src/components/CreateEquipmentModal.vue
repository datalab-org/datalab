<template>
  <form @submit.prevent="submitForm" class="modal-enclosure">
    <Modal
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :disableSubmit="Boolean(equipmentIDValidationMessage) || !Boolean(item_id)"
    >
      <template v-slot:header> Add equipment </template>

      <template v-slot:body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="equipment-id" class="col-form-label">ID:</label>
            <input v-model="item_id" type="text" class="form-control" id="equipment-id" required />
            <div class="form-error" v-html="equipmentIDValidationMessage"></div>
          </div>
          <div class="form-group col-md-6">
            <label for="item-type-select" class="col-form-label">Type:</label>
            <select
              v-model="item_type"
              class="form-control"
              id="item-type-select"
              required
              disabled
            >
              <option v-for="(obj, type) in availableTypes" :key="type" :value="type">
                {{ obj.display }}
              </option>
            </select>
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
            <label for="name">Name:</label>
            <input id="name" type="text" v-model="name" class="form-control" />
          </div>
          <div class="form-group col-md-12">
            <label for="name">Location:</label>
            <input id="name" type="text" v-model="location" class="form-control" />
          </div>
        </div>
        <!-- All item types can be added to a collection, so this is always available -->
        <!--         <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="startInCollection">(Optional) Insert into collection:</label>
            <CollectionSelect
              aria-labelledby="startInCollection"
              multiple
              v-model="startInCollection"
            />
          </div>
        </div> -->
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="copyFromSelectLabel"
              >(Optional) Copy from existing {{ itemTypeDisplayName }}:</label
            >
            <ItemSelect
              aria-labelledby="copyFromSelectLabel"
              :modelValue="selectedItemToCopy"
              :typesToQuery="[item_type]"
              @update:modelValue="
                selectedItemToCopy = $event;
                setCopiedName();
              "
            />
          </div>
        </div>
        <!-- dynamically insert addons to this modal for each item type. On mount, the component
        should emit a callback that can be called to get properly formatted
        data to provide to the server -->
        <!--         <component
          :is="itemCreateModalAddonComponent"
          @startingDataCallback="(callback) => (startingDataCallback = callback)"
        /> -->
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import ItemSelect from "@/components/ItemSelect.vue";
import { createNewItem } from "@/server_fetch_utils.js";
import { itemTypes } from "@/resources.js";
// import CollectionSelect from "@/components/CollectionSelect.vue";
export default {
  name: "CreateEquipmentModal",
  data() {
    return {
      item_id: null,
      item_type: "equipment",
      date: this.now(),
      name: "",
      location: "",
      startingDataCallback: null,
      // startInCollection: null,
      takenItemIds: [], // this holds ids that have been tried, whereas the computed takenEquipmentIds holds ids in the equipment table
      selectedItemToCopy: null,
      agesAgo: new Date("1970-01-01").toISOString().slice(0, -8), // a datetime for the unix epoch start
      //this is all just to filter an object in javascript:
      availableTypes: { equipment: itemTypes["equipment"] },
    };
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
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
    equipmentIDValidationMessage() {
      if (this.item_id == null) {
        return "";
      } // Don't throw an error before the user starts typing

      if (
        this.takenItemIds.includes(this.item_id) ||
        this.takenEquipmentIds.includes(this.item_id)
      ) {
        return `<a href='edit/${this.item_id}'>${this.item_id}</a> already in use.`;
      }
      if (!/^[a-zA-Z0-9._-]+$/.test(this.item_id)) {
        return "ID can only contain alphanumeric characters, dashes ('-') and underscores ('_') and periods ('.')";
      }
      if (/^[._-]/.test(this.item_id) | /[._-]$/.test(this.item_id)) {
        return "ID cannot start or end with puncutation";
      }
      if (this.item_id.length < 1 || this.item_id.length > 40) {
        return "ID must be between 1 and 40 characters in length";
      }
      return "";
    },
  },
  methods: {
    async submitForm() {
      console.log("new equipment form submit triggered");

      // get any extra data by calling the optional callback from the type-specific addon component
      // const extraData = this.startingDataCallback && this.startingDataCallback();
      // let startingCollection = [];
      // if (this.startInCollection != null) {
      //   startingCollection = this.startInCollection.map((x) => ({
      //     collection_id: x.collection_id,
      //     immutable_id: x.immutable_id,
      //     type: "collections",
      //   }));
      // }

      await createNewItem(
        this.item_id,
        this.item_type,
        this.date,
        this.name,
        null, // no startingCollection
        { location: this.location }, // no extra data
        this.selectedItemToCopy && this.selectedItemToCopy.item_id,
      )
        .then(() => {
          this.$emit("update:modelValue", false); // close this modal
          document.getElementById(this.item_id).scrollIntoView({ behavior: "smooth" });
          this.item_id = null;
          this.name = null;
          this.date = this.now(); // reset date to the new current time
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
              alert("Error with creating new equipment: " + error);
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
    // CollectionSelect,
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
