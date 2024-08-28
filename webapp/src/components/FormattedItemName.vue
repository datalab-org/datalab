<template>
  <span v-if="item_id">
    <span
      class="formatted-item-name badge badge-light"
      :class="{ clickable: enableClick || enableModifiedClick }"
      :style="{ backgroundColor: badgeColor }"
      @click.exact="enableClick ? openEditPageInNewTab() : null"
      @click.meta.stop="enableModifiedClick ? openEditPageInNewTab() : null"
      @click.ctrl.stop="enableModifiedClick ? openEditPageInNewTab() : null"
    >
      <span v-if="showType" class="item-type-label">&lt;{{ navbarName }}&gt;</span>
      {{ item_id }}
    </span>
    {{ shortenedName }}
    <span v-if="chemform && chemform != ' '"> [ <ChemicalFormula :formula="chemform" /> ] </span>
  </span>
  <span v-else>
    <font-awesome-icon v-if="selecting" :icon="['far', 'plus-square']" />
    {{ shortenedName }}
  </span>
</template>

<script>
import { itemTypes } from "@/resources.js";
import ChemicalFormula from "@/components/ChemicalFormula.vue";

export default {
  components: {
    ChemicalFormula,
  },
  props: {
    item_id: { type: String, required: true },
    itemType: { type: String, required: true },
    showType: { type: Boolean, default: false },
    selecting: {
      type: Boolean,
      default: false,
    },
    name: {
      type: String,
      default: "",
    },
    chemform: {
      type: String,
      default: "",
    },
    enableClick: {
      type: Boolean,
      default: false,
    },
    enableModifiedClick: {
      type: Boolean,
      default: false,
    },
    maxLength: {
      type: Number,
      default: NaN,
    },
  },
  emits: ["itemIdClicked"],
  computed: {
    badgeColor() {
      return itemTypes[this.itemType]?.lightColor || "LightGrey";
    },
    navbarName() {
      return itemTypes[this.itemType]?.navbarName || this.itemType;
    },
    shortenedName() {
      if (this.maxLength && this.maxLength < this.name.length) {
        return this.name.substring(0, this.maxLength) + "...";
      } else {
        return this.name || "";
      }
    },
  },
  methods: {
    openEditPageInNewTab() {
      this.$emit("itemIdClicked");
      window.open(`/edit/${this.item_id}`, "_blank");
    },
  },
};
</script>

<style scoped>
.formatted-item-name {
  border: 2px solid transparent;
}

.item-type-label {
  font-weight: bold;
  text-transform: uppercase;
  font-family: monospace;
}

.formatted-item-name.clickable:hover {
  border: 2px solid rgba(0, 0, 0, 0.6);
  box-shadow: 0 0 2px gray;
}
</style>
