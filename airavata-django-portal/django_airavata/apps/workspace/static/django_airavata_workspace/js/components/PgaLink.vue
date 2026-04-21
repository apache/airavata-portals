<template>
  <div v-if="showPGAUrl" class="row">
    <div class="col">
      <div class="alert alert-info">
        You're using the new portal interface. To switch back to the old interface, go to
        <a :href="settings.pgaUrl">{{ settings.pgaUrl }}</a>
      </div>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
export default {
  name: "PgaUrl",
  data() {
    return {
      settings: null,
    };
  },
  computed: {
    showPGAUrl() {
      // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
      return this.settings && this.settings.pgaUrl != null;
    },
  },
  beforeMount() {
    services.SettingsService.get().then((s) => {
      this.settings = s;
    });
  },
};
</script>

<style></style>
