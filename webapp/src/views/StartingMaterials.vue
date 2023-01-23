<template>
  <Navbar />
  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-10 mx-auto">
        <StartingMaterialTable></StartingMaterialTable>
      </div>
    </div>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import StartingMaterialTable from "@/components/StartingMaterialTable";

export default {
  components: {
    Navbar,
    StartingMaterialTable,
  },
};
</script>
