<template>
  <StyledTooltip v-if="groups.length > 0" :delay="500">
    <template #anchor>
      <div class="group-bubble-wrapper">
        <div class="group-bubble" :style="{ width: size + 'px', height: size + 'px' }">
          <font-awesome-icon icon="users" :style="{ fontSize: size * 0.5 + 'px' }" />
        </div>
        <span v-if="groups.length > 1" class="counter-badge">{{ displayCount }}</span>
      </div>
    </template>
    <template #content>
      <div v-if="groups.length === 1">
        {{ groups[0].display_name }}
      </div>
      <div v-else>
        <div v-for="group in groups" :key="group.immutable_id" class="group-item">
          {{ group.display_name }}
        </div>
      </div>
    </template>
  </StyledTooltip>
</template>

<script>
import StyledTooltip from "@/components/StyledTooltip";

export default {
  name: "GroupsIconCounter",
  components: {
    StyledTooltip,
  },
  props: {
    groups: {
      type: Array,
      default: () => [],
    },
    size: {
      type: Number,
      default: 24,
    },
    maxDisplay: {
      type: Number,
      default: 99,
    },
  },
  computed: {
    displayCount() {
      return this.groups.length > this.maxDisplay ? `${this.maxDisplay}+` : this.groups.length;
    },
  },
};
</script>

<style scoped>
.group-bubble-wrapper {
  position: relative;
  display: inline-block;
  vertical-align: middle;
}

.group-bubble {
  position: relative;
  border-radius: 50%;
  border: 2px solid grey;
  background-color: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #6c757d;
}

.group-bubble:hover {
  border: 2px solid black;
  transition: border 0.25s ease;
  box-shadow: 0 0 5px 0 skyblue;
}

.counter-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 14px;
  height: 14px;
  border-radius: 7px;
  background-color: #6c757d;
  color: white;
  font-size: 9px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid white;
  line-height: 1;
  padding: 0;
}

.group-item {
  padding: 2px 0;
}
</style>
