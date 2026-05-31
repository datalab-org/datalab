<template>
  <div ref="root" :class="rootClass">
    <button
      v-if="variant === 'button'"
      :id="triggerId"
      type="button"
      class="btn btn-primary dropdown-toggle"
      :data-testid="triggerTestid"
      aria-haspopup="true"
      :aria-expanded="isOpen"
      @click="toggle"
    >
      <font-awesome-icon icon="cubes" fixed-width /> Add a block
    </button>
    <a
      v-else
      :id="triggerId"
      class="nav-link dropdown-toggle"
      role="button"
      title="Add a block"
      :data-testid="triggerTestid"
      aria-haspopup="true"
      :aria-expanded="isOpen"
      @click="toggle"
    >
      <font-awesome-icon icon="cubes" fixed-width /> Add a block
    </a>
    <div
      class="dropdown-menu"
      :class="{ show: isOpen }"
      :data-testid="menuTestid"
      :aria-labelledby="triggerId"
    >
      <h6 v-if="suggestedBlockTypes.length > 0" class="dropdown-header">
        Suggested based on your files
      </h6>
      <span
        v-for="blockInfo in suggestedBlockTypes"
        :key="keyPrefix + '-suggested-' + blockInfo.id"
        @click="onSelect(blockInfo.id)"
      >
        <BlockTooltip :block-info="blockInfo.attributes" />
      </span>
      <div
        v-if="suggestedBlockTypes.length > 0 && allBlockTypes.length > 0"
        class="dropdown-divider"
      ></div>
      <h6 v-if="allBlockTypes.length > 0" class="dropdown-header">All block types</h6>
      <span
        v-for="blockInfo in allBlockTypes"
        :key="keyPrefix + '-all-' + blockInfo.id"
        @click="onSelect(blockInfo.id)"
      >
        <BlockTooltip :block-info="blockInfo.attributes" />
      </span>
    </div>
  </div>
</template>

<script>
import BlockTooltip from "@/components/BlockTooltip";

export default {
  name: "AddBlockDropdown",
  components: {
    BlockTooltip,
  },
  props: {
    suggestedBlockTypes: {
      type: Array,
      default: () => [],
    },
    allBlockTypes: {
      type: Array,
      default: () => [],
    },
    // "navlink" renders a navbar nav-link trigger; "button" renders a btn-primary trigger
    variant: {
      type: String,
      default: "navlink",
    },
    // "down" (default) or "up" for a dropup
    direction: {
      type: String,
      default: "down",
    },
    triggerTestid: {
      type: String,
      default: null,
    },
    // DOM id for the trigger (kept for existing selectors / aria-labelledby)
    triggerId: {
      type: String,
      default: null,
    },
    menuTestid: {
      type: String,
      default: null,
    },
    // disambiguates v-for keys when several instances are mounted at once
    keyPrefix: {
      type: String,
      default: "block",
    },
  },
  emits: ["select"],
  data() {
    return {
      isOpen: false,
    };
  },
  computed: {
    rootClass() {
      const base = this.variant === "button" ? ["d-inline-block"] : ["nav-item"];
      base.push(this.direction === "up" ? "dropup" : "dropdown");
      return base;
    },
  },
  mounted() {
    document.addEventListener("mousedown", this.handleClickOutside);
    document.addEventListener("keydown", this.handleEscape);
  },
  beforeUnmount() {
    document.removeEventListener("mousedown", this.handleClickOutside);
    document.removeEventListener("keydown", this.handleEscape);
  },
  methods: {
    toggle() {
      this.isOpen = !this.isOpen;
    },
    close() {
      this.isOpen = false;
    },
    onSelect(blockId) {
      this.$emit("select", blockId);
      this.close();
    },
    handleClickOutside(event) {
      if (this.isOpen && this.$refs.root && !this.$refs.root.contains(event.target)) {
        this.close();
      }
    },
    handleEscape(event) {
      if (event.key === "Escape") {
        this.close();
      }
    },
  },
};
</script>

<style scoped>
.dropdown-menu {
  cursor: pointer;
  max-height: 400px;
  overflow-y: auto;
}

.dropdown-header {
  font-weight: 600;
  color: #495057;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Inside the collapsed mobile navbar, render the menu inline instead of as an overlay */
@media (max-width: 767.98px) {
  .nav-item .dropdown-menu {
    position: static;
    float: none;
    width: 100%;
    border: 0;
    margin: 0;
    padding-left: 0.5rem;
    background-color: rgba(0, 0, 0, 0.15);
  }
  /* The dark inline background needs light text for the headers and block names
     (the latter are .dropdown-item rendered inside BlockTooltip, hence ::v-deep). */
  .nav-item .dropdown-header {
    color: rgba(255, 255, 255, 0.6);
  }
  .nav-item .dropdown-menu ::v-deep(.dropdown-item) {
    color: rgba(255, 255, 255, 0.85);
  }
  .nav-item .dropdown-menu ::v-deep(.dropdown-item:hover) {
    color: white;
    background-color: rgba(255, 255, 255, 0.1);
  }
}
</style>
