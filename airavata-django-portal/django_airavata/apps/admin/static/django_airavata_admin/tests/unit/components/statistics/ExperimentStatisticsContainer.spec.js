import { render, fireEvent, waitFor, within } from "@testing-library/vue";
import "@testing-library/jest-dom";
import { h } from "vue";
import ExperimentStatisticsContainer from "@/components/statistics/ExperimentStatisticsContainer.vue";
import { components as UI } from "django-airavata-common-ui";
import * as shadcnUI from "django-airavata-common-ui/js/components/ui";
import FlatPickr from "vue-flatpickr-component";

// Vue 3 has no global Vue; register the shared shadcn-vue UI components and the
// portal's common components per render via testing-library's `global` option.
// (The app's entry() registers the shadcn UI globally at runtime; the tests do
// the equivalent here since they mount the component directly.)
const globalComponents = { "flat-pickr": FlatPickr };
for (const [name, component] of Object.entries({ ...shadcnUI, ...UI })) {
  if (/^[A-Z]/.test(name) && component && typeof component === "object") {
    globalComponents[name] = component;
  }
}
const renderOptions = {
  global: {
    components: globalComponents,
  },
};

// The app's main.js wraps the whole tree in a <TooltipProvider> so the shadcn-vue
// <Tooltip> instances used across the admin app (incl. common components like
// ClipboardCopyLink) have the reka-ui provider context. Mirror that here when
// rendering a component directly.
function renderWithProviders(component) {
  const Wrapper = {
    render() {
      return h(shadcnUI.TooltipProvider, () => [h(component)]);
    },
  };
  return render(Wrapper, renderOptions);
}

import { models, services, utils } from "django-airavata-api";
import ExperimentStatus from "django-airavata-api/static/django_airavata_api/js/models/ExperimentStatus";
vi.mock("django-airavata-api", async () => {
  const originalModule = await vi.importActual("django-airavata-api");
  return {
    __esModule: true,
    ...originalModule,
    // Mock just the RESTful service calls
    services: {
      ApplicationInterfaceService: {
        list: vi.fn(),
      },
      ExperimentStatisticsService: {
        get: vi.fn(),
      },
      ComputeResourceService: {
        namesList: vi.fn(),
      },
      ExperimentSearchService: {
        list: vi.fn(),
      },
      ExperimentService: {
        retrieve: vi.fn(),
      },
      FullExperimentService: {
        retrieve: vi.fn(),
      },
      GroupResourceProfileService: {
        list: vi.fn(),
      },
      ExperimentArchiveService: {
        get: vi.fn(),
      },
    },
  };
});

beforeEach(() => {
  vi.resetAllMocks();

  const spinner = document.createElement("div");
  spinner.id = "airavata-spinner";
  document.body.appendChild(spinner);

  // jsdom doesn't implement scrollIntoView so just provide a stubbed implementation
  Element.prototype.scrollIntoView = vi.fn();
});

test("load experiment by job id when job id matches unique experiment", async () => {
  // Service call mocks
  services.ApplicationInterfaceService.list.mockResolvedValue([]);
  services.ExperimentStatisticsService.get.mockResolvedValue(
    new utils.PaginationIterator(
      {
        count: 0,
        next: null,
        previous: null,
        results: {
          all_experiment_count: 0,
          completed_experiment_count: 0,
          cancelled_experiment_count: 0,
          failed_experiment_count: 0,
          created_experiment_count: 0,
          running_experiment_count: 0,
          all_experiments: [],
          completed_experiments: [],
          failed_experiments: [],
          cancelled_experiments: [],
          created_experiments: [],
          running_experiments: [],
        },
        limit: 50,
        offset: 0,
      },
      models.ExperimentStatistics
    )
  );
  services.ComputeResourceService.namesList.mockResolvedValue([]);
  services.ExperimentSearchService.list.mockResolvedValue(
    new utils.PaginationIterator(
      {
        count: 1,
        next: null,
        previous: null,
        results: [{ experiment_id: "test-experiment-id" }],
      },
      models.ExperimentSummary
    )
  );
  // Mock just enough of Experiment and FullExperiment to get ExperimentDetailsView to render
  const experiment = new models.Experiment({
    experiment_id: "test-experiment-id",
    experiment_name: "Test Experiment",
    creation_time: Date.now(),
    experiment_status: [
      new ExperimentStatus({
        time_of_state_change: Date.now(),
        state: models.ExperimentState.COMPLETED,
      }),
    ],
  });
  services.ExperimentService.retrieve.mockResolvedValue(experiment);
  services.FullExperimentService.retrieve.mockResolvedValue(
    new models.FullExperiment({
      experiment_id: "test-experiment-id",
      experiment,
    })
  );
  services.ExperimentArchiveService.get.mockResolvedValue({
    archived: false,
    archive_name: null,
    created_date: null,
    max_age: 90,
  });

  // The render method returns a collection of utilities to query your component.
  const { findByText, findByPlaceholderText } = renderWithProviders(
    ExperimentStatisticsContainer
  );

  const byJobIDTab = await findByText("By Job ID");

  // reka-ui's Tabs (automatic activation) switch on focus; dispatch focus before
  // the click so the tab panel becomes active in jsdom (which does not emulate
  // the focus-follows-pointer behavior a real browser provides on click).
  const byJobIDTrigger = byJobIDTab.closest('[role="tab"]') || byJobIDTab;
  await fireEvent.focus(byJobIDTrigger);
  await fireEvent.click(byJobIDTrigger);

  const jobIDInputField = await findByPlaceholderText("Job ID");

  await fireEvent.update(jobIDInputField, "12345");

  const loadButton = await within(jobIDInputField.parentElement).findByText(
    "Load"
  );

  await fireEvent.click(loadButton);

  // The job's tab has the job id instead of the normal experiment name
  const jobTab = await findByText("Job 12345");

  expect(jobTab).toBeVisible();

  // Double check that the experiment services were called to load the experiment
  expect(services.ExperimentService.retrieve).toHaveBeenCalledWith(
    {
      lookup: experiment.experiment_id,
    },
    {
      ignoreErrors: true,
    }
  );
  // The experiment-details tab is activated asynchronously (setTimeout) and its
  // panel (ExperimentDetailsView) mounts lazily on activation, which is when it
  // calls FullExperimentService.retrieve. Wait for that to happen.
  await waitFor(() =>
    expect(services.FullExperimentService.retrieve).toHaveBeenCalledWith({
      lookup: experiment.experiment_id,
    })
  );
});

test("Hostname filter only shows compute resources that are configured in a GRP", async () => {
  // Service call mocks
  services.ApplicationInterfaceService.list.mockResolvedValue([]);
  services.ExperimentStatisticsService.get.mockResolvedValue(
    new utils.PaginationIterator(
      {
        count: 0,
        next: null,
        previous: null,
        results: {
          all_experiment_count: 0,
          completed_experiment_count: 0,
          cancelled_experiment_count: 0,
          failed_experiment_count: 0,
          created_experiment_count: 0,
          running_experiment_count: 0,
          all_experiments: [],
          completed_experiments: [],
          failed_experiments: [],
          cancelled_experiments: [],
          created_experiments: [],
          running_experiments: [],
        },
        limit: 50,
        offset: 0,
      },
      models.ExperimentStatistics
    )
  );
  services.ComputeResourceService.namesList.mockResolvedValue([
    { host_id: "compute4-abcd", host: "d-compute4" },
    { host_id: "compute2-abcd", host: "b-compute2" },
    { host_id: "compute5-abcd", host: "e-compute5" },
    { host_id: "compute3-abcd", host: "c-compute3" },
    { host_id: "compute1-abcd", host: "a-compute1" },
  ]);

  services.GroupResourceProfileService.list.mockResolvedValue([
    new models.GroupResourceProfile({
      compute_preferences: [
        new models.GroupComputeResourcePreference({
          compute_resource_id: "compute1-abcd",
        }),
        new models.GroupComputeResourcePreference({
          compute_resource_id: "compute3-abcd",
        }),
      ],
    }),
    new models.GroupResourceProfile({
      compute_preferences: [
        new models.GroupComputeResourcePreference({
          compute_resource_id: "compute1-abcd",
        }),
        new models.GroupComputeResourcePreference({
          compute_resource_id: "compute4-abcd",
        }),
      ],
    }),
  ]);

  // The render method returns a collection of utilities to query your component.
  const { findByText } = renderWithProviders(ExperimentStatisticsContainer);

  const addFiltersMenu = await findByText("Add Filters");

  await fireEvent.click(addFiltersMenu);

  const hostnameMenuItem = await findByText("Hostname");

  await fireEvent.click(hostnameMenuItem);

  const computeResourcesSelect = await findByText(
    "Select compute resource to filter on"
  );

  const options = computeResourcesSelect.parentElement.options;

  expect(options.length).toBe(4);
  // option 0 is the null one ("Select compute resource to filter on")
  // verify that options 1-3 are compute resources 1, 3, 4. That is, verify that
  // filtering worked and that they were sorted.
  expect(options[1].value).toBe("compute1-abcd");
  expect(options[2].value).toBe("compute3-abcd");
  expect(options[3].value).toBe("compute4-abcd");
});
