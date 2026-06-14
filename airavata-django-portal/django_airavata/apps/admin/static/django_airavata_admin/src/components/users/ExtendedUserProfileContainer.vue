<template>
  <main-layout
    title="Extended User Profile"
    subtitle="Add and edit additional user profile fields for gateway users to complete."
  >
    <div class="pb-20">
      <transition-group name="fade">
        <div
          v-for="field in extendedUserProfileFields"
          class="mb-4"
          :key="field.key"
        >
          <extended-user-profile-field-editor
            ref="extendedUserProfileFieldEditors"
            :extendedUserProfileField="field"
            :disabled="!field.userHasWriteAccess"
            @valid="recordValidChildComponent(field)"
            @invalid="recordInvalidChildComponent(field)"
          />
        </div>
      </transition-group>
      <div ref="bottom" />
    </div>
    <div class="bg-background fixed inset-x-0 bottom-0 border-t p-4 shadow-md">
      <div class="flex">
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="outline" :disabled="!isGatewayAdmin"
              >Add Field</Button
            >
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem @click="addField('text')">Text</DropdownMenuItem>
            <DropdownMenuItem @click="addField('single_choice')"
              >Single Choice</DropdownMenuItem
            >
            <DropdownMenuItem @click="addField('multi_choice')"
              >Multi Choice</DropdownMenuItem
            >
            <DropdownMenuItem @click="addField('user_agreement')"
              >User Agreement</DropdownMenuItem
            >
          </DropdownMenuContent>
        </DropdownMenu>
        <Button
          variant="default"
          @click="save"
          class="ml-2"
          :disabled="!isGatewayAdmin"
          >Save</Button
        >
        <Button variant="secondary" class="ml-auto" as-child>
          <a href="/admin/users">Return to Manage Users</a>
        </Button>
      </div>
    </div>
  </main-layout>
</template>

<script>
import { mapActions, mapState } from "pinia";
import { useExtendedUserProfileStore } from "../../store/modules/extendedUserProfile";
import ExtendedUserProfileFieldEditor from "./field-editors/ExtendedUserProfileFieldEditor.vue";
import { components, mixins } from "django-airavata-common-ui";
import { session } from "django-airavata-api";
export default {
  mixins: [mixins.ValidationParent],
  components: {
    ExtendedUserProfileFieldEditor,
    "main-layout": components.MainLayout,
  },
  data() {
    return {};
  },
  created() {
    this.loadExtendedUserProfileFields();
  },
  methods: {
    ...mapActions(useExtendedUserProfileStore, [
      "loadExtendedUserProfileFields",
      "saveExtendedUserProfileFields",
      "addExtendedUserProfileFieldOfType",
    ]),
    addField(field_type) {
      this.addExtendedUserProfileFieldOfType({ field_type });
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
    ...mapState(useExtendedUserProfileStore, ["extendedUserProfileFields"]),
    valid() {
      return this.childComponentsAreValid;
    },
    isGatewayAdmin() {
      return session.Session.isGatewayAdmin;
    },
  },
};
</script>
