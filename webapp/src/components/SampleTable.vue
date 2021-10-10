<template>
  <div v-if="isSampleFetchError" class="alert alert-danger">
    Server Error. Sample list not retreived.
  </div>
  <table class="table table-hover table-sm">
    <thead>
      <tr>
        <th scope="col">ID</th>
        <th scope="col">Sample name</th>
        <th scope="col">Formula</th>
        <th scope="col">Date</th>
        <th scope="col"># of blocks</th>
      </tr>
    </thead>
    <tbody>
      <tr
        :id="sample.item_id"
        v-for="sample in samples"
        :key="sample.item_id"
        v-on:click.exact="goToEditPage(sample.item_id)"
        v-on:click.meta="openEditPageInNewTab(sample.item_id)"
        v-on:click.ctrl="openEditPageInNewTab(sample.item_id)"
      >
        <td>{{ sample.item_id }}</td>
        <td>{{ sample.name }}</td>
        <td><ChemicalFormula :formula="sample.chemform" /></td>
        <td>{{ sample.date }}</td>
        <td>{{ sample.nblocks }}</td>
        <button type="button" class="close" @click.stop="deleteSample(sample)" aria-label="delete">
          <span aria-hidden="true">&times;</span>
        </button>
      </tr>
    </tbody>
  </table>
</template>

<script>
import ChemicalFormula from "@/components/ChemicalFormula";
import { getSampleList, deleteSample } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      isSampleFetchError: false,
    };
  },
  computed: {
    samples() {
      return this.$store.state.sample_list;
    },
  },
  methods: {
    goToEditPage(item_id) {
      this.$router.push(`/edit/${item_id}`);
    },
    openEditPageInNewTab(item_id) {
      window.open(`/edit/${item_id}`, "_blank");
    },
    // should also check response.OK? And retry if
    getSamples() {
      getSampleList().catch(() => {
        this.isSampleFetchError = true;
      });
    },
    deleteSample(sample) {
      if (confirm(`Are you sure you want to delete ${sample.item_id}?`)) {
        console.log("deleting...");
        deleteSample(sample.item_id, sample);
      }
      console.log("delete cancelled...");
    },
  },
  created() {
    this.getSamples();
  },
  components: {
    ChemicalFormula,
  },
};
</script>
