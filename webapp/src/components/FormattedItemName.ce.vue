<template>
  <span v-if="item_id">
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
    {{ shortenedName }}
    <span v-if="chemform && chemform != ' '"> [ <ChemicalFormula :formula="chemform" /> ] </span>
  </span>
  <span v-else>
    <!-- <font-awesome-icon v-if="selecting" :icon="['far', 'plus-square']" /> -->
    {{ shortenedName }}
  </span>
</template>

<script>
import { itemTypes } from "@/resources.js";
import ChemicalFormula from "@/components/ChemicalFormula.vue";

export default {
  props: {
    item_id: String,
    itemType: String,
    selecting: {
      type: Boolean,
      default: false,
    },
    name: {
      type: String,
      default: null,
    },
    chemform: {
      type: String,
      default: null,
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
  computed: {
    badgeColor() {
      return itemTypes[this.itemType]?.lightColor || "LightGrey";
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

.badge {
  border: 2px solid transparent;
}

.mr-2 {
  margin-right: 0.5rem !important;
}

.badge-light {
  color: #212529;
  /*  background-color: #f8f9fa;*/
}
</style>
