<template>
  <div v-if="count > 0" class="counter-wrapper" :title="hoverText">
    <font-awesome-icon class="icon" :icon="icon" />
    <!--<span class="counter-badge">{{ displayCount }}</span>-->
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
  display: inline-block;
}

.icon {
  color: #333;
}

.counter-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 16px;
  height: 16px;
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
