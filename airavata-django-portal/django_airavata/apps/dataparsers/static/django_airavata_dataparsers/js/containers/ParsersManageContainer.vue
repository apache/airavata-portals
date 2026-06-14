<template>
  <main-layout
    title="Parsers"
    subtitle="Manage data parsers for processing experiment outputs."
  >
    <template #actions>
      <Button as="a" href="create" variant="default">
        Create New Parser
        <Plus class="size-4" aria-hidden="true" />
      </Button>
    </template>
    <Card>
      <CardContent>
        <parser-list v-bind:parsers="parsers"></parser-list>
      </CardContent>
    </Card>
  </main-layout>
</template>

<script>
import { Plus } from "@lucide/vue";
import MainLayout from "django-airavata-common-ui/js/components/MainLayout.vue";
import ParserList from "../parser-components/ParserList.vue";

import { services } from "django-airavata-api";

export default {
  name: "parsers-manage-container",
  props: [],
  data() {
    return {
      parsers: null,
    };
  },
  components: {
    Plus,
    "main-layout": MainLayout,
    "parser-list": ParserList,
  },
  methods: {
    nextParsers: function () {
      this.parserPaginator.next();
    },
    previousParsers: function () {
      this.parserPaginator.previous();
    },
  },
  computed: {},
  beforeMount: function () {
    services.ParserService.list().then((result) => (this.parsers = result));
  },
};
</script>
