<template>
  <div class="activity-graph-container" :class="{ compact: compact }">
    <h5 v-if="title">{{ title }}</h5>
    <div v-if="isLoading" class="text-center p-4">
      <font-awesome-icon :icon="['fa', 'sync']" spin /> Loading activity...
    </div>
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>
    <div v-else class="heatmap-container">
      <div class="months-labels">
        <span
          v-for="(month, index) in monthLabels"
          :key="index"
          class="month-label"
          :style="{
            position: 'absolute',
            left: month.weekIndex * (cellSize + 3) + (compact ? 8 : 10) + 'px',
          }"
        >
          {{ month.month }}
        </span>
      </div>
      <div class="heatmap-grid">
        <div v-for="(week, weekIndex) in weeks" :key="weekIndex" class="week-column">
          <div
            v-for="(day, dayIndex) in week"
            v-show="day.count !== -1"
            :key="dayIndex"
            :class="['day-cell', getIntensityClass(day.count)]"
            :data-date="day.date"
            @mouseenter="showTooltip($event, day.date, day.count)"
            @mouseleave="hideTooltip"
          ></div>
        </div>
      </div>
      <div class="legend">
        <span>Less</span>
        <div class="legend-colors">
          <div class="day-cell intensity-0"></div>
          <div class="day-cell intensity-1"></div>
          <div class="day-cell intensity-2"></div>
          <div class="day-cell intensity-3"></div>
          <div class="day-cell intensity-4"></div>
        </div>
        <span>More</span>
      </div>
    </div>
  </div>
</template>

<script>
import { fetchUserActivity } from "@/server_fetch_utils";
import { createPopper } from "@popperjs/core";

export default {
  name: "UserActivityGraph",
  props: {
    userId: {
      type: String,
      default: null,
    },
    combined: {
      type: Boolean,
      default: false,
    },
    title: {
      type: String,
      default: "",
    },
    compact: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      activityData: {},
      isLoading: true,
      error: null,
      weeks: [],
      monthLabels: [],
      popperInstance: null,
      tooltipElement: null,
    };
  },
  computed: {
    cellSize() {
      return this.compact ? 7 : 10;
    },
    cellGap() {
      return this.compact ? 9 : 13;
    },
  },
  async mounted() {
    await this.fetchActivityData();
    this.generateCalendar();
  },
  beforeUnmount() {
    this.destroyTooltip();
  },
  methods: {
    async fetchActivityData() {
      this.isLoading = true;
      this.error = null;
      try {
        const data = await fetchUserActivity(this.userId);
        this.activityData = data.data;
      } catch (error) {
        console.error("Error fetching activity data:", error);
        this.error = "Failed to load activity data";
      } finally {
        this.isLoading = false;
      }
    },
    generateCalendar() {
      const weeks = [];
      const monthLabels = [];
      const today = new Date();
      today.setHours(23, 59, 59, 999);

      const maxWeeks = this.compact ? 36 : 54;
      const startDate = new Date(today);
      startDate.setDate(startDate.getDate() - maxWeeks * 7);
      startDate.setDate(startDate.getDate() - startDate.getDay());

      let currentDate = new Date(startDate);
      let currentWeek = [];
      let weekIndex = 0;
      let lastMonth = -1;

      while (currentDate <= today) {
        const dateStr = currentDate.toISOString().split("T")[0];
        const count = this.activityData[dateStr] || 0;
        const dayOfWeek = currentDate.getDay();

        currentWeek.push({
          date: dateStr,
          count: count,
        });

        const month = currentDate.getMonth();
        if (month !== lastMonth && dayOfWeek === 0) {
          if (
            monthLabels.length === 0 ||
            weekIndex - monthLabels[monthLabels.length - 1].weekIndex >= 4
          ) {
            monthLabels.push({
              month: currentDate.toLocaleDateString("en-US", { month: "short" }),
              weekIndex: weekIndex,
            });
            lastMonth = month;
          }
        }

        if (dayOfWeek === 6) {
          weeks.push([...currentWeek]);
          currentWeek = [];
          weekIndex++;
        }

        currentDate.setDate(currentDate.getDate() + 1);
      }

      if (currentWeek.length > 0) {
        while (currentWeek.length < 7) {
          currentWeek.push({ date: "", count: -1 });
        }
        weeks.push(currentWeek);
      }

      while (weeks.length > maxWeeks) {
        weeks.shift();
      }

      this.weeks = weeks;
      this.monthLabels = monthLabels;
    },
    getIntensityClass(count) {
      if (count === 0) return "intensity-0";
      if (count <= 2) return "intensity-1";
      if (count <= 5) return "intensity-2";
      if (count <= 10) return "intensity-3";
      return "intensity-4";
    },
    showTooltip(event, date, count) {
      if (!date) return;

      this.destroyTooltip();

      const tooltip = document.createElement("div");
      tooltip.className = "activity-tooltip";
      const formattedDate = new Date(date).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
      tooltip.textContent = `${count} contribution${count !== 1 ? "s" : ""} on ${formattedDate}`;
      tooltip.style.cssText = `
        background: #24292f;
        color: white;
        padding: 6px 10px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 9999;
        white-space: nowrap;
        pointer-events: none;
      `;

      document.body.appendChild(tooltip);
      this.tooltipElement = tooltip;

      this.popperInstance = createPopper(event.target, tooltip, {
        placement: "top",
        modifiers: [
          {
            name: "offset",
            options: {
              offset: [0, 8],
            },
          },
        ],
      });
    },
    hideTooltip() {
      this.destroyTooltip();
    },
    destroyTooltip() {
      if (this.popperInstance) {
        this.popperInstance.destroy();
        this.popperInstance = null;
      }
      if (this.tooltipElement) {
        this.tooltipElement.remove();
        this.tooltipElement = null;
      }
    },
  },
};
</script>

<style scoped>
.activity-graph-container {
  margin: 20px 0;
  width: 100%;
  overflow: hidden;
}

.activity-graph-container.compact {
  overflow-x: visible;
}

.heatmap-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: fit-content;
  min-width: 100%;
}

.activity-graph-container.compact .heatmap-container {
  transform: scale(1);
  min-width: fit-content;
}

.months-labels {
  position: relative;
  height: 20px;
  font-size: 11px;
  color: #586069;
  margin-bottom: 4px;
}

.month-label {
  display: inline-block;
  font-size: 10px;
  min-width: 35px;
}

.heatmap-grid {
  display: flex;
  gap: 3px;
  flex-wrap: nowrap;
  padding: 0 10px;
}

.week-column {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex-shrink: 0;
}

.day-cell {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  cursor: pointer;
  transition: transform 0.1s ease;
}

.activity-graph-container.compact .day-cell {
  width: 7px;
  height: 7px;
}

.day-cell:hover {
  outline: 2px solid rgba(27, 31, 35, 0.3);
  outline-offset: 1px;
  transform: scale(1.15);
  z-index: 100;
}

.intensity-0 {
  background-color: #ebedf0;
}

.intensity-1 {
  background-color: #9be9a8;
}

.intensity-2 {
  background-color: #40c463;
}

.intensity-3 {
  background-color: #30a14e;
}

.intensity-4 {
  background-color: #216e39;
}

.legend {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  font-size: 11px;
  color: #586069;
  margin-top: 8px;
  padding-right: 10px;
}

.legend-colors {
  display: flex;
  gap: 3px;
}

.legend .day-cell {
  pointer-events: none;
}

.activity-graph-container.compact .day-cell {
  width: 9px;
  height: 9px;
}

.activity-graph-container.compact .heatmap-grid {
  gap: 2px;
  padding: 0 8px;
}

.activity-graph-container.compact .week-column {
  gap: 2px;
}

.activity-graph-container.compact .month-label {
  font-size: 9px;
  min-width: 30px;
}

@media (max-width: 900px) {
  .day-cell {
    width: 10px;
    height: 10px;
  }

  .heatmap-grid {
    gap: 2px;
  }

  .week-column {
    gap: 2px;
  }

  .month-label {
    min-width: 32px;
  }
}

@media (max-width: 700px) {
  .day-cell {
    width: 7px;
    height: 7px;
  }

  .month-label {
    font-size: 8px;
    min-width: 28px;
  }
}
</style>
