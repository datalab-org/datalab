<template>
  <Navbar />
  <div class="container">
    <div class="row">
      <div class="col-sm-8 mx-auto">
        <h4 class="p-3 mx-auto" style="width: 90%">
          datalab is a place to store experimental data and the connections between them.
        </h4>

        <p>
          datalab is open source (MIT license) and development occurs on GitHub at
          <a href="https://github.com/the-grey-group/datalab"
            ><font-awesome-icon :icon="['fab', 'github']" />&nbsp;the-grey-group/datalab</a
          >
          with documentation available on
          <a href="https://the-datalab.readthedocs.io"
            ><font-awesome-icon icon="book" />&nbsp;ReadTheDocs</a
          >.
        </p>

        <h5>Deployment stats:</h5>
        <div class="mx-auto" style="width: 80%">
          <StatisticsTable />
        </div>

        <h5>Deployment info:</h5>
        <div class="p-3">
          <table>
            <tr>
              <td>API version</td>
              <td>
                <code>{{ apiInfo.apiVersion }}</code>
              </td>
            </tr>
            <tr>
              <td>App version</td>
              <td><code>0.3.2</code></td>
            </tr>
          </table>
        </div>

        datalab was primarily developed by:
        <ul>
          <li>
            <a href="https://github.com/jdbocarsly"
              ><font-awesome-icon :icon="['fab', 'github']" /></a
            >&nbsp;Joshua Bocarsly (Department of Chemistry, University of Houston, previously
            Department of Chemistry, University of Cambridge)
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
import { getInfo } from "@/server_fetch_utils.js";
import StatisticsTable from "@/components/StatisticsTable";

export default {
  components: { Navbar, StatisticsTable },
  data() {
    return {
      apiInfo: { apiVersion: "unknown" },
    };
  },
  async mounted() {
    this.apiInfo = await getInfo();
  },
};
</script>

<style scoped>
h1 {
  margin: 2rem 0rem;
}

td,
th {
  text-align: center;
  border-top: 1px solid #ddd;
  border-right: 1px solid #ddd;
  border-left: 1px solid #ddd;
  border-bottom: 1px solid #ddd;
}
</style>
