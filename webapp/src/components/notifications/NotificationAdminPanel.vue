<template>
  <section class="notification-admin-panel">
    <div class="notification-admin-toolbar">
      <button class="btn btn-default" type="button" @click="composerOpen = true">
        <font-awesome-icon icon="plus" class="mr-2" />
        New notification
      </button>
    </div>

    <div v-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
      <button class="btn btn-link p-0 ml-2" type="button" @click="loadNotifications">Retry</button>
    </div>

    <NotificationTable
      :notifications="notifications"
      admin-mode
      @notification-deleted="loadNotifications"
    />

    <NotificationComposer v-model="composerOpen" :allow-send-all="true" @sent="loadNotifications" />
  </section>
</template>

<script>
import NotificationComposer from "@/components/notifications/NotificationComposer.vue";
import NotificationTable from "@/components/notifications/NotificationTable.vue";
import { getAdminNotifications } from "@/server_fetch_utils.js";

export default {
  name: "NotificationAdminPanel",
  components: { NotificationComposer, NotificationTable },
  data() {
    return {
      notifications: null,
      composerOpen: false,
      errorMessage: "",
    };
  },
  created() {
    this.loadNotifications();
  },
  methods: {
    async loadNotifications() {
      this.errorMessage = "";
      try {
        const response = await getAdminNotifications();
        this.notifications = response.data;
      } catch (error) {
        this.notifications = [];
        this.errorMessage = `Unable to load notifications: ${String(error)}`;
      }
    },
  },
};
</script>

<style scoped>
.notification-admin-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}
</style>
