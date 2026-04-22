<template>
  <sidebar>
    <sidebar-header title="My Recent Experiments" :view-all-url="viewAllExperiments" />
    <sidebar-feed :feed-items="feedItems">
      <template #description="slotProps">
        <experiment-status-badge :status-name="slotProps.feedItem.statusName" />
        <i v-if="slotProps.feedItem.isProgressing" class="fa fa-sync-alt fa-spin ms-1"></i>
      </template>
    </sidebar-feed>
  </sidebar>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import urls from "../utils/urls";
import { errors, models, services, utils } from "django-airavata-api";
import { components } from "django-airavata-common-ui";

const Sidebar = components.Sidebar;
const SidebarHeader = components.SidebarHeader;
const SidebarFeed = components.SidebarFeed;
const ExperimentStatusBadge = components.ExperimentStatusBadge;

interface FeedItem {
  id: string;
  statusName: string;
  title: string;
  url: string;
  timestamp: unknown;
  interfaceId: string;
  isProgressing: boolean;
  type: string | null;
}

const props = withDefaults(defineProps<{
  viewAllExperiments?: string;
  username?: string;
}>(), {
  viewAllExperiments: undefined,
  username: undefined,
});

const feedItems = ref<FeedItem[] | null>(null);
const applicationInterfaces = ref<Record<string, unknown>>({});
const refreshDelay = 10000;

function pollExperiments(): void {
  loadExperiments()
    .then(() => {
      setTimeout(() => {
        pollExperiments();
      }, refreshDelay);
    })
    .catch(() => {
      // If loading experiments fails, just ignore. This can happen if the
      // user navigates away from the page while a request is executing.
    });
}

function loadExperiments(): Promise<void> {
  return services.ExperimentSearchService.list(
    {
      limit: 5,
      offset: 0,
      [models.ExperimentSearchFields.USER_NAME.name]: props.username,
    },
    {
      showSpinner: false,
      ignoreErrors: true,
    },
  ).then((experiments: { results: unknown[] }) => {
    feedItems.value = (experiments.results as Array<Record<string, unknown>>).map((e) => {
      const exp = e as Record<string, unknown>;
      const status = exp.experiment_status as Record<string, unknown>;
      return {
        id: exp.experiment_id as string,
        statusName: status.name as string,
        title: exp.name as string,
        url: urls.viewExperiment(
          exp.project_id as string,
          { experiment_id: exp.experiment_id as string },
        ),
        timestamp: exp.status_update_time,
        interfaceId: exp.execution_id as string,
        isProgressing: (exp as unknown as { convertToExperiment(): { isProgressing: boolean } }).convertToExperiment().isProgressing,
        type: null,
      };
    });
    // Load any application interfaces that haven't been loaded yet, so that
    // we can display the applicationName of each experiment
    const unloadedInterfaceIds: Record<string, boolean> = {};
    (feedItems.value ?? [])
      .filter((i) => !(i.interfaceId in applicationInterfaces.value))
      .forEach((i) => (unloadedInterfaceIds[i.interfaceId] = true));
    Promise.all(
      Object.keys(unloadedInterfaceIds).map((interfaceId) => {
        return loadApplicationInterface(interfaceId);
      }),
    ).then(() => {
      populateApplicationNames();
    });
  });
}

function loadApplicationInterface(interfaceId: string): Promise<void> {
  return services.ApplicationInterfaceService.retrieve(
    {
      lookup: interfaceId,
    },
    {
      showSpinner: false,
      ignoreErrors: true,
    },
  )
    .then((applicationInterface: unknown) => {
      applicationInterfaces.value[interfaceId] = applicationInterface;
    })
    .catch((error: unknown) => {
      // ignore if missing
      if (errors.ErrorUtils.isNotFoundError(error)) {
        applicationInterfaces.value[interfaceId] = null;
      } else {
        throw error;
      }
    })
    .catch((err: unknown) => (utils.FetchUtils as unknown as { reportError(_e: unknown): void }).reportError(err));
}

function populateApplicationNames(): void {
  (feedItems.value ?? [])
    .filter((i) => i.type === null)
    .forEach((feedItem) => {
      if (
        feedItem.interfaceId in applicationInterfaces.value &&
        applicationInterfaces.value[feedItem.interfaceId]
      ) {
        const iface = applicationInterfaces.value[feedItem.interfaceId] as Record<string, unknown>;
        feedItem.type = iface.application_name as string;
      }
    });
}

onMounted(() => {
  pollExperiments();
});
</script>
