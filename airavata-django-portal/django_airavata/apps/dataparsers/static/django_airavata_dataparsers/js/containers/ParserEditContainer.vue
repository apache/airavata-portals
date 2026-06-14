<template>
  <main-layout :title="title" :subtitle="subtitle">
    <parser-editor
      v-if="parser"
      :parser="parser"
      @saved="handleSaved"
      @cancelled="handleCancelled"
    ></parser-editor>
  </main-layout>
</template>

<script>
import MainLayout from "django-airavata-common-ui/js/components/MainLayout.vue";
import ParserEditor from "../parser-components/ParserEditor.vue";

import { models, services } from "django-airavata-api";

export default {
  name: "parser-edit-container",
  props: {
    parserId: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      parser: null,
    };
  },
  components: {
    "main-layout": MainLayout,
    ParserEditor,
  },
  methods: {
    handleSaved: function () {
      window.location.assign("/dataparsers/");
    },
    handleCancelled: function () {
      window.location.assign("/dataparsers/");
    },
  },
  computed: {
    title: function () {
      return this.parserId ? "Edit Parser" : "Create Parser";
    },
    subtitle: function () {
      return this.parserId
        ? "Update this data parser's configuration."
        : "Configure and register a new data parser.";
    },
  },
  mounted: function () {
    // No parserId means this is the "create parser" page: start from an empty
    // parser instead of fetching (retrieving a null id errors server-side).
    if (this.parserId) {
      services.ParserService.retrieve({ lookup: this.parserId }).then(
        (parser) => (this.parser = parser)
      );
    } else {
      this.parser = new models.Parser();
    }
  },
};
</script>
