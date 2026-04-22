<template>
  <div v-if="data" class="d-flex ps-3">
    {{ text }}
    <a class="ms-auto text-danger" @click="cancel">
      Cancel
      <i class="fa fa-times" aria-hidden="true"></i>
    </a>
  </div>
  <div v-else>
    <AutocompleteTextInput
      :suggestions="suggestions"
      :max-matches="10"
      @selected="selected"
      @search-changed="searchChanged"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { utils } from "django-airavata-api";
import { models } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import { useInputEditor } from "@/composables/useInputEditor";

const AutocompleteTextInput = components.AutocompleteTextInput;

type InputDataObjectType = InstanceType<typeof models.InputDataObjectType>;
type Experiment = InstanceType<typeof models.Experiment>;

interface SearchResult {
  value: string;
  text: string;
}

interface SearchResponse {
  results: SearchResult[];
}

interface Suggestion {
  id: string;
  name: string;
}

const props = withDefaults(
  defineProps<{
    modelValue?: string | null;
    experimentInput: InputDataObjectType;
    experiment?: Experiment;
    id: string;
    readOnly?: boolean;
  }>(),
  { modelValue: null, experiment: undefined, readOnly: false },
);

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
  valid: [];
  invalid: [messages: string[]];
}>();

const { data, valueChanged } = useInputEditor(
  props,
  (_, v) => emit("update:modelValue", v),
  () => emit("valid"),
  (msgs) => emit("invalid", msgs),
);

const text = ref<string | null>(null);
const searchString = ref("");
const searchResults = ref<SearchResponse | null>(null);
const lastUpdate = ref(Date.now());

const suggestions = computed<Suggestion[]>(() =>
  searchResults.value
    ? searchResults.value.results.map((r) => ({ id: r.value, name: r.text }))
    : [],
);

const autocompleteUrl = computed<string | null>(() => {
  if (props.experimentInput.editorConfig && "url" in props.experimentInput.editorConfig) {
    return props.experimentInput.editorConfig.url as string;
  } else {
    // eslint-disable-next-line no-console
    console.warn(
      "editor config is missing 'url'. Make sure input " +
        props.experimentInput.name +
        " has metadata configuration something like:\n" +
        JSON.stringify(
          {
            editor: {
              "ui-component-id": "autocomplete-input-editor",
              config: { url: "/some/custom/search/" },
            },
          },
          null,
          4,
        ),
    );
    return null;
  }
});

function loadTextForValue(value: string): Promise<string | null> {
  if (autocompleteUrl.value) {
    return utils.FetchUtils.get(
      autocompleteUrl.value,
      { exact: value },
      { ignoreErrors: true },
    )
      .then((resp: SearchResponse) => {
        if (resp.results && resp.results.length > 0) {
          return resp.results[0].text;
        } else {
          return `value: ${value}`;
        }
      })
      .catch((error: { details: { status: number } }) => {
        if (error.details.status === 404) {
          return `value: ${value}`;
        } else {
          throw error;
        }
      });
  } else {
    return Promise.resolve(null);
  }
}

function cancel() {
  data.value = null;
  valueChanged();
}

function selected(suggestion: Suggestion) {
  data.value = suggestion.id;
  text.value = suggestion.name;
  valueChanged();
}

// Inline debounce wrapper
let debounceTimer: ReturnType<typeof setTimeout> | undefined;
function searchChanged(newValue: string) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    searchString.value = newValue;
    const currentTime = Date.now();
    if (autocompleteUrl.value) {
      utils.FetchUtils.get(
        autocompleteUrl.value,
        { search: searchString.value },
        { showSpinner: false },
      ).then((resp: SearchResponse) => {
        if (currentTime > lastUpdate.value) {
          searchResults.value = resp;
          lastUpdate.value = currentTime;
        }
      });
    }
  }, 200);
}

onMounted(() => {
  if (data.value) {
    loadTextForValue(data.value).then((t) => (text.value = t));
  }
});
</script>
