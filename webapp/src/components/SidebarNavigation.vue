<template>
  <nav class="sidebar" :aria-label="title">
    <div class="sidebar-menu-header">{{ title }}</div>
    <ul>
      <li v-for="item in items" :key="item">
        <button
          type="button"
          class="sidebar-item"
          :class="{ selected: item === selectedItem }"
          :aria-current="item === selectedItem ? 'page' : undefined"
          @click="$emit('item-selected', item)"
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
  },
  emits: ["item-selected"],
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

@media (max-width: 767.98px) {
  .sidebar {
    margin-bottom: 0;
    border-right: 0;
    border-bottom: 1px solid lightgray;
  }

  ul {
    display: flex;
  }

  li {
    flex: 1 1 0;
    margin: 0.25rem;
  }
}
</style>
