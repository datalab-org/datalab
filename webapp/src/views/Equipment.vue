<template>
  <Navbar />

  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-12 mx-auto mb-3">
        <button class="btn btn-default" @click="createEquipmentModalIsOpen = true">
          Add an item
        </button>
      </div>
    </div>
    <div class="row">
      <div class="col-sm-12 mx-auto">
        <EquipmentTable />
      </div>
    </div>
  </div>
  <CreateEquipmentModal v-model="createEquipmentModalIsOpen" />
</template>

<script>
import Navbar from "@/components/Navbar";
import EquipmentTable from "@/components/EquipmentTable";
import CreateEquipmentModal from "@/components/CreateEquipmentModal";

export default {
  name: "Equipments",
  data() {
    return {
      createEquipmentModalIsOpen: false,
    };
  },
  components: {
    Navbar,
    EquipmentTable,
    CreateEquipmentModal,
  },
};
</script>

<style scoped>
.fade {
  opacity: 0;
  transition: opacity 0.15s linear;
}
.fade.show {
  opacity: 1;
}

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
