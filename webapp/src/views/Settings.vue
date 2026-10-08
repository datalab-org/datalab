<template>
  <Navbar />
  <div class="settings-container">
    <SidebarNavigation
      title="Settings"
      data-testid="settings-table"
      :items="items"
      :selected-item="selectedItem"
      @item-selected="onItemSelected"
    />
    <main class="settings-display">
      <AccountSettings v-show="selectedItem === accountItem" ref="accountSettings" />
      <template v-if="selectedItem === tagsItem">
        <h1 class="h3 mb-4">Tag management</h1>
        <TagManagementTable />
      </template>
    </main>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import AccountSettings from "@/components/AccountSettings.vue";
import SidebarNavigation from "@/components/SidebarNavigation.vue";
import TagManagementTable from "@/components/TagManagementTable";
import { DialogService } from "@/services/DialogService";

const ACCOUNT_ITEM = "Account";
const TAGS_ITEM = "Tag management";

export default {
  name: "Settings",
  components: {
    Navbar,
    AccountSettings,
    SidebarNavigation,
    TagManagementTable,
  },
  async beforeRouteLeave(to, from, next) {
    if (!this.hasUnsavedAccountChanges()) {
      next();
      return;
    }

    const leave = await DialogService.confirm({
      title: "Unsaved Changes",
      message: "You have unsaved changes. Leave without saving?",
      type: "warning",
      confirmButtonText: "Leave",
      cancelButtonText: "Stay",
    });

    if (leave) next();
    else next(false);
  },
  data() {
    return {
      accountItem: ACCOUNT_ITEM,
      tagsItem: TAGS_ITEM,
    };
  },
  computed: {
    serverInfo() {
      return this.$store.state.serverInfo;
    },
    tagsEnabled() {
      return Boolean(this.serverInfo?.features?.tags);
    },
    items() {
      const items = [ACCOUNT_ITEM];
      if (this.tagsEnabled) items.push(TAGS_ITEM);
      return items;
    },
    selectedItem() {
      return this.$route.query.section === "tags" && this.tagsEnabled ? TAGS_ITEM : ACCOUNT_ITEM;
    },
  },
  watch: {
    serverInfo: {
      handler: "normalizeSection",
      immediate: true,
    },
    "$route.query.section": "normalizeSection",
  },
  mounted() {
    window.addEventListener("beforeunload", this.leavePageWarningListener);
  },
  beforeUnmount() {
    window.removeEventListener("beforeunload", this.leavePageWarningListener);
  },
  methods: {
    hasUnsavedAccountChanges() {
      return Boolean(this.$refs.accountSettings?.hasChanges);
    },
    leavePageWarningListener(event) {
      if (!this.hasUnsavedAccountChanges()) return;

      event.preventDefault();
      event.returnValue = "";
    },
    onItemSelected(item) {
      this.navigateToSection(item === TAGS_ITEM ? "tags" : undefined);
    },
    navigateToSection(section, replace = false) {
      const query = { ...this.$route.query };
      if (section) query.section = section;
      else delete query.section;

      if (this.$route.query.section === section) return;

      const destination = { name: "settings", query, hash: this.$route.hash };
      if (replace) this.$router.replace(destination);
      else this.$router.push(destination);
    },
    normalizeSection() {
      if (!this.serverInfo) return;

      const section = this.$route.query.section;
      if (section && (section !== "tags" || !this.tagsEnabled)) {
        this.navigateToSection(undefined, true);
      }
    },
  },
};
</script>

<style scoped>
.settings-container {
  display: flex;
}

.settings-display {
  width: 100%;
  min-width: 0;
  padding: 1em;
  margin: 0.5em;
}
</style>
