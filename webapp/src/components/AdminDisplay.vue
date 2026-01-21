<template>
  <div class="admin-display">
    <template v-if="selectedItem === 'Users'">
      <UserTable />
    </template>
    <template v-if="selectedItem === 'Access Tokens'">
      <TokenTable />
    </template>
    <template v-if="selectedItem === 'Groups'">
      <div class="mb-3">
        <button class="btn btn-default" @click="showCreateGroupModal = true">
          <font-awesome-icon :icon="['fas', 'plus']" class="mr-2" />
          Create Group
        </button>
      </div>
      <GroupTable ref="groupTable" @group-updated="refreshGroups" />
      <CreateGroupModal
        :model-value="showCreateGroupModal"
        @update:model-value="showCreateGroupModal = $event"
        @group-created="onGroupCreated"
      />
    </template>
  </div>
</template>

<script>
import UserTable from "./UserTable.vue";
import TokenTable from "./TokenTable.vue";
import GroupTable from "./GroupTable.vue";
import CreateGroupModal from "./CreateGroupModal.vue";

export default {
  name: "AdminDisplay",
  components: {
    UserTable,
    TokenTable,
    GroupTable,
    CreateGroupModal,
  },
  props: {
    selectedItem: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      showCreateGroupModal: false,
    };
  },
  methods: {
    onGroupCreated() {
      this.showCreateGroupModal = false;
      this.$refs.groupTable.getGroups();
    },
    refreshGroups() {
      this.$refs.groupTable?.getGroups();
    },
  },
};
</script>

<style scoped>
.admin-display {
  max-width: 100%;
  min-width: 80%;
  padding: 1em;
  margin: 0.5em;
}
</style>
