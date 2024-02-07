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
    refcode: String,
    item_id: String,
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
  },
  methods: {
    openEditPageInNewTab() {
      this.$emit("itemIdClicked");
      window.open(`/edit/${this.item_id}`, "_blank");
    },
  },
  emits: ["itemIdClicked"],
};
</script>

<style scoped>
.clickable {
  cursor: pointer;
}
.badge {
  color: black;
}
</style>
