<template>
  <div class="creators-container">
    <span v-for="creator in creators" :key="creator.display_name">
      <span v-if="showBubble">
        <UserBubble v-if="showBubble" :creator="creator" :size="size" />
      </span>
      <span v-if="showNames && creator.display_name" class="display-name">
        {{ creator.display_name }}
        <span v-if="creator !== creators[creators.length - 1] || groups.length > 0">,</span>
      </span>
    </span>
    <span v-if="groups.length > 0">
      <GroupsIconCounter v-if="showBubble" :groups="groups" :size="size" />
      <span v-if="showNames" class="display-name">
        {{ groupsDisplayText }}
      </span>
    </span>
  </div>
</template>

<script>
import UserBubble from "@/components/UserBubble.vue";
import GroupsIconCounter from "@/components/GroupsIconCounter.vue";

export default {
  components: {
    UserBubble,
    GroupsIconCounter,
  },
  props: {
    creators: {
      type: Array,
      default: () => [],
    },
    showNames: {
      type: Boolean,
      default: true,
      required: false,
    },
    showBubble: {
      type: Boolean,
      default: true,
      required: false,
    },
    size: {
      type: Number,
      default: 24,
      required: false,
    },
    groups: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {};
  },
  computed: {
    groupsDisplayText() {
      if (this.groups.length === 0) return "";
      if (this.groups.length === 1) return this.groups[0].display_name;
      return `${this.groups.length} groups`;
    },
  },
};
</script>

<style scoped>
.creators-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem;
}
.display-name {
  margin-left: 0.5em;
}
</style>
