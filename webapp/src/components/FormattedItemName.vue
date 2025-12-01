<template>
  <span v-if="item_id">
    <span
      class="formatted-item-name badge badge-light"
      :class="{ clickable: enableClick || enableModifiedClick }"
      :style="{ backgroundColor: badgeColor }"
      @click.exact="enableClick ? openEditPageInSameTab() : null"
      @click.meta.stop="enableModifiedClick ? openEditPageInNewTab() : null"
      @click.ctrl.stop="enableModifiedClick ? openEditPageInNewTab() : null"
    >
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
    shortenedName() {
      const safeName = this.name || "";
      if (this.maxLength && this.maxLength < safeName.length) {
        return safeName.substring(0, this.maxLength) + "...";
      }
      return safeName;
    },
  },
  methods: {
    openEditPageInSameTab() {
      this.$emit("itemIdClicked");
      if (window.Cypress && window.location.href.includes("__cypress")) {
        return;
      }
      window.location.href = `/edit/${this.item_id}`;
    },
    openEditPageInNewTab() {
      this.$emit("itemIdClicked");
      if (window.Cypress && window.location.href.includes("__cypress")) {
        return;
      }
      const newWindow = window.open(`/edit/${this.item_id}`, "_blank");
      if (newWindow) newWindow.focus();
    },
  },
};
</script>

<style scoped>
.formatted-item-name {
  border: 2px solid transparent;
}

.formatted-item-name.clickable:hover {
  border: 2px solid rgba(0, 0, 0, 0.6);
  box-shadow: 0 0 2px gray;
}
</style>
