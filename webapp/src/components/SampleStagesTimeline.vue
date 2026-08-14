<template>
  <section class="sample-stages" :class="layoutClass">
    <header class="sample-stages__header">
      <div class="sample-stages__heading">
        <h3 class="sample-stages__title">{{ title }}</h3>
        <span class="sample-stages__badge">{{ shownRangeLabel }}</span>
      </div>

      <div v-if="showControls" class="sample-stages__controls">
        <slot name="controls"></slot>

        <div class="sample-stages__control-group">
          <div class="sample-stages__date-controls">
            <button
              type="button"
              class="sample-stages__icon-button"
              :title="sortOrder === 'asc' ? 'Sort date ascending' : 'Sort date descending'"
              @click="toggleSortOrder"
            >
              <i
                :class="sortOrder === 'asc' ? 'pi pi-sort-amount-up' : 'pi pi-sort-amount-down'"
                aria-hidden="true"
              ></i>
            </button>

            <button
              type="button"
              class="sample-stages__control-button"
              @click="toggleDateFilterPanel"
            >
              <i class="pi pi-filter" aria-hidden="true"></i>
              <span>Date</span>
              <i class="pi pi-chevron-down sample-stages__control-arrow" aria-hidden="true"></i>
            </button>
          </div>

          <div v-if="isDateFilterOpen" class="sample-stages__popover" @click.stop>
            <Select
              v-model="dateFilterMode"
              :options="dateFilterOptions"
              option-label="label"
              option-value="value"
              placeholder="Select filter type"
              class="sample-stages__select"
              @change="handleDateFilterModeChange"
            />

            <DatePicker
              v-if="dateFilterMode === 'range'"
              v-model="dateFilterValue"
              selection-mode="range"
              date-format="yy-mm-dd"
              placeholder="Select date range"
              :show-button-bar="true"
              :manual-input="false"
              :hide-on-range-selection="true"
              class="sample-stages__date-picker"
            />

            <DatePicker
              v-else
              v-model="dateFilterValue"
              date-format="yy-mm-dd"
              :placeholder="dateFilterMode === 'before' ? 'Created before' : 'Created after'"
              :show-button-bar="true"
              :manual-input="false"
              class="sample-stages__date-picker"
            />

            <div class="sample-stages__popover-actions">
              <button
                type="button"
                class="sample-stages__secondary-button"
                @click="clearDateFilter"
              >
                Clear
              </button>
              <button
                type="button"
                class="sample-stages__primary-button"
                @click="isDateFilterOpen = false"
              >
                Apply
              </button>
            </div>
          </div>
        </div>

        <div class="sample-stages__control-group">
          <button
            type="button"
            class="sample-stages__control-button"
            @click="toggleTypeFilterPanel"
          >
            <FilterIcon aria-hidden="true" />
            <span>Block types</span>
            <span class="sample-stages__control-count">{{ filterSummary }}</span>
          </button>

          <div v-if="isTypeFilterOpen" class="sample-stages__popover" @click.stop>
            <label class="sample-stages__filter-item sample-stages__filter-item--all">
              <input type="checkbox" :checked="allTypesSelected" @change="toggleAllTypes" />
              <span>All</span>
            </label>

            <label
              v-for="type in availableTypeOptions"
              :key="type.blocktype"
              class="sample-stages__filter-item"
            >
              <input
                type="checkbox"
                :checked="selectedTypes.includes(type.blocktype)"
                @change="toggleType(type.blocktype)"
              />
              <span>{{ type.label }}</span>
            </label>

            <div class="sample-stages__popover-actions">
              <button
                type="button"
                class="sample-stages__secondary-button"
                @click="clearTypeFilter"
              >
                Clear
              </button>
              <button
                type="button"
                class="sample-stages__primary-button"
                @click="isTypeFilterOpen = false"
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="sample-stages__viewport">
      <div v-if="visibleStages.length === 0" class="sample-stages__empty">No stages to show.</div>

      <div v-else :class="trackClass">
        <template v-for="(stage, index) in visibleStages" :key="stage.id">
          <StyledTooltip
            :delay="350"
            anchor-display="block"
            anchor-class="sample-stages__tooltip-anchor"
          >
            <template #anchor>
              <button
                type="button"
                class="sample-stage-card"
                :class="{ 'is-muted': !isHighlighted(stage.blocktype) }"
                @click="$emit('stage-click', stage.raw)"
              >
                <span class="sample-stage-card__type">{{ stage.blocktype }}</span>
                <div class="sample-stage-card__datetime">
                  <span class="sample-stage-card__date">{{ formatDate(stage.timestamp) }}</span>
                  <span class="sample-stage-card__time">{{ formatTime(stage.timestamp) }}</span>
                  <span class="sample-stage-card__timezone">{{
                    formatTimeZone(stage.timestamp)
                  }}</span>
                </div>
              </button>
            </template>

            <template #content>
              <div class="sample-stage-tooltip">
                <h4 class="sample-stage-tooltip__title">{{ stage.fullName }}</h4>
                <p class="sample-stage-tooltip__meta">{{ stage.blocktype }}</p>
                <p class="sample-stage-tooltip__meta">
                  {{ formatDate(stage.timestamp) }} {{ formatTime(stage.timestamp) }}
                  {{ formatTimeZone(stage.timestamp) }}
                </p>
                <p v-if="stage.details" class="sample-stage-tooltip__details">
                  {{ stage.details }}
                </p>
                <pre v-if="stage.extraText" class="sample-stage-tooltip__extra">{{
                  stage.extraText
                }}</pre>
              </div>
            </template>
          </StyledTooltip>

          <div
            v-if="index < visibleStages.length - 1"
            class="sample-stage-link"
            :class="{ 'is-muted': !linkIsHighlighted(stage, visibleStages[index + 1]) }"
          >
            <span class="sample-stage-link__label">{{
              connectorLabel(stage, visibleStages[index + 1])
            }}</span>
            <span class="sample-stage-link__line"></span>
            <ArrowLeftIcon
              v-if="orientation === 'horizontal'"
              aria-hidden="true"
              class="sample-stage-link__icon"
            />
            <ArrowDownIcon v-else aria-hidden="true" class="sample-stage-link__icon" />
          </div>
        </template>
      </div>
    </div>

    <footer v-if="sortedStages.length > 0" class="sample-stages__footer">
      <span class="sample-stages__order-label">{{ sortOrderLabel }}</span>

      <button
        type="button"
        class="sample-stages__pager-button"
        :disabled="currentPage === 0"
        @click="goToFirstPage"
      >
        <AngleDoubleLeftIcon aria-hidden="true" />
      </button>
      <button
        type="button"
        class="sample-stages__pager-button"
        :disabled="currentPage === 0"
        @click="goToPreviousPage"
      >
        <ChevronLeftIcon aria-hidden="true" />
      </button>

      <span class="sample-stages__page-indicator">{{ currentPage + 1 }} / {{ pageCount }}</span>

      <button
        type="button"
        class="sample-stages__pager-button"
        :disabled="currentPage >= pageCount - 1"
        @click="goToNextPage"
      >
        <ChevronRightIcon aria-hidden="true" />
      </button>
      <button
        type="button"
        class="sample-stages__pager-button"
        :disabled="currentPage >= pageCount - 1"
        @click="goToLastPage"
      >
        <AngleDoubleRightIcon aria-hidden="true" />
      </button>

      <label class="sample-stages__page-size">
        <span>Show</span>
        <select v-model.number="pageSize">
          <option v-for="option in pageSizeOptions" :key="option" :value="option">
            {{ option }}
          </option>
        </select>
      </label>
    </footer>
  </section>
</template>

<script>
import StyledTooltip from "@/components/StyledTooltip";
import AngleDoubleLeftIcon from "@primevue/icons/angledoubleleft";
import AngleDoubleRightIcon from "@primevue/icons/angledoubleright";
import ArrowDownIcon from "@primevue/icons/arrowdown";
import ArrowLeftIcon from "@primevue/icons/angleright";
import DatePicker from "primevue/datepicker";
import ChevronLeftIcon from "@primevue/icons/chevronleft";
import ChevronRightIcon from "@primevue/icons/chevronright";
import FilterIcon from "@primevue/icons/filter";
import Select from "primevue/select";
import "primeicons/primeicons.css";

export default {
  name: "SampleStagesTimeline",
  components: {
    StyledTooltip,
    AngleDoubleLeftIcon,
    AngleDoubleRightIcon,
    ArrowDownIcon,
    ArrowLeftIcon,
    DatePicker,
    ChevronLeftIcon,
    ChevronRightIcon,
    FilterIcon,
    Select,
  },
  props: {
    stages: {
      type: Array,
      default: () => [],
    },
    title: {
      type: String,
      default: "Sample blocks",
    },
    orientation: {
      type: String,
      default: "horizontal",
      validator: (value) => ["horizontal", "vertical"].includes(value),
    },
    showControls: {
      type: Boolean,
      default: true,
    },
    defaultSortOrder: {
      type: String,
      default: "desc",
      validator: (value) => ["asc", "desc"].includes(value),
    },
    pageSizeOptions: {
      type: Array,
      default: () => [10, 20, 50],
    },
    initialPageSize: {
      type: Number,
      default: 10,
    },
  },
  emits: ["stage-click", "update:sort-order", "update:selected-types"],
  data() {
    return {
      isDateFilterOpen: false,
      isTypeFilterOpen: false,
      dateFilterMode: "range",
      dateFilterValue: null,
      sortOrder: this.defaultSortOrder,
      selectedTypes: [],
      currentPage: 0,
      pageSize: this.initialPageSize,
    };
  },
  computed: {
    normalizedStages() {
      return (this.stages || [])
        .map((stage, index) => this.normalizeStage(stage, index))
        .filter((stage) => stage.timestamp !== null);
    },
    dateFilterOptions() {
      return [
        { label: "Date range", value: "range" },
        { label: "Created before", value: "before" },
        { label: "Created after", value: "after" },
      ];
    },
    filteredStages() {
      return this.normalizedStages.filter((stage) => this.matchesDateFilter(stage.timestamp));
    },
    sortedStages() {
      const stages = [...this.filteredStages];
      stages.sort((left, right) => {
        const leftTime = this.getTimestampMillis(left.timestamp);
        const rightTime = this.getTimestampMillis(right.timestamp);

        return this.sortOrder === "asc" ? leftTime - rightTime : rightTime - leftTime;
      });
      return stages;
    },
    availableTypeOptions() {
      const typeSet = new Map();
      const blockInfos = this.$store.state.blocksInfos || {};

      this.normalizedStages.forEach((stage) => {
        if (!stage.blocktype || typeSet.has(stage.blocktype)) {
          return;
        }

        typeSet.set(stage.blocktype, {
          blocktype: stage.blocktype,
          label: blockInfos[stage.blocktype]?.attributes?.name || stage.blocktype,
        });
      });

      return Array.from(typeSet.values()).sort((left, right) =>
        left.label.localeCompare(right.label),
      );
    },
    visibleStages() {
      const start = this.currentPage * this.pageSize;
      return this.sortedStages.slice(start, start + this.pageSize);
    },
    pageCount() {
      return Math.max(1, Math.ceil(this.sortedStages.length / this.pageSize));
    },
    allTypesSelected() {
      return (
        this.availableTypeOptions.length > 0 &&
        this.selectedTypes.length === this.availableTypeOptions.length
      );
    },
    filterSummary() {
      if (this.availableTypeOptions.length === 0 || this.allTypesSelected) {
        return "All";
      }

      return `${this.selectedTypes.length}/${this.availableTypeOptions.length}`;
    },
    shownRangeLabel() {
      if (this.sortedStages.length === 0) {
        return "0 / 0";
      }

      const start = this.currentPage * this.pageSize + 1;
      const end = Math.min(start + this.pageSize - 1, this.sortedStages.length);
      return `${start}-${end} / ${this.sortedStages.length}`;
    },
    sortOrderLabel() {
      if (this.sortOrder === "desc") {
        return "Order: Newest first";
      }

      return "Order: Oldest first";
    },
    layoutClass() {
      return {
        "is-horizontal": this.orientation === "horizontal",
        "is-vertical": this.orientation === "vertical",
      };
    },
    trackClass() {
      return ["sample-stages__track", `sample-stages__track--${this.orientation}`];
    },
  },
  watch: {
    stages: {
      immediate: true,
      handler() {
        const wereAllSelected = this.allTypesSelected || this.selectedTypes.length === 0;

        this.$nextTick(() => {
          this.syncSelectedTypes();
          if (wereAllSelected) {
            this.availableTypeOptions.forEach((type) => {
              if (!this.selectedTypes.includes(type.blocktype)) {
                this.selectedTypes.push(type.blocktype);
              }
            });
          }
        });
        this.currentPage = 0;
      },
    },
    pageSize() {
      this.currentPage = 0;
    },
    pageCount(newValue) {
      if (this.currentPage > newValue - 1) {
        this.currentPage = Math.max(0, newValue - 1);
      }
    },
    sortOrder(newValue) {
      this.$emit("update:sort-order", newValue);
      this.currentPage = 0;
    },
    selectedTypes: {
      deep: true,
      handler(value) {
        this.$emit("update:selected-types", [...value]);
      },
    },
  },
  methods: {
    normalizeStage(stage, index) {
      const timestamp = this.resolveTimestamp(stage);
      const blocktype =
        stage.blocktype || stage.blockType || stage.type || stage.stage_type || "Block";
      const fullName =
        stage.full_name ||
        stage.fullName ||
        stage.name ||
        stage.title ||
        stage.block_name ||
        blocktype;
      const details = stage.detail || stage.details || stage.description || stage.note || "";

      return {
        id:
          stage.id ||
          stage.stage_id ||
          stage.block_id ||
          stage.immutable_id ||
          `${blocktype}-${index}-${timestamp || "unknown"}`,
        blocktype,
        fullName,
        details,
        timestamp,
        extraText: this.formatExtra(stage.extra || stage.meta || stage.metadata || null),
        raw: stage,
      };
    },
    resolveTimestamp(stage) {
      const candidates = [
        stage.timestamp,
        stage.created_at,
        stage.date,
        stage.date_created,
        stage.createdAt,
      ];

      for (const candidate of candidates) {
        if (!candidate) {
          continue;
        }

        const timestamp = this.parseStageTimestamp(candidate);
        if (!Number.isNaN(timestamp.getTime())) {
          return candidate;
        }
      }

      return null;
    },
    getUserTimeZone() {
      try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
      } catch {
        return "UTC";
      }
    },
    parseStageTimestamp(value) {
      if (!value) {
        return new Date(NaN);
      }

      if (value instanceof Date) {
        return value;
      }

      if (typeof value === "string") {
        const normalizedValue = value.trim().replace(" ", "T");
        const hasZoneSuffix = /([zZ]|[+-]\d{2}:?\d{2})$/.test(normalizedValue);
        const parsed = new Date(hasZoneSuffix ? normalizedValue : `${normalizedValue}Z`);
        return parsed;
      }

      return new Date(value);
    },
    getTimestampMillis(value) {
      const parsed = this.parseStageTimestamp(value);
      return Number.isNaN(parsed.getTime()) ? 0 : parsed.getTime();
    },
    formatDate(timestamp) {
      if (!timestamp) {
        return "";
      }

      const parsed = this.parseStageTimestamp(timestamp);
      if (Number.isNaN(parsed.getTime())) {
        return "";
      }

      return parsed.toLocaleDateString([], {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        timeZone: this.getUserTimeZone(),
      });
    },
    formatTime(timestamp) {
      if (!timestamp) {
        return "";
      }

      const parsed = this.parseStageTimestamp(timestamp);
      if (Number.isNaN(parsed.getTime())) {
        return "";
      }

      return parsed.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: this.getUserTimeZone(),
      });
    },
    formatTimeZone(timestamp) {
      if (!timestamp) {
        return "";
      }

      const parsed = this.parseStageTimestamp(timestamp);
      if (Number.isNaN(parsed.getTime())) {
        return "";
      }

      const timeZone = this.getUserTimeZone();

      try {
        const parts = new Intl.DateTimeFormat([], {
          timeZone,
          timeZoneName: "short",
        }).formatToParts(parsed);
        const zonePart = parts.find((part) => part.type === "timeZoneName");
        return zonePart?.value || timeZone;
      } catch {
        return timeZone;
      }
    },
    formatExtra(value) {
      if (!value) {
        return "";
      }

      if (typeof value === "string") {
        return value;
      }

      try {
        return JSON.stringify(value, null, 2);
      } catch {
        return "";
      }
    },
    syncSelectedTypes() {
      const types = this.availableTypeOptions;

      if (types.length === 0) {
        this.selectedTypes = [];
        return;
      }

      if (this.selectedTypes.length === 0) {
        this.selectedTypes = types.map((type) => type.blocktype);
        return;
      }

      this.selectedTypes = this.selectedTypes.filter((selectedType) =>
        types.some((type) => type.blocktype === selectedType),
      );

      if (this.selectedTypes.length === 0) {
        this.selectedTypes = types.map((type) => type.blocktype);
      }
    },
    toggleDateFilterPanel() {
      this.isDateFilterOpen = !this.isDateFilterOpen;
      if (this.isDateFilterOpen) {
        this.isTypeFilterOpen = false;
      }
    },
    toggleTypeFilterPanel() {
      this.isTypeFilterOpen = !this.isTypeFilterOpen;
      if (this.isTypeFilterOpen) {
        this.isDateFilterOpen = false;
      }
    },
    clearDateFilter() {
      this.dateFilterMode = "range";
      this.dateFilterValue = null;
      this.currentPage = 0;
    },
    clearTypeFilter() {
      this.selectedTypes = this.availableTypeOptions.map((type) => type.blocktype);
      this.currentPage = 0;
    },
    toggleAllTypes() {
      if (this.allTypesSelected) {
        this.selectedTypes = [];
      } else {
        this.selectedTypes = this.availableTypeOptions.map((type) => type.blocktype);
      }
      this.currentPage = 0;
    },
    toggleType(blocktype) {
      const idx = this.selectedTypes.indexOf(blocktype);
      if (idx === -1) {
        this.selectedTypes.push(blocktype);
      } else {
        this.selectedTypes.splice(idx, 1);
      }
      this.currentPage = 0;
    },
    toggleSortOrder() {
      this.sortOrder = this.sortOrder === "asc" ? "desc" : "asc";
      this.currentPage = 0;
    },
    handleDateFilterModeChange() {
      this.dateFilterValue = null;
      this.currentPage = 0;
    },
    normalizeDateInput(value) {
      if (!value) {
        return null;
      }

      if (value instanceof Date) {
        return Number.isNaN(value.getTime()) ? null : value;
      }

      const parsed = new Date(value);
      return Number.isNaN(parsed.getTime()) ? null : parsed;
    },
    startOfDay(value) {
      const date = this.normalizeDateInput(value);
      if (!date) {
        return null;
      }

      date.setHours(0, 0, 0, 0);
      return date;
    },
    endOfDay(value) {
      const date = this.normalizeDateInput(value);
      if (!date) {
        return null;
      }

      date.setHours(23, 59, 59, 999);
      return date;
    },
    matchesDateFilter(timestamp) {
      if (!timestamp || !this.dateFilterValue) {
        return true;
      }

      const stageDate = this.parseStageTimestamp(timestamp);
      if (Number.isNaN(stageDate.getTime())) {
        return false;
      }

      if (this.dateFilterMode === "range") {
        const [startValue, endValue] = Array.isArray(this.dateFilterValue)
          ? this.dateFilterValue
          : [null, null];

        const start = this.startOfDay(startValue);
        const end = this.endOfDay(endValue);

        if (!start && !end) {
          return true;
        }

        if (start && stageDate < start) {
          return false;
        }

        if (end && stageDate > end) {
          return false;
        }

        return true;
      }

      const selectedDate = this.normalizeDateInput(this.dateFilterValue);
      if (!selectedDate) {
        return true;
      }

      if (this.dateFilterMode === "before") {
        return stageDate <= this.endOfDay(selectedDate);
      }

      return stageDate >= this.startOfDay(selectedDate);
    },
    isHighlighted(type) {
      if (this.selectedTypes.length === 0) {
        return false;
      }

      return this.selectedTypes.includes(type);
    },
    linkIsHighlighted(leftStage, rightStage) {
      return this.isHighlighted(leftStage.blocktype) && this.isHighlighted(rightStage.blocktype);
    },
    connectorLabel(leftStage, rightStage) {
      return leftStage.raw.transition_label || rightStage.raw.transition_label || "";
    },
    goToFirstPage() {
      this.currentPage = 0;
    },
    goToPreviousPage() {
      this.currentPage = Math.max(0, this.currentPage - 1);
    },
    goToNextPage() {
      this.currentPage = Math.min(this.pageCount - 1, this.currentPage + 1);
    },
    goToLastPage() {
      this.currentPage = this.pageCount - 1;
    },
  },
};
</script>

<style scoped>
.sample-stages {
  --surface: #ffffff;
  --surface-muted: #f4f6f9;
  --border: #d7dfeb;
  --text: #263248;
  --text-muted: #6b7484;
  --accent: #2c7be5;
  --accent-soft: rgba(44, 123, 229, 0.12);
  --connector: #8a96a8;
  background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1rem;
  box-shadow: 0 10px 28px rgba(18, 38, 63, 0.06);
}

.sample-stages__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.9rem;
}

.sample-stages__heading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.sample-stages__title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text);
}

.sample-stages__badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}

.sample-stages__controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.sample-stages__control-group {
  position: relative;
}

.sample-stages__control-button,
.sample-stages__pager-button {
  appearance: none;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  border-radius: 12px;
  min-height: 2.5rem;
  padding: 0.45rem 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  transition:
    border-color 0.15s ease,
    background-color 0.15s ease,
    transform 0.15s ease,
    opacity 0.15s ease;
}

.sample-stages__pager-button {
  justify-content: center;
}

.sample-stages__pager-button :deep(svg) {
  width: 0.95rem;
  height: 0.95rem;
}

.sample-stages__date-controls {
  display: inline-flex;
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.sample-stages__icon-button {
  appearance: none;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  border-radius: 10px;
  width: 2.6rem;
  height: 2.6rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.sample-stages__icon-button .pi,
.sample-stages__control-button .pi {
  font-size: 0.95rem;
  line-height: 1;
}

.sample-stages__icon-button:hover {
  border-color: #b8c5d8;
  background: #f8fbff;
  transform: translateY(-1px);
}

.sample-stages__control-arrow {
  margin-left: auto;
  font-size: 0.72rem;
}

.sample-stages__control-button {
  background: #ffffff;
}

.sample-stages__control-button:hover,
.sample-stages__pager-button:hover {
  border-color: #b8c5d8;
  background: #f8fbff;
  transform: translateY(-1px);
}

.sample-stages__control-button:active,
.sample-stages__pager-button:active {
  transform: translateY(0);
}

.sample-stages__control-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  background: #edf2f7;
  color: var(--text-muted);
  font-size: 0.8rem;
  font-weight: 700;
}

.sample-stages__popover {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  z-index: 20;
  width: 20rem;
  padding: 0.85rem;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 16px 32px rgba(18, 38, 63, 0.12);
}

.sample-stages__select,
.sample-stages__date-picker {
  width: 100%;
}

.sample-stages__filter-item {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.25rem;
  color: var(--text);
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
}

.sample-stages__filter-item--all {
  background: #eaf6ee;
  border-radius: 12px;
  padding-inline: 0.55rem;
}

.sample-stages__filter-item input {
  margin: 0;
}

.sample-stages__popover-actions {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 0.85rem;
}

.sample-stages__secondary-button,
.sample-stages__primary-button {
  appearance: none;
  border-radius: 12px;
  min-height: 2.4rem;
  padding: 0.45rem 0.9rem;
  font-weight: 700;
  border: 1px solid transparent;
}

.sample-stages__secondary-button {
  background: #ffffff;
  color: #19b67a;
  border-color: #9beec9;
}

.sample-stages__primary-button {
  background: #19b67a;
  color: #ffffff;
}

.sample-stages__viewport {
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 0.25rem;
}

.sample-stages__empty {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--text-muted);
}

.sample-stages__track {
  display: flex;
  align-items: stretch;
  gap: 0.35rem;
  min-height: 100%;
}

.sample-stages__track--vertical {
  flex-direction: column;
}

.sample-stages__tooltip-anchor {
  flex: 0 0 auto;
}

.sample-stage-card {
  width: 6.3rem;
  min-height: 7rem;
  padding: 0.45rem 0.4rem;
  padding-bottom: 2.2rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
  color: var(--text);
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
  box-shadow: 0 6px 18px rgba(18, 38, 63, 0.05);
  transition:
    opacity 0.18s ease,
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease,
    background-color 0.18s ease;
}

.sample-stage-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(18, 38, 63, 0.1);
}

.sample-stage-card.is-muted {
  opacity: 0.55;
  background: var(--surface-muted);
  filter: grayscale(0.85);
  transform: scale(0.55);
  transform-origin: center center;
  width: 1.4rem;
  min-height: 7rem;
  align-items: center;
  justify-content: center;
  align-self: center;
  gap: 0;
  padding: 0.25rem 0.15rem;
  overflow: hidden;
}

.sample-stage-card__type {
  display: inline-flex;
  width: fit-content;
  max-width: 100%;
  padding: 0.16rem 0.3rem;
  border-radius: 999px;
  background: #e9f1ff;
  color: #1557b0;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  white-space: normal;
  word-break: break-word;
  box-sizing: border-box;
}

.sample-stage-card__name {
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1.2;
  color: var(--text);
  margin-top: 0.15rem;
}

.sample-stage-card__date,
.sample-stage-card__time,
.sample-stage-card__timezone {
  color: var(--text-muted);
  font-size: 0.68rem;
  font-weight: 500;
}

.sample-stage-card__timezone {
  font-size: 0.56rem;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  opacity: 0.8;
}

.sample-stage-card__datetime {
  position: absolute;
  right: 0.5rem;
  bottom: 0.45rem;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.08rem;
}

.sample-stage-card {
  position: relative;
}

.sample-stage-card__date {
  display: block;
  width: 100%;
  background: var(--surface-muted);
  padding: 0.18rem 0.35rem;
  border-radius: 8px;
  text-align: center;
  margin-top: 0.25rem;
}

.sample-stage-card__time {
  display: block;
  text-align: center;
  margin-top: 0.08rem;
}

.sample-stage-card.is-muted .sample-stage-card__name,
.sample-stage-card.is-muted .sample-stage-card__date,
.sample-stage-card.is-muted .sample-stage-card__time,
.sample-stage-card.is-muted .sample-stage-card__timezone {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  margin-top: 0;
  transition:
    opacity 0.15s ease,
    max-height 0.15s ease,
    margin-top 0.15s ease;
}

.sample-stage-card.is-muted .sample-stage-card__type {
  justify-content: center;
  text-align: center;
  font-size: 0.68rem;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  white-space: nowrap;
  word-break: normal;
  line-height: 1;
}

.sample-stage-card.is-muted:hover .sample-stage-card__name,
.sample-stage-card.is-muted:hover .sample-stage-card__date,
.sample-stage-card.is-muted:hover .sample-stage-card__time,
.sample-stage-card.is-muted:hover .sample-stage-card__timezone {
  max-height: 3rem;
  opacity: 1;
  margin-top: 0.15rem;
}

.sample-stage-card.is-muted:hover {
  transform: scale(0.6) translateY(-2px);
}

.sample-stage-card.is-muted .sample-stage-card__type {
  background: rgba(21, 87, 176, 0.09);
  color: #4f6a8e;
}

.sample-stage-link {
  min-width: 1.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 0.25rem;
  color: var(--connector);
  flex: 0 0 auto;
}

.sample-stage-link__label {
  max-width: 2rem;
  text-align: center;
  font-size: 0.68rem;
  line-height: 1.2;
  color: var(--text-muted);
}

.sample-stage-link__line {
  width: 100%;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(138, 150, 168, 0.15), rgba(138, 150, 168, 0.8));
}

.sample-stage-link__icon {
  color: var(--connector);
  transform: scale(-1);
}

.sample-stage-link.is-muted {
  opacity: 0.4;
}

.sample-stage-link.is-muted .sample-stage-link__label {
  display: none;
}

.sample-stage-link.is-muted .sample-stage-link__line {
  width: 0.85rem;
  height: 1px;
  opacity: 0.35;
}

.sample-stage-link.is-muted .sample-stage-link__icon {
  font-size: 0.75rem;
  opacity: 0.45;
}

.sample-stages__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.55rem;
  margin-top: 0.9rem;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.sample-stages__page-indicator {
  color: var(--text-muted);
  font-weight: 600;
  min-width: 4.5rem;
  text-align: center;
}

.sample-stages__order-label {
  color: var(--text-muted);
  font-size: 0.82rem;
  font-weight: 600;
  margin-right: 0.2rem;
  white-space: nowrap;
}

.sample-stages__page-size {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--text-muted);
  font-weight: 600;
  margin-top: 0.5rem;
}

.sample-stages__page-size select {
  appearance: none;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.45rem 0.8rem;
  background: var(--surface);
  color: var(--text);
}

.sample-stage-tooltip {
  max-width: 19rem;
}

.sample-stage-tooltip__title {
  margin: 0 0 0.35rem;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text);
}

.sample-stage-tooltip__meta,
.sample-stage-tooltip__details,
.sample-stage-tooltip__extra {
  margin: 0 0 0.45rem;
  color: var(--text-muted);
  white-space: pre-wrap;
}

.sample-stage-tooltip__extra {
  padding: 0.65rem;
  border-radius: 12px;
  background: #f5f7fb;
  border: 1px solid var(--border);
  font-size: 0.82rem;
}

.sample-stages.is-vertical .sample-stages__track {
  overflow-x: visible;
}

.sample-stages.is-vertical .sample-stage-link {
  min-width: 100%;
  min-height: 4.5rem;
}

.sample-stages.is-vertical .sample-stage-link__line {
  width: 3px;
  height: 100%;
  background: linear-gradient(180deg, rgba(138, 150, 168, 0.15), rgba(138, 150, 168, 0.8));
}

.sample-stages.is-vertical .sample-stage-link__label {
  max-width: 12rem;
}

@media (max-width: 768px) {
  .sample-stages__header {
    align-items: flex-start;
    flex-direction: column;
  }

  .sample-stage-card {
    width: 6.3rem;
  }

  .sample-stage-link {
    min-width: 1.4rem;
  }
}
</style>
