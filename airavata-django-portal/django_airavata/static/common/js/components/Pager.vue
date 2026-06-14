<template>
  <div class="flex items-center justify-end gap-2 text-sm text-muted-foreground">
    <span v-if="hasPrevious">
      <a
        href="#"
        class="inline-flex items-center gap-1 whitespace-nowrap text-primary hover:underline"
        v-on:click.prevent="getPrevious"
      >
        <ChevronLeft class="size-4" aria-hidden="true" /> Previous</a
      >
    </span>
    <span> Showing {{ first }} - {{ last }} </span>
    <span v-if="hasNext">
      <a
        href="#"
        class="inline-flex items-center gap-1 whitespace-nowrap text-primary hover:underline"
        v-on:click.prevent="getNext"
        >Next <ChevronRight class="size-4" aria-hidden="true"
      /></a>
    </span>
  </div>
</template>

<script>
/* eslint-disable vue/multi-word-component-names */
import { ChevronLeft, ChevronRight } from "@lucide/vue";
import { utils } from "django-airavata-api";

export default {
  components: { ChevronLeft, ChevronRight },
  props: {
    paginator: utils.PaginationIterator,
  },
  name: "pager",
  methods: {
    getNext: function () {
      this.$emit("next");
    },
    getPrevious: function () {
      this.$emit("previous");
    },
  },
  computed: {
    hasNext: function () {
      return this.paginator && this.paginator.hasNext();
    },
    hasPrevious: function () {
      return this.paginator && this.paginator.hasPrevious();
    },
    first: function () {
      return this.paginator ? this.paginator.offset + 1 : null;
    },
    last: function () {
      if (this.paginator) {
        if (this.paginator.count) {
          return Math.min(
            this.paginator.offset + this.paginator.limit,
            this.paginator.count
          );
        } else {
          return this.paginator.offset + this.paginator.results.length;
        }
      } else {
        return null;
      }
    },
  },
};
</script>
