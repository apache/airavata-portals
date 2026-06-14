<template>
  <div class="autocomplete-text-input">
    <div class="relative">
      <SearchIcon
        class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
      />
      <Input
        type="text"
        class="pl-9"
        :model-value="searchValue"
        :placeholder="placeholder"
        @update:model-value="updateSearchValue"
        @keydown.enter="enter"
        @keydown.down="down"
        @keydown.up="up"
      />
    </div>
    <ul
      v-if="open"
      class="autocomplete-suggestion-list overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md"
    >
      <li
        v-for="(suggestion, index) in filtered"
        :key="suggestion.id"
        class="cursor-pointer px-3 py-2 text-sm"
        :class="
          isActive(index)
            ? 'bg-accent text-accent-foreground'
            : 'hover:bg-accent/60'
        "
        @click="suggestionClick(index)"
      >
        <slot name="suggestion" :suggestion="suggestion">
          {{ suggestion.name }}
        </slot>
      </li>
    </ul>
  </div>
</template>

<script>
import { Search as SearchIcon } from "@lucide/vue";

export default {
  name: "autocomplete-text-input",
  components: { SearchIcon },
  props: {
    suggestions: {
      type: Array,
      required: true,
    },
    placeholder: {
      type: String,
      default: "Type to get suggestions...",
    },
    maxMatches: {
      type: Number,
      default: 5,
    },
  },
  data() {
    return {
      open: false,
      current: 0,
      searchValue: "",
    };
  },

  computed: {
    filtered() {
      return this.suggestions
        .filter((data) => {
          // Case insensitive search
          return (
            data.name.toLowerCase().indexOf(this.searchValue.toLowerCase()) >= 0
          );
        })
        .slice(0, this.maxMatches);
    },
  },
  methods: {
    updateSearchValue(value) {
      if (this.open === false) {
        this.open = true;
        this.current = 0;
      }
      if (value === "") {
        this.open = false;
      }
      this.searchValue = value;
      this.$emit("search-changed", value);
    },
    enter() {
      if (this.filtered.length === 0) {
        return;
      }
      this.emitSelectedItem(this.current);
      this.searchValue = "";
      this.open = false;
    },
    up() {
      if (this.current > 0) {
        this.current--;
      }
    },
    down() {
      if (this.current < this.filtered.length - 1) {
        this.current++;
      }
    },
    isActive(index) {
      return index === this.current;
    },
    suggestionClick(index) {
      this.emitSelectedItem(index);
      this.searchValue = "";
      this.open = false;
    },
    emitSelectedItem(index) {
      this.$emit("selected", this.filtered[index]);
    },
  },
};
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
