<template>
  <div ref="container" class="w-100 position-relative">
    <div v-if="series.length > 1" class="d-flex flex-wrap small text-secondary mb-1">
      <span v-for="s in series" :key="s.key" class="d-inline-flex align-items-center mr-3">
        <svg
          v-if="mode !== 'stacked'"
          width="12"
          height="12"
          class="mr-1 flex-shrink-0"
          overflow="visible"
          viewBox="0 0 12 12"
        >
          <path :d="markerPath(s.key, 6, 6)" :fill="s.color" />
        </svg>
        <svg v-else width="10" height="10" class="mr-2 flex-shrink-0" aria-hidden="true">
          <rect width="10" height="10" rx="3" :fill="s.color" /></svg
        >{{ s.label }}
      </span>
    </div>
    <div class="position-relative" @mouseleave="hoverIndex = null">
      <svg
        :width="width"
        :height="height"
        :viewBox="`0 0 ${width} ${height}`"
        role="img"
        :aria-label="ariaLabel"
      >
        <!-- Gridlines and y-axis ticks -->
        <g class="grid">
          <g v-for="tick in yTicks" :key="`y-${tick}`">
            <line :x1="margin.left" :x2="width - margin.right" :y1="y(tick)" :y2="y(tick)" />
            <text :x="margin.left - 8" :y="y(tick)" text-anchor="end" dominant-baseline="middle">
              {{ formatTick(tick) }}
            </text>
          </g>
        </g>

        <!-- x-axis labels -->
        <g class="x-axis">
          <text
            v-for="tick in xTicks"
            :key="`x-${tick.index}`"
            :x="xCenter(tick.index)"
            :y="height - 6"
            text-anchor="middle"
          >
            {{ tick.label }}
          </text>
        </g>

        <!-- Stacked columns -->
        <g v-if="mode === 'stacked'">
          <g v-for="(column, i) in stackedColumns" :key="`col-${i}`">
            <path
              v-for="segment in column"
              :key="segment.key"
              :d="segment.path"
              :fill="segment.color"
              :opacity="hoverIndex === null || hoverIndex === i ? 1 : 0.45"
            />
          </g>
        </g>

        <!-- Lines, with a faint wash under a single series -->
        <g v-else>
          <path
            v-if="series.length === 1 && linePaths.length"
            :d="areaPath"
            :fill="series[0].color"
            opacity="0.1"
          />
          <path
            v-for="line in linePaths"
            :key="line.key"
            :d="line.path"
            :stroke="line.color"
            fill="none"
            stroke-width="2"
            stroke-linejoin="round"
            stroke-linecap="round"
          />
          <g v-for="label in endLabels" :key="`end-${label.key}`">
            <path
              :d="markerPath(label.key, label.x, label.y)"
              :fill="label.color"
              stroke="#fff"
              stroke-linejoin="round"
              stroke-width="2"
            />
            <text class="end-label" :x="label.x + 8" :y="label.y" dominant-baseline="middle">
              {{ formatValue(label.value) }}
            </text>
          </g>
        </g>

        <!-- Hover crosshair and markers -->
        <g v-if="hoverIndex !== null && mode !== 'stacked'" class="crosshair">
          <line
            :x1="xCenter(hoverIndex)"
            :x2="xCenter(hoverIndex)"
            :y1="margin.top"
            :y2="height - margin.bottom"
          />
          <path
            v-for="s in series"
            :key="`hover-${s.key}`"
            :d="markerPath(s.key, xCenter(hoverIndex), y(s.values[hoverIndex]))"
            :fill="s.color"
            stroke="#fff"
            stroke-linejoin="round"
            stroke-width="2"
          />
        </g>

        <rect
          class="hit-area"
          :x="margin.left"
          :y="margin.top"
          :width="plotWidth"
          :height="plotHeight"
          @mousemove="onMouseMove"
        />
      </svg>

      <div
        v-if="hoverIndex !== null"
        class="chart-tooltip position-absolute bg-white border rounded shadow-sm px-2 py-1 small"
        :style="tooltipStyle"
      >
        <div class="font-weight-bold mb-1">{{ formatMonth(months[hoverIndex]) }}</div>
        <div
          v-for="s in tooltipSeries"
          :key="`tt-${s.key}`"
          class="d-flex align-items-center text-secondary"
        >
          <svg
            v-if="mode !== 'stacked'"
            width="12"
            height="12"
            class="mr-1 flex-shrink-0"
            overflow="visible"
            viewBox="0 0 12 12"
          >
            <path :d="markerPath(s.key, 6, 6)" :fill="s.color" />
          </svg>
          <svg v-else width="10" height="10" class="mr-1 flex-shrink-0" aria-hidden="true">
            <rect width="10" height="10" rx="3" :fill="s.color" />
          </svg>
          <span class="flex-grow-1 mr-3">{{ s.label }}</span>
          <span class="tabular-nums font-weight-bold text-dark">{{
            formatValue(s.values[hoverIndex])
          }}</span>
        </div>
        <div
          v-if="mode === 'stacked' && series.length > 1"
          class="d-flex align-items-center text-secondary border-top mt-1 pt-1"
        >
          <span class="flex-grow-1 mr-3">Total</span>
          <span class="tabular-nums font-weight-bold text-dark">{{
            formatValue(stackTotals[hoverIndex])
          }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

// Each line series gets its own marker shape, so series can be told apart without colour
const MARKER_SHAPES = ["circle", "square", "diamond", "triangle", "triangle-down"];

// SVG path for a marker centred on (x, y), sized to roughly match a circle of radius r
function shapePath(shape, x, y, r = 4) {
  switch (shape) {
    case "square": {
      const h = r * 0.9;
      return `M${x - h},${y - h}H${x + h}V${y + h}H${x - h}Z`;
    }
    case "diamond": {
      const h = r * 1.25;
      return `M${x},${y - h}L${x + h},${y}L${x},${y + h}L${x - h},${y}Z`;
    }
    case "triangle":
    case "triangle-down": {
      // Centred on the centroid; flipped vertically for the downward variant
      const R = r * 1.35 * (shape === "triangle" ? 1 : -1);
      const dx = Math.abs(R) * 0.866;
      return `M${x},${y - R}L${x + dx},${y + R / 2}L${x - dx},${y + R / 2}Z`;
    }
    default:
      return `M${x - r},${y}a${r},${r} 0 1,0 ${2 * r},0a${r},${r} 0 1,0 ${-2 * r},0Z`;
  }
}

function niceStep(rawStep) {
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const residual = rawStep / magnitude;
  const nice = residual > 5 ? 10 : residual > 2 ? 5 : residual > 1 ? 2 : 1;
  return nice * magnitude;
}

export default {
  name: "StatsTimeChart",
  props: {
    // Month keys in the format YYYY-MM, one per value in each series
    months: { type: Array, required: true },
    // [{ key, label, color, values }]
    series: { type: Array, required: true },
    // "line" or "stacked" (columns)
    mode: { type: String, default: "line" },
    height: { type: Number, default: 240 },
    formatValue: {
      type: Function,
      default: (v) => (v == null ? "" : Math.round(v).toLocaleString()),
    },
    ariaLabel: { type: String, default: "Chart" },
  },
  data() {
    return {
      width: 600,
      hoverIndex: null,
      resizeObserver: null,
    };
  },
  computed: {
    margin() {
      return { top: 12, right: this.mode === "stacked" ? 8 : 56, bottom: 24, left: 48 };
    },
    plotWidth() {
      return Math.max(this.width - this.margin.left - this.margin.right, 10);
    },
    plotHeight() {
      return this.height - this.margin.top - this.margin.bottom;
    },
    band() {
      return this.plotWidth / Math.max(this.months.length, 1);
    },
    stackTotals() {
      return this.months.map((_, i) => this.series.reduce((acc, s) => acc + (s.values[i] || 0), 0));
    },
    yMax() {
      const values =
        this.mode === "stacked" ? this.stackTotals : this.series.flatMap((s) => s.values);
      return Math.max(...values, 1);
    },
    yStep() {
      return niceStep(this.yMax / 4);
    },
    yTop() {
      // Leave a little headroom so end labels and column caps clear the top edge
      return Math.ceil((this.yMax * 1.05) / this.yStep) * this.yStep;
    },
    yTicks() {
      const ticks = [];
      for (let t = 0; t <= this.yTop + 1e-9; t += this.yStep) ticks.push(t);
      return ticks;
    },
    xTicks() {
      const n = this.months.length;
      if (!n) return [];
      // Aim for one label roughly every 70px, snapping to years or quarters
      const every = Math.max(1, Math.ceil(70 / this.band));
      const ticks = [];
      if (every > 6 || n > 30) {
        const yearStep = Math.max(1, Math.ceil(every / 12));
        this.months.forEach((m, i) => {
          const [year, month] = m.split("-").map(Number);
          if (month === 1 && year % yearStep === 0) ticks.push({ index: i, label: String(year) });
        });
      } else {
        const monthStep = every <= 1 ? 1 : every <= 3 ? 3 : 6;
        this.months.forEach((m, i) => {
          const [year, month] = m.split("-").map(Number);
          if ((month - 1) % monthStep === 0) {
            ticks.push({
              index: i,
              label: `${MONTH_NAMES[month - 1]} ${String(year).slice(2)}`,
            });
          }
        });
      }
      return ticks;
    },
    linePaths() {
      return this.series.map((s) => ({
        key: s.key,
        color: s.color,
        path: s.values
          .map((v, i) => `${i === 0 ? "M" : "L"}${this.xCenter(i)},${this.y(v || 0)}`)
          .join(""),
      }));
    },
    areaPath() {
      const values = this.series[0].values;
      if (!values.length) return "";
      const baseline = this.y(0);
      const top = values.map((v, i) => `L${this.xCenter(i)},${this.y(v || 0)}`).join("");
      return `M${this.xCenter(0)},${baseline}${top}L${this.xCenter(values.length - 1)},${baseline}Z`;
    },
    endLabels() {
      // Label the end of each line, dropping any label that would collide with a larger one
      const last = this.months.length - 1;
      if (last < 0) return [];
      const labels = this.series
        .map((s) => ({
          key: s.key,
          color: s.color,
          value: s.values[last] || 0,
          x: this.xCenter(last),
          y: this.y(s.values[last] || 0),
        }))
        .sort((a, b) => b.value - a.value);
      const kept = [];
      for (const label of labels) {
        if (kept.every((k) => Math.abs(k.y - label.y) >= 14)) kept.push(label);
      }
      return kept;
    },
    stackedColumns() {
      const barWidth = Math.max(Math.min(24, this.band * 0.72), 1);
      const gap = this.band > 6 ? 2 : 0;
      return this.months.map((_, i) => {
        const x = this.xCenter(i) - barWidth / 2;
        let base = 0;
        const segments = [];
        const visible = this.series.filter((s) => (s.values[i] || 0) > 0);
        visible.forEach((s, j) => {
          const value = s.values[i];
          const y0 = this.y(base);
          const y1 = this.y(base + value);
          base += value;
          // A surface gap separates stacked segments; only the top segment gets a rounded cap
          const bottom = j === 0 ? y0 : y0 - gap / 2;
          const top = j === visible.length - 1 ? y1 : y1 + gap / 2;
          if (bottom - top <= 0) return;
          segments.push({
            key: s.key,
            color: s.color,
            path: this.columnPath(x, top, barWidth, bottom - top, j === visible.length - 1),
          });
        });
        return segments;
      });
    },
    markerShapes() {
      return Object.fromEntries(
        this.series.map((s, i) => [s.key, MARKER_SHAPES[i % MARKER_SHAPES.length]]),
      );
    },
    tooltipSeries() {
      return this.mode === "stacked" ? [...this.series].reverse() : this.series;
    },
    tooltipStyle() {
      const x = this.xCenter(this.hoverIndex);
      const flip = x > this.width * 0.6;
      return flip
        ? { right: `${this.width - x + 12}px`, top: `${this.margin.top}px` }
        : { left: `${x + 12}px`, top: `${this.margin.top}px` };
    },
  },
  mounted() {
    this.measure();
    if (typeof ResizeObserver !== "undefined") {
      this.resizeObserver = new ResizeObserver(() => this.measure());
      this.resizeObserver.observe(this.$refs.container);
    }
  },
  beforeUnmount() {
    if (this.resizeObserver) this.resizeObserver.disconnect();
  },
  methods: {
    measure() {
      const width = this.$refs.container?.clientWidth;
      if (width) this.width = width;
    },
    xCenter(i) {
      return this.margin.left + this.band * (i + 0.5);
    },
    y(v) {
      return this.margin.top + this.plotHeight * (1 - (v || 0) / this.yTop);
    },
    columnPath(x, y, w, h, rounded) {
      const r = rounded ? Math.min(4, w / 2, h) : 0;
      return (
        `M${x},${y + h}` +
        `L${x},${y + r}` +
        (r ? `Q${x},${y} ${x + r},${y}` : "") +
        `L${x + w - r},${y}` +
        (r ? `Q${x + w},${y} ${x + w},${y + r}` : "") +
        `L${x + w},${y + h}Z`
      );
    },
    markerPath(key, x, y) {
      return shapePath(this.markerShapes[key], x, y);
    },
    formatTick(v) {
      return this.formatValue(v);
    },
    formatMonth(m) {
      if (!m) return "";
      const [year, month] = m.split("-").map(Number);
      return `${MONTH_NAMES[month - 1]} ${year}`;
    },
    onMouseMove(event) {
      const rect = event.currentTarget.getBoundingClientRect();
      const i = Math.floor((event.clientX - rect.left) / this.band);
      this.hoverIndex = Math.min(Math.max(i, 0), this.months.length - 1);
    },
  },
};
</script>

<style scoped>
svg {
  display: block;
  overflow: visible;
}

.grid line {
  stroke: #e9ecef;
}

.grid text,
.x-axis text {
  fill: #6c757d;
  font-size: 11px;
}

.end-label {
  fill: #343a40;
  font-size: 12px;
  font-weight: 600;
}

.crosshair line {
  stroke: #adb5bd;
}

.hit-area {
  fill: transparent;
  cursor: crosshair;
}

.chart-tooltip {
  pointer-events: none;
  min-width: 140px;
  z-index: 10;
}

.tabular-nums,
.grid text,
.x-axis text {
  font-variant-numeric: tabular-nums;
}
</style>
