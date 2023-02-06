<template>
  <Navbar />
  <div class="container">
    <div class="row">
      <div class="col-sm-8 mx-auto">
        <h2>About datalab</h2>
        <p>Datalab is a place to store experimental data and the connections between them.</p>

        <p>
          Datalab development occurs on GitHub at
          <a href="https://github.com/the-grey-group/datalabvue/"> the-grey-group/datalabvue</a>.
        </p>

        Datalab was primarily developed by:
        <ul>
          <li>Joshua Bocarsly (Department of Chemistry, University of Cambridge)</li>
          <li>Matthew Evans (MODL-IMCN, UCLouvain & Matgenix)</li>
        </ul>

        This project has received funding from the European Union's Horizon 2020 research and
        innovation programme under grant agreement 957189 (DOI:
        <a href="https://doi.org/10.3030/957189">10.3030/957189</a>), the
        <a href="https://www.big-map.eu"
          >Battery Interface Genome - Materials Acceleration Platform (BIG-MAP)</a
        >
        , as an external stakeholder project.

        <div align="center">
          <img src="https://avatars.githubusercontent.com/u/75324577" width="100" />
        </div>

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
