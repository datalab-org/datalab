<template>
  <Navbar />

  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-12 mx-auto mb-3">
        <button class="btn btn-default" @click="createItemModalIsOpen = true">Add an item</button>
        <button class="btn btn-default ml-2" @click="BatchCreateItemModalIsOpen = true">
          Add batch of samples
        </button>
      </div>
    </div>
    <div class="row">
      <div class="col-sm-12 mx-auto">
        <FancySampleTable />
      </div>
    </div>
  </div>
  <CreateItemModal v-model="createItemModalIsOpen" />
  <BatchCreateItemModal v-model="BatchCreateItemModalIsOpen" />
</template>

<script>
import Navbar from "@/components/Navbar";
import FancySampleTable from "@/components/FancySampleTable";
import CreateItemModal from "@/components/CreateItemModal";
import BatchCreateItemModal from "@/components/BatchCreateItemModal";

export default {
  name: "Samples",
  components: {
    Navbar,
    FancySampleTable,
    CreateItemModal,
    BatchCreateItemModal,
  },
  data() {
    return {
      createItemModalIsOpen: false,
      BatchCreateItemModalIsOpen: false,
    };
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
