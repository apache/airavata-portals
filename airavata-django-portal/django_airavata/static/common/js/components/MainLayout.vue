<template>
  <div class="main-content-wrapper">
    <main class="main-content" :class="{ 'main-content--with-sidebar': showSidebar }">
      <ssh-prompt-notification />
      <notifications-display />
      <div class="container-fluid">
        <slot />
      </div>
    </main>
    <aside v-if="showSidebar" class="sidebar" :class="{ 'is-collapsed': collapsed }">
      <div class="sidebar-tabs">
        <button
          v-if="hasSidebarSlot"
          class="sidebar-tabs__btn"
          :class="{ 'is-active': activePanel === 'content' }"
          @click="switchPanel('content')"
        >
          <i class="fa fa-flask"></i>
        </button>
        <button
          class="sidebar-tabs__btn"
          :class="{ 'is-active': activePanel === 'notifications' }"
          @click="switchPanel('notifications')"
        >
          <i class="fa fa-bell"></i>
          <span v-if="unreadCount > 0" class="sidebar-tabs__badge">{{ unreadCount }}</span>
        </button>
      </div>
      <div v-show="activePanel === 'content' && hasSidebarSlot" class="sidebar-panel">
        <slot name="sidebar" />
      </div>
      <div v-show="activePanel === 'notifications'" class="sidebar-panel">
        <notifications-panel
          :notices="notices"
          :unread-count="unreadCount"
          @update:unread="unreadCount = $event"
        />
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, useSlots } from "vue";
import NotificationsDisplay from "./NotificationsDisplay.vue";
import NotificationsPanel from "./NotificationsPanel.vue";
import SshPromptNotification from "./SshPromptNotification.vue";
import { utils } from "django-airavata-api";

const slots = useSlots();

const collapsed = ref(false);
const activePanel = ref("content");
interface Notice {
  notificationId: string | number;
  [key: string]: unknown;
}

const notices = ref<Notice[]>([]);
const unreadCount = ref(0);

const hasSidebarSlot = computed(() => !!slots.sidebar);
const showSidebar = computed(() => hasSidebarSlot.value || notices.value.length > 0);

onMounted(() => {
  // Load notices from the DOM data attribute (set in base.html)
  const el = document.getElementById("gateway-notices");
  if (el) {
    unreadCount.value = parseInt(el.dataset["unreadCount"] || "0");
    notices.value = JSON.parse(el.dataset["notices"] || "[]") as Notice[];
  }

  // Default to content panel if sidebar slot exists, otherwise notifications
  activePanel.value = hasSidebarSlot.value ? "content" : "notifications";

  // Restore collapsed state
  collapsed.value = localStorage.getItem("rightSidebarCollapsed") === "true";

  // Listen for footer bar toggle events
  window.addEventListener("sidebar:toggle", handleToggle);
  window.addEventListener("sidebar:show", handleShowEvent);

  // Connect SSE client for real-time events
  if (utils.SSEClient) {
    utils.SSEClient.connect();
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("sidebar:toggle", handleToggle);
  window.removeEventListener("sidebar:show", handleShowEvent);
  if (utils.SSEClient) {
    utils.SSEClient.disconnect();
  }
});

function switchPanel(panel: string): void {
  if (activePanel.value === panel && !collapsed.value) {
    // Clicking the active tab collapses
    collapsed.value = true;
  } else {
    activePanel.value = panel;
    collapsed.value = false;
  }
  persistState();
}

function handleToggle(): void {
  collapsed.value = !collapsed.value;
  persistState();
}

function handleShowEvent(e: Event): void {
  handleShow(e as CustomEvent);
}

function handleShow(e: CustomEvent): void {
  const panel = e.detail;
  if (panel) {
    switchPanel(panel);
  }
}

function persistState(): void {
  localStorage.setItem("rightSidebarCollapsed", String(collapsed.value));
}
</script>
