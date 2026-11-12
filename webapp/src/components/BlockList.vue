<template>
  <transition-group name="block-list" tag="div">
    <div
      v-for="group in displayGroups"
      :key="group.type === 'section' ? group.section.section_id : group.block_id"
      class="block-list-item"
    >
      <component
        :is="getBlockDisplayType(group.block_id)"
        v-if="group.type === 'block'"
        :item_id="item_id"
        :block_id="group.block_id"
      />
      <BlockSection
        v-else
        :item-id="item_id"
        :section-id="group.section.section_id"
        :block-count="group.block_ids.length"
        :expanded="isSectionExpanded(group.section.section_id)"
        :loading="hasUnloadedBlocks(group)"
        @toggle="toggleSection(group.section.section_id)"
      >
        <div v-for="block_id in loadedBlockIdsOf(group)" :key="block_id" class="block-list-item">
          <component :is="getBlockDisplayType(block_id)" :item_id="item_id" :block_id="block_id" />
        </div>
      </BlockSection>
    </div>
  </transition-group>
</template>

<script>
import BlockSection from "@/components/BlockSection";
import BokehBlock from "@/components/datablocks/BokehBlock.vue";
import ErrorBlock from "@/components/datablocks/ErrorBlock.vue";
import { customBlockTypes } from "@/resources.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";
import { groupDisplayOrder, isSection } from "@/utils/displayOrderSections.js";

export default {
  components: {
    BlockSection,
  },
  props: {
    item_id: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      expandedSectionIds: [],
      loadedBlockIds: [],
      knownBlockSections: {},
      knownSectionIds: [],
      sectionsBeingLoaded: [],
      loadGeneration: 0,
    };
  },
  computed: {
    displayOrder() {
      return this.$store.state.all_item_data[this.item_id]?.display_order || [];
    },
    displayGroups() {
      return groupDisplayOrder(this.displayOrder);
    },
    blockSections() {
      return Object.fromEntries(
        this.displayGroups.flatMap((group) =>
          group.type === "block"
            ? [[group.block_id, null]]
            : group.block_ids.map((block_id) => [block_id, group.section.section_id]),
        ),
      );
    },
    allSectionIds() {
      return this.displayOrder.filter(isSection).map((section) => section.section_id);
    },
  },
  watch: {
    allSectionIds(sectionIds) {
      const addedSectionIds = sectionIds.filter((id) => !this.knownSectionIds.includes(id));
      this.knownSectionIds = sectionIds;
      this.expandSections(addedSectionIds);
    },
    blockSections(blockSections) {
      const known = this.knownBlockSections;
      const addedBlockIds = Object.keys(blockSections).filter((id) => !(id in known));
      const movedBlockIds = Object.keys(blockSections).filter(
        (id) => id in known && known[id] !== blockSections[id] && this.isBlockLoaded(id),
      );
      this.knownBlockSections = blockSections;
      this.loadedBlockIds = [...this.loadedBlockIds, ...addedBlockIds];
      this.expandSections([...addedBlockIds, ...movedBlockIds].map((id) => blockSections[id]));
      this.loadVisibleBlocks();
    },
  },
  mounted() {
    this.reloadBlocks();
  },
  methods: {
    reloadBlocks() {
      this.knownBlockSections = this.blockSections;
      this.knownSectionIds = this.allSectionIds;
      this.expandedSectionIds = [];
      this.loadedBlockIds = [];
      this.sectionsBeingLoaded = [];
      this.loadGeneration += 1;
      this.loadVisibleBlocks();
    },
    getBlockDisplayType(block_id) {
      const block = this.$store.state.all_item_data[this.item_id]?.blocks_obj?.[block_id];
      if (!block || this.$store.state.block_errors[block_id]) {
        return ErrorBlock;
      }
      const type = block.blocktype;
      if (!(type in this.$store.state.blocksInfos)) {
        return ErrorBlock;
      }
      return type in customBlockTypes ? customBlockTypes[type].component : BokehBlock;
    },
    isSectionExpanded(section_id) {
      return this.expandedSectionIds.includes(section_id);
    },
    expandSections(section_ids) {
      const toExpand = section_ids.filter((id) => id && !this.isSectionExpanded(id));
      if (toExpand.length > 0) {
        this.expandedSectionIds = [...new Set([...this.expandedSectionIds, ...toExpand])];
      }
    },
    toggleSection(section_id) {
      if (this.isSectionExpanded(section_id)) {
        this.expandedSectionIds = this.expandedSectionIds.filter((id) => id !== section_id);
        return;
      }
      this.expandSections([section_id]);
      this.loadSectionBlocks(section_id);
    },
    isBlockLoaded(block_id) {
      return this.loadedBlockIds.includes(block_id);
    },
    loadedBlockIdsOf(group) {
      return group.block_ids.filter(this.isBlockLoaded);
    },
    hasUnloadedBlocks(group) {
      return group.block_ids.some((block_id) => !this.isBlockLoaded(block_id));
    },
    loadBlock(block_id) {
      this.loadedBlockIds = [...this.loadedBlockIds, block_id];
      const block_data = this.$store.state.all_item_data[this.item_id].blocks_obj[block_id];
      return updateBlockFromServer(this.item_id, block_id, block_data).catch((error) => {
        console.error(`Error updating block ${block_id}:`, error);
      });
    },
    loadVisibleBlocks() {
      this.displayGroups.forEach((group) => {
        if (group.type === "block" && !this.isBlockLoaded(group.block_id)) {
          this.loadBlock(group.block_id);
        } else if (group.type === "section" && this.isSectionExpanded(group.section.section_id)) {
          this.loadSectionBlocks(group.section.section_id);
        }
      });
    },
    nextUnloadedBlockId(section_id) {
      const group = this.displayGroups.find(
        (entry) => entry.type === "section" && entry.section.section_id === section_id,
      );
      return group?.block_ids.find((block_id) => !this.isBlockLoaded(block_id));
    },
    async loadSectionBlocks(section_id) {
      if (this.sectionsBeingLoaded.includes(section_id)) {
        return;
      }
      this.sectionsBeingLoaded = [...this.sectionsBeingLoaded, section_id];
      const generation = this.loadGeneration;
      try {
        let block_id = this.nextUnloadedBlockId(section_id);
        while (
          block_id &&
          this.isSectionExpanded(section_id) &&
          generation === this.loadGeneration
        ) {
          await this.loadBlock(block_id);
          block_id = this.nextUnloadedBlockId(section_id);
        }
      } finally {
        if (generation === this.loadGeneration) {
          this.sectionsBeingLoaded = this.sectionsBeingLoaded.filter((id) => id !== section_id);
        }
      }
    },
  },
};
</script>

<style scoped>
.block-list-item {
  transition: all 0.6s ease;
  width: 100%;
  position: relative;
}

.block-list-enter-from,
.block-list-leave-to {
  opacity: 0;
}

.block-list-leave-active {
  position: absolute;
  max-width: calc(100% - 30px);
}
</style>
