<template>
  <label class="mr-2">Collection Members</label>

  <table class="table table-hover table-sm" data-testid="sample-table">
    <thead>
      <tr align="center">
        <th scope="col">ID</th>
        <th scope="col">Sample name</th>
        <th scope="col">Formula</th>
        <th scope="col">Date</th>
        <th scope="col">Creators</th>
        <th scope="col"># of blocks</th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="sample in samples"
        :id="sample.item_id"
        :key="sample.item_id"
        v-on:click.exact="goToEditPage(sample.item_id)"
        v-on:click.meta="openEditPageInNewTab(sample.item_id)"
        v-on:click.ctrl="openEditPageInNewTab(sample.item_id)"
      >
        <td align="left">{{ sample.item_id }}</td>
        <td align="left">{{ sample.name }}</td>
        <td><ChemicalFormula :formula="sample.chemform" /></td>
        <td align="center">{{ $filters.IsoDatetimeToDate(sample.date) }}</td>
        <td align="center">
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
        <td align="right">{{ sample.nblocks }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script>
// import FormattedItemName from "@/components/FormattedItemName"

export default {
  data() {
    return {
      activeTab: "parents",
    };
  },
  computed: {
    samples() {
      return this.$store.state.all_collection_children[this.collection_id];
    },
  },

  methods: {
    openEditPageInNewTab(item_id) {
      window.open(`/edit/${item_id}`, "_blank");
    },
    goToEditPage(item_id) {
      this.$router.push(`/edit/${item_id}`);
    },
  },
  props: {
    collection_id: String,
  },
};
</script>

<style scoped>
.nav-link {
  cursor: pointer;
}

.contents-item {
  cursor: pointer;
}

.contents-blocktype {
  font-style: italic;
  color: gray;
  margin-right: 1rem;
}

.contents-blocktitle {
  color: #004175;
}

#contents-ol {
  margin-bottom: 0rem;
  padding-left: 1rem;
}
</style>
