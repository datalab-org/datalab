<template>
  <span>{{ members.length }}</span>
</template>

<script>
export default {
  name: "GroupMembersCell",
  props: {
    members: {
      type: Array,
      required: true,
      default: () => [],
    },
  },
};
</script>
