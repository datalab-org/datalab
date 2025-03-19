<template>
  <table class="table table-hover table-sm" data-testid="user-table">
    <thead>
      <tr>
        <th scope="col">Group ID</th>
        <th scope="col">Name</th>
        <th scope="col">Description</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="group in groups" :key="group.group_id">
        <td align="left">
          <span class="badge badge-light table-group-id">{{ group.group_id }}</span>
        </td>
        <td align="left">{{ group.display_name }}</td>
        <td align="left">{{ group.description }}</td>
        <td align="right"><font-awesome-icon :icon="['far', 'plus-square']" /></td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import { getGroupsList } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      groups: null,
      original_groups: null,
    };
  },
  created() {
    this.getGroups();
  },
  methods: {
    async getGroups() {
      let data = await getGroupsList();
      if (data != null) {
        this.groups = JSON.parse(JSON.stringify(data));
        this.original_groups = JSON.parse(JSON.stringify(data));
      }
    },
  },
};
</script>

<style scoped>
td {
  vertical-align: middle;
}

.table-group-id {
  border: 2px solid #ccc;
}

select {
  border: 1px solid #ccc;
  border-radius: 0.25rem;
}

.badge {
  margin-left: 1em;
  font-family: "Andalé Mono", monospace;
}
</style>
