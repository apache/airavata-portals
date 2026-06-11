<template>
  <div class="w-100">
    <ul style="list-style: none; margin: 0px; padding: 0px;">
      <li v-for="(notice, noticeIndex) in notices" :key="noticeIndex">
        <b-alert show>
          <div class="d-flex flex-row">
            <strong class="flex-fill" style="white-space: pre;">{{ notice.title }}</strong>
            <human-date v-if="notice.published_time" :date="notice.published_time" style="font-size: 10px;"/>
          </div>
          <div style="white-space: pre;font-size: 12px;">
            <linkify>{{ notice.notification_message }}</linkify>
          </div>
        </b-alert>
      </li>
    </ul>
  </div>
</template>

<script>
import {services} from "django-airavata-api";
import {components} from "django-airavata-common-ui";

export default {
  name: "workspace-notices-management-container",
  props: ["data"],
  data() {
    return {
      notices: null
    };
  },
  components: {
    "human-date": components.HumanDate,
    linkify: components.Linkify
  },
  created() {
    const now = new Date();
    if (this.data) {
      this.notices = this.data;
    } else {
      services.ManageNotificationService.list().then(notices => {
        if (!!notices && Array.isArray(notices)) {
          this.notices = notices.filter(({show_in_dashboard, published_time, expiration_time}) => {
            return !!show_in_dashboard && new Date(expiration_time) > now && new Date(published_time) <= now
          });
        } else {
          this.notices = [];
        }
      });
    }
  }
};
</script>
