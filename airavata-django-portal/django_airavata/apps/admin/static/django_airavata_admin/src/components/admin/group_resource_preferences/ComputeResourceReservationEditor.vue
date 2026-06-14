<template>
  <form class="space-y-4">
    <div class="space-y-1.5">
      <Label for="reservation-name">Reservation name</Label>
      <Input
        id="reservation-name"
        v-model="data.reservation_name"
        type="text"
        @input="nameInputBegins = true"
        :aria-invalid="nameValidationState === false"
      />
      <p v-if="nameValidationState === false" class="text-sm text-destructive">
        {{ nameValidationFeedback }}
      </p>
    </div>
    <div class="space-y-1.5">
      <Label for="start-time">Start Time</Label>
      <flat-pickr
        id="start-time"
        class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
        :model-value="startTimeAsString"
        :config="startTimeConfig"
        @update:model-value="data.start_time = stringToDate($event)"
      />
      <p
        v-if="getValidationState('start_time') === false"
        class="text-sm text-destructive"
      >
        {{ getValidationFeedback("start_time") }}
      </p>
    </div>
    <div class="space-y-1.5">
      <Label for="end-time">End Time</Label>
      <flat-pickr
        id="end-time"
        class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
        :class="{ 'border-destructive': getValidationState('end_time') }"
        :model-value="endTimeAsString"
        :config="endTimeConfig"
        @update:model-value="data.end_time = stringToDate($event)"
      />
      <p
        v-if="getValidationState('end_time') === false"
        class="text-sm text-destructive"
      >
        {{ getValidationFeedback("end_time") }}
      </p>
    </div>
    <div class="space-y-1.5">
      <Label>Queues</Label>
      <div class="flex flex-col gap-2">
        <label
          v-for="queueName in queueNameOptions"
          :key="queueName"
          class="flex items-center gap-2 text-sm"
        >
          <Checkbox
            :model-value="data.queue_names.includes(queueName)"
            @update:model-value="toggleQueue(queueName, $event)"
          />
          {{ queueName }}
        </label>
      </div>
      <p
        v-if="getValidationState('queue_names') === false"
        class="text-sm text-destructive"
      >
        {{ getValidationFeedback("queue_names") }}
      </p>
    </div>
  </form>
</template>

<script>
import { mixins, utils } from "django-airavata-common-ui";

export default {
  name: "compute-resource-reservation-editor",
  // <flat-pickr> is registered globally in main.js (vue-flatpickr-component),
  // replacing the Vue 2-only vue-datetime <datetime> picker.
  mixins: [mixins.VModelMixin],
  props: {
    queues: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      nameInputBegins: false,
    };
  },
  watch: {
    // Vue 3 removed component $on; this replaces the previous
    // `this.$on("input", this.valuesChanged)` self-listener: re-validate
    // whenever the bound model changes.
    data: {
      handler() {
        this.valuesChanged();
      },
      deep: true,
    },
  },
  computed: {
    startTimeConfig() {
      return {
        enableTime: true,
        dateFormat: "Z",
        altInput: true,
        altFormat: "Y-m-d h:i K",
        minuteIncrement: 30,
        time_24hr: false,
      };
    },
    endTimeConfig() {
      return {
        enableTime: true,
        dateFormat: "Z",
        altInput: true,
        altFormat: "Y-m-d h:i K",
        minuteIncrement: 30,
        time_24hr: false,
        minDate: this.startTimeAsString,
      };
    },
    startTimeAsString() {
      return this.data.start_time.toISOString();
    },
    endTimeAsString() {
      return this.data.end_time.toISOString();
    },
    nameValidationFeedback() {
      return this.getValidationFeedback("reservation_name");
    },
    nameValidationState() {
      if (this.nameInputBegins === false) {
        return null;
      }
      return this.getValidationState("reservation_name");
    },
    queueNameOptions() {
      return this.queues.slice().sort();
    },
  },
  methods: {
    toggleQueue(queueName, checked) {
      if (checked) {
        if (!this.data.queue_names.includes(queueName)) {
          this.data.queue_names.push(queueName);
        }
      } else {
        const index = this.data.queue_names.indexOf(queueName);
        if (index >= 0) {
          this.data.queue_names.splice(index, 1);
        }
      }
    },
    stringToDate(datetimeString) {
      return new Date(datetimeString);
    },
    getValidationFeedback: function (properties) {
      return utils.getProperty(this.data.validate(), properties);
    },
    getValidationState: function (properties) {
      return this.getValidationFeedback(properties) ? false : null;
    },
    valuesChanged() {
      const validationResults = this.data.validate();
      if (Object.keys(validationResults).length === 0) {
        this.$emit("valid");
      } else {
        this.$emit("invalid");
      }
    },
  },
};
</script>
