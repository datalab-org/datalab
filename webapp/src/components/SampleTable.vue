<template>
  <div v-if="isSampleFetchError" class="alert alert-danger">
    <font-awesome-icon icon="exclamation-circle" />&nbsp;Server Error. Sample list could not be
    retreived.
  </div>
  <table class="table table-hover table-sm" data-testid="sample-table">
    <thead>
      <tr>
        <th scope="col">ID</th>
        <th scope="col">Type</th>
        <th scope="col">Sample name</th>
        <th scope="col">Formula</th>
        <th class="text-center" scope="col">Date</th>
        <th scope="col">Collections</th>
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
        <td align="left" class="table-item-id">
          <FormattedItemName
            :item_id="sample.item_id"
            :itemType="sample?.type"
            enableModifiedClick
          />
        </td>
        <td align="center">{{ itemTypes[sample.type].display }}</td>
        <td align="left">{{ sample.name }}</td>
        <td><ChemicalFormula :formula="sample.chemform" /></td>
        <td class="text-center">{{ $filters.IsoDatetimeToDate(sample.date) }}</td>
        <td><CollectionList :collections="sample.collections" /></td>
        <td align="center"><Creators :creators="sample.creators" /></td>
        <td class="text-right">{{ sample.nblocks }}</td>
        <td align="right">
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
import FormattedItemName from "@/components/FormattedItemName";
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";
import { getSampleList, deleteSample } from "@/server_fetch_utils.js";
import { itemTypes } from "@/resources.js";

export default {
  data() {
    return {
      isSampleFetchError: false,
      itemTypes: itemTypes,
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
      if (confirm(`Are you sure you want to delete sample "${sample.item_id}"?`)) {
        console.log("deleting...");
        deleteSample(sample.item_id);
      }
      console.log("delete cancelled...");
    },
  },
  created() {
    this.getSamples();
  },
  components: {
    ChemicalFormula,
    FormattedItemName,
    Creators,
    CollectionList,
  },
};
</script>

<style scoped>
.clickable {
  cursor: pointer;
}
</style>
