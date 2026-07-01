<template>
  <div>
    <div class="flex">
      <slot name="title"> </slot>
    </div>
    <form class="space-y-4" @input="onUserInput" novalidate>
      <div class="space-y-1.5">
        <Label for="notice-title">Notice Title</Label>
        <Input
          id="notice-title"
          type="text"
          v-model="data.title"
          required
          placeholder="Notice Title"
          :aria-invalid="getValidationState('title') === false"
        />
        <p
          v-if="getValidationState('title') === false"
          class="text-sm text-destructive"
        >
          {{ getValidationFeedback("title") }}
        </p>
      </div>

      <div class="space-y-1.5">
        <Label for="notice-message">Notice Message</Label>
        <Textarea
          id="notice-message"
          v-model="data.notification_message"
          required
          placeholder="Notice Message"
          :aria-invalid="getValidationState('notificationMessage') === false"
          :rows="3"
        ></Textarea>
        <p
          v-if="getValidationState('notificationMessage') === false"
          class="text-sm text-destructive"
        >
          {{ getValidationFeedback("notificationMessage") }}
        </p>
      </div>

      <div class="space-y-1.5">
        <Label for="publish-date">Publish Date</Label>
        <flat-pickr
          id="publish-date"
          v-model="inputPublishedTime"
          class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-[250px] rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
          :config="publishDateConfig"
        />
      </div>

      <div class="space-y-1.5">
        <Label for="expiration-date">Expiration Date</Label>
        <flat-pickr
          id="expiration-date"
          v-model="inputExpirationTime"
          class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-[250px] rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
          :config="expirationDateConfig"
        />
      </div>

      <div class="space-y-1.5">
        <Label for="priority">Priority</Label>
        <select
          id="priority"
          v-model="data.priority"
          class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
        >
          <option
            v-for="opt in select.options"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.text }}
          </option>
        </select>
        <p
          v-if="getValidationState('priority') === false"
          class="text-sm text-destructive"
        >
          {{ getValidationFeedback("priority") }}
        </p>
      </div>

      <div class="space-y-1.5">
        <Label for="showInDashboard">Show In Dashboard</Label>
        <div>
          <Checkbox id="showInDashboard" v-model="data.show_in_dashboard" />
        </div>
      </div>

      <template v-if="!editNotification">
        <div class="flex gap-2">
          <Button @click="saveNewNotice" :disabled="isSaveDisabled">
            Save
          </Button>
          <Button variant="secondary" @click="cancelNewNotice"> Cancel </Button>
        </div>
      </template>
    </form>
  </div>
</template>
<script>
import { models } from "django-airavata-api";
import { mixins, utils } from "django-airavata-common-ui";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

dayjs.extend(utc);

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
      this.inputPublishedTime = dayjs(
        this.value.published_time.toISOString(),
      )
        .utc()
        .format();
      this.inputExpirationTime = dayjs(
        this.value.expiration_time.toISOString(),
      )
        .utc()
        .format();
      this.data.priority = this.value.priority.name;
      this.data.show_in_dashboard = this.value.show_in_dashboard;
      this.today = dayjs(
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
      today: dayjs().format(),
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
