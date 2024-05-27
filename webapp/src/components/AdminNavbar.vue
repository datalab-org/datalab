<template>
  <div class="sidebar">
    <table class="table table-hover table-sm" data-testid="admin-table">
      <thead>
        <tr>
          <th scope="col" class="admin-menu-header">Admin Menu</th>
        </tr>
      </thead>
    </table>
    <ul>
      <li
        v-for="item in items"
        :key="item.id"
        @click="selectItem(item)"
        :class="{ selected: item === selectedItem }"
      >
        {{ item }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  props: ["items", "selectedItem"],
  methods: {
    selectItem(item) {
      this.$emit("item-selected", item);
    },
  },
  name: "AdminNavbar",
};
</script>

<style scoped>
.sidebar {
  padding: 1em;
  margin: 0.5em;
  border-right: 1px solid lightgray;
  cursor: pointer;
}

.admin-menu-header {
  white-space: nowrap;
}

ul {
  text-align: center;
  list-style-type: none;
  margin: 0;
  padding: 0;
}
li {
  margin: 1em;
}
.selected {
  font-weight: bold;
  text-decoration: underline;
  text-underline-offset: 0.2em;
}
</style>
