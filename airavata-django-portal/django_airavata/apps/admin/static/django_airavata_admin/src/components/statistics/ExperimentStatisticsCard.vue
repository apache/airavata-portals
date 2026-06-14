<template>
  <Card class="statistics-card overflow-hidden">
    <CardHeader>
      <div class="text-right">
        <div class="statistic-count whitespace-nowrap">
          <abbr :title="count">{{ displayedCount }}</abbr>
        </div>
        <div>{{ title }}</div>
      </div>
    </CardHeader>
    <CardContent>
      <a
        href="#"
        class="text-primary hover:no-underline"
        @click.prevent="$emit('click')"
      >
        <slot name="link-text">
          <div v-for="state in states" :key="state.value">
            {{ shortName(state) }}
          </div>
        </slot>
      </a>
    </CardContent>
  </Card>
</template>

<script>
export default {
  name: "experiment-statistics-card",
  props: {
    bgVariant: {
      type: String,
      default: "light",
    },
    headerTextVariant: {
      type: String,
      default: "dark",
    },
    linkVariant: {
      type: String,
      default: "primary",
    },
    count: {
      type: Number,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
    states: {
      type: Array,
      default: () => [],
    },
  },
  computed: {
    displayedCount() {
      // Round large numbers and display m for 10^6 and k for 10^3
      if (this.count >= Math.pow(10, 6)) {
        return (this.count / Math.pow(10, 6)).toFixed(0) + "m";
      } else if (this.count >= Math.pow(10, 3)) {
        return (this.count / Math.pow(10, 3)).toFixed(0) + "k";
      } else {
        return this.count;
      }
    },
  },
  methods: {
    // Render the prefix-stripped short alias (e.g. "COMPLETED") instead of the
    // raw proto member name ("EXPERIMENT_STATE_COMPLETED"), matching the rest of
    // the portal (see ExperimentStatusBadge).
    shortName(state) {
      return state.constructor.shortAlias(state.name);
    },
  },
};
</script>

<style scoped>
.statistic-count {
  font-size: 2.8rem;
  overflow: hidden;
}
.statistics-card {
  height: calc(100% - 30px);
}
abbr {
  text-decoration: none;
}
</style>
