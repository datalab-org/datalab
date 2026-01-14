<template>
  <StyledTooltip :delay="500">
    <template #anchor>
      <div class="group-chip">
        <div class="group-bubble" :style="{ width: size + 'px', height: size + 'px' }">
          <font-awesome-icon icon="users" :style="{ fontSize: size * 0.5 + 'px' }" />
        </div>
        <span class="group-name">{{ group.display_name }}</span>
      </div>
    </template>
    <template #content>
      <div>
        <strong>{{ group.display_name }}</strong>
        <div v-if="group.group_id" class="text-muted small">ID: {{ group.group_id }}</div>
        <div v-if="group.description" class="mt-1">{{ group.description }}</div>
      </div>
    </template>
  </StyledTooltip>
</template>

<script>
import StyledTooltip from "@/components/StyledTooltip";

export default {
  name: "GroupChip",
  components: {
    StyledTooltip,
  },
  props: {
    group: {
      type: Object,
      required: true,
    },
    size: {
      type: Number,
      default: 24,
    },
  },
};
</script>

<style scoped>
.group-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-right: 8px;
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
  flex-shrink: 0;
}

.group-bubble:hover {
  border: 2px solid black;
  transition: border 0.25s ease;
  box-shadow: 0 0 5px 0 skyblue;
}
</style>
