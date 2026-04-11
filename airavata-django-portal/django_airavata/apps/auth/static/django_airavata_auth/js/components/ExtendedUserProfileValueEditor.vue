<template>
  <div class="mb-3">
    <label class="form-label">
      {{ extendedUserProfileField.name }}
      <small
        v-if="!extendedUserProfileField.required"
        class="text-muted text-small"
        >(Optional)</small
      >
    </label>
    <div class="card ms-3 mb-3"
      v-for="link in extendedUserProfileField.links"
      :key="link.id"
    >
      <div class="card-header">{{ link.label }}</div>
      <div class="card-body">
        <div v-if="link.display_inline">
          <iframe :src="link.url" />
        </div>
        <a
          v-if="link.display_link"
          :href="link.url"
          target="_blank"
          class="card-link"
          >Open '{{ link.label }}' in separate tab.</a
        >
      </div>
    </div>
    <slot />
    <small v-if="extendedUserProfileField.help_text" class="form-text text-muted">
      {{ extendedUserProfileField.help_text }}
    </small>
  </div>
</template>

<script>
export default {
  props: ["extendedUserProfileField"],
};
</script>

<style scoped>
iframe {
  border: none;
  width: 100%;
  height: 50vh;
}
</style>
