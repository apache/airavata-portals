<template>
  <div class="w-full">
    <!-- Chart surface. Responsive via viewBox; the SVG scales to its container
         width while keeping a fixed aspect ratio. -->
    <div
      ref="surface"
      class="relative w-full"
      @mousemove="onMouseMove"
      @mouseleave="hoverIndex = null"
    >
      <svg
        :viewBox="`0 0 ${width} ${height}`"
        class="w-full"
        :style="{ height: 'auto' }"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        :aria-label="ariaLabel"
      >
        <!-- Horizontal gridlines + Y axis tick labels -->
        <g>
          <line
            v-for="tick in yTicks"
            :key="`grid-${tick.value}`"
            :x1="plot.left"
            :x2="plot.left + plot.width"
            :y1="tick.y"
            :y2="tick.y"
            stroke="var(--border)"
            stroke-width="1"
          />
          <text
            v-for="tick in yTicks"
            :key="`ylabel-${tick.value}`"
            :x="plot.left - 8"
            :y="tick.y + 4"
            text-anchor="end"
            font-size="11"
            fill="var(--muted-foreground)"
          >
            {{ tick.label }}
          </text>
        </g>
        <!-- X axis tick labels -->
        <g>
          <text
            v-for="tick in xTicks"
            :key="`xlabel-${tick.index}`"
            :x="tick.x"
            :y="plot.top + plot.height + 18"
            text-anchor="middle"
            font-size="11"
            fill="var(--muted-foreground)"
          >
            {{ tick.label }}
          </text>
        </g>
        <!-- One polyline per visible series -->
        <g>
          <polyline
            v-for="series in visibleSeries"
            :key="series.key"
            :points="series.points"
            fill="none"
            :stroke="series.color"
            stroke-width="2"
            stroke-linejoin="round"
            stroke-linecap="round"
          />
        </g>
        <!-- Hover guideline + per-series markers -->
        <g v-if="hoverIndex !== null">
          <line
            :x1="xForIndex(hoverIndex)"
            :x2="xForIndex(hoverIndex)"
            :y1="plot.top"
            :y2="plot.top + plot.height"
            stroke="var(--muted-foreground)"
            stroke-width="1"
            stroke-dasharray="3 3"
          />
          <circle
            v-for="series in visibleSeries"
            :key="`marker-${series.key}`"
            :cx="xForIndex(hoverIndex)"
            :cy="yForValue(series.values[hoverIndex])"
            r="3"
            :fill="series.color"
          />
        </g>
        <!-- Empty state -->
        <text
          v-if="buckets.length === 0"
          :x="width / 2"
          :y="height / 2"
          text-anchor="middle"
          font-size="13"
          fill="var(--muted-foreground)"
        >
          No data for the selected range.
        </text>
      </svg>
      <!-- HTML tooltip positioned over the SVG (rendered in DOM so text wraps
           and themed colors apply cleanly). -->
      <div
        v-if="hoverIndex !== null && tooltip"
        class="pointer-events-none absolute z-10 rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md"
        :style="tooltipStyle"
      >
        <div class="mb-1 font-medium">{{ tooltip.label }}</div>
        <div
          v-for="row in tooltip.rows"
          :key="row.key"
          class="flex items-center justify-between gap-3"
        >
          <span class="flex items-center gap-1.5">
            <span
              class="inline-block size-2 rounded-full"
              :style="{ backgroundColor: row.color }"
            />
            {{ row.label }}
          </span>
          <span class="font-medium tabular-nums">{{ row.value }}</span>
        </div>
      </div>
    </div>
    <!-- Legend doubling as on/off toggles. -->
    <div class="mt-3 flex flex-wrap gap-x-4 gap-y-2">
      <button
        v-for="series in series"
        :key="series.key"
        type="button"
        class="flex items-center gap-2 text-sm transition-opacity"
        :class="series.visible ? 'opacity-100' : 'opacity-40'"
        :aria-pressed="series.visible"
        @click="$emit('toggle-series', series.key)"
      >
        <span
          class="inline-block h-0.5 w-4 rounded-full"
          :style="{ backgroundColor: series.color }"
        />
        <span>{{ series.label }}</span>
        <span class="text-muted-foreground tabular-nums">{{
          series.total
        }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import moment from "moment";

// Hand-rolled, dependency-free SVG multi-line chart. Each `series` is a status
// line plotted across the time `buckets`; the legend doubles as on/off toggles
// (the parent owns visibility state and handles the `toggle-series` event).
export default {
  name: "experiment-statistics-chart",
  props: {
    // Time buckets: [{ start: Date|number, end: Date|number, label: string }]
    buckets: {
      type: Array,
      default: () => [],
    },
    // Series: [{ key, label, color, visible, values: number[], total }]
    series: {
      type: Array,
      default: () => [],
    },
  },
  emits: ["toggle-series"],
  data() {
    return {
      width: 800,
      height: 320,
      hoverIndex: null,
    };
  },
  computed: {
    plot() {
      const left = 44;
      const right = 16;
      const top = 12;
      const bottom = 32;
      return {
        left,
        top,
        width: this.width - left - right,
        height: this.height - top - bottom,
      };
    },
    visibleSeries() {
      return this.series
        .filter((s) => s.visible)
        .map((s) => ({
          ...s,
          points: this.pointsFor(s.values),
        }));
    },
    maxValue() {
      let max = 0;
      for (const s of this.series) {
        if (!s.visible) continue;
        for (const v of s.values) {
          if (v > max) max = v;
        }
      }
      // Always keep a non-zero axis so a flat zero line still renders sensibly.
      return max <= 0 ? 1 : max;
    },
    yTicks() {
      const tickCount = 4;
      const ticks = [];
      for (let i = 0; i <= tickCount; i++) {
        const value = Math.round((this.maxValue / tickCount) * i);
        ticks.push({
          value,
          label: this.formatCount(value),
          y: this.yForValue(value),
        });
      }
      return ticks;
    },
    xTicks() {
      const n = this.buckets.length;
      if (n === 0) return [];
      // Cap to ~6 labels to avoid crowding on long ranges.
      const maxLabels = 6;
      const step = Math.max(1, Math.ceil(n / maxLabels));
      const ticks = [];
      for (let i = 0; i < n; i += step) {
        ticks.push({
          index: i,
          x: this.xForIndex(i),
          label: this.buckets[i].label,
        });
      }
      // Ensure the last bucket is labeled.
      if (ticks.length && ticks[ticks.length - 1].index !== n - 1) {
        ticks.push({
          index: n - 1,
          x: this.xForIndex(n - 1),
          label: this.buckets[n - 1].label,
        });
      }
      return ticks;
    },
    ariaLabel() {
      const names = this.series
        .filter((s) => s.visible)
        .map((s) => s.label)
        .join(", ");
      return `Experiment counts over time for: ${names || "no series"}.`;
    },
    tooltip() {
      if (this.hoverIndex === null || !this.buckets[this.hoverIndex]) {
        return null;
      }
      const bucket = this.buckets[this.hoverIndex];
      return {
        label: this.tooltipLabel(bucket),
        rows: this.series
          .filter((s) => s.visible)
          .map((s) => ({
            key: s.key,
            label: s.label,
            color: s.color,
            value: s.values[this.hoverIndex] ?? 0,
          })),
      };
    },
    tooltipStyle() {
      if (this.hoverIndex === null) return {};
      // Position the tooltip near the hovered bucket, as a fraction of width so
      // it tracks the responsive SVG. Flip to the left past the midpoint.
      const fraction = this.xForIndex(this.hoverIndex) / this.width;
      const onRightHalf = fraction > 0.5;
      const style = { top: "8px" };
      if (onRightHalf) {
        style.right = `${(1 - fraction) * 100}%`;
        style.marginRight = "8px";
      } else {
        style.left = `${fraction * 100}%`;
        style.marginLeft = "8px";
      }
      return style;
    },
  },
  methods: {
    xForIndex(index) {
      const n = this.buckets.length;
      if (n <= 1) {
        return this.plot.left + this.plot.width / 2;
      }
      return this.plot.left + (this.plot.width * index) / (n - 1);
    },
    yForValue(value) {
      const ratio = value / this.maxValue;
      return this.plot.top + this.plot.height * (1 - ratio);
    },
    pointsFor(values) {
      return values
        .map((v, i) => `${this.xForIndex(i)},${this.yForValue(v)}`)
        .join(" ");
    },
    onMouseMove(event) {
      const n = this.buckets.length;
      if (n === 0) {
        this.hoverIndex = null;
        return;
      }
      const surface = this.$refs.surface;
      if (!surface) return;
      const rect = surface.getBoundingClientRect();
      // Map the pointer's pixel x into the SVG's user-space x, then to the
      // nearest bucket index.
      const svgX = ((event.clientX - rect.left) / rect.width) * this.width;
      const relative = (svgX - this.plot.left) / this.plot.width;
      const clamped = Math.min(1, Math.max(0, relative));
      this.hoverIndex = Math.round(clamped * (n - 1));
    },
    formatCount(value) {
      if (value >= 1e6) return (value / 1e6).toFixed(0) + "m";
      if (value >= 1e3) return (value / 1e3).toFixed(0) + "k";
      return String(value);
    },
    tooltipLabel(bucket) {
      const start = moment(bucket.start);
      const end = moment(bucket.end);
      // Sub-day buckets show the hour window; multi-day buckets show the date.
      if (end.diff(start, "hours") <= 24 && start.isSame(end, "day")) {
        return `${start.format("MMM D, HH:mm")}–${end.format("HH:mm")}`;
      }
      if (end.diff(start, "hours") <= 24) {
        return start.format("MMM D, HH:mm");
      }
      return start.format("MMM D, YYYY");
    },
  },
};
</script>
