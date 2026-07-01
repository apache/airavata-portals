<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <button
        :class="triggerClasses"
        type="button"
        title="Notifications"
      >
        <span class="relative flex size-5 items-center justify-center">
          <Bell class="size-4 shrink-0" />
          <span
            v-if="localUnreadCount > 0"
            class="absolute -right-1.5 -top-1.5 flex min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold leading-4 text-primary-foreground"
            >{{ localUnreadCount }}</span
          >
        </span>
      </button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end" side="bottom" class="w-80 p-0">
      <DropdownMenuLabel class="px-3 py-2">Notifications</DropdownMenuLabel>
      <DropdownMenuSeparator class="my-0" />
      <div class="max-h-80 overflow-y-auto">
        <p
          v-if="!unreadNotices || unreadNotices.length === 0"
          class="px-3 py-4 text-center text-sm text-muted-foreground"
        >
          No notifications
        </p>
        <div
          v-for="notice in unreadNotices"
          :key="notice.notificationId"
          class="border-b border-border px-3 py-2 last:border-b-0"
        >
          <div class="flex items-start justify-between gap-2">
            <span class="text-sm font-semibold" :class="textColor(notice)">{{
              notice.title
            }}</span>
            <Button
              v-if="!notice.is_read"
              variant="ghost"
              size="icon-sm"
              title="Mark as read"
              class="shrink-0 text-muted-foreground"
              @click="ackNotification(notice)"
            >
              <CheckCircle2 class="size-4" />
            </Button>
          </div>
          <p class="mt-0.5 text-sm text-muted-foreground">
            <strong>{{ notice.notificationMessage }}</strong>
          </p>
          <p class="mt-0.5 text-xs italic text-muted-foreground/70">
            {{ fromNow(notice.publishedTime) }}
          </p>
        </div>
      </div>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

<script>
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { Bell, CheckCircle2 } from "@lucide/vue";
import { utils } from "django-airavata-api";

dayjs.extend(relativeTime);

export default {
  name: "gateway-notices-container",
  components: {
    Bell,
    CheckCircle2,
  },
  props: ["notices", "unreadCount"],
  data() {
    return {
      localUnreadCount: this.unreadCount,
    };
  },
  methods: {
    fromNow(date) {
      return dayjs(date).fromNow();
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
        return "text-destructive";
      }
      return "";
    },
  },
  computed: {
    triggerClasses() {
      return "flex size-9 shrink-0 items-center justify-center rounded-md text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring";
    },
    unreadNotices() {
      return this.notices;
    },
  },
};
</script>
