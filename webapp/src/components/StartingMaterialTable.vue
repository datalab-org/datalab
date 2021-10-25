<template>
  <div v-if="isFetchError" class="alert alert-danger">
    Server Error. Starting material list not retreived.
  </div>
  <table class="table table-hover table-sm">
    <thead>
      <tr>
        <th scope="col">ID</th>
        <th scope="col">Name</th>
        <th scope="col">Formula</th>
        <th scope="col">Date acquired</th>
        <th scope="col">Purity</th>
        <th scope="col"># of blocks</th>
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
        <td>{{ item.item_id }}</td>
        <td>{{ item.name }}</td>
        <td><ChemicalFormula :formula="item.chemform" /></td>
        <td>{{ $filters.IsoDatetimeToDate(item.date_acquired) }}</td>
        <td>{{ item.chemical_purity }}</td>
        <td>{{ item.nblocks }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import ChemicalFormula from "@/components/ChemicalFormula";
import { getStartingMaterialList } from "@/server_fetch_utils.js";

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
  },
  created() {
    this.getStartingMaterials();
  },
  components: {
    ChemicalFormula,
  },
};
</script>
