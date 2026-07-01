<template>
  <!-- pt-6 leaves room for the value label that floats above the thumb -->
  <div class="pt-6">
    <SliderRoot
      :model-value="[sliderValue]"
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
      <SliderThumb
        class="relative block h-4 w-4 rounded-full border border-primary bg-background shadow focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1"
      >
        <!-- reka-ui has no built-in tooltip; render the always-visible value
             label above the thumb, formatted via tooltipFormatter -->
        <span
          class="pointer-events-none absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs text-muted-foreground"
        >
          {{ tooltipFormatter(sliderValue) }}
        </span>
      </SliderThumb>
    </SliderRoot>
  </div>
</template>

<script>
import { InputEditorMixin } from "django-airavata-workspace-plugin-api";
import { SliderRange, SliderRoot, SliderThumb, SliderTrack } from "reka-ui";

export default {
  name: "slider-input-editor",
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
  },
  components: {
    SliderRoot,
    SliderTrack,
    SliderRange,
    SliderThumb,
  },
  data() {
    return {
      sliderValue: null,
    };
  },
  created() {
    this.initializeSliderValue();
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
  },
  methods: {
    initializeSliderValue() {
      this.sliderValue = this.parseValue(this.data);
      // If parsing the value resulted in it changing (failed to parse so
      // initialized to the 'sliderMin'), update the value
      if (this.data !== this.formatValue(this.sliderValue)) {
        this.onChange(this.sliderValue);
      }
    },
    parseValue(value) {
      // Just remove any percentage signs
      const result = value ? parseFloat(value.replaceAll("%", "")) : NaN;
      return !isNaN(result) ? result : this.sliderMin;
    },
    // reka-ui's modelValue is always a number[]; unwrap the single value.
    onUpdate(value) {
      this.sliderValue = value[0];
      this.onChange(value[0]);
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
      if (this.valueFormat) {
        if (this.valueFormat === "percentage") {
          return `${value}%`;
        }
      } else if ("valueFormat" in this.editorConfig) {
        if (this.editorConfig.valueFormat.percentage) {
          return `${value}%`;
        }
      }
      return String(value);
    },
  },
  watch: {
    data() {
      this.initializeSliderValue();
    },
  },
};
</script>
