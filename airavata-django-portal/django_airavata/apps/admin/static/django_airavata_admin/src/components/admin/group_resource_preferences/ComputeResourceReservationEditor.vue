<template>
  <form>
    <div class="mb-3">
      <label for="reservation-name" class="form-label">Reservation name</label>
      <input class="form-control"
        id="reservation-name"
        v-model="data.reservation_name"
        type="text"
        @input="nameInputBegins = true"
        :class="{ 'is-invalid': nameValidationState === false }"
      />
      <div class="invalid-feedback" v-if="nameValidationFeedback">{{ nameValidationFeedback }}</div>
    </div>
    <div class="mb-3">
      <label for="start-time" class="form-label">Start Time</label>
      <flat-pickr
        id="start-time"
        :value="startTimeAsString"
        :config="startTimeConfig"
        class="form-control"
        @on-change="onStartTimeChange"
      />
      <div class="invalid-feedback d-block" v-if="getValidationFeedback('start_time')">
        {{ getValidationFeedback('start_time') }}
      </div>
    </div>
    <div class="mb-3">
      <label for="end-time" class="form-label">End Time</label>
      <flat-pickr
        id="end-time"
        :value="endTimeAsString"
        :config="endTimeConfig"
        :class="{ 'form-control': true, 'is-invalid': getValidationState('end_time') === false }"
        @on-change="onEndTimeChange"
      />
      <div class="invalid-feedback d-block" v-if="getValidationFeedback('end_time')">
        {{ getValidationFeedback('end_time') }}
      </div>
    </div>
    <div class="mb-3">
      <label class="form-label">Queues</label>
      <div
        v-for="queue in queueNameOptions"
        :key="queue"
        class="form-check"
      >
        <input
          class="form-check-input"
          type="checkbox"
          :id="'queue-' + queue"
          :value="queue"
          v-model="data.queue_names"
        />
        <label class="form-check-label" :for="'queue-' + queue">{{ queue }}</label>
      </div>
      <div class="invalid-feedback d-block" v-if="getValidationFeedback('queue_names')">
        {{ getValidationFeedback('queue_names') }}
      </div>
    </div>
  </form>
</template>

<script>
import { mixins, utils } from "django-airavata-common-ui";
import FlatPickr from "vue-flatpickr-component";

export default {
  name: "compute-resource-reservation-editor",
  mixins: [mixins.VModelMixin],
  components: {
    FlatPickr,
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
  computed: {
    startTimeAsString() {
      return this.data.start_time.toISOString();
    },
    endTimeAsString() {
      return this.data.end_time.toISOString();
    },
    startTimeConfig() {
      return {
        enableTime: true,
        dateFormat: "Z",
        altInput: true,
        altFormat: "m/d/Y h:i K T",
        minuteIncrement: 30,
      };
    },
    endTimeConfig() {
      return {
        enableTime: true,
        dateFormat: "Z",
        altInput: true,
        altFormat: "m/d/Y h:i K T",
        minuteIncrement: 30,
        minDate: this.startTimeAsString,
      };
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
    onStartTimeChange(selectedDates) {
      if (selectedDates.length > 0) {
        this.data.start_time = selectedDates[0];
        this.valuesChanged();
      }
    },
    onEndTimeChange(selectedDates) {
      if (selectedDates.length > 0) {
        this.data.end_time = selectedDates[0];
        this.valuesChanged();
      }
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
