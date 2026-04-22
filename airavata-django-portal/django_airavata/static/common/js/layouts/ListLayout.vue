<template>
  <div>
    <div class="row">
      <div class="col-auto me-auto">
        <slot name="title">
          <h1 class="h4 mb-4">{{ title }}</h1>
        </slot>
      </div>
      <div class="col-auto">
        <slot name="additional-buttons"> </slot>
        <slot name="new-item-button">
          <button class="btn btn-primary" :disabled="newButtonDisabled" @click="addNewItem">
            {{ newItemButtonText }}
            <i class="fa fa-plus" aria-hidden="true"></i>
          </button>
        </slot>
      </div>
    </div>
    <div v-if="subtitle" class="row">
      <div class="col">
        <h2 class="subtitle text-uppercase text-muted">{{ subtitle }}</h2>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <slot name="new-item-editor"></slot>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <slot name="item-list" :items="itemsList">Item List goes here</slot>
        <pager
          v-if="itemsPaginator"
          :paginator="itemsPaginator"
          @next="nextItems"
          @previous="previousItems"
        ></pager>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import Pager from "../components/Pager.vue";

const props = withDefaults(defineProps<{
  items?: unknown[] | null;
  itemsPaginator?: unknown | null;
  title?: string;
  subtitle?: string;
  newItemButtonText?: string;
  newButtonDisabled?: boolean;
}>(), {
  items: null,
  itemsPaginator: null,
  title: "Items",
  subtitle: undefined,
  newItemButtonText: "New Item",
  newButtonDisabled: false,
});

const emit = defineEmits<{
  "add-new-item": [];
}>();

const itemsList = computed<unknown[]>(() => {
  if (props.itemsPaginator) {
    return (props.itemsPaginator as { results: unknown[] }).results;
  }
  return props.items ?? [];
});

function nextItems(): void {
  if (props.itemsPaginator) {
    (props.itemsPaginator as { next(): void }).next();
  }
}

function previousItems(): void {
  if (props.itemsPaginator) {
    (props.itemsPaginator as { previous(): void }).previous();
  }
}

function addNewItem(): void {
  emit("add-new-item");
}
</script>

<style scoped>
.subtitle {
  font-size: 0.8125rem;
}
</style>
