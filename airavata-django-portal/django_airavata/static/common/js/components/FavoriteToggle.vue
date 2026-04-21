<template>
  <a v-b-tooltip class="text-primary" :title="titleText" @click.stop="toggleFavorite">
    <i class="fa fa-star favorite-toggle" :class="classes"
      ><span class="visually-hidden">Toggle favorite</span></i
    >
  </a>
</template>

<script>
export default {
  name: "FavoriteToggle",
  props: {
    favorite: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    classes() {
      if (!this.favorite) {
        return ["not-favorite"];
      } else {
        return [];
      }
    },
    titleText() {
      if (this.favorite) {
        return "Unmark as favorite";
      } else {
        return "Mark as favorite";
      }
    },
  },
  methods: {
    toggleFavorite() {
      if (this.favorite) {
        this.$emit("unfavorite");
      } else {
        this.$emit("favorite");
      }
    },
  },
};
</script>

<style scoped>
.not-favorite {
  color: #999999;
}
.not-favorite:hover {
  color: inherit;
}
</style>
