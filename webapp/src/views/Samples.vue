<template>
  <Navbar />

  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-12 mx-auto mb-3">
        <button class="btn btn-default" @click="createItemModalIsOpen = true">Add an item</button>
        <button class="btn btn-default ml-2" @click="batchCreateItemModalIsOpen = true">
          Add batch of items
        </button>
      </div>
    </div>
    <div class="row">
      <div class="col-sm-12 mx-auto">
        <SampleTable />
      </div>
    </div>
  </div>
  <CreateItemModal v-model="createItemModalIsOpen" :allowed-types="allowedTypes" />
  <BatchCreateItemModal v-model="batchCreateItemModalIsOpen" />
</template>

<script>
import Navbar from "@/components/Navbar";
import SampleTable from "@/components/SampleTable";
import CreateItemModal from "@/components/CreateItemModal";
import BatchCreateItemModal from "@/components/BatchCreateItemModal";
import { SAMPLE_TABLE_TYPES } from "@/resources.js";

export default {
  name: "Samples",
  components: {
    Navbar,
    SampleTable,
    CreateItemModal,
    BatchCreateItemModal,
  },
  data() {
    return {
      createItemModalIsOpen: false,
      batchCreateItemModalIsOpen: false,
      allowedTypes: SAMPLE_TABLE_TYPES,
    };
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
