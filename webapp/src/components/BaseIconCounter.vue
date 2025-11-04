<template>
  <div v-if="count > 0" class="counter-wrapper" :title="hoverText">
    <font-awesome-icon v-if="showIcon" class="icon" :icon="icon" />
    <span :class="showIcon ? 'counter-badge' : 'counter'">
      {{ displayCount }}
    </span>
  </div>
</template>

<script>
export default {
  name: "BaseIconCounter",
  props: {
    count: {
      type: Number,
      default: 0,
    },
    showIcon: {
      type: Boolean,
      default: false,
    },
    icon: {
      type: Array,
      default: () => ["fa", "cubes"],
    },
    maxDisplay: {
      type: Number,
      default: 99,
    },
    hoverText: {
      type: String,
      default: "",
    },
  },
  computed: {
    displayCount() {
      return this.count > this.maxDisplay ? `${this.maxDisplay}+` : this.count;
    },
  },
};
</script>

<style scoped>
.counter-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.icon {
  color: #333;
}
.counter {
  align-items: center;
  justify-content: center;
  text-decoration: underline;
  min-width: 20px;
  height: 20px;
  font-size: 14px;
  font-weight: bold;
  font-weight: bold;
  display: flex;
}

.counter:hover {
  border: 2px solid #000000;
}

.counter-badge {
  position: relative;
  min-width: 16px;
  height: 16px;
  margin-left: 4px;
  padding: 0 5px;
  border-radius: 9px;
  background-color: #ff4757;
  color: white;
  font-size: 12px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
