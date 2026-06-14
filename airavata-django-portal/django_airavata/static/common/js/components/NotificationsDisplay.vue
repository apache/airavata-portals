<template>
  <div id="notifications-display">
    <transition-group name="fade" tag="div" class="space-y-2">
      <template v-for="unhandledError in unhandledErrors">
        <Alert
          v-if="isUnauthenticatedError(unhandledError.error)"
          class="border-transparent bg-warning text-warning-foreground"
          :key="unhandledError.id"
        >
          <AlertDescription
            class="flex w-full items-start gap-2 text-warning-foreground"
          >
            <span>
              Your login session has expired. Please
              <a class="font-medium underline" :href="loginLinkWithNext"
                >log in again</a
              >. You can also
              <a
                class="inline-flex items-center gap-1 font-medium underline"
                :href="loginLink"
                target="_blank"
                >login in a separate tab
                <ExternalLink class="size-3.5" aria-hidden="true" /></a>
              and then return to this tab and try again.
            </span>
            <Button
              variant="ghost"
              size="icon-sm"
              class="ml-auto shrink-0"
              @click="dismissUnhandledError(unhandledError)"
            >
              <X class="size-4" />
            </Button>
          </AlertDescription>
        </Alert>
        <Alert v-else variant="destructive" :key="unhandledError.id">
          <AlertDescription class="flex w-full items-start gap-2">
            <span>{{ unhandledError.message }}</span>
            <Button
              variant="ghost"
              size="icon-sm"
              class="ml-auto shrink-0"
              @click="dismissUnhandledError(unhandledError)"
            >
              <X class="size-4" />
            </Button>
          </AlertDescription>
        </Alert>
      </template>
      <Alert
        v-for="notification in notifications"
        :variant="variant(notification) === 'destructive' ? 'destructive' : 'default'"
        :class="alertClass(notification)"
        :key="notification.id"
      >
        <AlertDescription
          class="flex w-full items-start gap-2"
          :class="alertTextClass(notification)"
        >
          <span>{{ notification.message }}</span>
          <Button
            variant="ghost"
            size="icon-sm"
            class="ml-auto shrink-0"
            @click="dismissNotification(notification)"
          >
            <X class="size-4" />
          </Button>
        </AlertDescription>
      </Alert>
    </transition-group>
    <Alert
      v-if="apiServerBackUp === false"
      variant="destructive"
      class="mt-2"
    >
      <AlertDescription>
        <div>
          <p>API Server is down.</p>
          <p class="flex items-center gap-2">
            <RefreshCw class="size-4 animate-spin" /> Checking status ...
          </p>
        </div>
      </AlertDescription>
    </Alert>
    <Alert
      v-if="apiServerBackUp"
      class="mt-2 border-transparent bg-success text-success-foreground"
    >
      <AlertDescription class="text-success-foreground">
        API Server is back up. Please try again.
      </AlertDescription>
    </Alert>
  </div>
</template>

<script>
import { ExternalLink, RefreshCw, X } from "@lucide/vue";
import { errors, services } from "django-airavata-api";
import NotificationList from "../notifications/NotificationList";

export default {
  name: "notifications-display",
  components: {
    ExternalLink,
    RefreshCw,
    X,
  },
  data() {
    return {
      notifications: NotificationList.list,
      unhandledErrors: errors.UnhandledErrorDisplayList.list,
      apiServerBackUp: null,
      apiServerBackUpTimestamp: null,
      pollingDelay: 10000,
    };
  },
  methods: {
    dismissNotification: function (notification) {
      NotificationList.remove(notification);
    },
    dismissUnhandledError: function (unhandledError) {
      errors.UnhandledErrorDisplayList.remove(unhandledError);
    },
    variant: function (notification) {
      if (notification.type === "ERROR") {
        return "destructive";
      } else {
        return "default";
      }
    },
    alertClass: function (notification) {
      if (notification.type === "SUCCESS") {
        return "border-transparent bg-success text-success-foreground";
      } else if (notification.type === "WARNING") {
        return "border-transparent bg-warning text-warning-foreground";
      }
      return "";
    },
    alertTextClass: function (notification) {
      if (notification.type === "SUCCESS") {
        return "text-success-foreground";
      } else if (notification.type === "WARNING") {
        return "text-warning-foreground";
      }
      return "";
    },
    loadAPIServerStatus() {
      return services.APIServerStatusCheckService.get(
        {},
        { ignoreErrors: true, showSpinner: false }
      ).then((status) => {
        if (status.apiServerUp === true) {
          this.apiServerBackUp = true;
          this.apiServerBackUpTimestamp = Date.now();
        }
      });
    },
    initPollingAPIServerStatus: function () {
      const pollAPIServerStatus = function () {
        if (!this.apiServerBackUp) {
          const repoll = () =>
            setTimeout(pollAPIServerStatus.bind(this), this.pollingDelay);
          this.loadAPIServerStatus().then(repoll, repoll);
        }
      }.bind(this);
      setTimeout(pollAPIServerStatus.bind(this), this.pollingDelay);
    },
    isUnauthenticatedError(error) {
      return errors.ErrorUtils.isUnauthenticatedError(error);
    },
  },
  computed: {
    apiServerDown() {
      // Return true if any notifications indicate that the API Server is down,
      // but excludes notifications that came before the timestamp of the last
      // API server status check
      const notificationsApiServerDown = this.notifications
        ? this.notifications
            .filter((n) => {
              if (this.apiServerBackUpTimestamp) {
                return (
                  n.createdDate.getTime() - this.apiServerBackUpTimestamp > 0
                );
              } else {
                return true;
              }
            })
            .some(
              (n) =>
                n.details &&
                n.details.response &&
                n.details.response.apiServerDown
            )
        : false;
      const unhandledErrorsApiServerDown = this.unhandledErrors
        ? this.unhandledErrors
            .filter((n) => {
              if (this.apiServerBackUpTimestamp) {
                return (
                  n.createdDate.getTime() - this.apiServerBackUpTimestamp > 0
                );
              } else {
                return true;
              }
            })
            .some(
              (e) =>
                e.details &&
                e.details.response &&
                e.details.response.apiServerDown
            )
        : false;
      return notificationsApiServerDown || unhandledErrorsApiServerDown;
    },
    loginLinkWithNext() {
      return errors.ErrorUtils.buildLoginUrl();
    },
    loginLink() {
      return errors.ErrorUtils.buildLoginUrl(false);
    },
  },
  watch: {
    /*
     * Whenever notifications indicate that the API server is down, start
     * polling the API server status so we can let the user know when it is
     * back up.
     */
    apiServerDown(newValue) {
      if (newValue) {
        this.apiServerBackUp = false;
        this.initPollingAPIServerStatus();
      }
    },
  },
};
</script>

<style>
#notifications-display {
  position: fixed;
  top: 20px;
  left: 20vw;
  width: 60vw;
  z-index: 10000;
}
</style>
