<template>
  <div class="w-100">
    <ul style="list-style: none; margin: 0px; padding: 0px">
      <li v-for="(notice, noticeIndex) in notices" :key="noticeIndex">
        <div class="alert" show>
          <div class="d-flex flex-row">
            <strong class="flex-fill" style="white-space: pre">{{ notice.title }}</strong>
            <human-date
              v-if="notice.publishedTime"
              :date="notice.publishedTime"
              style="font-size: 10px"
            />
          </div>
          <div style="white-space: pre; font-size: 12px">
            <linkify>{{ notice.notificationMessage }}</linkify>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { services } from "django-airavata-api";
import { components } from "django-airavata-common-ui";

const HumanDate = components.HumanDate;
const Linkify = components.Linkify;

type Notice = {
  title?: string;
  notificationMessage?: string;
  publishedTime?: string | Date;
  expirationTime?: string | Date;
  showInDashboard?: boolean;
};

const props = defineProps<{
  data?: Notice[] | null;
}>();

const notices = ref<Notice[] | null>(null);

onMounted(() => {
  const now = new Date();
  if (props.data) {
    notices.value = props.data;
  } else {
    services.ManageNotificationService.list().then((result: unknown) => {
      if (result && Array.isArray(result)) {
        notices.value = (result as Notice[]).filter(
          ({ showInDashboard, publishedTime, expirationTime }) => {
            return (
              !!showInDashboard &&
              new Date(expirationTime as string) > now &&
              new Date(publishedTime as string) <= now
            );
          },
        );
      } else {
        notices.value = [];
      }
    });
  }
});
</script>
