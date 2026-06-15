<script setup>
import { Area, Axis, CurveType, Line } from "@unovis/ts";
import { VisArea, VisAxis, VisLine, VisXYContainer } from "@unovis/vue";
import { useMounted } from "@vueuse/core";
import { useId } from "reka-ui";
import { computed, ref } from "vue";
import { cn } from "@/lib/utils";
import { ChartCrosshair, ChartLegend, defaultColors } from "../chart";

const props = defineProps({
  // The source data, where each entry is a dictionary.
  data: { type: Array, required: true },
  // Categories selected from the data; populate the legend and tooltip.
  categories: { type: Array, required: true },
  // The key used to map the data to the x axis.
  index: { type: String, required: true },
  // Override the default colors.
  colors: { type: Array, required: false },
  // Margin of the container.
  margin: {
    type: Object,
    required: false,
    default: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
  },
  // Opacity of non-selected series.
  filterOpacity: { type: Number, required: false, default: 0.2 },
  // Function to format the X tick label.
  xFormatter: { type: Function, required: false },
  // Function to format the Y tick label.
  yFormatter: { type: Function, required: false },
  showXAxis: { type: Boolean, required: false, default: true },
  showYAxis: { type: Boolean, required: false, default: true },
  showTooltip: { type: Boolean, required: false, default: true },
  showLegend: { type: Boolean, required: false, default: true },
  showGridLine: { type: Boolean, required: false, default: true },
  // Render a custom tooltip component.
  customTooltip: { type: null, required: false },
  // Curve interpolation type. Defaults to a smooth monotone curve.
  curveType: { type: String, required: false, default: CurveType.MonotoneX },
  // Controls the visibility of the translucent area gradient fill.
  showGradient: { type: Boolean, required: false, default: true },
});

const emits = defineEmits(["legendItemClick"]);

const chartRef = useId();

const index = computed(() => props.index);
const colors = computed(() =>
  props.colors?.length ? props.colors : defaultColors(props.categories.length),
);

const legendItems = ref(
  props.categories.map((category, i) => ({
    name: category,
    color: colors.value[i],
    inactive: false,
  })),
);

const isMounted = useMounted();

function handleLegendItemClick(d, i) {
  emits("legendItemClick", d, i);
}
</script>

<template>
  <div :class="cn('flex h-full w-full flex-col items-end', $attrs.class ?? '')">
    <ChartLegend
      v-if="showLegend"
      v-model:items="legendItems"
      @legend-item-click="handleLegendItemClick"
    />

    <VisXYContainer
      :style="{ height: isMounted ? '100%' : 'auto' }"
      :margin="{ left: 20, right: 20 }"
      :data="data"
    >
      <svg width="0" height="0">
        <defs>
          <linearGradient
            v-for="(color, i) in colors"
            :id="`${chartRef}-color-${i}`"
            :key="i"
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >
            <template v-if="showGradient">
              <stop offset="5%" :stop-color="color" stop-opacity="0.4" />
              <stop offset="95%" :stop-color="color" stop-opacity="0" />
            </template>
            <template v-else>
              <stop offset="0%" :stop-color="color" />
            </template>
          </linearGradient>
        </defs>
      </svg>

      <ChartCrosshair
        v-if="showTooltip"
        :colors="colors"
        :items="legendItems"
        :index="index"
        :custom-tooltip="customTooltip"
      />

      <template v-for="(category, i) in categories" :key="category">
        <VisArea
          :x="(d, i) => i"
          :y="(d) => d[category]"
          color="auto"
          :curve-type="curveType"
          :attributes="{
            [Area.selectors.area]: {
              fill: `url(#${chartRef}-color-${i})`,
            },
          }"
          :opacity="
            legendItems.find((item) => item.name === category)?.inactive
              ? filterOpacity
              : 1
          "
        />
      </template>

      <template v-for="(category, i) in categories" :key="category">
        <VisLine
          :x="(d, i) => i"
          :y="(d) => d[category]"
          :color="colors[i]"
          :curve-type="curveType"
          :attributes="{
            [Line.selectors.line]: {
              opacity: legendItems.find((item) => item.name === category)
                ?.inactive
                ? filterOpacity
                : 1,
            },
          }"
        />
      </template>

      <VisAxis
        v-if="showXAxis"
        type="x"
        :tick-format="xFormatter ?? ((v) => data[v]?.[index])"
        :grid-line="false"
        :tick-line="false"
        tick-text-color="var(--muted-foreground)"
      />
      <VisAxis
        v-if="showYAxis"
        type="y"
        :tick-line="false"
        :tick-format="yFormatter"
        :domain-line="false"
        :grid-line="showGridLine"
        :attributes="{
          [Axis.selectors.grid]: {
            class: 'text-muted',
          },
        }"
        tick-text-color="var(--muted-foreground)"
      />

      <slot />
    </VisXYContainer>
  </div>
</template>
