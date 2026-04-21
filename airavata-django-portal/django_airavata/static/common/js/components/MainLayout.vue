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

<script>
import NotificationsDisplay from "./NotificationsDisplay.vue";
import NotificationsPanel from "./NotificationsPanel.vue";
import SshPromptNotification from "./SshPromptNotification.vue";
import { utils } from "django-airavata-api";

export default {
  name: "MainLayout",
  components: {
    NotificationsDisplay,
    NotificationsPanel,
    SshPromptNotification,
  },
  data() {
    return {
      collapsed: false,
      activePanel: "content",
      notices: [],
      unreadCount: 0,
    };
  },
  computed: {
    hasSidebarSlot() {
      return !!this.$slots.sidebar;
    },
    showSidebar() {
      return this.hasSidebarSlot || this.notices.length > 0;
    },
  },
  created() {
    // Load notices from the DOM data attribute (set in base.html)
    const el = document.getElementById("gateway-notices");
    if (el) {
      this.unreadCount = parseInt(el.dataset.unreadCount || "0");
      this.notices = JSON.parse(el.dataset.notices || "[]");
    }

    // Default to content panel if sidebar slot exists, otherwise notifications
    this.activePanel = this.hasSidebarSlot ? "content" : "notifications";

    // Restore collapsed state
    this.collapsed = localStorage.getItem("rightSidebarCollapsed") === "true";

    // Listen for footer bar toggle events
    window.addEventListener("sidebar:toggle", this.handleToggle);
    window.addEventListener("sidebar:show", this.handleShow);

    // Connect SSE client for real-time events
    if (utils.SSEClient) {
      utils.SSEClient.connect();
    }
  },
  beforeUnmount() {
    window.removeEventListener("sidebar:toggle", this.handleToggle);
    window.removeEventListener("sidebar:show", this.handleShow);
    if (utils.SSEClient) {
      utils.SSEClient.disconnect();
    }
  },
  methods: {
    switchPanel(panel) {
      if (this.activePanel === panel && !this.collapsed) {
        // Clicking the active tab collapses
        this.collapsed = true;
      } else {
        this.activePanel = panel;
        this.collapsed = false;
      }
      this.persistState();
    },
    handleToggle() {
      this.collapsed = !this.collapsed;
      this.persistState();
    },
    handleShow(e) {
      const panel = e.detail;
      if (panel) {
        this.switchPanel(panel);
      }
    },
    persistState() {
      localStorage.setItem("rightSidebarCollapsed", this.collapsed);
    },
  },
};
</script>
