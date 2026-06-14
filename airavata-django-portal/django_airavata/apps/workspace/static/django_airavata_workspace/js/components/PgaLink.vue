<template>
  <div v-if="showPGAUrl">
    <Alert>
      <AlertDescription>
        You're using the new portal interface. To switch back to the old
        interface, go to
        <a class="font-medium text-primary" :href="settings.pgaUrl">{{
          settings.pgaUrl
        }}</a>
      </AlertDescription>
    </Alert>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
export default {
  name: "pga-url",
  data() {
    return {
      settings: null,
    };
  },
  computed: {
    showPGAUrl() {
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
