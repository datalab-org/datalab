<template>
  <div
    v-if="logo_url != null"
    class="pt-3"
    style="display: flex; justify-content: center; align-items: center"
  >
    <a
      v-if="homepage_url != null"
      :href="homepage_url"
      style="display: inline-block"
      target="_blank"
    >
      <img class="logo-banner" :width="logo_width + 'px'" :src="logo_url" />
    </a>
    <img v-else class="logo-banner" :width="logo_width + 'px'" :src="logo_url" />
  </div>

  <div
    class="container d-flex flex-column align-items-center pt-3"
    data-testid="navbar-logindetails"
  >
    <LoginDetails />
  </div>

  <div id="nav" data-testid="navbar-navigation">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/collections">Collections</router-link> |
    <router-link to="/starting-materials">Inventory</router-link> |
    <router-link to="/equipment">Equipment</router-link> |
    <router-link to="/item-graph"
      ><font-awesome-icon icon="project-diagram" />&nbsp;Graph View</router-link
    >
    |
    <span v-on-click-outside="closeToolsMenu" class="dropdown d-inline-block">
      <button
        class="btn btn-link dropdown-toggle border-0 p-0 align-baseline"
        type="button"
        :aria-expanded="toolsMenuOpen"
        aria-haspopup="true"
        data-testid="tools-menu-toggle"
        @click.stop="toggleToolsMenu"
      >
        <font-awesome-icon icon="laptop-code" />&nbsp;Tools
      </button>
      <div v-show="toolsMenuOpen" class="dropdown-menu show" role="menu">
        <span v-if="toolsLoading" class="dropdown-item-text text-muted">Loading tools...</span>
        <span v-else-if="toolsError" class="dropdown-item-text text-danger">
          {{ toolsError }}
        </span>
        <span v-else-if="tools.length === 0" class="dropdown-item-text text-muted">
          No tools available.
        </span>
        <template v-else>
          <button
            v-for="tool in tools"
            :key="tool.id"
            class="dropdown-item"
            type="button"
            role="menuitem"
            :disabled="launchingToolId === tool.id || !isSupportedTool(tool)"
            @click="openTool(tool)"
          >
            <font-awesome-icon :icon="toolIcon(tool)" fixed-width class="mr-1" />
            {{ tool.name }}
          </button>
        </template>
        <div class="dropdown-divider"></div>
        <router-link class="dropdown-item" to="/tools" role="menuitem" @click="closeToolsMenu">
          All tools
        </router-link>
      </div>
    </span>
  </div>
  <div v-if="!isLoggedIn" class="container">
    <div class="alert alert-info col-md-6 col-lg-4 text-center mx-auto info-banner">
      <div class="info-banner-text">
        <font-awesome-icon icon="info-circle" fixed-width /> Please login to view or create items.
      </div>
    </div>
  </div>
  <div v-if="adminSuperUserMode" class="container">
    <div class="alert alert-warning col-md-8 col-lg-8 text-center mx-auto super-user-banner">
      <div class="super-user-banner-text">
        <font-awesome-icon icon="exclamation-triangle" fixed-width /> Super-user mode is currently
        active. You have read access to all items.
        <div>
          <a href="#" class="disable-link" @click.prevent="disableSuperUserMode">(disable)</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { API_URL, LOGO_URL, LOGO_WIDTH, HOMEPAGE_URL } from "@/resources.js";
import LoginDetails from "@/components/LoginDetails.vue";
import { vOnClickOutside } from "@vueuse/components";
import { loadToolCatalog } from "@/tool_catalog.js";
import { isSupportedTool, openTool, toolIcon } from "@/tool_launch_utils.js";

export default {
  name: "Navbar",
  directives: {
    onClickOutside: vOnClickOutside,
  },
  components: {
    LoginDetails,
  },
  data() {
    return {
      apiUrl: API_URL,
      logo_url: LOGO_URL,
      logo_width: LOGO_WIDTH,
      homepage_url: HOMEPAGE_URL,
      user: null,
      tools: [],
      toolsLoaded: false,
      toolsLoading: false,
      toolsError: null,
      toolsMenuOpen: false,
      launchingToolId: null,
    };
  },
  computed: {
    isLoggedIn() {
      return Boolean(this.$store.state.currentUserDisplayName);
    },
    adminSuperUserMode() {
      return this.$store.getters.isAdminSuperUserModeActive;
    },
  },
  methods: {
    closeToolsMenu() {
      this.toolsMenuOpen = false;
    },
    disableSuperUserMode() {
      this.$store.commit("setAdminSuperUserMode", false);
      window.location.reload();
    },
    async loadTools() {
      if (this.toolsLoaded || this.toolsLoading) {
        return;
      }

      this.toolsLoading = true;
      this.toolsError = null;

      try {
        this.tools = await loadToolCatalog();
        this.toolsLoaded = true;
      } catch (error) {
        this.tools = [];
        this.toolsError = error instanceof Error ? error.message : String(error);
      } finally {
        this.toolsLoading = false;
      }
    },
    async toggleToolsMenu() {
      this.toolsMenuOpen = !this.toolsMenuOpen;
      if (this.toolsMenuOpen) {
        await this.loadTools();
      }
    },
    isSupportedTool(tool) {
      return isSupportedTool(tool);
    },
    toolIcon(tool) {
      return toolIcon(tool);
    },
    async openTool(tool) {
      this.launchingToolId = tool.id;

      try {
        await openTool(tool, this.$router);
        this.closeToolsMenu();
      } catch (error) {
        this.toolsError = `Unable to open ${tool.name}: ${
          error instanceof Error ? error.message : String(error)
        }`;
      } finally {
        this.launchingToolId = null;
      }
    },
  },
};
</script>

<style scoped>
.logo-banner {
  max-width: 200px;
  display: block;
  margin-left: auto;
  margin-right: auto;
  filter: alpha(opacity=100);
  opacity: 1;
}
a > .logo-banner:hover {
  filter: alpha(opacity=40);
  opacity: 0.4;
}

.info-banner {
  background-color: white;
  border-color: #007bff;
  color: #004085;
  background: repeating-linear-gradient(
    45deg,
    #004085,
    #004085 1px,
    transparent 1px,
    transparent 10px
  );
}

.info-banner-text {
  background-color: white;
  display: inline-block;
  padding: 0.25rem 0.5rem;
}

.super-user-banner {
  background-color: white;
  background: repeating-linear-gradient(
    45deg,
    #a52a2a,
    #a52a2a 1px,
    transparent 1px,
    transparent 10px
  );
  border-color: #a52a2a;
  color: #721c24;
}

.super-user-banner-text {
  background-color: white;
  display: inline-block;
  padding: 0.25rem 0.5rem;
}

.super-user-banner .disable-link {
  color: #721c24;
  text-decoration: underline;
}

.super-user-banner .disable-link:hover {
  color: #721c24;
}
</style>
