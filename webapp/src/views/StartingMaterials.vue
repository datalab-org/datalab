<template>
  <Navbar />
  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-12 mx-auto mb-3">
        <button
          v-if="editable_inventory"
          class="btn btn-default"
          @click="createItemModalIsOpen = true"
        >
          Add a starting material
        </button>
      </div>
    </div>
    <div class="row">
      <div class="col-sm-12 mx-auto">
        <StartingMaterialTable></StartingMaterialTable>
      </div>
    </div>
  </div>
  <CreateItemModal v-model="createItemModalIsOpen" :allowed-types="allowedTypes" />
</template>

<script>
import Navbar from "@/components/Navbar";
import StartingMaterialTable from "@/components/StartingMaterialTable";
import CreateItemModal from "@/components/CreateItemModal";
import { INVENTORY_TABLE_TYPES, EDITABLE_INVENTORY } from "@/resources.js";

export default {
  name: "StartingMaterials",
  components: {
    Navbar,
    StartingMaterialTable,
    CreateItemModal,
  },
  data() {
    return {
      createItemModalIsOpen: false,
      allowedTypes: INVENTORY_TABLE_TYPES,
    };
  },
  created() {
    this.editable_inventory = EDITABLE_INVENTORY;
  },
};
</script>

<style scoped>
#tableContainer.overlay:after {
  content: "";
  display: block;
  position: fixed; /* could also be absolute */
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  z-index: 10;
  background-color: rgba(0, 0, 0, 0.2);
}
</style>
