<template>
  <div class="autocomplete-text-input">
    <div class="input-group">
      <span class="input-group-text">
        <i class="fa fa-search"></i>
      </span>
      <input
        class="form-control"
        type="text"
        :value="searchValue"
        :placeholder="placeholder"
        @input="updateSearchValue"
        @keydown.enter="enter"
        @keydown.down="down"
        @keydown.up="up"
      />
    </div>
    <ul v-if="open" class="list-group autocomplete-suggestion-list">
      <li
        v-for="(suggestion, index) in filtered"
        :key="suggestion.id"
        class="list-group-item"
        :class="{ active: isActive(index) }"
        @click="suggestionClick(index)"
      >
        <slot name="suggestion" :suggestion="suggestion">
          {{ suggestion.name }}
        </slot>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";

interface Suggestion {
  id: string | number;
  name: string;
  type?: string;
  user?: {
    first_name?: string;
    last_name?: string;
    user_id?: string;
    email?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

const props = defineProps<{
  suggestions: Suggestion[];
  placeholder?: string;
  maxMatches?: number;
}>();

const emit = defineEmits<{
  "search-changed": [value: string];
  selected: [suggestion: Suggestion];
}>();

const open = ref(false);
const current = ref(0);
const searchValue = ref("");

const filtered = computed(() =>
  props.suggestions
    .filter((data) => data.name.toLowerCase().indexOf(searchValue.value.toLowerCase()) >= 0)
    .slice(0, props.maxMatches ?? 5),
);

function updateSearchValue(event: Event): void {
  const value = (event.target as HTMLInputElement).value;
  if (open.value === false) {
    open.value = true;
    current.value = 0;
  }
  if (value === "") {
    open.value = false;
  }
  searchValue.value = value;
  emit("search-changed", value);
}

function enter(): void {
  if (filtered.value.length === 0) {
    return;
  }
  emitSelectedItem(current.value);
  searchValue.value = "";
  open.value = false;
}

function up(): void {
  if (current.value > 0) {
    current.value--;
  }
}

function down(): void {
  if (current.value < filtered.value.length - 1) {
    current.value++;
  }
}

function isActive(index: number): boolean {
  return index === current.value;
}

function suggestionClick(index: number): void {
  emitSelectedItem(index);
  searchValue.value = "";
  open.value = false;
}

function emitSelectedItem(index: number): void {
  emit("selected", filtered.value[index]);
}
</script>

<style scoped>
.autocomplete-text-input {
  position: relative;
}
.autocomplete-suggestion-list {
  width: 100%;
  position: absolute;
  z-index: 3;
}
</style>
