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
      {{ collection_id }}
    </span>
    {{ shortenedName }}
  </div>
</template>

<script>
import { itemTypes } from "@/resources.js";

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
    maxLength: {
      type: Number,
      default: NaN,
    },
  },
  computed: {
    badgeColor() {
      return "LightGrey";
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

<style scoped>
.clickable {
  cursor: pointer;
}
</style>
