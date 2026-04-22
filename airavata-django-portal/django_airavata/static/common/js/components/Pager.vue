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

<script setup lang="ts">
/* eslint-disable vue/multi-word-component-names */
import { computed } from "vue";

interface Paginator {
  hasNext(): boolean;
  hasPrevious(): boolean;
  offset: number;
  limit: number;
  count?: number;
  results: unknown[];
}

const props = defineProps<{
  paginator?: Paginator;
}>();

const emit = defineEmits<{
  next: [];
  previous: [];
}>();

const hasNext = computed(() => props.paginator && props.paginator.hasNext());
const hasPrevious = computed(() => props.paginator && props.paginator.hasPrevious());
const first = computed(() => (props.paginator ? props.paginator.offset + 1 : null));
const last = computed(() => {
  if (props.paginator) {
    if (props.paginator.count) {
      return Math.min(props.paginator.offset + props.paginator.limit, props.paginator.count);
    } else {
      return props.paginator.offset + props.paginator.results.length;
    }
  } else {
    return null;
  }
});

function getNext(): void {
  emit("next");
}

function getPrevious(): void {
  emit("previous");
}
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
