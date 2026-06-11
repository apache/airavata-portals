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
      <datetime
        id="start-time"
        type="datetime"
        :value="startTimeAsString"
        input-class="form-control"
        :format="{
          year: 'numeric',
          month: '2-digit',
          day: 'numeric',
          hour: 'numeric',
          minute: '2-digit',
          timeZoneName: 'short',
        }"
        :phrases="{ ok: 'Continue', cancel: 'Exit' }"
        :hour-step="1"
        :minute-step="30"
        :week-start="7"
        use12-hour
        auto
        @input="data.start_time = stringToDate($event)"
      ></datetime>
    </b-form-group>
    <b-form-group
      label="End Time"
      label-for="end-time"
      :invalid-feedback="getValidationFeedback('end_time')"
      :state="getValidationState('end_time')"
    >
      <datetime
        id="end-time"
        type="datetime"
        :value="endTimeAsString"
        :input-class="{
          'form-control': true,
          'is-invalid': getValidationState('end_time'),
        }"
        :format="{
          year: 'numeric',
          month: '2-digit',
          day: 'numeric',
          hour: 'numeric',
          minute: '2-digit',
          timeZoneName: 'short',
        }"
        :phrases="{ ok: 'Continue', cancel: 'Exit' }"
        :hour-step="1"
        :minute-step="30"
        :week-start="7"
        :min-datetime="startTimeAsString"
        use12-hour
        auto
        @input="data.end_time = stringToDate($event)"
      ></datetime>
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
import { Datetime } from "vue-datetime";
import "vue-datetime/dist/vue-datetime.css";

export default {
  name: "compute-resource-reservation-editor",
  mixins: [mixins.VModelMixin],
  components: {
    datetime: Datetime,
  },
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
  created() {
    this.$on("input", this.valuesChanged);
  },
  computed: {
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
