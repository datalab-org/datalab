<template>
  <span
    class="formatted-collection-name badge badge-light"
    :class="{ clickable: enableClick || enableModifiedClick }"
    :style="{ 'border-color': badgeColor, color: badgeColor }"
    @click.exact="enableClick ? openEditPageInSameTab() : null"
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
  props: {
    collection_id: {
      type: String,
      default: null,
    },
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
  emits: ["collectionIdClicked"],
  data() {
    return {
      itemType: "collections",
    };
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
    openEditPageInSameTab() {
      this.$emit("collectionIdClicked");
      window.location.href = `/collections/${this.collection_id}`;
    },
    openEditPageInNewTab() {
      this.$emit("collectionIdClicked");
      const newWindow = window.open(`/collections/${this.collection_id}`, "_blank");
      if (newWindow) newWindow.focus();
    },
  },
};
</script>

<style scoped>
.formatted-collection-name {
  border: 1.5px solid;
  margin: 1px;
}

.formatted-collection-name:hover {
  border-width: 2px;
  margin: 0px;
  box-shadow: 0 0 2px gray;
}
</style>
