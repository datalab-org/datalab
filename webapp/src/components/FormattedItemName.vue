<template>
  <div>
    <span
      class="item-id-badge badge badge-light mr-2"
      :style="{ backgroundColor: badgeColor }"
      @click.meta="openEditPageInNewTab"
      @click.ctrl="openEditPageInNewTab"
    >
      {{ item_id }}
    </span>
    {{ name }}
    <span v-if="chemform && chemform != ' '"> [ <ChemicalFormula :formula="chemform" /> ] </span>
  </div>
</template>

<script>
import { itemTypes } from "@/resources.js";
import ChemicalFormula from "@/components/ChemicalFormula.vue";

export default {
  props: {
    item_id: String,
    itemType: String,
    name: String,
    chemform: String,
  },
  computed: {
    badgeColor() {
      return itemTypes[this.itemType]?.lightColor || "LightGrey";
    },
  },
  methods: {
    openEditPageInNewTab() {
      this.$emit("itemIdClicked");
      window.open(`/edit/${this.item_id}`, "_blank");
    },
  },
  components: {
    ChemicalFormula,
  },
  emits: ["itemIdClicked"],
};
</script>

<style scoped>
.item-id-badge {
  cursor: pointer;
}
</style>
