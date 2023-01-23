<template>
  <Navbar />
  <div class="container">
    <div class="row">
      <div class="col-sm-8 mx-auto">
        <h2>About datalab</h2>
        Datalab is a place to store experimental data and the connections between them.
        <!-- <tiny-mce-inline /> -->
      </div>
    </div>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";

export default {
  components: { Navbar },
};
</script>

<style scoped>
h1 {
  margin: 2rem 0rem;
}
</style>
