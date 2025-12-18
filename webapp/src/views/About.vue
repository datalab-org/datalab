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
          <a href="https://github.com/datalab-org/datalab"
            ><font-awesome-icon :icon="['fab', 'github']" />&nbsp;datalab-org/datalab</a
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

        <UserActivityGraph :combined="true" :title="'User activity:'" />

        <h5>Deployment info:</h5>
        <div class="p-3">
          <table>
            <tbody>
              <tr>
                <td>API version</td>
                <td>
                  <code>{{ apiInfo?.server_version ?? "unknown" }}</code>
                </td>
              </tr>
              <tr>
                <td>App version</td>
                <td>
                  <code>{{ appVersion }}</code>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <h5>Credits and acknowledgements</h5>

        <p><i>datalab</i> was initially conceived and developed by:</p>
        <ul>
          <li>
            <a href="https://jdbocarsly.github.io">Prof Joshua Bocarsly</a> (<a
              href="https://www.uh.edu/nsm/chemistry"
              >Department of Chemistry, University of Houston</a
            >, previously
            <a href="https://www.ch.cam.ac.uk/">Department of Chemistry, University of Cambridge</a
            >)
          </li>
          <li>
            <a href="https://ml-evs.science">Dr Matthew Evans</a> (<a
              href="https://www.ch.cam.ac.uk/"
              >Department of Chemistry, University of Cambridge</a
            >, previously
            <a href="https://uclouvain.be/en/research-institutes/imcn/modl">MODL-IMCN, UCLouvain</a>
            &amp; <a href="https://matgenix.com">Matgenix</a>)
          </li>
        </ul>
        <p>
          with support from the group of
          <a href="https://grey.group.ch.cam.ac.uk/group">Professor Clare Grey</a> (University of
          Cambridge), and major contributions from:
        </p>
        <ul>
          <li><a href="https://github.com/BenjaminCharmes">Benjamin Charmes</a></li>
          <li><a href="https://github.com/be-smith/">Dr Ben Smith</a></li>
          <li><a href="https://github.com/yue-here">Dr Yue Wu</a></li>
        </ul>
        <p>
          plus contributions, feedback and testing performed by other members of the community, in
          particular, the groups of
          <a href="https://cliffegroup.co.uk">Prof Matt Cliffe</a> (University of Nottingham) and
          <a href="https://www.tu.berlin/en/concat">Dr Peter Kraus</a> (TUBerlin) and the company
          <a href="https://matgenix.com">Matgenix SRL</a>.
        </p>
        <p>
          A full list of code contributions can be found on
          <a href="https://github.com/datalab-org/datalab/graphs/contributors">GitHub</a>.
        </p>

        <p>
          Contributions to <i>datalab</i> have been supported by a mixture of academic funding and
          consultancy work through
          <a href="https://datalab.industries"><em>datalab industries ltd</em></a
          >.
        </p>
        <p>In particular, the developers thank:</p>
        <ul>
          <li>
            Initial proof-of-concept funding from the European Union's Horizon 2020 research and
            innovation programme under grant agreement 957189 (DOI:
            <a href="https://doi.org/10.3030/957189">10.3030/957189</a>), the
            <a href="https://www.big-map.eu"
              >Battery Interface Genome - Materials Acceleration Platform (BIG-MAP)</a
            >, as an external stakeholder project.
          </li>
          <li>
            The <a href="https://www.faraday.ac.uk">Faraday Institution</a> CATMAT project (FIRG016)
            for support of Dr Joshua Bocarsly during initial development of <em>datalab</em>.
          </li>
          <li>
            The <a href="https://leverhulme.ac.uk">Leverhulme Trust</a> and
            <a href="https://newtontrust.cam.ac.uk">Isaac Newton Trust</a> for support provided by
            an early career fellowship for Dr Matthew Evans.
          </li>
        </ul>

        <div align="center" style="padding-top: 20px">
          <a href="https://wwww.big-map.eu"
            ><img
              class="funding-logo"
              src="https://avatars.githubusercontent.com/u/75324577"
              width="100"
              target="_blank"
          /></a>
          <a href="https://wwww.leverhulme.ac.uk"
            ><img
              class="funding-logo"
              src="https://www.leverhulme.ac.uk/sites/default/files/Leverhulme_Trust_RGB_blue_0_0.png"
              width="250"
              target="_blank"
          /></a>
          <a href="https://www.faraday.ac.uk"
            ><img
              class="funding-logo"
              src="https://www.faraday.ac.uk/wp-content/themes/faraday/assets/faraday-logo-highres.png"
              width="250"
              target="_blank"
          /></a>
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
import UserActivityGraph from "@/components/UserActivityGraph.vue";
import { APP_VERSION } from "@/resources.js";

export default {
  components: { Navbar, StatisticsTable, UserActivityGraph },
  data() {
    return {
      apiInfo: { server_version: "unknown" },
      appVersion: APP_VERSION,
    };
  },
  async mounted() {
    this.apiInfo = this.$store.state.serverInfo;
    if (this.apiInfo == null) {
      this.apiInfo = await getInfo();
    }
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

.funding-logo {
  margin: 10px;
}
</style>
