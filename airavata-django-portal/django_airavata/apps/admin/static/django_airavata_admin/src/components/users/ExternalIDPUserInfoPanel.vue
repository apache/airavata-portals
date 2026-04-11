<template>
  <div class="card" header="External IDP Userinfo">
    <!-- TODO: Replace b-table with native table --><table class="table" :items="items" small borderless sort-by="claim" />
    <small class="text-muted"
      >This is the user information provided by the user's authentication
      provider. The IDP alias used is
      {{ externalIDPUserInfo.idp_alias || "N/A" }}.
    </small>
  </div>
</template>

<script>
export default {
  name: "external-idp-user-info-panel",
  props: ["externalIDPUserInfo"],
  computed: {
    userinfo() {
      return this.external_idp_user_info.userinfo
        ? this.external_idp_user_info.userinfo
        : {};
    },
    items() {
      return Object.keys(this.userinfo).map((claim) => {
        return {
          claim: claim,
          value: this.external_idp_user_info.userinfo[claim],
        };
      });
    },
  },
};
</script>

<style></style>
