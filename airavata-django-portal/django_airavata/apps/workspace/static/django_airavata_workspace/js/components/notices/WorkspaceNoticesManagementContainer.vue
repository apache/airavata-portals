<template>
  <div class="w-full">
    <ul class="m-0 list-none space-y-2 p-0">
      <li v-for="(notice, noticeIndex) in notices" :key="noticeIndex">
        <Alert>
          <AlertDescription>
            <div class="flex w-full flex-row">
              <strong class="flex-1 whitespace-pre">{{ notice.title }}</strong>
              <human-date
                v-if="notice.published_time"
                :date="notice.published_time"
                class="text-xs text-muted-foreground"
              />
            </div>
            <div class="whitespace-pre text-sm">
              <linkify>{{ notice.notification_message }}</linkify>
            </div>
          </AlertDescription>
        </Alert>
      </li>
    </ul>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import { components } from "django-airavata-common-ui";

export default {
  name: "workspace-notices-management-container",
  props: ["data"],
  data() {
    return {
      notices: null,
    };
  },
  components: {
    "human-date": components.HumanDate,
    linkify: components.Linkify,
  },
  created() {
    const now = new Date();
    if (this.data) {
      this.notices = this.data;
    } else {
      services.ManageNotificationService.list().then((notices) => {
        if (!!notices && Array.isArray(notices)) {
          this.notices = notices.filter(
            ({ show_in_dashboard, published_time, expiration_time }) => {
              return (
                !!show_in_dashboard &&
                new Date(expiration_time) > now &&
                new Date(published_time) <= now
              );
            },
          );
        } else {
          this.notices = [];
        }
      });
    }
  },
};
</script>
