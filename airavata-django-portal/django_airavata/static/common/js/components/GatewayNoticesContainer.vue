<template>
  <div class="btn-group ml-3">
    <div class="dropdown">
      <a
        href="#"
        class="dropdown-toggle text-dark"
        id="dropdownNoticeButton"
        data-toggle="dropdown"
        title="Notifications"
        aria-haspopup="true"
        aria-expanded="false"
      >
        <span
          class="fa-stack fa-1x has-badge"
          :data-count="totalUnreadCount"
          id="unread_notification_count"
        >
          <i class="fa fa-circle fa-stack-2x fa-inverse"></i>
          <i class="fa fa-bell fa-stack-1x"></i>
        </span>
      </a>
      <div
        class="dropdown-menu widget-notifications no-padding"
        style="width: 300px;"
      >
        <div class="notifications-list">
          <div class="text-center text-primary">Notifications</div>

          <template v-for="setupError in setupErrors">
            <div class="dropdown-divider" :key="'setup-' + setupError.id"></div>
            <div class="dropdown-item" :key="'setup-' + setupError.id">
              <div>
                <a
                  class="notification-title text-wrap text-danger"
                  :href="experimentUrl(setupError)"
                  :title="setupError.experimentName || setupError.experimentId"
                >
                  <i class="fa fa-exclamation-triangle"></i>
                  {{ setupError.experimentName || setupError.experimentId }}
                </a>
              </div>
              <div class="notification-description text-wrap">
                <strong>{{ setupError.message }}</strong>
                <span v-if="setupError.count > 1">
                  &times;{{ setupError.count }}
                </span>
              </div>
              <div class="notification-ago time">
                {{ fromNow(setupError.updated || setupError.created) }}
              </div>
            </div>
          </template>

          <template v-for="notice in unreadNotices">
            <div class="dropdown-divider" :key="notice.notificationId"></div>
            <div class="dropdown-item" :key="notice.notificationId">
              <div>
                <span
                  class="notification-title text-wrap"
                  :class="textColor(notice)"
                  >{{ notice.title }}</span
                >
                <a
                  v-if="!notice.is_read"
                  class="fas fa-dot-circle"
                  data-toggle="tooltip"
                  data-placement="left"
                  title="Mark as read"
                  :id="notice.notificationId"
                  @click="ackNotification(notice)"
                >
                </a>
              </div>
              <div
                class="notification-description text-wrap"
                id="notification_description"
              >
                <strong>{{ notice.notificationMessage }}</strong>
              </div>
              <div class="notification-ago time">
                {{ fromNow(notice.publishedTime) }}
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import moment from "moment";
import { services, utils } from "django-airavata-api";

export default {
  name: "gateway-notices-container",
  props: ["notices", "unreadCount"],
  data() {
    return {
      localUnreadCount: this.unreadCount,
      setupErrors: [],
    };
  },
  created() {
    // Surface this user's experiment setup errors alongside gateway notices.
    // Best-effort: this renders on every page, so never let a failure here
    // disrupt the header.
    services.UserSetupErrorService.list(
      {},
      { ignoreErrors: true, showSpinner: false }
    )
      .then((setupErrors) => {
        this.setupErrors = setupErrors;
      })
      .catch(() => {
        /* ignore */
      });
  },
  methods: {
    fromNow(date) {
      return moment(date).fromNow();
    },
    experimentUrl(setupError) {
      return (
        "/workspace/experiments/" + encodeURIComponent(setupError.experimentId)
      );
    },
    ackNotification(notice) {
      utils.FetchUtils.get(notice.url).then(() => {
        notice.is_read = true;
        this.localUnreadCount--;
      });
    },
    textColor(notice) {
      if (notice.priority === 0) {
        return "text-primary";
      } else if (notice.priority === 1) {
        return "text-warning";
      } else if (notice.priority === 2) {
        return "text-danger";
      }
    },
  },
  computed: {
    unreadNotices() {
      return this.notices;
    },
    // Badge total = unread admin notices + the user's setup errors. Setup
    // errors are display-only (no ack), so each one always counts.
    totalUnreadCount() {
      return (this.localUnreadCount || 0) + this.setupErrors.length;
    },
  },
};
</script>
