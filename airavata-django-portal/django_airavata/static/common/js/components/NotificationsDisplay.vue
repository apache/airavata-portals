<template>
  <div id="notifications-display">
    <transition-group name="fade" tag="div">
      <template v-for="unhandledError in unhandledErrors">
        <div
          v-if="isUnauthenticatedError(unhandledError.error)"
          :key="unhandledError.id"
          class="alert alert-warning alert-dismissible"
        >
          Your login session has expired. Please
          <a class="alert-link" :href="loginLinkWithNext">log in again</a>. You can also
          <a class="alert-link" :href="loginLink" target="_blank"
            >login in a separate tab <i class="fa fa-external-link-alt" aria-hidden="true"></i
          ></a>
          and then return to this tab and try again.
        </div>
        <div v-else :key="unhandledError.id" class="alert alert-danger alert-dismissible">
          {{ unhandledError.message }}
        </div>
      </template>
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="['alert', 'alert-' + variant(notification), 'alert-dismissible']"
      >
        {{ notification.message }}
      </div>
    </transition-group>
    <div v-if="apiServerDown && apiServerBackUp === false" class="alert alert-danger">
      <p>API Server is down.</p>
      <i class="fa fa-sync-alt fa-spin"></i> Checking status ...
    </div>
    <div v-if="apiServerBackUp" class="alert alert-success">
      API Server is back up. Please try again.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { errors, services } from "django-airavata-api";
import NotificationList from "../notifications/NotificationList";
import type Notification from "../notifications/Notification";

interface ErrorEntry {
  id: number;
  error: unknown;
  message: string;
  createdDate: Date;
  details?: { response?: { apiServerDown?: boolean } };
}

const notifications = ref<Notification[]>(NotificationList.list);
const unhandledErrors = ref<ErrorEntry[]>(errors.UnhandledErrorDisplayList.list);
const apiServerBackUp = ref<boolean | null>(null);
const apiServerBackUpTimestamp = ref<number | null>(null);
const pollingDelay = 10000;

const apiServerDown = computed(() => {
  // Return true if any notifications indicate that the API Server is down,
  // but excludes notifications that came before the timestamp of the last
  // API server status check
  const notificationsApiServerDown = notifications.value
    ? notifications.value
        .filter((n) => {
          if (apiServerBackUpTimestamp.value) {
            return n.createdDate.getTime() - apiServerBackUpTimestamp.value > 0;
          } else {
            return true;
          }
        })
        .some((n) => {
          const d = n.details as { response?: { apiServerDown?: boolean } } | null;
          return d && d.response && d.response.apiServerDown;
        })
    : false;
  const unhandledErrorsApiServerDown = unhandledErrors.value
    ? unhandledErrors.value
        .filter((n) => {
          if (apiServerBackUpTimestamp.value) {
            return n.createdDate.getTime() - apiServerBackUpTimestamp.value > 0;
          } else {
            return true;
          }
        })
        .some((e) => e.details && e.details.response && e.details.response.apiServerDown)
    : false;
  return notificationsApiServerDown || unhandledErrorsApiServerDown;
});

const loginLinkWithNext = computed(() => errors.ErrorUtils.buildLoginUrl());
const loginLink = computed(() => errors.ErrorUtils.buildLoginUrl(false));

/*
 * Whenever notifications indicate that the API server is down, start
 * polling the API server status so we can let the user know when it is
 * back up.
 */
watch(apiServerDown, (newValue) => {
  if (newValue) {
    apiServerBackUp.value = false;
    initPollingAPIServerStatus();
  }
});

function variant(notification: Notification): string {
  if (notification.type === "SUCCESS") {
    return "success";
  } else if (notification.type === "ERROR") {
    return "danger";
  } else if (notification.type === "WARNING") {
    return "warning";
  } else {
    return "secondary";
  }
}

function loadAPIServerStatus(): Promise<void> {
  return services.APIServerStatusCheckService.get(
    {},
    { ignoreErrors: true, showSpinner: false },
  ).then((status: { apiServerUp?: boolean }) => {
    if (status.apiServerUp === true) {
      apiServerBackUp.value = true;
      apiServerBackUpTimestamp.value = Date.now();
    }
  });
}

function initPollingAPIServerStatus(): void {
  const pollAPIServerStatus = function () {
    if (!apiServerBackUp.value) {
      const repoll = () => setTimeout(pollAPIServerStatus, pollingDelay);
      loadAPIServerStatus().then(repoll, repoll);
    }
  };
  setTimeout(pollAPIServerStatus, pollingDelay);
}

function isUnauthenticatedError(error: unknown): boolean {
  return errors.ErrorUtils.isUnauthenticatedError(error);
}
</script>

<style>
#notifications-display {
  position: fixed;
  top: 75px;
  left: 20vw;
  width: 60vw;
  z-index: 10000;
}
</style>
