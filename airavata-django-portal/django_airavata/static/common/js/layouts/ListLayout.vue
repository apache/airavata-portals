<template>
  <div>
    <div class="flex items-start justify-between gap-2">
      <div class="mr-auto">
        <slot name="title">
          <h1 class="mb-4 text-xl font-semibold">{{ title }}</h1>
        </slot>
      </div>
      <div class="flex items-center gap-2">
        <slot name="additional-buttons"> </slot>
        <slot name="new-item-button">
          <Button @click="addNewItem" :disabled="newButtonDisabled">
            {{ newItemButtonText }}
            <Plus class="size-4" aria-hidden="true" />
          </Button>
        </slot>
      </div>
    </div>
    <div v-if="subtitle">
      <h2 class="text-sm uppercase text-muted-foreground">{{ subtitle }}</h2>
    </div>
    <div>
      <slot name="new-item-editor"></slot>
    </div>
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
