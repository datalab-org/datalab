<template>
  <div v-if="isFetchError" class="alert alert-danger">
    <font-awesome-icon icon="exclamation-circle" />&nbsp;Server error: inventory could not be
    retrieved.
  </div>
  <table class="table table-hover table-sm">
    <thead>
      <tr align="center">
        <th scope="col">ID</th>
        <th scope="col">Name</th>
        <th scope="col">Formula</th>
        <th scope="col">Date acquired</th>
        <th scope="col">Purity</th>
        <th scope="col"># of blocks</th>
        <th scope="col"></th>
      </tr>
    </thead>
    <tbody>
      <tr
        :id="item.item_id"
        v-for="item in startingMaterials"
        :key="item.item_id"
        v-on:click.exact="goToEditPage(item.item_id)"
        v-on:click.meta="openEditPageInNewTab(item.item_id)"
        v-on:click.ctrl="openEditPageInNewTab(item.item_id)"
      >
        <td>
          <FormattedItemName
            :item_id="item.item_id"
            :itemType="item?.type || 'starting_materials'"
            enableModifiedClick
          />
        </td>
        <td>{{ item.name }}</td>
        <td><ChemicalFormula :formula="item.chemform" /></td>
        <td>{{ $filters.IsoDatetimeToDate(item.date) }}</td>
        <td>{{ item.chemical_purity }}</td>
        <td>{{ item.nblocks }}</td>
        <td align="right">
          <button type="button" class="close" @click.stop="deleteItem(item)" aria-label="delete">
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
import { getStartingMaterialList, deleteStartingMaterial } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      isFetchError: false,
    };
  },
  computed: {
    startingMaterials() {
      return this.$store.state.starting_material_list;
    },
  },
  methods: {
    goToEditPage(item_id) {
      this.$router.push(`/edit/${item_id}`);
    },
    openEditPageInNewTab(item_id) {
      window.open(`/edit/${item_id}`, "_blank");
    },
    getStartingMaterials() {
      getStartingMaterialList().catch(() => {
        this.isFetchError = true;
      });
    },
    deleteItem(item) {
      if (confirm(`Are you sure you want to delete starting material "${item.item_id}"?`)) {
        console.log("deleting...");
        deleteStartingMaterial(item.item_id);
      }
      console.log("delete cancelled.");
    },
  },
  created() {
    this.getStartingMaterials();
  },
  components: {
    ChemicalFormula,
    FormattedItemName,
  },
};
</script>
