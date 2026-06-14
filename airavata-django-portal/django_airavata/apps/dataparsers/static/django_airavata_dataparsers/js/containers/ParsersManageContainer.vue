<template>
  <div>
    <div class="mb-4 flex items-center justify-between gap-2">
      <h1 class="text-xl font-semibold">Parsers</h1>
      <Button as="a" href="create" variant="default">
        Create New Parser
        <Plus class="size-4" aria-hidden="true" />
      </Button>
    </div>
    <Card>
      <CardContent>
        <parser-list v-bind:parsers="parsers"></parser-list>
      </CardContent>
    </Card>
  </div>
</template>

<script>
import { Plus } from "@lucide/vue";
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
  computed: {
    // parsers: function() {
    //     return this.parserPaginator ? this.parserPaginator.results : null;
    // },
  },
  beforeMount: function () {
    services.ParserService.list().then((result) => (this.parsers = result));
  },
};
</script>
