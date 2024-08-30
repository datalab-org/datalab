<template>
  <Navbar />

  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-12 mx-auto">
        <EquipmentPrimeTable />
      </div>
    </div>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import EquipmentPrimeTable from "@/components/EquipmentPrimeTable";

export default {
  name: "TestPrime",
  components: {
    Navbar,
    EquipmentPrimeTable,
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
