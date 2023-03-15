<template>
  <Navbar />
  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-10 mx-auto">
        <FancyStartingMaterialTable />
      </div>
    </div>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import FancyStartingMaterialTable from "@/components/FancyStartingMaterialTable";

export default {
  components: {
    Navbar,
    FancyStartingMaterialTable,
  },
};
</script>
