<template>
  <Navbar />

  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-10 mx-auto mb-3">
        <button class="btn btn-default" @click="createCollectionModalIsOpen = true">
          Create new collection
        </button>
      </div>
    </div>
    <div class="row">
      <div class="col-sm-10 mx-auto">
        <CollectionTable />
      </div>
    </div>
  </div>
  <CreateCollectionModal v-model="createCollectionModalIsOpen" />
</template>

<script>
import Navbar from "@/components/Navbar";
import CollectionTable from "@/components/CollectionTable";
import CreateCollectionModal from "@/components/CreateCollectionModal";

export default {
  name: "Collections",
  components: {
    Navbar,
    CollectionTable,
    CreateCollectionModal,
  },
  data() {
    return {
      createCollectionModalIsOpen: false,
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
