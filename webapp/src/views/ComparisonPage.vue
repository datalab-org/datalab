<template>
  <Navbar />

  <div class="container-fluid comparison-page px-4 px-xl-5 py-3">
    <!-- Page header -->
    <div class="page-header d-flex align-items-center justify-content-between flex-wrap mb-4">
      <div class="d-flex align-items-center">
        <h3 class="mb-0 mr-2">
          <font-awesome-icon icon="layer-group" class="text-muted mr-2" />Sample comparison
        </h3>
        <span v-if="items.length" class="badge badge-pill badge-secondary">{{ items.length }}</span>
      </div>
      <div class="add-sample-control">
        <ItemSelect
          v-model="itemToAdd"
          placeholder="Add a sample to compare..."
          @update:model-value="onAddItem"
        />
      </div>
    </div>

    <div v-if="loading" class="text-center text-muted py-5">
      <font-awesome-icon :icon="['fa', 'sync']" :spin="true" size="2x" />
      <p class="mt-2 mb-0">Loading samples...</p>
    </div>

    <!-- Empty state -->
    <div v-else-if="items.length < 1" class="empty-state text-center py-5">
      <font-awesome-icon icon="layer-group" size="3x" class="text-muted mb-3" />
      <h5>Nothing to compare yet</h5>
      <p class="text-muted mb-0">
        Use the search box above to add samples, or pick samples from the
        <router-link to="/samples">samples list</router-link> and choose <em>Compare selected</em>.
      </p>
    </div>

    <template v-else>
      <!-- Metadata comparison (samples as rows, fields as columns) -->
      <section class="comparison-card mb-4">
        <header class="comparison-card-header d-flex align-items-center flex-wrap">
          <button
            class="collapse-toggle"
            title="Collapse"
            @click="metadataCollapsed = !metadataCollapsed"
          >
            <font-awesome-icon
              icon="caret-down"
              class="collapse-caret"
              :class="{ collapsed: metadataCollapsed }"
            />
          </button>
          <span class="mr-auto">Metadata</span>
          <div class="d-flex align-items-center small font-weight-normal">
            <div v-if="totalPages > 1" class="d-flex align-items-center mr-3 pager">
              <button
                class="pager-btn"
                title="Previous samples"
                :disabled="metadataPage === 0"
                @click="metadataPage--"
              >
                <font-awesome-icon icon="chevron-left" />
              </button>
              <span class="text-muted mx-2"
                >{{ pageStart }}–{{ pageEnd }} of {{ items.length }}</span
              >
              <button
                class="pager-btn"
                title="Next samples"
                :disabled="metadataPage >= totalPages - 1"
                @click="metadataPage++"
              >
                <font-awesome-icon icon="chevron-right" />
              </button>
            </div>
            <div class="btn-group btn-group-sm" role="group">
              <button
                type="button"
                class="btn"
                :class="showDiffOnly ? 'btn-primary' : 'btn-outline-secondary'"
                @click="showDiffOnly = true"
              >
                Differences
                <span v-if="hiddenIdenticalCount" class="diff-count">{{
                  displayedMetadataRows.length
                }}</span>
              </button>
              <button
                type="button"
                class="btn"
                :class="!showDiffOnly ? 'btn-primary' : 'btn-outline-secondary'"
                @click="showDiffOnly = false"
              >
                All fields
              </button>
            </div>
          </div>
        </header>
        <div v-show="!metadataCollapsed" class="table-responsive">
          <table class="table comparison-table mb-0">
            <thead>
              <tr>
                <th class="field-col">Field</th>
                <th
                  v-for="entry in pagedItems"
                  :key="entry.item.item_id"
                  class="sample-col"
                  :style="{ borderTopColor: sampleColor(entry.index) }"
                >
                  <div class="d-flex align-items-center justify-content-between">
                    <span class="d-flex align-items-center">
                      <span
                        class="sample-dot"
                        :style="{ backgroundColor: sampleColor(entry.index) }"
                      />
                      <FormattedItemName
                        :item_id="entry.item.item_id"
                        :item-type="entry.item.type || 'samples'"
                        :name="entry.item.name"
                        enable-click
                        enable-modified-click
                      />
                    </span>
                    <button
                      class="btn btn-sm btn-link text-muted p-0 ml-2 remove-btn"
                      title="Remove from comparison"
                      @click="removeItem(entry.item.item_id)"
                    >
                      <font-awesome-icon icon="times" />
                    </button>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="field in displayedMetadataRows"
                :key="field.label"
                :class="{ 'row-differs': !showDiffOnly && fieldDiffers(field) }"
              >
                <th class="field-col">{{ field.label }}</th>
                <td v-for="entry in pagedItems" :key="entry.item.item_id">
                  <ChemicalFormula
                    v-if="field.key === 'chemform' && entry.item.chemform"
                    :formula="entry.item.chemform"
                  />
                  <span v-else :class="{ 'text-muted': field.render(entry.item) === '—' }">{{
                    field.render(entry.item)
                  }}</span>
                </td>
              </tr>
              <tr v-if="!displayedMetadataRows.length">
                <td :colspan="pagedItems.length + 1" class="text-muted text-center py-3">
                  <font-awesome-icon icon="check-circle" class="text-success mr-1" />
                  These samples share the same metadata. Switch to
                  <a href="#" @click.prevent="showDiffOnly = false">All fields</a> to see
                  everything.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Block comparison -->
      <section class="comparison-card sticky-card mb-4">
        <header class="comparison-card-header sticky-header">
          <div class="d-flex align-items-center flex-wrap">
            <button
              class="collapse-toggle"
              title="Collapse"
              @click="blocksCollapsed = !blocksCollapsed"
            >
              <font-awesome-icon
                icon="caret-down"
                class="collapse-caret"
                :class="{ collapsed: blocksCollapsed }"
              />
            </button>
            <span class="mr-auto">Block comparison</span>

            <div
              v-if="selectedBlockType && !blocksCollapsed"
              class="d-flex align-items-center flex-wrap font-weight-normal"
            >
              <div class="btn-group btn-group-sm mr-3" role="group">
                <button
                  type="button"
                  class="btn"
                  :class="mode === 'side-by-side' ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="mode = 'side-by-side'"
                >
                  Side-by-side
                </button>
                <button
                  type="button"
                  class="btn"
                  :class="mode === 'overlay' ? 'btn-primary' : 'btn-outline-secondary'"
                  :disabled="!overlaySupported"
                  :title="overlaySupported ? '' : 'Overlay not yet supported for this block type'"
                  @click="setOverlayMode"
                >
                  Overlay
                </button>
              </div>
            </div>
          </div>

          <!-- Block-type pills with counts -->
          <div
            v-if="blockTypeStats.length && !blocksCollapsed"
            class="type-pills mt-2"
            data-testid="comparison-blocktype-pills"
          >
            <button
              v-for="t in blockTypeStats"
              :key="t.type"
              type="button"
              class="type-pill"
              :class="{ active: t.type === selectedBlockType, partial: t.partial }"
              :title="
                t.partial
                  ? `${t.name}: ${t.blockCount} block(s) in ${t.sampleCount}/${items.length} samples`
                  : `${t.name}: ${t.blockCount} block(s)`
              "
              @click="selectedBlockType = t.type"
            >
              {{ t.name }} <span class="pill-count">{{ t.blockCount }}</span>
            </button>
          </div>
        </header>

        <div v-show="!blocksCollapsed" class="comparison-card-body">
          <div v-if="!blockTypeStats.length" class="text-muted text-center py-4">
            None of the selected samples contain any data blocks.
          </div>

          <div v-else-if="!matchingBlocks.length" class="text-muted text-center py-4">
            No “{{ blockTypeName(selectedBlockType) }}” blocks found in the selected samples.
          </div>

          <template v-else>
            <!-- Participating blocks: explicit, toggleable set shared by both views -->
            <div v-if="matchingBlocks.length > 1" class="block-toggle-bar">
              <span class="small text-muted mr-2">Blocks:</span>
              <button
                v-for="entry in matchingBlocks"
                :key="entry.key"
                type="button"
                class="block-chip"
                :class="{ inactive: !isBlockEnabled(entry.key) }"
                :style="isBlockEnabled(entry.key) ? { borderColor: entry.color } : {}"
                :title="chipTooltip(entry)"
                @click="toggleBlock(entry.key)"
              >
                <span class="sample-dot" :style="{ backgroundColor: entry.color }" />
                {{ entry.chipLabel }}
                <span v-if="entry.distinguisher" class="chip-detail">{{
                  entry.distinguisher
                }}</span>
              </button>
            </div>

            <!-- Side-by-side -->
            <div v-if="mode === 'side-by-side'">
              <div v-if="!activeBlocks.length" class="text-muted text-center py-4">
                No blocks selected. Enable at least one block above.
              </div>
              <div v-else class="block-grid" :style="gridStyle">
                <div
                  v-for="entry in activeBlocks"
                  :key="entry.key"
                  class="block-cell"
                  :style="{ borderTopColor: entry.color }"
                >
                  <div class="block-cell-title">
                    <span class="sample-dot" :style="{ backgroundColor: entry.color }" />
                    <FormattedItemName
                      :item_id="entry.item_id"
                      :item-type="entry.item_type"
                      :name="entry.item_name"
                      enable-click
                      enable-modified-click
                    />
                    <span
                      v-if="entry.distinguisher"
                      class="text-muted small ml-2 file-label"
                      :title="entry.fileTooltip"
                      >· {{ entry.distinguisher }}</span
                    >
                  </div>
                  <div v-if="entry.error" class="alert alert-danger small mb-0">
                    {{ entry.error }}
                  </div>
                  <BokehPlot
                    v-else-if="entry.bokehPlotData"
                    :bokeh-plot-data="entry.bokehPlotData"
                  />
                  <img
                    v-else-if="entry.imageData"
                    :src="entry.imageData"
                    :alt="entry.fileLabel || 'media'"
                    class="comparison-media"
                  />
                  <div v-else-if="entry.comment" class="comparison-comment">
                    {{ entry.comment }}
                  </div>
                  <div
                    v-else-if="isUpdating(entry) || !isProcessed(entry)"
                    class="text-muted small py-3 text-center"
                  >
                    <font-awesome-icon :icon="['fa', 'sync']" :spin="true" /> Generating preview...
                  </div>
                  <div v-else class="text-muted small py-3 text-center">
                    No preview available for this block type.
                  </div>
                </div>
              </div>
            </div>

            <!-- Overlay -->
            <div v-else-if="mode === 'overlay'">
              <div v-if="!overlaySupported" class="alert alert-info mb-0">
                Overlay comparison is not yet supported for
                {{ blockTypeName(selectedBlockType) }} blocks. Use side-by-side instead.
              </div>
              <div v-else-if="overlayError" class="alert alert-danger mb-0">{{ overlayError }}</div>
              <div v-else-if="overlayLoading" class="text-muted text-center py-4">
                <font-awesome-icon :icon="['fa', 'sync']" :spin="true" /> Building overlay...
              </div>
              <div v-else-if="overlayPlotData" class="overlay-plot-wrapper">
                <BokehPlot :bokeh-plot-data="overlayPlotData" />
              </div>
            </div>
          </template>
        </div>
      </section>
    </template>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import FormattedItemName from "@/components/FormattedItemName";
import ChemicalFormula from "@/components/ChemicalFormula";
import BokehPlot from "@/components/BokehPlot";
import ItemSelect from "@/components/ItemSelect";
import { getItemData, updateBlockFromServer, compareBlocks } from "@/server_fetch_utils.js";
import { API_URL } from "@/resources.js";

// How many sample rows to show per page in the metadata table before paging.
const PAGE_SIZE = 5;

// Mirrors the backend Dark2[8] palette (pydatalab.bokeh_plots.COLORS) so that a
// sample's accent colour here matches its trace colour in the overlay plot.
const SAMPLE_COLORS = [
  "#1b9e77",
  "#d95f02",
  "#7570b3",
  "#e7298a",
  "#66a61e",
  "#e6ab02",
  "#a6761d",
  "#666666",
];

export default {
  name: "ComparisonPage",
  components: {
    Navbar,
    FormattedItemName,
    ChemicalFormula,
    BokehPlot,
    ItemSelect,
  },
  data() {
    return {
      loading: true,
      mode: "side-by-side",
      selectedBlockType: null,
      overlayPlotData: null,
      overlayLoading: false,
      overlayError: null,
      itemToAdd: null,
      requestedBlocks: new Set(),
      processedBlocks: new Set(),
      // Per-block-key enable flags for the participating-blocks toggle bar.
      // A key absent from this map is treated as enabled (default-on).
      blockEnabled: {},
      // UI controls
      showDiffOnly: true,
      metadataCollapsed: false,
      blocksCollapsed: false,
      metadataPage: 0,
    };
  },
  computed: {
    itemIds() {
      const ids = this.$route.query.ids;
      if (!ids) return [];
      return ids
        .split(",")
        .map((id) => id.trim())
        .filter(Boolean);
    },
    items() {
      return this.itemIds.map((id) => this.$store.state.all_item_data[id]).filter(Boolean);
    },
    coreMetadataRows() {
      return [
        { label: "Name", key: "name", render: (i) => i.name || "—" },
        { label: "ID", key: "item_id", render: (i) => i.item_id },
        { label: "Date", key: "date", render: (i) => this.formatDate(i.date) },
        { label: "Chemical formula", key: "chemform", render: (i) => i.chemform || "—" },
        { label: "Description", key: "description", render: (i) => i.description || "—" },
        {
          label: "Blocks",
          key: "blocks",
          render: (i) => Object.keys(i.blocks_obj || {}).length,
        },
      ];
    },
    extraMetadataRows() {
      return [
        { label: "Refcode", key: "refcode", render: (i) => i.refcode || "—" },
        { label: "Type", key: "type", render: (i) => i.type || "—" },
        { label: "Status", key: "status", render: (i) => i.status || "—" },
        {
          label: "Creators",
          key: "creators",
          render: (i) => (i.creators || []).map((c) => c.display_name).join(", ") || "—",
        },
        {
          label: "Collections",
          key: "collections",
          render: (i) => (i.collections || []).map((c) => c.collection_id).join(", ") || "—",
        },
      ];
    },
    visibleMetadataRows() {
      return [...this.coreMetadataRows, ...this.extraMetadataRows];
    },
    displayedMetadataRows() {
      if (!this.showDiffOnly) return this.visibleMetadataRows;
      return this.visibleMetadataRows.filter((field) => this.fieldDiffers(field));
    },
    hiddenIdenticalCount() {
      if (!this.showDiffOnly) return 0;
      return this.visibleMetadataRows.length - this.displayedMetadataRows.length;
    },
    // Samples shown on the current metadata page, keeping each one's global index
    // (so its accent colour matches its overlay trace).
    pagedItems() {
      const start = this.metadataPage * PAGE_SIZE;
      return this.items
        .slice(start, start + PAGE_SIZE)
        .map((item, i) => ({ item, index: start + i }));
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.items.length / PAGE_SIZE));
    },
    pageStart() {
      return this.items.length ? this.metadataPage * PAGE_SIZE + 1 : 0;
    },
    pageEnd() {
      return Math.min((this.metadataPage + 1) * PAGE_SIZE, this.items.length);
    },
    allBlockTypes() {
      return this.blockTypeStats.map((t) => t.type);
    },
    // Per-type stats for the pills: how many blocks, and in how many samples.
    blockTypeStats() {
      const stats = {};
      for (const item of this.items) {
        const typesInItem = new Set();
        for (const block of Object.values(item.blocks_obj || {})) {
          if (!block.blocktype) continue;
          stats[block.blocktype] = stats[block.blocktype] || {
            type: block.blocktype,
            blockCount: 0,
            sampleCount: 0,
          };
          stats[block.blocktype].blockCount += 1;
          typesInItem.add(block.blocktype);
        }
        typesInItem.forEach((t) => (stats[t].sampleCount += 1));
      }
      return Object.values(stats)
        .map((s) => ({
          ...s,
          name: this.blockTypeName(s.type),
          partial: s.sampleCount < this.items.length,
        }))
        .sort((a, b) => a.name.localeCompare(b.name));
    },
    overlaySupported() {
      return Boolean(
        this.$store.state.blocksInfos[this.selectedBlockType]?.attributes?.supports_overlay,
      );
    },
    // Fixed two-column layout: one block spans full width, two or more lay out
    // in two equal columns. A stable column count keeps each Bokeh plot's
    // container width from shifting as blocks render in asynchronously.
    gridStyle() {
      const cols = Math.min(this.activeBlocks.length || 1, 2);
      return { gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` };
    },
    // Every block of the selected type across all samples (the candidate set).
    matchingBlocks() {
      if (!this.selectedBlockType) return [];
      const entries = [];
      this.items.forEach((item, index) => {
        const sameTypeOnItem = Object.values(item.blocks_obj || {}).filter(
          (b) => b.blocktype === this.selectedBlockType,
        ).length;
        const nameOf = (fid) =>
          (item.files || []).find((f) => f.immutable_id === fid)?.name || null;
        let ordinal = 0;
        for (const [block_id, block] of Object.entries(item.blocks_obj || {})) {
          if (block.blocktype !== this.selectedBlockType) continue;
          ordinal += 1;
          const baseLabel = item.name || item.item_id;
          const fileIds = block.file_id
            ? [block.file_id]
            : Array.isArray(block.file_ids)
              ? block.file_ids
              : [];
          const fileNames = fileIds.map(nameOf).filter(Boolean);
          const fileLabel =
            fileNames.length === 1
              ? fileNames[0]
              : fileNames.length > 1
                ? `${fileNames.length} files`
                : null;
          // When a sample has several blocks of this type, distinguish them by
          // file name (preferred) or a positional #N fallback. null otherwise.
          const distinguisher = sameTypeOnItem > 1 ? fileLabel || `#${ordinal}` : null;
          // Non-Bokeh content: mirrors MediaBlock.vue logic.
          // TIF/TIFF are base64-encoded server-side; other web images use a direct URL.
          const b64 = block.b64_encoded_image;
          let imageData = null;
          if (b64 && block.file_id && b64[block.file_id]) {
            imageData = `data:image/png;base64,${b64[block.file_id]}`;
          } else if (block.file_id) {
            const fileName = nameOf(block.file_id);
            if (fileName) {
              const ext = fileName.split(".").pop().toLowerCase();
              if (["png", "jpeg", "jpg"].includes(ext)) {
                imageData = `${API_URL}/files/${block.file_id}/${fileName}`;
              }
            }
          }
          entries.push({
            key: `${item.item_id}:${block_id}`,
            item_id: item.item_id,
            item_type: item.type || "samples",
            item_name: item.name,
            block_id,
            title: block.title,
            chipLabel: baseLabel,
            distinguisher,
            fileLabel,
            fileTooltip: fileNames.length ? fileNames.join(", ") : null,
            color: this.sampleColor(index),
            bokehPlotData: block.bokeh_plot_data || null,
            imageData,
            comment: block.freeform_comment || null,
            error: (block.errors && block.errors.join("; ")) || null,
          });
        }
      });
      return entries;
    },
    // The subset of matching blocks the user has toggled on; both views render this.
    activeBlocks() {
      return this.matchingBlocks.filter((entry) => this.isBlockEnabled(entry.key));
    },
    // Membership-only signal (ignores plot-data changes) for watchers.
    activeBlockKeys() {
      return this.activeBlocks.map((entry) => entry.key).join(",");
    },
  },
  watch: {
    itemIds: {
      immediate: true,
      handler() {
        this.loadItems();
      },
    },
    allBlockTypes(newTypes) {
      if (!this.selectedBlockType || !newTypes.includes(this.selectedBlockType)) {
        this.selectedBlockType = newTypes[0] || null;
      }
    },
    selectedBlockType() {
      // Rendering is driven by the activeBlockKeys watcher; here we only reset
      // overlay state and fall back to side-by-side if the new type can't overlay.
      this.overlayPlotData = null;
      this.overlayError = null;
      if (!this.overlaySupported && this.mode === "overlay") {
        this.mode = "side-by-side";
      }
    },
    mode(newMode) {
      if (newMode === "side-by-side") this.ensureSideBySidePlots();
      else if (newMode === "overlay") this.runOverlay();
    },
    // Re-render the active view when the toggled set of blocks changes.
    activeBlockKeys() {
      if (this.mode === "side-by-side") this.ensureSideBySidePlots();
      else if (this.mode === "overlay") this.runOverlay();
    },
  },
  methods: {
    async loadItems() {
      this.loading = true;
      this.metadataPage = 0;
      await Promise.all(
        this.itemIds.map((id) =>
          this.$store.state.all_item_data[id] ? Promise.resolve() : getItemData(id).catch(() => {}),
        ),
      );
      this.loading = false;
      this.ensureSideBySidePlots();
    },
    // Trigger block processing so that each active block's bokeh_plot_data is
    // populated in the store (it is not returned by get-item-data).
    ensureSideBySidePlots() {
      if (this.mode !== "side-by-side") return;
      for (const entry of this.activeBlocks) {
        // Skip blocks that already have something to show (plot/image/comment) or
        // that we've already requested.
        if (
          entry.bokehPlotData ||
          entry.imageData ||
          entry.comment ||
          this.requestedBlocks.has(entry.key)
        ) {
          continue;
        }
        const block = this.$store.state.all_item_data[entry.item_id]?.blocks_obj?.[entry.block_id];
        if (!block) continue;
        this.requestedBlocks.add(entry.key);
        updateBlockFromServer(entry.item_id, entry.block_id, { ...block })
          .catch(() => {
            this.requestedBlocks.delete(entry.key);
          })
          .finally(() => {
            this.processedBlocks.add(entry.key);
            this.nudgeBokehResize();
          });
      }
      // Plots that were already cached render synchronously; nudge them too.
      this.nudgeBokehResize();
    },
    // Bokeh plots use sizing_mode="scale_width" and measure their container at
    // embed time. When cells settle to their final width after async renders,
    // a window resize event makes every embedded plot recompute its size so
    // side-by-side plots end up identically sized. Debounced to one call.
    nudgeBokehResize() {
      if (this._resizeNudge) clearTimeout(this._resizeNudge);
      this._resizeNudge = setTimeout(() => {
        window.dispatchEvent(new Event("resize"));
      }, 100);
    },
    isUpdating(entry) {
      return Boolean(this.$store.state.updating[entry.block_id]);
    },
    isProcessed(entry) {
      return this.processedBlocks.has(entry.key);
    },
    setOverlayMode() {
      if (!this.overlaySupported) return;
      // The mode watcher triggers runOverlay.
      this.mode = "overlay";
    },
    async runOverlay() {
      if (this.mode !== "overlay" || !this.overlaySupported) return;
      const refs = this.activeBlocks.map((entry) => ({
        item_id: entry.item_id,
        block_id: entry.block_id,
        // Legend label: sample name, plus a shortened distinguisher when the
        // sample contributes more than one block to the overlay.
        label: entry.distinguisher
          ? `${entry.chipLabel} · ${this.shortenName(entry.distinguisher)}`
          : entry.chipLabel,
      }));
      if (refs.length < 2) {
        this.overlayError = "Enable at least two blocks above to overlay.";
        this.overlayPlotData = null;
        return;
      }
      this.overlayLoading = true;
      this.overlayError = null;
      try {
        this.overlayPlotData = await compareBlocks(refs);
      } catch (error) {
        this.overlayError = error?.message || String(error);
        this.overlayPlotData = null;
      } finally {
        this.overlayLoading = false;
      }
    },
    removeItem(item_id) {
      const remaining = this.itemIds.filter((id) => id !== item_id);
      this.$router.replace({ name: "compare", query: { ids: remaining.join(",") } });
    },
    onAddItem(item) {
      const newId = item && item.item_id;
      this.itemToAdd = null;
      if (!newId || this.itemIds.includes(newId)) return;
      this.$router.replace({
        name: "compare",
        query: { ids: [...this.itemIds, newId].join(",") },
      });
    },
    // True when the samples don't all share the same value for this field.
    fieldDiffers(field) {
      if (this.items.length < 2) return false;
      const values = this.items.map((i) => String(field.render(i)));
      return new Set(values).size > 1;
    },
    isBlockEnabled(key) {
      return this.blockEnabled[key] !== false;
    },
    chipTooltip(entry) {
      const detail = entry.fileTooltip || entry.title;
      const action = this.isBlockEnabled(entry.key) ? "click to hide" : "click to show";
      return detail ? `${detail} — ${action}` : action;
    },
    // Middle-ellipsis shortening for long file names, keeping the extension,
    // e.g. "stru_doped_structure.cif" -> "stru_doped…e.cif".
    shortenName(name, head = 10, tail = 6) {
      if (!name || name.length <= head + tail + 1) return name;
      return `${name.slice(0, head)}…${name.slice(-tail)}`;
    },
    toggleBlock(key) {
      this.blockEnabled[key] = !this.isBlockEnabled(key);
    },
    sampleColor(index) {
      return SAMPLE_COLORS[index % SAMPLE_COLORS.length];
    },
    blockTypeName(bt) {
      return this.$store.state.blocksInfos[bt]?.attributes?.name || bt;
    },
    formatDate(date) {
      if (!date) return "—";
      return String(date).replace("T", " ").slice(0, 16);
    },
  },
};
</script>

<style scoped>
.comparison-page {
  max-width: 1800px;
  margin: 0 auto;
}
.add-sample-control {
  min-width: 24rem;
}
.empty-state {
  border: 1px dashed #d0d5da;
  border-radius: 0.5rem;
  background: #fafbfc;
}

/* Card shell */
.comparison-card {
  border: 1px solid #e7eaee;
  border-radius: 0.5rem;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}
/* sticky-card opts out of clipping so its header can stick to the viewport */
.comparison-card.sticky-card {
  overflow: visible;
}
.comparison-card-header {
  padding: 0.6rem 1rem;
  font-weight: 600;
  background: #f7f9fa;
  border-bottom: 1px solid #e7eaee;
  border-top-left-radius: 0.5rem;
  border-top-right-radius: 0.5rem;
}
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 20;
}
.comparison-card-body {
  padding: 1rem;
}
.collapse-toggle {
  border: none;
  background: transparent;
  padding: 0 0.5rem 0 0;
  cursor: pointer;
  color: #55606a;
}
.collapse-caret {
  transition: transform 0.15s ease;
}
.collapse-caret.collapsed {
  transform: rotate(-90deg);
}

/* Block-type pills */
.type-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.type-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.7rem;
  font-size: 0.85rem;
  font-weight: 500;
  border: 1px solid #c8ced3;
  border-radius: 1rem;
  background: #fff;
  color: #2c3e50;
  cursor: pointer;
}
.type-pill.active {
  background: #007bff;
  border-color: #007bff;
  color: #fff;
}
.type-pill.partial:not(.active) {
  opacity: 0.6;
  border-style: dashed;
}
.pill-count {
  font-size: 0.7rem;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 0.7rem;
  padding: 0 0.4rem;
}
.type-pill.active .pill-count {
  background: rgba(255, 255, 255, 0.25);
}

/* Count badge inside the "Differences" toggle button */
.diff-count {
  display: inline-block;
  font-size: 0.7rem;
  line-height: 1;
  padding: 0.15rem 0.4rem;
  margin-left: 0.3rem;
  border-radius: 0.7rem;
  background: rgba(255, 255, 255, 0.25);
}
.btn-outline-secondary .diff-count {
  background: rgba(0, 0, 0, 0.08);
}

/* Metadata table (fields as rows, samples as paged columns) */
.comparison-table {
  margin-bottom: 0;
  table-layout: fixed;
  width: 100%;
}
.comparison-table td,
.comparison-table th {
  overflow-wrap: anywhere;
  vertical-align: top;
  border-color: #eef1f3;
  padding: 0.3rem 0.6rem;
}
/* zebra striping by field row */
.comparison-table tbody tr:nth-child(odd) td,
.comparison-table tbody tr:nth-child(odd) .field-col {
  background-color: #fcfcfd;
}
/* highlight field rows whose values differ across samples (overrides zebra) */
.comparison-table tbody tr.row-differs td {
  background-color: #fff8e1;
}
.comparison-table tbody tr.row-differs th.field-col {
  background-color: #fff3cd;
  box-shadow: inset 3px 0 0 #f0ad4e;
}
.comparison-table th.field-col {
  width: 11rem;
  background-color: #f7f9fa;
  white-space: nowrap;
  font-weight: 600;
  color: #55606a;
}
.comparison-table thead th.sample-col {
  border-top: 3px solid transparent;
  background: #fff;
}
/* pager */
.pager {
  white-space: nowrap;
}
.pager-btn {
  border: none;
  background: transparent;
  color: #007bff;
  cursor: pointer;
  padding: 0 0.25rem;
}
.pager-btn:disabled {
  color: #c8ced3;
  cursor: default;
}
.sample-dot {
  display: inline-block;
  width: 0.65rem;
  height: 0.65rem;
  border-radius: 50%;
  margin-right: 0.4rem;
  flex: 0 0 auto;
}
.remove-btn {
  opacity: 0.5;
}
.remove-btn:hover {
  opacity: 1;
}

/* Participating-blocks toggle bar */
.block-toggle-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #eef1f3;
}
.block-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.6rem;
  font-size: 0.85rem;
  border: 1px solid #c8ced3;
  border-radius: 1rem;
  background: #fff;
  color: #2c3e50;
  cursor: pointer;
}
.block-chip.inactive {
  opacity: 0.45;
  text-decoration: line-through;
  border-style: dashed;
}
.block-chip.inactive .sample-dot {
  filter: grayscale(1);
}
.chip-detail {
  margin-left: 0.35rem;
  font-size: 0.75rem;
  color: #6c757d;
  max-width: 9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-label {
  display: inline-block;
  max-width: 14rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}

/* Block grid: column count is set inline (gridStyle), capped at two. */
.block-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.25rem;
}
/* Collapse to a single column on narrow viewports. !important is needed to
   override the inline grid-template-columns set by gridStyle. */
@media (max-width: 900px) {
  .block-grid {
    grid-template-columns: minmax(0, 1fr) !important;
  }
}
.block-cell {
  border: 1px solid #e7eaee;
  border-top: 3px solid #ccc;
  border-radius: 0.35rem;
  padding: 0.75rem;
  background: #fff;
  min-width: 0;
}
.block-cell-title {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
}
.comparison-media {
  display: block;
  max-width: 100%;
  max-height: 360px;
  margin: 0 auto;
  object-fit: contain;
}
.comparison-comment {
  white-space: pre-wrap;
  font-size: 0.9rem;
  color: #2c3e50;
}
.overlay-plot-wrapper {
  max-width: 1100px;
  margin: 0 auto;
}
</style>
