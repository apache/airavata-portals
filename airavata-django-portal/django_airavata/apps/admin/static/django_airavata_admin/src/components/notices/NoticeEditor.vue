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
<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models } from "django-airavata-api";
import { utils } from "django-airavata-common-ui";
import FlatPickr from "vue-flatpickr-component";
import { formatShort, formatUtc } from "django-airavata-common-ui/js/utils/dates.js";

const props = defineProps<{
  modelValue: InstanceType<typeof models.Notification>;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: InstanceType<typeof models.Notification>];
  userBeginsInput: [];
  cancelNewNotice: [];
  saveNewNotice: [];
}>();

// Local copy of the notification (VModelMixin pattern)
const data = ref<InstanceType<typeof models.Notification>>(props.modelValue.clone());

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = newValue.clone();
  },
  { deep: true }
);

watch(
  data,
  (newValue) => {
    emit("update:modelValue", newValue);
  },
  { deep: true }
);

const editNotification = ref(false);
const userBeginsInput = ref(false);
const inputPublishedTime = ref<string | null>(null);
const inputExpirationTime = ref<string | null>(null);
const today = ref(formatShort(new Date()));
const select = ref({
  selected: "LOW",
  options: [
    { text: "LOW", value: "LOW" },
    { text: "NORMAL", value: "NORMAL" },
    { text: "HIGH", value: "HIGH" },
  ],
});

watch(inputExpirationTime, (val) => {
  data.value.expirationTime = val;
});
watch(inputPublishedTime, (val) => {
  data.value.publishedTime = val;
});

const dateTimeConfig = computed(() => ({
  enableTime: true,
  dateFormat: "Z",
  altInput: true,
  altFormat: "F j, Y h:i K",
  minDate: today.value,
}));

const expirationDateConfig = computed(() => ({
  enableTime: true,
  dateFormat: "Z",
  altInput: true,
  altFormat: "F j, Y h:i K",
  minDate: inputPublishedTime.value || today.value,
}));

const valid = computed(() => {
  const validation = data.value.validate();
  return Object.keys(validation).length === 0;
});

const isSaveDisabled = computed(() => !valid.value);

onMounted(() => {
  // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
  if (props.modelValue.notificationId != null) {
    editNotification.value = true;
    inputPublishedTime.value = formatUtc(props.modelValue.publishedTime.toISOString());
    inputExpirationTime.value = formatUtc(props.modelValue.expirationTime.toISOString());
    data.value.priority = props.modelValue.priority.name;
    data.value.showInDashboard = props.modelValue.showInDashboard;
    today.value = formatShort(props.modelValue.expirationTime.toISOString());
  }
});

function onUserInput() {
  userBeginsInput.value = true;
  emit("userBeginsInput");
}

function reset() {
  userBeginsInput.value = false;
}

function getValidationFeedback(properties: string) {
  return utils.getProperty(data.value.validate(), properties);
}

function getValidationState(properties: string) {
  if (!userBeginsInput.value) {
    return null;
  }
  return getValidationFeedback(properties) ? false : true;
}

function cancelNewNotice() {
  emit("cancelNewNotice");
}

function saveNewNotice() {
  emit("saveNewNotice");
}

defineExpose({ reset });
</script>
