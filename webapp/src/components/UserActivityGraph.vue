<template>
  <div class="activity-graph-container" :class="{ compact: compact }">
    <div v-if="isLoading" class="text-center p-4">
      <font-awesome-icon :icon="['fa', 'sync']" spin />
    </div>
    <div v-else-if="showErrors && error" class="alert alert-danger">
      {{ error }}
    </div>
    <div v-else-if="!error" class="heatmap-wrapper">
      <h5 v-if="title">{{ title }}</h5>
      <div class="heatmap-container">
        <div class="months-labels">
          <span
            v-for="(month, index) in monthLabels"
            :key="index"
            class="month-label"
            :style="{
              position: 'absolute',
              left: month.weekIndex * (cellSize + cellGap) + 10 + 'px',
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
      </div>
      <div class="legend">
        <div class="legend-scale">
          <div class="legend-label">0</div>
          <div class="legend-gradient"></div>
          <div class="legend-label">10+</div>
        </div>
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
    showErrors: {
      type: Boolean,
      default: false,
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
      return this.compact ? 10 : 10;
    },
    cellGap() {
      return this.compact ? 2 : 2;
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
        month: "long",
        day: "numeric",
      });
      tooltip.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 2px;">${count} contribution${
          count !== 1 ? "s" : ""
        }</div>
        <div style="font-size: 11px; opacity: 0.9;">${formattedDate}</div>
      `;
      tooltip.style.cssText = `
        background: linear-gradient(135deg, #00897b 0%, #00695c 100%);
        color: white;
        padding: 10px 14px;
        border-radius: 10px;
        font-size: 12px;
        z-index: 9999;
        white-space: nowrap;
        pointer-events: none;
        box-shadow: 0 6px 16px rgba(0, 137, 123, 0.4);
      `;

      document.body.appendChild(tooltip);
      this.tooltipElement = tooltip;

      this.popperInstance = createPopper(event.target, tooltip, {
        placement: "top",
        modifiers: [
          {
            name: "offset",
            options: {
              offset: [0, 12],
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
}

.activity-graph-container.compact {
  overflow-x: visible;
}

.heatmap-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.heatmap-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  overflow: hidden;
  padding: 15px;
  background: #fafafa;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
}

.months-labels {
  position: relative;
  height: 20px;
  font-size: 11px;
  color: #00695c;
  font-weight: 700;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  min-width: fit-content;
}

.month-label {
  display: inline-block;
  font-size: 10px;
  min-width: 35px;
}

.heatmap-grid {
  display: flex;
  gap: 2px;
  flex-wrap: nowrap;
  padding: 0 10px;
  min-width: fit-content;
}

.week-column {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
}

.day-cell {
  width: 10px;
  height: 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.activity-graph-container.compact .day-cell {
  width: 10px;
  height: 10px;
}

.day-cell:hover {
  transform: scale(1.25) rotate(5deg);
  box-shadow: 0 4px 12px rgba(0, 137, 123, 0.5);
  z-index: 100;
  border-color: transparent;
}

.intensity-0 {
  background-color: #e0f2f1;
  border-color: #b2dfdb;
}

.intensity-1 {
  background-color: #80cbc4;
}

.intensity-2 {
  background-color: #26a69a;
}

.intensity-3 {
  background-color: #00897b;
}

.intensity-4 {
  background-color: #00695c;
}

.legend {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 5px;
}

.legend-scale {
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  padding: 8px 16px;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.legend-gradient {
  width: 150px;
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(
    to right,
    #e0f2f1 0%,
    #80cbc4 25%,
    #26a69a 50%,
    #00897b 75%,
    #00695c 100%
  );
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
}

.legend-label {
  font-size: 11px;
  font-weight: 600;
  color: #00695c;
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

  .legend-gradient {
    width: 100px;
  }
}
</style>
