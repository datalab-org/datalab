<template>
  <span
    class="formatted-collection-name badge badge-light"
    :class="{ clickable: enableClick || enableModifiedClick }"
    :style="{ 'border-color': badgeColor, color: badgeColor }"
    @click.exact="enableClick ? openEditPageInNewTab() : null"
    @click.meta.stop="enableModifiedClick ? openEditPageInNewTab() : null"
    @click.ctrl.stop="enableModifiedClick ? openEditPageInNewTab() : null"
  >
    {{ collection_id }}
  </span>
  {{ shortenedName }}
</template>

<script>
import { itemTypes } from "@/resources.js";

export default {
  data() {
    return {
      itemType: "collections",
    };
  },
  props: {
    collection_id: String,
    title: {
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
  computed: {
    badgeColor() {
      return itemTypes[this.itemType]?.navbarColor || "LightGrey";
    },
    shortenedName() {
      if (this.maxLength && this.maxLength < this.name.length) {
        return this.title.substring(0, this.maxLength) + "...";
      } else {
        return this.title;
      }
    },
  },
  methods: {
    openEditPageInNewTab() {
      this.$emit("collectionIdClicked");
      window.open(`/collections/${this.collection_id}`, "_blank");
    },
  },
  emits: ["collectionIdClicked"],
};
</script>
