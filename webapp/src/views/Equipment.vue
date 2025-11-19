<template>
  <Navbar />

  <div id="tableContainer" class="container-fluid">
    <div class="w-100 px-5 mx-auto">
      <EquipmentTable />
    </div>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import EquipmentTable from "@/components/EquipmentTable";

export default {
  name: "Equipment",
  components: {
    Navbar,
    EquipmentTable,
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
