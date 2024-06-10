<template>
  <span
    class="badge"
    :class="{ clickable: enableClick || enableModifiedClick }"
    :style="{ backgroundColor: badgeColor }"
    @click.exact="enableClick ? openEditPageInNewTab() : null"
    @click.meta.stop="enableModifiedClick ? openEditPageInNewTab() : null"
    @click.ctrl.stop="enableModifiedClick ? openEditPageInNewTab() : null"
  >
    {{ refcode }}
  </span>
</template>

<script>
export default {
  props: {
    refcode: {
      type: String,
      default: null,
    },
    item_id: { type: String, required: true },
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
      return "LightGrey";
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
.badge {
  color: black;
}
</style>
