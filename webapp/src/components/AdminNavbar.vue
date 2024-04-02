<template>
  <div class="sidebar">
    <ul>
      <li v-for="item in items" :key="item.id" @click="selectItem(item)">
        {{ item }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  props: ["items"],
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
  background-color: lightgreen;
  border: 1px solid green;
  border-radius: 0.5em;
  cursor: pointer;
}
ul {
  list-style-type: none;
  margin: 0;
  padding: 0;
}
li {
  margin: 1em;
}
</style>
