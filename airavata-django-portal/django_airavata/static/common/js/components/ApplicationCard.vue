<template>
  <div class="col-md-6 col-xl-4">
    <div class="card application-card" :class="cardClasses">
      <a
        :disabled="disabled"
        class="card-link text-dark"
        @click.prevent="handleAppClick"
      >
        <div class="card-body">
          <h2 class="card-title h5">{{ appModule.app_module_name }}</h2>
          <span
            class="badge badge-primary me-1"
            v-for="tag in appModule.tags"
            :key="tag"
            >{{ tag }}</span
          >
          <span
            class="badge badge-primary me-1"
            v-if="appModule.app_module_version"
            >{{ appModule.app_module_version }}</span
          >
          <p class="card-text card-text--small mt-3 text-secondary">
            <linkify>
              {{ appModule.app_module_description }}
            </linkify>
          </p>
          <p class="card-text">
            <slot name="card-actions"> </slot>
          </p>
        </div>
      </a>
    </div>
  </div>
</template>

<script>
import Linkify from "./Linkify.vue";
export default {
  components: { Linkify },
  name: "application-card",
  props: ["appModule", "disabled"],
  data: function () {
    return {};
  },
  methods: {
    handleAppClick: function () {
      this.$emit("app-selected", this.appModule);
    },
  },
  computed: {
    cardClasses() {
      return this.disabled ? ["is-disabled"] : [];
    },
  },
};
</script>

<style>
.application-card {
  height: calc(100% - 1.5rem);
}
.application-card .card-link,
.application-card .card-body {
  height: 100%;
}
.application-card .card-title {
  font-size: 0.875rem;
}
</style>
