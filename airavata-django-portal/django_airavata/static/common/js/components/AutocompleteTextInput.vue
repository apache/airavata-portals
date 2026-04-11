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
    <ul class="list-group autocomplete-suggestion-list" v-if="open">
      <li
        class="list-group-item"
        v-for="(suggestion, index) in filtered"
        v-bind:class="{ active: isActive(index) }"
        @click="suggestionClick(index)"
        v-bind:key="suggestion.id"
      >
        <slot name="suggestion" :suggestion="suggestion">
          {{ suggestion.name }}
        </slot>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: "autocomplete-text-input",
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
    updateSearchValue(event) {
      const value = event.target.value;
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
