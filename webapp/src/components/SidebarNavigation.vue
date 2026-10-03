<template>
  <nav class="sidebar" :aria-label="title" :data-testid="testId">
    <h2 class="sidebar-menu-header">{{ title }}</h2>
    <ul>
      <li v-for="item in items" :key="item">
        <button
          type="button"
          class="sidebar-item"
          :class="{ selected: item === selectedItem }"
          :aria-current="item === selectedItem ? 'page' : undefined"
          @click="selectItem(item)"
        >
          {{ item }}
        </button>
      </li>
    </ul>
  </nav>
</template>

<script>
export default {
  name: "SidebarNavigation",
  props: {
    title: {
      type: String,
      required: true,
    },
    items: {
      type: Array,
      required: true,
    },
    selectedItem: {
      type: String,
      required: true,
    },
    testId: {
      type: String,
      default: undefined,
    },
  },
  emits: ["item-selected"],
  methods: {
    selectItem(item) {
      this.$emit("item-selected", item);
    },
  },
};
</script>

<style scoped>
.sidebar {
  padding: 1em;
  margin: 0.5em;
  border-right: 1px solid lightgray;
}

.sidebar-menu-header {
  padding: 0.3rem;
  margin: 0 0 0.5rem;
  border-bottom: 2px solid #dee2e6;
  font-size: 1rem;
  font-weight: 700;
  white-space: nowrap;
}

ul {
  text-align: center;
  list-style-type: none;
  margin: 0;
  padding: 0;
}
li {
  margin: 0.25rem 0;
}
.sidebar-item {
  width: 100%;
  padding: 0.5rem 1rem;
  border: 0;
  color: inherit;
  background: transparent;
  cursor: pointer;
}
.sidebar-item:hover,
.sidebar-item:focus-visible {
  background-color: rgba(0, 0, 0, 0.075);
}
.selected {
  font-weight: bold;
  text-decoration: underline;
  text-underline-offset: 0.2em;
}
</style>
