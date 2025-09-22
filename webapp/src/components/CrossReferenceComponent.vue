<template>
  <node-view-wrapper class="cross-reference-wrapper" contenteditable="false">
    <span
      v-if="isValid"
      class="formatted-cross-reference badge badge-light clickable"
      :style="{ backgroundColor: badgeColor }"
      @click="openEditPage"
    >
      @{{ node.attrs.itemId }}
    </span>
    <span v-else class="badge badge-secondary"> @{{ node.attrs.itemId }} </span>
    <span v-if="isValid && displayName">
      {{ displayName }}
      <span v-if="node.attrs.chemform">
        [ <ChemicalFormula :formula="node.attrs.chemform" /> ]
      </span>
    </span>
  </node-view-wrapper>
</template>

<script>
import { NodeViewWrapper } from "@tiptap/vue-3";
import ChemicalFormula from "@/components/ChemicalFormula.vue";
import { itemTypes } from "@/resources.js";

export default {
  components: {
    NodeViewWrapper,
    ChemicalFormula,
  },
  props: {
    node: {
      type: Object,
      required: true,
    },
    editor: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      isValid: false,
    };
  },
  computed: {
    badgeColor() {
      const itemType = this.node.attrs.itemType || "samples";
      return itemTypes[itemType]?.lightColor || "LightGrey";
    },
    displayName() {
      return this.node.attrs.name || "";
    },
  },
  watch: {
    "node.attrs.itemId": {
      handler() {
        this.checkValidity();
      },
      immediate: true,
    },
  },
  methods: {
    async checkValidity() {
      if (!this.node.attrs.itemId) {
        this.isValid = false;
        return;
      }

      this.isValid = true;
    },
    openEditPage() {
      window.open(`/edit/${this.node.attrs.itemId}`, "_blank");
    },
  },
};
</script>

<style scoped>
.cross-reference-wrapper {
  display: inline;
}

.formatted-cross-reference {
  border: 2px solid transparent;
  cursor: pointer;
}

.formatted-cross-reference.clickable:hover {
  border: 2px solid rgba(0, 0, 0, 0.6);
  box-shadow: 0 0 2px gray;
}
</style>
