<template>
  <div v-if="pgaUrl != null" class="row">
    <div class="col">
      <div class="alert alert-info">
        You're using the new portal interface. To switch back to the old interface, go to
        <a :href="pgaUrl">{{ pgaUrl }}</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeMount } from "vue";
import { services } from "django-airavata-api";

const pgaUrl = ref<string | null>(null);

onBeforeMount(() => {
  services.SettingsService.get().then((s: { pgaUrl?: string | null }) => {
    pgaUrl.value = s.pgaUrl ?? null;
  });
});
</script>

<style></style>
