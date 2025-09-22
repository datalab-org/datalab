<template>
  <node-view-wrapper class="cross-reference-wrapper" contenteditable="false">
    <FormattedItemName
      :item_id="node.attrs.itemId"
      :item-type="node.attrs.itemType"
      :selecting="true"
      enable-click
      :max-length="formattedItemNameMaxLength"
      class="formatted-cross-reference-badge"
    />
  </node-view-wrapper>
</template>

<script>
import { NodeViewWrapper } from "@tiptap/vue-3";
import FormattedItemName from "@/components/FormattedItemName.vue";

export default {
  components: {
    NodeViewWrapper,
    FormattedItemName,
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
    formattedItemNameMaxLength: {
      type: Number,
      default: NaN,
    },
  },
  methods: {
    openEditPage() {
      if (!this.node.attrs.itemId) return;
      window.open(`/edit/${this.node.attrs.itemId}`, "_blank");
    },
  },
};
</script>

<style scoped>
.cross-reference-wrapper {
  display: inline;
}

.formatted-cross-reference-badge {
  cursor: pointer;
  display: inline-flex;
}
</style>
