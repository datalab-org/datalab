<template>
  <div>
    <span
      class="badge badge-light mr-2"
      :class="{ clickable: enableClick || enableModifiedClick }"
      :style="{ backgroundColor: badgeColor }"
      @click.exact="enableClick ? openEditPageInNewTab() : null"
      @click.meta.stop="enableModifiedClick ? openEditPageInNewTab() : null"
      @click.ctrl.stop="enableModifiedClick ? openEditPageInNewTab() : null"
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
    enableClick: {
      type: Boolean,
      default: false,
    },
    enableModifiedClick: {
      type: Boolean,
      default: false,
    },
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
.clickable {
  cursor: pointer;
}
</style>
