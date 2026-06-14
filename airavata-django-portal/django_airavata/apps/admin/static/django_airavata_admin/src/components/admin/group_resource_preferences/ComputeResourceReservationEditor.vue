<template>
  <b-form>
    <b-form-group
      label="Reservation name"
      label-for="reservation-name"
      :invalid-feedback="nameValidationFeedback"
      :state="nameValidationState"
    >
      <b-form-input
        id="reservation-name"
        v-model="data.reservation_name"
        type="text"
        @input="nameInputBegins = true"
        :state="nameValidationState"
      />
    </b-form-group>
    <b-form-group
      label="Start Time"
      label-for="start-time"
      :invalid-feedback="getValidationFeedback('start_time')"
      :state="getValidationState('start_time')"
    >
      <flat-pickr
        id="start-time"
        class="form-control"
        :model-value="startTimeAsString"
        :config="startTimeConfig"
        @update:model-value="data.start_time = stringToDate($event)"
      />
    </b-form-group>
    <b-form-group
      label="End Time"
      label-for="end-time"
      :invalid-feedback="getValidationFeedback('end_time')"
      :state="getValidationState('end_time')"
    >
      <flat-pickr
        id="end-time"
        :class="{
          'form-control': true,
          'is-invalid': getValidationState('end_time'),
        }"
        :model-value="endTimeAsString"
        :config="endTimeConfig"
        @update:model-value="data.end_time = stringToDate($event)"
      />
    </b-form-group>
    <b-form-group
      label="Queues"
      label-for="queues"
      :invalid-feedback="getValidationFeedback('queue_names')"
      :state="getValidationState('queue_names')"
    >
      <b-form-checkbox-group
        id="queues"
        v-model="data.queue_names"
        :options="queueNameOptions"
        :state="getValidationState('queue_names')"
      />
    </b-form-group>
  </b-form>
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
