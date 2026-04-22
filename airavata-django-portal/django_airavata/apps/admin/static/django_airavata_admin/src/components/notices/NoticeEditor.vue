<template>
  <div>
    <div class="d-flex">
      <slot name="title"> </slot>
    </div>
    <form novalidate @input="onUserInput">
      <form-group
        label="Notice Title"
        label-for="notice-title"
        :invalid-feedback="getValidationFeedback('title')"
        :state="getValidationState('title')"
      >
        <input
          id="notice-title"
          v-model="data.title"
          class="form-control"
          type="text"
          required
          placeholder="Notice Title"
          :state="getValidationState('title')"
        />
      </form-group>

      <form-group
        label="Notice Message"
        label-for="notice-message"
        :invalid-feedback="getValidationFeedback('notificationMessage')"
        :state="getValidationState('notificationMessage')"
      >
        <textarea
          id="notice-message"
          v-model="data.notificationMessage"
          class="form-control"
          type="text"
          required
          placeholder="Notice Message"
          :state="getValidationState('notificationMessage')"
          :rows="3"
        ></textarea>
      </form-group>

      <div class="mb-3">
        <label for="publish-date" class="form-label">Publish Date</label>
        <flat-pickr
          id="publish-date"
          v-model="inputPublishedTime"
          :config="dateTimeConfig"
          class="form-control"
        />
      </div>

      <div class="mb-3">
        <label for="expiration-date" class="form-label">Expiration Date</label>
        <flat-pickr
          id="expiration-date"
          v-model="inputExpirationTime"
          :config="expirationDateConfig"
          class="form-control"
        />
      </div>

      <form-group
        label="Priority"
        label-for="priority"
        :invalid-feedback="getValidationFeedback('priority')"
        :state="getValidationState('priority')"
      >
        <select
          id="priority"
          v-model="data.priority"
          class="form-select"
          :options="select.options"
          :state="getValidationState('priority')"
        ></select>
      </form-group>

      <div class="mb-3">
        <div class="form-check">
          <input
            id="showInDashboard"
            v-model="data.showInDashboard"
            class="form-check-input"
            type="checkbox"
          />
          <label class="form-check-label" for="showInDashboard"> Show In Dashboard </label>
        </div>
      </div>

      <template v-if="!editNotification">
        <div class="row">
          <div id="col-exp-buttons" class="col">
            <button
              class="btn btn-primary btn-sm"
              :disabled="isSaveDisabled"
              @click="saveNewNotice"
            >
              Save
            </button>
            <button class="btn btn-secondary btn-sm" @click="cancelNewNotice">Cancel</button>
          </div>
        </div>
      </template>
    </form>
  </div>
</template>
<script>
import { models } from "django-airavata-api";
import { mixins, utils } from "django-airavata-common-ui";
import FlatPickr from "vue-flatpickr-component";
import { formatShort, formatUtc } from "django-airavata-common-ui/js/utils/dates.js";

export default {
  name: "NoticeEditor",
  components: {
    FlatPickr,
  },
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: models.Notification,
      required: true,
    },
  },
  data() {
    return {
      editNotification: false,
      userBeginsInput: false,
      inputPublishedTime: null,
      inputExpirationTime: null,
      today: formatShort(new Date()),
      select: {
        selected: "LOW",
        options: [
          { text: "LOW", value: "LOW" },
          { text: "NORMAL", value: "NORMAL" },
          { text: "HIGH", value: "HIGH" },
        ],
      },
    };
  },
  computed: {
    dateTimeConfig() {
      return {
        enableTime: true,
        dateFormat: "Z",
        altInput: true,
        altFormat: "F j, Y h:i K",
        minDate: this.today,
      };
    },
    expirationDateConfig() {
      return {
        enableTime: true,
        dateFormat: "Z",
        altInput: true,
        altFormat: "F j, Y h:i K",
        minDate: this.inputPublishedTime || this.today,
      };
    },
    valid: function () {
      const validation = this.data.validate();
      return Object.keys(validation).length === 0;
    },
    isSaveDisabled: function () {
      return !this.valid;
    },
  },
  watch: {
    inputExpirationTime() {
      this.data.expirationTime = this.inputExpirationTime;
    },
    inputPublishedTime() {
      this.data.publishedTime = this.inputPublishedTime;
    },
  },
  created() {
    //checks whether the component is used for editing or updating the notificaion
    // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
    if (this.value.notificationId != null) {
      this.editNotification = true;
      this.inputPublishedTime = formatUtc(this.value.publishedTime.toISOString());
      this.inputExpirationTime = formatUtc(this.value.expirationTime.toISOString());
      this.data.priority = this.value.priority.name;
      this.data.showInDashboard = this.value.showInDashboard;
      this.today = formatShort(this.value.expirationTime.toISOString());
    }
  },
  methods: {
    onUserInput() {
      this.userBeginsInput = true;
      return this.$emit("userBeginsInput");
    },
    reset() {
      this.userBeginsInput = false;
    },
    getValidationFeedback: function (properties) {
      return utils.getProperty(this.data.validate(), properties);
    },
    getValidationState: function (properties) {
      if (this.userBeginsInput === false) {
        return null;
      }
      return this.getValidationFeedback(properties) ? false : true;
    },
    cancelNewNotice() {
      return this.$emit("cancelNewNotice");
    },
    saveNewNotice() {
      return this.$emit("saveNewNotice");
    },
  },
};
</script>
