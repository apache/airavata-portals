<template>
  <div>
    <div class="d-flex">
      <slot name="title"> </slot>
    </div>
    <b-form @input="onUserInput" novalidate>
      <b-form-group
        label="Notice Title"
        label-for="notice-title"
        :invalid-feedback="getValidationFeedback('title')"
        :state="getValidationState('title')"
      >
        <b-form-input
          id="notice-title"
          type="text"
          v-model="data.title"
          required
          placeholder="Notice Title"
          :state="getValidationState('title')"
        ></b-form-input>
      </b-form-group>

      <b-form-group
        label="Notice Message"
        label-for="notice-message"
        :invalid-feedback="getValidationFeedback('notificationMessage')"
        :state="getValidationState('notificationMessage')"
      >
        <b-form-textarea
          id="notice-message"
          type="text"
          v-model="data.notification_message"
          required
          placeholder="Notice Message"
          :state="getValidationState('notificationMessage')"
          :rows="3"
        ></b-form-textarea>
      </b-form-group>

      <b-form-group label="Publish Date" label-for="publish-date">
        <flat-pickr
          id="publish-date"
          v-model="inputPublishedTime"
          class="form-control my-class"
          :config="publishDateConfig"
        />
      </b-form-group>

      <b-form-group label="Expiration Date" label-for="expiration-date">
        <flat-pickr
          id="expiration-date"
          v-model="inputExpirationTime"
          class="form-control my-class"
          :config="expirationDateConfig"
        />
      </b-form-group>

      <b-form-group
        label="Priority"
        label-for="priority"
        :invalid-feedback="getValidationFeedback('priority')"
        :state="getValidationState('priority')"
      >
        <b-form-select
          id="priority"
          v-model="data.priority"
          :options="select.options"
          :state="getValidationState('priority')"
        >
        </b-form-select>
      </b-form-group>

      <b-form-group
        label="Show In Dashboard"
        label-for="showInDashboard"
        :state="getValidationState('show_in_dashboard')"
      >
        <b-form-checkbox
          id="showInDashboard"
          v-model="data.show_in_dashboard"
          :state="getValidationState('show_in_dashboard')"
        >
        </b-form-checkbox>
      </b-form-group>

      <template v-if="!editNotification">
        <div class="row">
          <div id="col-exp-buttons" class="col">
            <b-button
              variant="success"
              @click="saveNewNotice"
              :disabled="isSaveDisabled"
            >
              Save
            </b-button>
            <b-button variant="primary" @click="cancelNewNotice">
              Cancel
            </b-button>
          </div>
        </div>
      </template>
    </b-form>
  </div>
</template>
<style>
.my-class {
  width: 250px;
}
</style>
<script>
import { models } from "django-airavata-api";
import { mixins, utils } from "django-airavata-common-ui";
import moment from "moment";

export default {
  name: "notice-editor",
  // <flat-pickr> is registered globally in main.js (vue-flatpickr-component),
  // replacing the Vue 2-only vue-datetime <datetime> picker.
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: models.Notification,
      required: true,
    },
  },
  created() {
    //checks whether the component is used for editing or updating the notificaion
    if (this.value.notification_id != null) {
      this.editNotification = true;
      this.inputPublishedTime = new moment(
        this.value.published_time.toISOString(),
      )
        .utc()
        .format();
      this.inputExpirationTime = new moment(
        this.value.expiration_time.toISOString(),
      )
        .utc()
        .format();
      this.data.priority = this.value.priority.name;
      this.data.show_in_dashboard = this.value.show_in_dashboard;
      this.today = new moment(
        this.value.expiration_time.toISOString(),
      ).format();
    }
  },
  data() {
    return {
      editNotification: false,
      userBeginsInput: false,
      inputPublishedTime: null,
      inputExpirationTime: null,
      today: new moment().format(),
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
    valid: function () {
      const validation = this.data.validate();
      return Object.keys(validation).length === 0;
    },
    isSaveDisabled: function () {
      return !this.valid;
    },
    // flatpickr datetime config. dateFormat "Z" emits an ISO-8601 string so the
    // v-model value stays an ISO string like vue-datetime did.
    publishDateConfig() {
      return {
        enableTime: true,
        dateFormat: "Z",
        altInput: true,
        altFormat: "F j, Y h:i K",
        minuteIncrement: 5,
        time_24hr: false,
        minDate: this.today,
      };
    },
    expirationDateConfig() {
      return {
        enableTime: true,
        dateFormat: "Z",
        altInput: true,
        altFormat: "F j, Y h:i K",
        minuteIncrement: 5,
        time_24hr: false,
        minDate: this.inputPublishedTime,
      };
    },
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
      if (this.userBeginsInput == false) {
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
  watch: {
    inputExpirationTime() {
      this.data.expiration_time = this.inputExpirationTime;
    },
    inputPublishedTime() {
      this.data.published_time = this.inputPublishedTime;
    },
  },
};
</script>
