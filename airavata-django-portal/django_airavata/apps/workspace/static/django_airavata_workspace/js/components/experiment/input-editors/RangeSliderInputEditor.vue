<template>
  <!-- pt-6 leaves room for the value labels that float above the thumbs -->
  <div class="pt-6">
    <SliderRoot
      :model-value="sliderValues"
      :min="sliderMin"
      :max="sliderMax"
      :step="sliderStep"
      :disabled="readOnly"
      class="relative flex h-5 w-full touch-none select-none items-center data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
      @update:model-value="onUpdate"
    >
      <SliderTrack class="relative h-1 w-full grow rounded-full bg-muted">
        <SliderRange class="absolute h-full rounded-full bg-primary" />
      </SliderTrack>
      <!-- Two ordered thumbs; reka-ui prevents them from crossing by default,
           replacing the old enable-cross=false behavior. -->
      <SliderThumb
        v-for="(thumbValue, index) in sliderValues"
        :key="index"
        class="relative block h-4 w-4 rounded-full border border-primary bg-background shadow focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1"
      >
        <!-- reka-ui has no built-in tooltip; render the always-visible value
             label above each thumb, formatted via tooltipFormatter -->
        <span
          class="pointer-events-none absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs text-muted-foreground"
        >
          {{ tooltipFormatter(thumbValue) }}
        </span>
      </SliderThumb>
    </SliderRoot>
  </div>
</template>

<script>
import { InputEditorMixin } from "django-airavata-workspace-plugin-api";
import { SliderRange, SliderRoot, SliderThumb, SliderTrack } from "reka-ui";

export default {
  name: "range-slider-input-editor",
  mixins: [InputEditorMixin],
  props: {
    value: {
      type: String,
    },
    min: Number,
    max: Number,
    step: Number,
    valueFormat: {
      type: String,
      validator(value) {
        return ["percentage"].indexOf(value) !== -1;
      },
    },
    displayFormat: {
      type: String,
      validator(value) {
        return ["percentage"].indexOf(value) !== -1;
      },
    },
    delimiter: String,
  },
  components: {
    SliderRoot,
    SliderTrack,
    SliderRange,
    SliderThumb,
  },
  data() {
    return {
      sliderValues: null,
    };
  },
  created() {
    this.initializeSliderValues();
  },
  computed: {
    sliderMin: function () {
      return typeof this.min !== "undefined"
        ? this.min
        : "min" in this.editorConfig
          ? this.editorConfig.min
          : 0;
    },
    sliderMax: function () {
      return typeof this.max !== "undefined"
        ? this.max
        : "max" in this.editorConfig
          ? this.editorConfig.max
          : 100;
    },
    sliderStep: function () {
      return typeof this.step !== "undefined"
        ? this.step
        : "step" in this.editorConfig
          ? this.editorConfig.step
          : 1;
    },
    sliderDelimiter() {
      return this.delimiter
        ? this.delimiter
        : "delimiter" in this.editorConfig
          ? this.editorConfig.delimiter
          : "-";
    },
  },
  methods: {
    initializeSliderValues() {
      this.sliderValues = this.parseValue(this.data);
      // If parsing the value resulted in it changing (failed to parse so
      // initialized to ['sliderMin', 'sliderMax']), update the value
      if (this.data !== this.formatValue(this.sliderValues)) {
        this.onChange(this.sliderValues);
      }
    },
    parseValue(value) {
      // Just remove any percentage signs
      const result = value
        ? value.replaceAll("%", "").split(this.sliderDelimiter).map(parseFloat)
        : [];
      return result.length === 2 && !isNaN(result[0]) && !isNaN(result[1])
        ? result
        : [this.sliderMin, this.sliderMax];
    },
    // reka-ui's modelValue is the two-element number[] of thumb positions.
    onUpdate(value) {
      this.sliderValues = value;
      this.onChange(value);
    },
    onChange(value) {
      this.data = this.formatValue(value);
      this.valueChanged();
    },
    tooltipFormatter(value) {
      if (this.displayFormat) {
        if (this.displayFormat === "percentage") {
          return `${value}%`;
        }
      } else if ("displayFormat" in this.editorConfig) {
        if (this.editorConfig.displayFormat.percentage) {
          return `${value}%`;
        }
      }
      return value;
    },
    formatValue(value) {
      let values = value.map(String);
      if (this.valueFormat) {
        if (this.valueFormat === "percentage") {
          values = values.map((v) => `${v}%`);
        }
      } else if ("valueFormat" in this.editorConfig) {
        if (this.editorConfig.valueFormat.percentage) {
          values = values.map((v) => `${v}%`);
        }
      }
      return values.join(this.sliderDelimiter);
    },
  },
  watch: {
    data() {
      this.initializeSliderValues();
    },
  },
};
</script>
