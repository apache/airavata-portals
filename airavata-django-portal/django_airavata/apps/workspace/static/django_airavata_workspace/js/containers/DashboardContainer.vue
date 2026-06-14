<template>
  <div>
    <pga-link />
    <div>
      <workspace-notices-management-container />
      <h2 class="mb-2 text-sm font-semibold text-muted-foreground uppercase">
        Applications
      </h2>
    </div>
    <div v-if="showNewUserMessage" class="mb-4">
      <Alert>
        <AlertDescription
          >Welcome {{ userProfile.first_name }} {{ userProfile.last_name }}! You
          currently don't have access to run any applications but the
          administrator of this gateway has been notified and will be in contact
          to grant you the appropriate privileges.</AlertDescription
        >
      </Alert>
    </div>
    <template v-if="favoriteApplicationsData.length > 0">
      <div>
        <h2 class="mb-2 text-lg font-semibold">Favorites</h2>
      </div>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <application-card
          v-for="item in favoriteApplicationsData"
          v-bind:appModule="item.appModule"
          v-bind:key="item.appModule.app_module_id"
          @app-selected="handleAppSelected"
          :disabled="item.disabled"
          @favorite="markFavorite(item.appModule)"
          @unfavorite="markNotFavorite(item.appModule)"
          ref="favoriteApplicationCards"
        >
          <template #card-actions>
            <favorite-toggle
              :favorite="true"
              @favorite="markFavorite(item.appModule)"
              @unfavorite="markNotFavorite(item.appModule)"
            />
          </template>
        </application-card>
      </div>
      <Separator class="my-4" />
    </template>
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <application-card
        v-for="item in nonFavoriteApplicationsData"
        v-bind:appModule="item.appModule"
        v-bind:key="item.appModule.app_module_id"
        @app-selected="handleAppSelected"
        :disabled="item.disabled"
        @favorite="markFavorite(item.appModule)"
        @unfavorite="markNotFavorite(item.appModule)"
      >
        <template #card-actions>
          <favorite-toggle
            :favorite="false"
            @favorite="markFavorite(item.appModule)"
            @unfavorite="markNotFavorite(item.appModule)"
          />
        </template>
      </application-card>
    </div>
  </div>
</template>

<script>
import { services, session } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";
import urls from "../utils/urls";
import PgaLink from "../components/PgaLink";
import WorkspaceNoticesManagementContainer from "../components/notices/WorkspaceNoticesManagementContainer";

export default {
  name: "dashboard-container",
  data() {
    return {
      accessibleAppModules: null,
      userProfile: null,
      allApplicationModules: null,
      workspacePreferences: null,
    };
  },
  components: {
    WorkspaceNoticesManagementContainer,
    "application-card": comps.ApplicationCard,
    "favorite-toggle": comps.FavoriteToggle,
    "pga-link": PgaLink,
  },
  methods: {
    handleAppSelected: function (appModule) {
      urls.navigateToCreateExperiment(appModule);
    },
    markFavorite(appModule) {
      services.ApplicationModuleService.favorite({
        lookup: appModule.app_module_id,
      })
        .then(() => {
          return services.WorkspacePreferencesService.get().then(
            (prefs) => (this.workspacePreferences = prefs),
          );
        })
        .then(() => {
          const index = this.favoriteApplicationsData.findIndex(
            (data) => data.appModule.app_module_id === appModule.app_module_id,
          );
          this.$nextTick(() => {
            this.$refs.favoriteApplicationCards[index].$el.scrollIntoView({
              behavior: "smooth",
              block: "center",
            });
          });
        });
    },
    markNotFavorite(appModule) {
      services.ApplicationModuleService.unfavorite({
        lookup: appModule.app_module_id,
      }).then(() => {
        return services.WorkspacePreferencesService.get().then(
          (prefs) => (this.workspacePreferences = prefs),
        );
      });
    },
  },
  computed: {
    isNewUser() {
      return (
        this.userProfile &&
        Date.now() - this.userProfile.creation_time.getTime() <
          7 * 24 * 60 * 60 * 1000
      );
    },
    showNewUserMessage() {
      return (
        this.isNewUser &&
        this.userProfile &&
        this.accessibleAppModules &&
        this.accessibleAppModules.length === 0
      );
    },
    accessibleModuleIds() {
      return this.accessibleAppModules
        ? this.accessibleAppModules.map((a) => a.app_module_id)
        : [];
    },
    allApplicationData() {
      return this.allApplicationModules
        ? this.allApplicationModules.map((app) => {
            return {
              appModule: app,
              disabled: this.accessibleModuleIds.indexOf(app.app_module_id) < 0,
            };
          })
        : [];
    },
    favoriteApplicationsData() {
      return this.allApplicationData.filter(
        (app) =>
          this.favoriteApplicationIds.indexOf(app.appModule.app_module_id) >= 0,
      );
    },
    nonFavoriteApplicationsData() {
      return this.allApplicationData.filter(
        (app) =>
          this.favoriteApplicationIds.indexOf(app.appModule.app_module_id) < 0,
      );
    },
    favoriteApplicationIds() {
      if (
        this.workspacePreferences &&
        this.workspacePreferences.application_preferences
      ) {
        return this.workspacePreferences.application_preferences
          .filter((p) => p.favorite)
          .map((p) => p.application_id);
      } else {
        return [];
      }
    },
  },
  beforeMount: function () {
    services.ApplicationModuleService.list().then(
      (result) => (this.accessibleAppModules = result),
    );
    services.UserProfileService.retrieve({
      lookup: session.Session.username,
    }).then((userProfile) => (this.userProfile = userProfile));
    // Load all application, including ones that aren't accessible by this user
    services.ApplicationModuleService.listAll().then(
      (result) => (this.allApplicationModules = result),
    );
    services.WorkspacePreferencesService.get().then(
      (prefs) => (this.workspacePreferences = prefs),
    );
  },
};
</script>
