<template>
  <TooltipProvider :delay-duration="150">
    <aside
      class="bg-sidebar text-sidebar-foreground flex h-full w-64 shrink-0 flex-col border-r border-sidebar-border"
    >
      <!-- Brand / logo -->
      <a
        href="/"
        class="flex items-center gap-3 px-4 py-4 text-sidebar-foreground"
      >
        <span
          class="flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-md bg-sidebar-accent"
          :style="logoBackgroundStyle"
        >
          <img
            v-if="logoUrl"
            :src="logoUrl"
            alt=""
            class="size-full object-contain"
          />
          <FlaskConical v-else class="size-5 text-sidebar-primary" />
        </span>
        <span class="truncate text-base font-semibold leading-tight">{{
          title
        }}</span>
      </a>

      <Separator class="bg-sidebar-border" />

      <!-- Primary navigation -->
      <nav class="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        <p
          v-if="navItems.length"
          class="px-2 pb-1 text-xs font-medium uppercase tracking-wide text-sidebar-foreground/50"
        >
          Navigation
        </p>
        <a
          v-for="item in navItems"
          :key="item.label + item.url"
          :href="item.url"
          :class="navItemClasses(item.active)"
        >
          <component :is="iconFor(item)" class="size-4 shrink-0" />
          <span class="truncate">{{ item.label }}</span>
        </a>
      </nav>

      <Separator class="bg-sidebar-border" />

      <!-- Bottom utilities: app switcher, notifications, user menu -->
      <div class="space-y-1 px-3 py-3">
        <!-- App switcher -->
        <DropdownMenu v-if="apps.length">
          <DropdownMenuTrigger as-child>
            <button :class="utilityButtonClasses">
              <component :is="currentAppIcon" class="size-4 shrink-0" />
              <span class="flex-1 truncate text-left">{{
                currentAppLabel
              }}</span>
              <ChevronsUpDown class="size-4 shrink-0 opacity-60" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="start"
            side="top"
            class="w-56"
          >
            <DropdownMenuLabel>Switch app</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              v-for="app in apps"
              :key="app.label + app.url"
              as-child
            >
              <a :href="app.url" class="cursor-pointer">
                <component :is="iconFor(app)" class="size-4" />
                <span class="truncate">{{ app.label }}</span>
                <Check
                  v-if="app.current"
                  class="ml-auto size-4 text-primary"
                />
              </a>
            </DropdownMenuItem>
            <template v-if="menuLinks.length">
              <DropdownMenuSeparator />
              <DropdownMenuItem
                v-for="link in menuLinks"
                :key="link.link"
                as-child
              >
                <a :href="link.link" class="cursor-pointer">
                  <Link2 class="size-4" />
                  <span class="truncate">{{ link.link_text }}</span>
                </a>
              </DropdownMenuItem>
            </template>
          </DropdownMenuContent>
        </DropdownMenu>

        <!-- Notifications -->
        <gateway-notices-container
          v-if="notices !== null"
          :notices="notices"
          :unread-count="unreadCount"
        />

        <!-- User menu -->
        <DropdownMenu v-if="user">
          <DropdownMenuTrigger as-child>
            <button :class="utilityButtonClasses">
              <span
                class="flex size-7 shrink-0 items-center justify-center rounded-full bg-sidebar-primary text-sidebar-primary-foreground text-xs font-semibold"
              >
                {{ userInitials }}
              </span>
              <span class="flex-1 truncate text-left">{{ userName }}</span>
              <ChevronsUpDown class="size-4 shrink-0 opacity-60" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" side="top" class="w-56">
            <DropdownMenuLabel>
              <div class="flex flex-col">
                <span class="truncate font-medium">{{ userName }}</span>
                <span
                  v-if="user.email"
                  class="truncate text-xs font-normal text-muted-foreground"
                  >{{ user.email }}</span
                >
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem v-if="accountUrl" as-child>
              <a
                :href="accountUrl"
                target="_blank"
                rel="noopener"
                class="cursor-pointer"
              >
                <Settings class="size-4" />
                <span>User Settings</span>
              </a>
            </DropdownMenuItem>
            <DropdownMenuItem v-if="logoutUrl" as-child>
              <a :href="logoutUrl" class="cursor-pointer">
                <LogOut class="size-4" />
                <span>Logout</span>
              </a>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  </TooltipProvider>
</template>

<script>
import {
  Check,
  ChevronsUpDown,
  Folder,
  FolderOpen,
  FlaskConical,
  Layers,
  LayoutDashboard,
  Link2,
  LogOut,
  Settings,
  Settings2,
  Users,
} from "@lucide/vue";
import GatewayNoticesContainer from "./GatewayNoticesContainer.vue";

// Map the legacy Font Awesome icon class names (still emitted by the Django
// context processors) onto @lucide/vue components for the sidebar nav.
const FA_ICON_MAP = {
  "fa-flask": FlaskConical,
  "fa-cog": Settings2,
  "fa-cogs": Settings2,
  "fa-users": Users,
  "fa-copy": Layers,
  "fa-folder": Folder,
  "fa-folder-open": FolderOpen,
  "fa-tachometer-alt": LayoutDashboard,
  "fa-th": LayoutDashboard,
};

export default {
  name: "app-shell",
  components: {
    Check,
    ChevronsUpDown,
    FlaskConical,
    GatewayNoticesContainer,
    Link2,
    LogOut,
    Settings,
  },
  props: {
    title: { type: String, default: "Airavata" },
    logoUrl: { type: String, default: null },
    logoBackgroundColor: { type: String, default: null },
    navItems: {
      type: Array,
      default: () => [],
    },
    apps: {
      type: Array,
      default: () => [],
    },
    menuLinks: {
      type: Array,
      default: () => [],
    },
    user: {
      type: Object,
      default: null,
    },
    accountUrl: { type: String, default: null },
    logoutUrl: { type: String, default: null },
    notices: {
      type: Array,
      default: null,
    },
    unreadCount: {
      type: Number,
      default: 0,
    },
  },
  computed: {
    logoBackgroundStyle() {
      return this.logoBackgroundColor
        ? { backgroundColor: this.logoBackgroundColor }
        : {};
    },
    currentApp() {
      return this.apps.find((app) => app.current) || null;
    },
    currentAppLabel() {
      return this.currentApp ? this.currentApp.label : "Menu";
    },
    currentAppIcon() {
      return this.currentApp ? this.iconFor(this.currentApp) : Layers;
    },
    userName() {
      if (!this.user) {
        return "";
      }
      const name = [this.user.first_name, this.user.last_name]
        .filter(Boolean)
        .join(" ")
        .trim();
      return name || this.user.username || "Account";
    },
    userInitials() {
      const source = this.userName;
      if (!source) {
        return "?";
      }
      const parts = source.split(/\s+/).filter(Boolean);
      const initials = parts.slice(0, 2).map((p) => p[0]);
      return initials.join("").toUpperCase() || "?";
    },
    utilityButtonClasses() {
      return "flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm font-medium text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring";
    },
  },
  methods: {
    iconFor(item) {
      // The context processors emit icon strings like "fa fa-flask"; pull the
      // specific fa-* token and map it, defaulting to a generic icon.
      const raw = item && item.icon ? String(item.icon) : "";
      const token = raw.split(/\s+/).find((t) => t.startsWith("fa-"));
      return FA_ICON_MAP[token] || LayoutDashboard;
    },
    navItemClasses(active) {
      const base =
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring";
      return active
        ? `${base} bg-sidebar-primary text-sidebar-primary-foreground`
        : `${base} text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground`;
    },
  },
};
</script>
