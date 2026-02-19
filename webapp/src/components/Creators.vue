<template>
  <div class="creators-container">
    <span v-for="creator in creators" :key="creator.display_name">
      <span v-if="showBubble">
        <UserBubble :creator="creator" :size="size" />
      </span>
      <span v-if="showNames && creator.display_name && groups.length === 0" class="display-name">
        {{ creator.display_name }}
        <span v-if="creator !== creators[creators.length - 1]">,</span>
      </span>
    </span>
    <span v-if="groups.length > 0">
      <span v-if="groups.length === 1">
        <FormattedGroupName
          v-if="showBubble"
          :group="groups[0]"
          :size="size"
          :show-name="creators.length === 0"
        />
      </span>
      <span v-else>
        <GroupsIconCounter v-if="showBubble" :groups="groups" :size="size" />
      </span>
    </span>
  </div>
</template>

<script>
import UserBubble from "@/components/UserBubble.vue";
import FormattedGroupName from "@/components/FormattedGroupName.vue";
import GroupsIconCounter from "@/components/GroupsIconCounter.vue";

export default {
  components: {
    UserBubble,
    FormattedGroupName,
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
  watch: {
    groups: {
      immediate: true,
      handler(val) {
        console.log("Creators component - groups prop:", val);
      },
    },
    creators: {
      immediate: true,
      handler(val) {
        console.log("Creators component - creators prop:", val);
      },
    },
  },
};
</script>

<style scoped>
.creators-container {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}
.display-name {
  margin-left: 0.25em;
}
</style>
