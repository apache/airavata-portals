<template>
  <div v-if="value" class="flex items-center pl-3">
    {{ text }}
    <a
      href="#"
      @click.prevent="cancel"
      class="ml-auto inline-flex items-center gap-1 text-destructive"
      >Cancel
      <X class="size-4" aria-hidden="true" />
    </a>
  </div>
  <div v-else>
    <autocomplete-text-input
      :suggestions="suggestions"
      @selected="selected"
      @search-changed="searchChanged"
      :max-matches="10"
    />
  </div>
</template>

<script>
import { X } from "@lucide/vue";
import { utils } from "django-airavata-api";
import { InputEditorMixin } from "django-airavata-workspace-plugin-api";
import { components } from "django-airavata-common-ui";
import { useDebounceFn } from "@vueuse/core";

export default {
  name: "autocomplete-input-editor",
  mixins: [InputEditorMixin],
  components: {
    X,
    "autocomplete-text-input": components.AutocompleteTextInput,
  },
  props: {
    value: {
      type: String,
    },
  },
  data() {
    return {
      text: null,
      searchString: "",
      searchResults: null,
      lastUpdate: Date.now(),
    };
  },
  computed: {
    suggestions() {
      return this.searchResults
        ? this.searchResults.results.map((r) => {
            return {
              id: r.value,
              name: r.text,
            };
          })
        : [];
    },
    autocompleteUrl() {
      if (
        this.experimentInput.editorConfig &&
        "url" in this.experimentInput.editorConfig
      ) {
        return this.experimentInput.editorConfig.url;
      } else {
        console.warn(
          "editor config is missing 'url'. Make sure input " +
            this.experimentInput.name +
            " has metadata configuration something like:\n" +
            JSON.stringify(
              {
                editor: {
                  "ui-component-id": "autocomplete-input-editor",
                  config: {
                    url: "/some/custom/search/",
                  },
                },
              },
              null,
              4,
            ),
        );
        return null;
      }
    },
  },
  methods: {
    loadTextForValue(value) {
      if (this.autocompleteUrl) {
        return utils.FetchUtils.get(
          this.autocompleteUrl,
          {
            exact: value,
          },
          {
            ignoreErrors: true, // don't automatically report errors to user - code will handle 404s
          },
        )
          .then((resp) => {
            if (resp.results && resp.results.length > 0) {
              return resp.results[0].text;
            } else {
              return `value: ${value}`;
            }
          })
          .catch((error) => {
            if (error.details.status === 404) {
              // if we can't fine an exact match, just return the value as the text
              return `value: ${value}`;
            } else {
              throw error;
            }
          });
      } else {
        return Promise.resolve(null);
      }
    },
    cancel() {
      this.data = null;
      this.valueChanged();
    },
    selected(suggestion) {
      this.data = suggestion.id;
      this.text = suggestion.name;
      this.valueChanged();
    },
    searchChanged: useDebounceFn(function (newValue) {
      // TODO: don't query when search value is empty string
      this.searchString = newValue;
      const currentTime = Date.now();
      if (this.autocompleteUrl) {
        utils.FetchUtils.get(
          this.autocompleteUrl,
          {
            search: this.searchString,
          },
          { showSpinner: false },
        ).then((resp) => {
          // Prevent older responses from overwriting newer ones
          if (currentTime > this.lastUpdate) {
            this.searchResults = resp;
            this.lastUpdate = currentTime;
          }
        });
      }
    }, 200),
  },
  created() {
    if (this.value) {
      this.loadTextForValue(this.value).then((text) => (this.text = text));
    }
  },
};
</script>
