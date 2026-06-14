<template>
  <div class="space-y-4">
    <!-- Section header: title + optional subtitle on the left, actions on the
         right. Matches MainLayout's title/subtitle conventions but at section
         (h2) level, since multiple list-layouts can appear on one page. -->
    <header class="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
      <div class="min-w-0">
        <slot name="title">
          <h2 class="text-lg font-semibold">{{ title }}</h2>
        </slot>
        <p v-if="subtitle" class="mt-1 text-sm text-muted-foreground">
          {{ subtitle }}
        </p>
      </div>
      <div class="flex shrink-0 flex-wrap items-center gap-2">
        <slot name="additional-buttons"> </slot>
        <slot name="new-item-button">
          <Button @click="addNewItem" :disabled="newButtonDisabled">
            {{ newItemButtonText }}
            <Plus class="size-4" aria-hidden="true" />
          </Button>
        </slot>
      </div>
    </header>
    <slot name="new-item-editor"></slot>
    <div>
      <slot name="item-list" :items="itemsList">Item List goes here</slot>
      <pager
        v-if="itemsPaginator"
        :paginator="itemsPaginator"
        next="nextItems"
        v-on:previous="previousItems"
      ></pager>
    </div>
  </div>
</template>

<script>
import { Plus } from "@lucide/vue";
import { utils } from "django-airavata-api";
import Pager from "../components/Pager.vue";

export default {
  components: { Plus, pager: Pager },
  props: {
    items: Array,
    itemsPaginator: utils.PaginationIterator,
    title: {
      type: String,
      default: "Items",
    },
    subtitle: {
      type: String,
    },
    newItemButtonText: {
      type: String,
      default: "New Item",
    },
    newButtonDisabled: {
      type: Boolean,
      default: false,
    },
  },
  name: "list-layout",
  data() {
    return {};
  },
  methods: {
    nextItems: function () {
      this.itemsPaginator.next();
    },
    previousItems: function () {
      this.itemsPaginator.previous();
    },
    addNewItem: function () {
      this.$emit("add-new-item");
    },
  },
  computed: {
    itemsList: function () {
      return this.itemsPaginator ? this.itemsPaginator.results : this.items;
    },
  },
};
</script>
