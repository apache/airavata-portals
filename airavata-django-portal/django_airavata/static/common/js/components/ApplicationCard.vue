<template>
  <div class="application-card">
    <Card
      class="h-full transition-colors"
      :class="
        disabled
          ? 'cursor-not-allowed bg-muted'
          : 'cursor-pointer hover:bg-accent/40'
      "
    >
      <a
        href="#"
        class="block h-full text-foreground"
        :class="{ 'pointer-events-none': disabled }"
        @click.prevent="handleAppClick"
      >
        <CardContent class="space-y-2">
          <h2 class="text-lg font-semibold leading-tight">
            {{ appModule.app_module_name }}
          </h2>
          <div class="flex flex-wrap gap-1">
            <Badge v-for="tag in appModule.tags" :key="tag">{{ tag }}</Badge>
            <Badge v-if="appModule.app_module_version">{{
              appModule.app_module_version
            }}</Badge>
          </div>
          <p class="text-sm leading-snug text-muted-foreground">
            <linkify>
              {{ appModule.app_module_description }}
            </linkify>
          </p>
          <div>
            <slot name="card-actions"> </slot>
          </div>
        </CardContent>
      </a>
    </Card>
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
      if (this.disabled) {
        return;
      }
      this.$emit("app-selected", this.appModule);
    },
  },
};
</script>
