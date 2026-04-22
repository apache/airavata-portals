<template>
  <div class="card" header="External IDP Userinfo">
    <!-- TODO: Replace b-table with native table -->
    <table class="table" :items="items" small borderless sort-by="claim" />
    <small class="text-muted"
      >This is the user information provided by the user's authentication provider. The IDP alias
      used is {{ externalIDPUserInfo.idp_alias || "N/A" }}.
    </small>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  externalIDPUserInfo: {
    idp_alias?: string;
    userinfo?: Record<string, unknown>;
  };
}>();

const userinfo = computed(() => props.externalIDPUserInfo.userinfo ?? {});

const items = computed(() =>
  Object.keys(userinfo.value).map((claim) => ({
    claim,
    value: userinfo.value[claim],
  }))
);
</script>

<style></style>
