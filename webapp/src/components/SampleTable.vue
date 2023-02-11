<template>
  <div v-if="isSampleFetchError" class="alert alert-danger">
    Server Error. Sample list not retreived.
  </div>
  <table class="table table-hover table-sm" data-testid="sample-table">
    <thead>
      <tr>
        <th scope="col">ID</th>
        <th scope="col">Type</th>
        <th scope="col">Sample name</th>
        <th scope="col">Formula</th>
        <th class="text-center" scope="col">Date</th>
        <th class="text-center" scope="col">Creators</th>
        <th class="text-center" scope="col"># of blocks</th>
        <th scope="col"></th>
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
        <td align="left">{{ sample.item_id }}</td>
        <td aligh="center">{{ itemTypes[sample.type].display }}</td>
        <td align="left">{{ sample.name }}</td>
        <td><ChemicalFormula :formula="sample.chemform" /></td>
        <td class="text-center">{{ $filters.IsoDatetimeToDate(sample.date) }}</td>
        <td class="text-center">
          <div v-for="creator in sample.creators" :key="creator.display_name">
            <img
              :src="
                'https://www.gravatar.com/avatar/' +
                md5(creator.contact_email || creator.display_name) +
                '?s=20&d=' +
                this.gravatar_style
              "
              class="avatar"
              width="20"
              height="20"
              :title="creator.display_name"
            />
          </div>
        </td>
        <td class="text-right">{{ sample.nblocks }}</td>
        <td class="clickable" @click.stop="deleteSample(sample)">
          <button
            type="button"
            class="close"
            @click.stop="deleteSample(sample)"
            aria-label="delete"
          >
            <span aria-hidden="true" style="color: grey">&times;</span>
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import ChemicalFormula from "@/components/ChemicalFormula";
import { getSampleList, deleteSample } from "@/server_fetch_utils.js";
import crypto from "crypto";
import { GRAVATAR_STYLE, itemTypes } from "@/resources.js";

export default {
  data() {
    return {
      isSampleFetchError: false,
      gravatar_style: GRAVATAR_STYLE,
      itemTypes: itemTypes,
    };
  },
  computed: {
    samples() {
      return this.$store.state.sample_list;
    },
  },
  methods: {
    md5(value) {
      // Returns the MD5 hash of the given string.
      return crypto.createHash("md5").update(value).digest("hex");
    },
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
      if (confirm(`Are you sure you want to delete sample "${sample.item_id}"?`)) {
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

<style scoped>
.avatar {
  border: 2px solid grey;
  border-radius: 50%;
}
.avatar:hover {
  border: 2px solid skyblue;
}

.clickable {
  cursor: pointer;
}
</style>
