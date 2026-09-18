<!-- This file was edited with the assistance of an AI model and requires human review from the contributor. -->
<template>
  <div class="deployment-stats">
    <div v-if="loading" class="text-center p-4 text-muted">
      <font-awesome-icon :icon="['fa', 'sync']" spin /> Crunching the numbers...
    </div>
    <div v-else-if="error" class="alert alert-warning">{{ error }}</div>
    <div v-else-if="!stats" class="text-muted">
      Log in to see usage statistics for this <i>datalab</i>.
    </div>

    <template v-else>
      <p v-if="headline" class="stats-headline">
        Since <strong>{{ headline.since }}</strong
        >, this <i>datalab</i> has recorded
        <span class="hero-number">{{ headline.items.toLocaleString() }}</span>
        items from <strong>{{ headline.users.toLocaleString() }}</strong> users.
      </p>

      <!-- Stat tiles, each with a cumulative sparkline -->
      <div class="stat-tiles">
        <div
          v-for="tile in tiles"
          :key="tile.key"
          class="stat-tile"
          :data-testid="`tile-${tile.key}`"
        >
          <div class="tile-label">
            <span class="legend-swatch" :style="{ background: tile.color }"></span>{{ tile.label }}
          </div>
          <div class="tile-value">{{ compact(tile.value) }}</div>
          <div class="tile-sub">
            <template v-if="tile.sub">{{ tile.sub }}</template>
            <template v-else-if="tile.thisMonth"
              >+{{ compact(tile.thisMonth) }} this month</template
            >
            <template v-else>&nbsp;</template>
          </div>
          <svg
            v-if="tile.sparkline"
            class="tile-sparkline"
            viewBox="0 0 100 28"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path :d="tile.sparkline.area" :fill="tile.color" opacity="0.1" />
            <path
              :d="tile.sparkline.line"
              :stroke="tile.color"
              fill="none"
              stroke-width="2"
              vector-effect="non-scaling-stroke"
              stroke-linejoin="round"
            />
          </svg>
        </div>
      </div>

      <!-- Controls apply to every time series below -->
      <div class="stats-controls">
        <div class="btn-group btn-group-sm" role="group" aria-label="Time range">
          <button
            v-for="r in ranges"
            :key="r.value"
            type="button"
            class="btn"
            :class="range === r.value ? 'btn-secondary' : 'btn-outline-secondary'"
            @click="range = r.value"
          >
            {{ r.label }}
          </button>
        </div>
      </div>

      <section class="stats-card">
        <header>
          <h6>Items</h6>
          <div class="btn-group btn-group-sm" role="group" aria-label="Item chart mode">
            <button
              type="button"
              class="btn"
              :class="itemsMode === 'cumulative' ? 'btn-secondary' : 'btn-outline-secondary'"
              @click="itemsMode = 'cumulative'"
            >
              Total
            </button>
            <button
              type="button"
              class="btn"
              :class="itemsMode === 'monthly' ? 'btn-secondary' : 'btn-outline-secondary'"
              @click="itemsMode = 'monthly'"
            >
              New per month
            </button>
          </div>
        </header>
        <StatsTimeChart
          :months="visibleMonths"
          :series="itemSeries"
          :mode="itemsMode === 'monthly' ? 'stacked' : 'line'"
          :height="260"
          aria-label="Items over time by type"
        />
      </section>

      <div class="stats-grid">
        <section class="stats-card">
          <header>
            <h6>Activity</h6>
            <select v-model="activityMetric" class="form-control form-control-sm metric-select">
              <option v-for="(m, key) in activityMetrics" :key="key" :value="key">
                {{ m.label }}
              </option>
            </select>
          </header>
          <p class="card-caption">{{ activityMetrics[activityMetric].caption }}</p>
          <StatsTimeChart
            :months="visibleMonths"
            :series="activitySeries"
            mode="stacked"
            :height="180"
            :aria-label="activityMetrics[activityMetric].label"
          />
        </section>

        <section class="stats-card">
          <header>
            <h6>Data</h6>
            <div class="btn-group btn-group-sm" role="group" aria-label="Data chart mode">
              <button
                type="button"
                class="btn"
                :class="dataMetric === 'file_bytes' ? 'btn-secondary' : 'btn-outline-secondary'"
                @click="dataMetric = 'file_bytes'"
              >
                Storage
              </button>
              <button
                type="button"
                class="btn"
                :class="dataMetric === 'files' ? 'btn-secondary' : 'btn-outline-secondary'"
                @click="dataMetric = 'files'"
              >
                Files
              </button>
            </div>
          </header>
          <p class="card-caption">
            {{
              dataMetric === "file_bytes" ? "Total size of uploaded files" : "Total uploaded files"
            }}
          </p>
          <StatsTimeChart
            :months="visibleMonths"
            :series="dataSeries"
            mode="line"
            :height="180"
            :format-value="dataMetric === 'file_bytes' ? formatBytes : compact"
            :aria-label="dataMetric === 'file_bytes' ? 'Storage over time' : 'Files over time'"
          />
        </section>
      </div>

      <section v-if="blockBars.length" class="stats-card">
        <header>
          <h6>Blocks in use</h6>
          <span class="card-caption mb-0">{{ totalBlocks.toLocaleString() }} blocks</span>
        </header>
        <ul class="bar-list">
          <li
            v-for="bar in blockBars"
            :key="bar.key"
            :title="`${bar.label}: ${bar.value.toLocaleString()}`"
          >
            <span class="bar-label">{{ bar.label }}</span>
            <span class="bar-track">
              <span
                class="bar-fill"
                :style="{ width: `${bar.fraction * 100}%`, background: bar.color }"
              ></span>
            </span>
            <span class="bar-value">{{ bar.value.toLocaleString() }}</span>
          </li>
        </ul>
      </section>

      <p v-if="stats.updated_at" class="stats-footnote">
        Monthly counts are recorded from when each entry was created; totals reflect the current
        database. Last updated {{ formatDate(stats.updated_at) }}.
      </p>
    </template>
  </div>
</template>

<script>
import StatsTimeChart from "@/components/StatsTimeChart.vue";
import { getStatsHistory } from "@/server_fetch_utils.js";
import { itemTypes } from "@/resources.js";

// Hues for item types without their own colour, and for anything folded into "Other"
const FALLBACK_COLORS = ["#7b52ab", "#d0457a"];
const OTHER_COLOR = "#9aa1a9";
const MAX_ITEM_SERIES = 5;
// Inventory entries rather than research outputs, so left out of the usage stats
const EXCLUDED_ITEM_TYPES = ["starting_materials"];
const MAX_BLOCK_BARS = 10;
const ACTIVITY_COLOR = "#00897b";
const DATA_COLOR = "#52606d";

function cumulative(values) {
  let total = 0;
  return values.map((v) => (total += v || 0));
}

function humanise(key) {
  const words = key.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

export default {
  name: "DeploymentStats",
  components: { StatsTimeChart },
  data() {
    return {
      stats: null,
      loading: true,
      error: null,
      range: "all",
      ranges: [
        { value: "all", label: "All time" },
        { value: 24, label: "2 years" },
        { value: 12, label: "1 year" },
      ],
      itemsMode: "cumulative",
      activityMetric: "active_users",
      activityMetrics: {
        active_users: {
          label: "Active users",
          caption: "Users who created or saved an item each month",
        },
        users: { label: "New users", caption: "New accounts registered each month" },
        versions: { label: "Item saves", caption: "Saved versions of items each month" },
        collections: { label: "New collections", caption: "Collections created each month" },
      },
      dataMetric: "file_bytes",
    };
  },
  computed: {
    allMonths() {
      return this.stats?.months || [];
    },
    startIndex() {
      if (this.range === "all") return 0;
      return Math.max(this.allMonths.length - this.range, 0);
    },
    visibleMonths() {
      return this.allMonths.slice(this.startIndex);
    },
    itemTypeOrder() {
      // Largest item types first, so the most important series keep their own colour
      const items = this.stats?.items || {};
      return Object.keys(items)
        .filter((type) => !EXCLUDED_ITEM_TYPES.includes(type))
        .sort((a, b) => this.sum(items[b]) - this.sum(items[a]) || a.localeCompare(b));
    },
    itemTypeColors() {
      const colors = {};
      let fallback = 0;
      this.itemTypeOrder.forEach((type) => {
        if (itemTypes[type]?.navbarColor) {
          colors[type] = itemTypes[type].navbarColor;
        } else if (fallback < FALLBACK_COLORS.length) {
          colors[type] = FALLBACK_COLORS[fallback++];
        }
      });
      return colors;
    },
    monthlyItemSeries() {
      const items = this.stats?.items || {};
      const own = this.itemTypeOrder
        .filter((type) => this.itemTypeColors[type])
        .slice(0, MAX_ITEM_SERIES - 1);
      const rest = this.itemTypeOrder.filter((type) => !own.includes(type));
      const series = own.map((type) => ({
        key: type,
        label: humanise(type),
        color: this.itemTypeColors[type],
        values: items[type],
      }));
      if (rest.length) {
        series.push({
          key: "other",
          label: "Other",
          color: OTHER_COLOR,
          values: this.allMonths.map((_, i) =>
            rest.reduce((acc, type) => acc + (items[type][i] || 0), 0),
          ),
        });
      }
      return series;
    },
    itemSeries() {
      return this.monthlyItemSeries.map((s) => ({
        ...s,
        values: this.window(this.itemsMode === "cumulative" ? cumulative(s.values) : s.values),
      }));
    },
    activitySeries() {
      return [
        {
          key: this.activityMetric,
          label: this.activityMetrics[this.activityMetric].label,
          color: ACTIVITY_COLOR,
          values: this.window(this.stats?.[this.activityMetric] || []),
        },
      ];
    },
    dataSeries() {
      return [
        {
          key: this.dataMetric,
          label: this.dataMetric === "file_bytes" ? "Storage" : "Files",
          color: DATA_COLOR,
          values: this.window(cumulative(this.stats?.[this.dataMetric] || [])),
        },
      ];
    },
    headline() {
      if (!this.allMonths.length) return null;
      const [year, month] = this.allMonths[0].split("-").map(Number);
      const since = new Date(Date.UTC(year, month - 1, 1)).toLocaleDateString(undefined, {
        month: "long",
        year: "numeric",
        timeZone: "UTC",
      });
      const totals = this.stats.totals || {};
      return {
        since,
        items: this.sum(
          Object.entries(totals.items || {})
            .filter(([type]) => !EXCLUDED_ITEM_TYPES.includes(type))
            .map(([, count]) => count),
        ),
        users: totals.users || 0,
      };
    },
    tiles() {
      const totals = this.stats?.totals || {};
      const last = this.allMonths.length - 1;
      const tile = (key, label, color, value, monthly, extra = {}) => ({
        key,
        label,
        color,
        value,
        thisMonth: monthly ? monthly[last] : null,
        sparkline: monthly ? this.sparkline(cumulative(monthly)) : null,
        ...extra,
      });
      const monthlyItems = this.allMonths.map((_, i) =>
        this.sum(this.monthlyItemSeries.map((s) => s.values[i])),
      );
      const tiles = [
        tile("users", "Users", itemTypes.users.navbarColor, totals.users, this.stats?.users),
        tile("items", "Items", itemTypes.samples.navbarColor, this.headline?.items, monthlyItems),
        tile(
          "collections",
          "Collections",
          itemTypes.collections.navbarColor,
          totals.collections,
          this.stats?.collections,
        ),
        // Blocks carry no creation time, so there is no history to draw
        tile("blocks", "Blocks", itemTypes.blocks.navbarColor, this.totalBlocks, null, {
          sub: `across ${Object.keys(this.stats?.blocks || {}).length} block types`,
        }),
      ];
      return tiles;
    },
    totalBlocks() {
      return this.sum(Object.values(this.stats?.blocks || {}));
    },
    blockBars() {
      const blocks = Object.entries(this.stats?.blocks || {}).sort((a, b) => b[1] - a[1]);
      const top = blocks.slice(0, MAX_BLOCK_BARS);
      const rest = blocks.slice(MAX_BLOCK_BARS);
      const bars = top.map(([key, value]) => ({
        key,
        label: this.$store.state.blocksInfos?.[key]?.attributes?.name || key,
        value,
        color: itemTypes.blocks.navbarColor,
      }));
      if (rest.length) {
        bars.push({
          key: "other",
          label: `Other (${rest.length} types)`,
          value: this.sum(rest.map(([, v]) => v)),
          color: OTHER_COLOR,
        });
      }
      const max = Math.max(...bars.map((b) => b.value), 1);
      return bars.map((b) => ({ ...b, fraction: b.value / max }));
    },
  },
  async mounted() {
    try {
      this.stats = await getStatsHistory();
    } catch (error) {
      this.error = `Unable to load deployment statistics: ${error}`;
    } finally {
      this.loading = false;
    }
  },
  methods: {
    sum(values) {
      return (values || []).reduce((acc, v) => acc + (v || 0), 0);
    },
    window(values) {
      return values.slice(this.startIndex);
    },
    sparkline(values) {
      const windowed = this.window(values);
      if (windowed.length < 2) return null;
      const min = Math.min(...windowed);
      const max = Math.max(...windowed);
      const span = max - min || 1;
      const points = windowed.map((v, i) => [
        (100 * i) / (windowed.length - 1),
        26 - (24 * (v - min)) / span,
      ]);
      const line = points.map(([x, y], i) => `${i ? "L" : "M"}${x},${y}`).join("");
      return { line, area: `${line}L100,28L0,28Z` };
    },
    compact(value) {
      if (value == null) return "–";
      return Intl.NumberFormat(undefined, {
        notation: "compact",
        maximumFractionDigits: 1,
      }).format(value);
    },
    formatBytes(bytes) {
      if (!bytes) return "0 B";
      const units = ["B", "kB", "MB", "GB", "TB", "PB"];
      const exponent = Math.min(Math.floor(Math.log10(bytes) / 3), units.length - 1);
      const value = bytes / Math.pow(1000, exponent);
      return `${value.toLocaleString(undefined, { maximumFractionDigits: value < 10 ? 1 : 0 })} ${units[exponent]}`;
    },
    formatDate(value) {
      return new Date(value).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
    },
  },
};
</script>

<style scoped>
.stats-headline {
  font-size: 1.05rem;
  color: #495057;
  margin-bottom: 1rem;
}

.hero-number {
  font-size: 2.2rem;
  font-weight: 700;
  color: #212529;
  line-height: 1;
  margin: 0 0.15em;
}

.stat-tiles {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 1rem;
}

.stat-tile {
  border: 1px solid #e9ecef;
  border-radius: 10px;
  padding: 10px 12px 0;
  background: #fff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}

.stat-tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.tile-label {
  font-size: 0.8rem;
  color: #6c757d;
  display: flex;
  align-items: center;
}

.tile-value {
  font-size: 1.6rem;
  font-weight: 600;
  color: #212529;
  line-height: 1.2;
}

.tile-sub {
  font-size: 0.75rem;
  color: #6c757d;
  margin-bottom: 4px;
}

.tile-sparkline {
  width: calc(100% + 24px);
  height: 28px;
  margin: auto -12px 0;
  display: block;
}

.legend-swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
  margin-right: 6px;
  flex-shrink: 0;
}

.stats-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 0 12px;
}

.stats-card {
  border: 1px solid #e9ecef;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
  background: #fff;
  min-width: 0;
}

.stats-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.stats-card h6 {
  margin: 0;
  font-weight: 600;
}

.card-caption {
  font-size: 0.8rem;
  color: #6c757d;
  margin-bottom: 6px;
}

.metric-select {
  width: auto;
}

.bar-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.bar-list li {
  display: grid;
  grid-template-columns: minmax(90px, 35%) 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 3px 0;
  font-size: 0.85rem;
}

.bar-label {
  color: #495057;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-track {
  height: 12px;
}

.bar-fill {
  display: block;
  height: 100%;
  min-width: 2px;
  border-radius: 0 4px 4px 0;
  transition: width 0.4s ease;
}

.bar-value {
  font-variant-numeric: tabular-nums;
  color: #212529;
  font-weight: 600;
  text-align: right;
}

.stats-footnote {
  font-size: 0.75rem;
  color: #868e96;
  margin: 0.25rem 0 0;
}
</style>
