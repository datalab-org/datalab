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
        id="sample_id"
        v-for="sample in samples"
        :key="sample.sample_id"
        v-on:click.exact="goToSamplePage(sample.sample_id)"
        v-on:click.meta="openSamplePageInNewTab(sample.sample_id)"
        v-on:click.ctrl="openSamplePageInNewTab(sample.sample_id)"
      >
        <td>{{ sample.sample_id }}</td>
        <td>{{ sample.name }}</td>
        <td>{{ sample.chemform }}</td>
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
    goToSamplePage(sample_id) {
      this.$router.push(`/edit/${sample_id}`);
    },
    openSamplePageInNewTab(sample_id) {
      window.open(`/edit/${sample_id}`, "_blank");
    },
    // should also check response.OK? And retry if
    getSamples() {
      getSampleList().catch((error) => {
        console.error("Fetch error");
        console.error(error);
        this.isSampleFetchError = true;
      });
    },
    deleteSample(sample) {
      if (confirm(`Are you sure you want to delete ${sample.sample_id}?`)) {
        console.log("deleting...");
        deleteSample(sample.sample_id, sample);
      }
      console.log("delete cancelled...");
    },
  },
  created() {
    this.getSamples();
  },
};
</script>
