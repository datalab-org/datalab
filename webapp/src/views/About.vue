<template>
  <Navbar />
  <div class="container">
    <div class="row">
      <div class="col-sm-8 mx-auto">
        <h2>About datalab</h2>
        <p>Datalab is a place to store experimental data and the connections between them.</p>

        <p>
          Datalab is open source (MIT license) and development occurs on GitHub at
          <a href="https://github.com/the-grey-group/datalab"
            ><font-awesome-icon :icon="['fab', 'github']" />&nbsp;the-grey-group/datalab</a
          >
          with documentation available on
          <a href="https://the-datalab.readthedocs.io"
            ><font-awesome-icon icon="book" />&nbsp;ReadTheDocs</a
          >.
        </p>

        <StatisticsTable />

        Datalab was primarily developed by:
        <ul>
          <li>
            <a href="https://github.com/jdbocarsly"
              ><font-awesome-icon :icon="['fab', 'github']" /></a
            >&nbsp;Joshua Bocarsly (Department of Chemistry, University of Cambridge)
          </li>
          <li>
            <a href="https://github.com/ml-evs"><font-awesome-icon :icon="['fab', 'github']" /></a
            >&nbsp;Matthew Evans (MODL-IMCN, UCLouvain & Matgenix)
          </li>
        </ul>

        This project has received funding from the European Union's Horizon 2020 research and
        innovation programme under grant agreement 957189 (DOI:
        <a href="https://doi.org/10.3030/957189">10.3030/957189</a>), the
        <a href="https://www.big-map.eu"
          >Battery Interface Genome - Materials Acceleration Platform (BIG-MAP)</a
        >
        , as an external stakeholder project.

        <div align="center" style="padding-top: 20px">
          <img src="https://avatars.githubusercontent.com/u/75324577" width="100" target="_blank" />
        </div>

        <!-- <tiny-mce-inline /> -->
      </div>
    </div>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import StatisticsTable from "@/components/StatisticsTable";

export default {
  components: { Navbar, StatisticsTable },
};
</script>

<style scoped>
h1 {
  margin: 2rem 0rem;
}
</style>
