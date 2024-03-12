<template>
  <Navbar />
  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-12 mx-auto mb-3">
        <button class="btn btn-default" @click="createItemModalIsOpen = true">
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
  <CreateItemModal v-model="createItemModalIsOpen" />
</template>

<script>
import Navbar from "@/components/Navbar";
import StartingMaterialTable from "@/components/StartingMaterialTable";
import CreateItemModal from "@/components/CreateItemModal";

export default {
  name: "StartingMaterials",
  data() {
    return {
      createItemModalIsOpen: false,
    };
  },
  components: {
    Navbar,
    StartingMaterialTable,
    CreateItemModal,
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
