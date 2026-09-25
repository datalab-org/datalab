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
    <span
      class="tools-menu"
      @mouseenter="openToolsMenu"
      @mouseleave="scheduleToolsMenuClose"
      @click.stop
    >
      <button
        class="tools-menu-toggle"
        type="button"
        :aria-expanded="toolsMenuOpen"
        aria-haspopup="true"
        @click="handleToolsMenuClick"
      >
        <font-awesome-icon icon="laptop-code" />&nbsp;Tools
        <font-awesome-icon icon="caret-down" class="tools-menu-caret" />
      </button>
      <div v-if="toolsMenuOpen" class="tools-menu-dropdown" role="menu">
        <div v-if="toolsLoading" class="tools-menu-status">Loading tools...</div>
        <div v-else-if="toolsError" class="tools-menu-status text-danger">
          {{ toolsError }}
        </div>
        <div v-else-if="tools.length === 0" class="tools-menu-status">No tools available.</div>
        <template v-else>
          <button
            v-for="tool in tools"
            :key="tool.id"
            class="tools-menu-item"
            type="button"
            role="menuitem"
            :disabled="launchingToolId === tool.id || !isSupportedTool(tool)"
            @click="openTool(tool)"
          >
            <font-awesome-icon :icon="tool.icon || 'laptop-code'" fixed-width />
            <span>{{ tool.name }}</span>
          </button>
        </template>
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
import { getTools } from "@/server_fetch_utils.js";
import { isSupportedTool, openTool } from "@/tool_launch_utils.js";

export default {
  name: "Navbar",
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
      toolsMenuCloseTimeout: null,
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
  mounted() {
    document.addEventListener("click", this.closeToolsMenu);
  },
  beforeUnmount() {
    document.removeEventListener("click", this.closeToolsMenu);
    if (this.toolsMenuCloseTimeout) {
      window.clearTimeout(this.toolsMenuCloseTimeout);
    }
  },
  methods: {
    closeToolsMenu() {
      if (this.toolsMenuCloseTimeout) {
        window.clearTimeout(this.toolsMenuCloseTimeout);
        this.toolsMenuCloseTimeout = null;
      }
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
        this.tools = await getTools();
        this.toolsLoaded = true;
      } catch (error) {
        this.tools = [];
        this.toolsError = error instanceof Error ? error.message : String(error);
      } finally {
        this.toolsLoading = false;
      }
    },
    async openToolsMenu() {
      if (this.toolsMenuCloseTimeout) {
        window.clearTimeout(this.toolsMenuCloseTimeout);
        this.toolsMenuCloseTimeout = null;
      }
      this.toolsMenuOpen = true;
      await this.loadTools();
    },
    scheduleToolsMenuClose() {
      if (this.toolsMenuCloseTimeout) {
        window.clearTimeout(this.toolsMenuCloseTimeout);
      }
      this.toolsMenuCloseTimeout = window.setTimeout(this.closeToolsMenu, 150);
    },
    async handleToolsMenuClick() {
      if (this.toolsMenuOpen) {
        this.closeToolsMenu();
        if (this.$route.path !== "/tools") {
          this.$router.push("/tools");
        }
        return;
      }

      await this.openToolsMenu();
    },
    isSupportedTool(tool) {
      return isSupportedTool(tool);
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

.tools-menu {
  position: relative;
  display: inline-block;
}

.tools-menu-toggle {
  border: 0;
  padding: 0;
  background: transparent;
  color: #2c3e50;
}

.tools-menu-toggle:hover {
  color: #42b983;
  text-decoration: underline;
}

.tools-menu-caret {
  margin-left: 0.15rem;
  font-size: 0.8em;
}

.tools-menu-dropdown {
  position: absolute;
  top: 1.6rem;
  right: 0;
  z-index: 1000;
  min-width: 12rem;
  padding: 0.25rem 0;
  border: 1px solid #d8dee2;
  border-radius: 0.25rem;
  background: white;
  box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.12);
  text-align: left;
}

.tools-menu-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 0.35rem;
  border: 0;
  padding: 0.35rem 0.65rem;
  background: transparent;
  color: #42b983;
  text-align: left;
  white-space: nowrap;
}

.tools-menu-item:hover:not(:disabled) {
  background: #f4fbf8;
  text-decoration: underline;
}

.tools-menu-item:disabled {
  color: #6c757d;
  cursor: not-allowed;
}

.tools-menu-status {
  padding: 0.35rem 0.65rem;
  color: #6c757d;
  white-space: nowrap;
}
</style>
