<template>
  <div class="has-fixed-footer">
    <div class="row mb-2">
      <div class="col-auto me-auto">
        <h1 class="h4">Extended User Profile Editor</h1>
        <p class="text-muted small">
          Add and edit additional user profile fields for gateway users to
          complete.
        </p>
      </div>
    </div>
    <transition-group name="fade">
      <div
        v-for="field in extendedUserProfileFields"
        class="row"
        :key="field.key"
      >
        <div class="col">
          <extended-user-profile-field-editor
            ref="extendedUserProfileFieldEditors"
            :extendedUserProfileField="field"
            :disabled="!field.user_has_write_access"
            @valid="recordValidChildComponent(field)"
            @invalid="recordInvalidChildComponent(field)"
          />
        </div>
      </div>
    </transition-group>
    <div ref="bottom" />
    <div class="fixed-footer">
      <div class="d-flex">
        <div class="dropdown" text="Add Field" :disabled="!isGatewayAdmin">
          <a class="dropdown-item" @click="addField('text')">Text</a>
          <a class="dropdown-item" @click="addField('single_choice')"
            >Single Choice</a
          >
          <a class="dropdown-item" @click="addField('multi_choice')"
            >Multi Choice</a
          >
          <a class="dropdown-item" @click="addField('user_agreement')"
            >User Agreement</a
          >
        </div>
        <button class="btn btn-primary btn-sm ms-2"
          @click="save"
          :disabled="!isGatewayAdmin"
          >Save</button
        >
        <button class="btn btn-secondary btn-sm ms-auto" href="/admin/users"
          >Return to Manage Users</button
        >
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters } from "vuex";
import ExtendedUserProfileFieldEditor from "./field-editors/ExtendedUserProfileFieldEditor.vue";
import { mixins } from "django-airavata-common-ui";
import { session } from "django-airavata-api";
export default {
  mixins: [mixins.ValidationParent],
  components: { ExtendedUserProfileFieldEditor },
  data() {
    return {};
  },
  created() {
    this.loadExtendedUserProfileFields();
  },
  methods: {
    ...mapActions("extendedUserProfile", [
      "loadExtendedUserProfileFields",
      "saveExtendedUserProfileFields",
      "addExtendedUserProfileField",
    ]),
    addField(field_type) {
      this.addExtendedUserProfileField({ field_type });
      this.$nextTick(() => {
        this.$refs.bottom.scrollIntoView();
      });
    },
    addOption(field) {
      if (!field.options) {
        field.options = [];
      }
      field.options.push({ id: null, name: "" });
    },
    deleteOption(field, option) {
      const i = field.options.indexOf(option);
      field.options.splice(i, 1);
    },
    addLink(field) {
      if (!field.links) {
        field.links = [];
      }
      field.links.push({
        id: null,
        url: "",
        title: "",
        display_link: true,
        display_inline: false,
      });
    },
    addConditional(field) {
      if (!field.conditional) {
        field.conditional = {
          id: null,
          conditions: [],
          require_when: true,
          show_when: true,
        };
      }
    },
    deleteLink(field, link) {
      const i = field.links.indexOf(link);
      field.links.splice(i, 1);
    },
    save() {
      if (this.valid) {
        this.saveExtendedUserProfileFields();
      } else {
        this.$refs.extendedUserProfileFieldEditors.forEach((c) => c.touch());
      }
    },
  },
  computed: {
    ...mapGetters("extendedUserProfile", ["extendedUserProfileFields"]),
    valid() {
      return this.childComponentsAreValid;
    },
    isGatewayAdmin() {
      return session.Session.is_gateway_admin;
    },
  },
};
</script>
