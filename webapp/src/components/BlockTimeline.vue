<template>
  <div class="block-timeline" data-testid="block-timeline">
    <section v-for="group in groups" :key="group.key" class="timeline-group">
      <div class="timeline-divider" data-testid="timeline-divider">
        <font-awesome-icon :icon="['fas', 'clock']" fixed-width class="mr-1" />
        <span>{{ groupLabel(group) }}</span>
      </div>
      <div v-for="block_id in group.blockIds" :key="block_id" class="block-list-item">
        <component :is="blockComponent(block_id)" :item_id="item_id" :block_id="block_id" />
      </div>
    </section>
  </div>
</template>

<script>
import { groupBlocksByDay } from "@/block_timeline.js";

export default {
  props: {
    item_id: { type: String, required: true },
    blockComponent: { type: Function, required: true },
  },
  computed: {
    item_data() {
      return this.$store.state.all_item_data[this.item_id] || {};
    },
    groups() {
      return groupBlocksByDay(this.item_data.display_order, this.item_data.blocks_obj);
    },
  },
  methods: {
    groupLabel(group) {
      if (!group.date) {
        return "Date unknown";
      }
      return group.date.toLocaleDateString(undefined, {
        weekday: "short",
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    },
  },
};
</script>

<style scoped>
.timeline-group + .timeline-group {
  margin-top: 1.5rem;
}

.timeline-divider {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--color-border);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-secondary);
}
</style>
