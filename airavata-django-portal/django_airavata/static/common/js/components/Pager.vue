<template>
  <div class="pager">
    <span v-if="hasPrevious" class="pager-element">
      <a href="#" class="action-link" @click.prevent="getPrevious"
        ><i class="fa fa-chevron-left" aria-hidden="true"></i> Previous</a
      >
    </span>
    <span class="pager-element"> Showing {{ first }} - {{ last }} </span>
    <span v-if="hasNext" class="pager-element">
      <a href="#" class="action-link" @click.prevent="getNext"
        >Next <i class="fa fa-chevron-right" aria-hidden="true"></i
      ></a>
    </span>
  </div>
</template>

<script>
/* eslint-disable vue/multi-word-component-names */
import { utils } from "django-airavata-api";

export default {
  name: "Pager",
  props: {
    paginator: utils.PaginationIterator,
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
          return Math.min(this.paginator.offset + this.paginator.limit, this.paginator.count);
        } else {
          return this.paginator.offset + this.paginator.results.length;
        }
      } else {
        return null;
      }
    },
  },
  methods: {
    getNext: function () {
      this.$emit("next");
    },
    getPrevious: function () {
      this.$emit("previous");
    },
  },
};
</script>

<style scoped>
.pager {
  text-align: right;
  font-size: 0.8125rem;
  color: #6c757d;
  padding: 0.5rem 0;
}
.pager-element + .pager-element {
  margin-left: 0.5rem;
}
</style>
