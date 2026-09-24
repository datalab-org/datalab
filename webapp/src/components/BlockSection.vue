<template>
  <div :id="sectionId" class="block-section">
    <div class="section-header collapsible" :class="{ expanded: isExpanded }">
      <font-awesome-icon
        :icon="['fas', 'chevron-right']"
        fixed-width
        class="collapse-arrow"
        @click="toggleExpanded"
      />
      <font-awesome-icon :icon="['fas', 'folder-open']" fixed-width />
      <input v-model="title" class="form-control-plaintext section-title" type="text" />
      <span class="section-block-count ml-auto mr-3">
        {{ blockCount }} block{{ blockCount === 1 ? "" : "s" }}
      </span>
      <font-awesome-icon
        :icon="['fas', 'times']"
        class="block-header-icon delete-section-button"
        title="Ungroup section"
        @click="confirmDeleteSection"
      />
    </div>
    <div v-show="isExpanded" class="section-body">
      <TiptapInline
        v-model="description"
        placeholder="Add a description..."
        class="section-description"
      />
      <div class="section-content">
        <slot />
      </div>
    </div>
  </div>
</template>

<script>
import { DialogService } from "@/services/DialogService";
import TiptapInline from "@/components/TiptapInline";
import { isSection } from "@/utils/displayOrderSections.js";

export default {
  components: {
    TiptapInline,
  },
  props: {
    itemId: {
      type: String,
      required: true,
    },
    sectionId: {
      type: String,
      required: true,
    },
    blockCount: {
      type: Number,
      default: 0,
    },
  },
  data() {
    return {
      isExpanded: false,
    };
  },
  computed: {
    section() {
      return (this.$store.state.all_item_data[this.itemId]?.display_order || []).find(
        (entry) => isSection(entry) && entry.section_id === this.sectionId,
      );
    },
    title: {
      get() {
        return this.section?.title || "";
      },
      set(value) {
        this.$store.commit("updateSection", {
          item_id: this.itemId,
          section_id: this.sectionId,
          section_data: { title: value },
        });
      },
    },
    description: {
      get() {
        return this.section?.description || "";
      },
      set(value) {
        this.$store.commit("updateSection", {
          item_id: this.itemId,
          section_id: this.sectionId,
          section_data: { description: value === "" ? null : value },
        });
      },
    },
  },
  methods: {
    toggleExpanded() {
      this.isExpanded = !this.isExpanded;
    },
    async confirmDeleteSection() {
      const confirmed = await DialogService.confirm({
        title: "Ungroup Section",
        message: "Remove this section? The blocks inside it will not be deleted, just ungrouped.",
        type: "warning",
      });
      if (confirmed) {
        this.$store.commit("removeSection", { item_id: this.itemId, section_id: this.sectionId });
      }
    },
  },
};
</script>

<style scoped>
.block-section {
  padding-bottom: 18px;
  border: 1px solid #d8dee6;
  border-radius: 3px;
  background-color: #fafbfc;
}

.section-header {
  display: flex;
  align-items: center;
  font-size: large;
  height: 35px;
  background-color: #e9edf2;
  color: #444;
  border: 1px solid #ccc;
  border-radius: 3px;
}

.section-title {
  margin-left: 1em;
  font-size: large;
  font-weight: 500;
}

.section-block-count {
  font-style: italic;
  color: grey;
  font-size: medium;
  white-space: nowrap;
}

.collapse-arrow {
  font-size: large;
  margin-left: 10px;
  margin-right: 10px;
  color: #004175;
  transition: all 0.4s;
  cursor: pointer;
}

.collapse-arrow:hover {
  color: #7ca7ca;
}

.expanded .collapse-arrow {
  transform: rotate(90deg);
}

.block-header-icon {
  font-size: large;
  color: #004175;
  margin-right: 10px;
  cursor: pointer;
}

.block-header-icon:hover {
  color: #7ca7ca;
}

.section-body {
  padding: 18px 18px 0px 18px;
}

.section-description {
  margin-bottom: 1em;
}
</style>
