<template>
  <Navbar />

  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-12 mx-auto">
        <SampleTablePrime />
      </div>
    </div>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import SampleTablePrime from "@/components/SampleTablePrime";

export default {
  name: "Samples",
  components: {
    Navbar,
    SampleTablePrime,
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
