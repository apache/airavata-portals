<template>
  <Card :class="v$.$anyDirty && v$.$invalid ? 'border-destructive' : ''">
    <CardHeader>
      <CardTitle>{{ title }}</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <TooltipProvider :delay-duration="150">
        <fieldset :disabled="disabled" class="space-y-4">
          <div class="grid grid-cols-[1fr_3fr] items-start gap-3">
            <Label>Name</Label>
            <div class="space-y-1.5">
              <Input
                v-model="name"
                :aria-invalid="validateState(v$.name) === false"
              />
              <p
                v-if="validateState(v$.name) === false"
                class="text-sm text-destructive"
              >
                This field is required.
              </p>
            </div>
          </div>
          <div
            class="grid grid-cols-[1fr_3fr] items-start gap-3"
            v-if="extendedUserProfileField.field_type === 'user_agreement'"
          >
            <Label>Checkbox Label</Label>
            <div class="space-y-1.5">
              <Input
                v-model="checkbox_label"
                :aria-invalid="validateState(v$.checkbox_label) === false"
                placeholder="E.g. I accept the Terms of Service listed above"
              />
              <p
                v-if="validateState(v$.checkbox_label) === false"
                class="text-sm text-destructive"
              >
                This field is required.
              </p>
            </div>
          </div>
          <div class="grid grid-cols-[1fr_3fr] items-start gap-3">
            <Label>
              Help text
              <small class="text-sm text-muted-foreground">(Optional)</small>
            </Label>
            <Input v-model="help_text" />
          </div>
          <label class="flex items-center gap-2 text-sm">
            <Checkbox v-model="required" /> Required
          </label>
        </fieldset>
        <Card v-if="extendedUserProfileField.supportsChoices">
          <CardHeader>
            <CardTitle>Options</CardTitle>
          </CardHeader>
          <CardContent class="space-y-3">
            <transition-group name="fade">
              <template
                v-for="(choice, index) in extendedUserProfileField.choices"
                :key="choice.key"
              >
                <fieldset :disabled="disabled" class="space-y-1.5">
                  <div class="flex items-stretch gap-2">
                    <Input
                      :model-value="choice.display_text"
                      @update:model-value="
                        handleChoiceDisplayTextChanged(choice, $event)
                      "
                      :aria-invalid="choiceDisplayTextState(index) === false"
                    />
                    <Tooltip>
                      <TooltipTrigger as-child>
                        <Button
                          variant="outline"
                          size="icon"
                          @click="handleChoiceMoveUp(choice)"
                          :disabled="index === 0"
                        >
                          <ArrowUp class="size-4" aria-hidden="true" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="left">Move Up</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger as-child>
                        <Button
                          variant="outline"
                          size="icon"
                          @click="handleChoiceMoveDown(choice)"
                          :disabled="
                            index ===
                            extendedUserProfileField.choices.length - 1
                          "
                        >
                          <ArrowDown class="size-4" aria-hidden="true" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="left">Move Down</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger as-child>
                        <Button
                          variant="destructive"
                          size="icon"
                          @click="handleChoiceDeleted(choice)"
                        >
                          <Trash2 class="size-4" aria-hidden="true" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="left">Delete Option</TooltipContent>
                    </Tooltip>
                  </div>
                  <p
                    v-if="choiceDisplayTextState(index) === false"
                    class="text-sm text-destructive"
                  >
                    This field is required.
                  </p>
                </fieldset>
              </template>
              <fieldset
                :key="'other'"
                v-if="extendedUserProfileField.other"
                :disabled="disabled"
              >
                <div class="flex items-stretch gap-2">
                  <Input
                    placeholder="User will see: Other (please specify)"
                    disabled
                  />
                  <Button variant="outline" size="icon" disabled>
                    <ArrowUp class="size-4" aria-hidden="true" />
                  </Button>
                  <Button variant="outline" size="icon" disabled>
                    <ArrowDown class="size-4" aria-hidden="true" />
                  </Button>
                  <Tooltip>
                    <TooltipTrigger as-child>
                      <Button
                        variant="destructive"
                        size="icon"
                        @click="other = false"
                      >
                        <Trash2 class="size-4" aria-hidden="true" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left"
                      >Remove Other option</TooltipContent
                    >
                  </Tooltip>
                </div>
              </fieldset>
            </transition-group>
            <fieldset :disabled="disabled">
              <Button
                variant="outline"
                @click="addChoice({ field: extendedUserProfileField })"
                size="sm"
                >Add Option</Button
              >
            </fieldset>
            <fieldset :disabled="disabled">
              <label class="flex items-center gap-2 text-sm">
                <Checkbox v-model="other" />
                Allow user to type in an "Other" option
              </label>
            </fieldset>
          </CardContent>
        </Card>

        <template v-if="links && links.length > 0">
          <transition-group name="fade">
            <Card v-for="(link, index) in links" :key="link.key">
              <CardHeader>
                <CardTitle>{{ `Link: ${link.label}` }}</CardTitle>
              </CardHeader>
              <CardContent class="space-y-4">
                <fieldset
                  :disabled="disabled"
                  class="grid grid-cols-[1fr_3fr] items-start gap-3"
                >
                  <Label>Label</Label>
                  <div class="space-y-1.5">
                    <Input
                      :model-value="link.label"
                      @update:model-value="handleLinkLabelChanged(link, $event)"
                      :aria-invalid="linkLabelState(index) === false"
                    />
                    <p
                      v-if="linkLabelState(index) === false"
                      class="text-sm text-destructive"
                    >
                      This field is required.
                    </p>
                  </div>
                </fieldset>
                <fieldset
                  :disabled="disabled"
                  class="grid grid-cols-[1fr_3fr] items-start gap-3"
                >
                  <Label>URL</Label>
                  <div class="space-y-1.5">
                    <Input
                      :model-value="link.url"
                      @update:model-value="handleLinkURLChanged(link, $event)"
                      :aria-invalid="linkUrlState(index) === false"
                    />
                    <p
                      v-if="linkUrlState(index) === false"
                      class="text-sm text-destructive"
                    >
                      This field is required.
                    </p>
                  </div>
                </fieldset>
                <div class="grid grid-cols-2 gap-3">
                  <fieldset :disabled="disabled">
                    <label class="flex items-center gap-2 text-sm">
                      <Checkbox
                        :model-value="link.display_link"
                        @update:model-value="
                          handleLinkDisplayLinkChanged(link, $event)
                        "
                      />
                      Show as link?
                    </label>
                  </fieldset>
                  <fieldset :disabled="disabled">
                    <label class="flex items-center gap-2 text-sm">
                      <Checkbox
                        :model-value="link.display_inline"
                        @update:model-value="
                          handleLinkDisplayInlineChanged(link, $event)
                        "
                      />
                      Show inline?
                    </label>
                  </fieldset>
                </div>
                <Button
                  @click="handleLinkDeleted(link)"
                  variant="destructive"
                  size="sm"
                  :disabled="disabled"
                >
                  Delete Link
                </Button>
              </CardContent>
            </Card>
          </transition-group>
        </template>
        <div class="flex flex-wrap gap-2">
          <Button
            variant="outline"
            @click="addLink({ field: extendedUserProfileField })"
            size="sm"
            :disabled="disabled"
            >Add Link</Button
          >
          <Button
            variant="outline"
            @click="handleMoveUp({ field: extendedUserProfileField })"
            :disabled="
              disabled ||
              extendedUserProfileFields.indexOf(extendedUserProfileField) === 0
            "
            size="sm"
            >Move Up</Button
          >
          <Button
            variant="outline"
            @click="handleMoveDown({ field: extendedUserProfileField })"
            :disabled="
              disabled ||
              extendedUserProfileFields.indexOf(extendedUserProfileField) ===
                extendedUserProfileFields.length - 1
            "
            size="sm"
            >Move Down</Button
          >
          <Button
            @click="handleDelete"
            variant="destructive"
            size="sm"
            :disabled="disabled"
            >Delete</Button
          >
        </div>
      </TooltipProvider>
    </CardContent>
  </Card>
</template>

<script>
import { ArrowDown, ArrowUp, Trash2 } from "@lucide/vue";
import { mapActions, mapState } from "pinia";
import { useExtendedUserProfileStore } from "../../../store/modules/extendedUserProfile";
import { useVuelidate } from "@vuelidate/core";
import { helpers, required, requiredIf } from "@vuelidate/validators";
import { errors } from "django-airavata-common-ui";
export default {
  components: { ArrowDown, ArrowUp, Trash2 },
  setup() {
    return { v$: useVuelidate() };
  },
  props: ["extendedUserProfileField", "disabled"],
  computed: {
    ...mapState(useExtendedUserProfileStore, ["extendedUserProfileFields"]),
    name: {
      get() {
        return this.extendedUserProfileField.name;
      },
      set(value) {
        this.setName({ value, field: this.extendedUserProfileField });
        this.v$.name.$touch();
      },
    },
    checkbox_label: {
      get() {
        return this.extendedUserProfileField.checkbox_label;
      },
      set(value) {
        this.setCheckboxLabel({ value, field: this.extendedUserProfileField });
        this.v$.checkbox_label.$touch();
      },
    },
    help_text: {
      get() {
        return this.extendedUserProfileField.help_text;
      },
      set(value) {
        this.setHelpText({ value, field: this.extendedUserProfileField });
      },
    },
    required: {
      get() {
        return this.extendedUserProfileField.required;
      },
      set(value) {
        this.setRequired({ value, field: this.extendedUserProfileField });
      },
    },
    other: {
      get() {
        return this.extendedUserProfileField.other;
      },
      set(value) {
        this.setOther({ value, field: this.extendedUserProfileField });
      },
    },
    title() {
      const fieldTypes = {
        text: "Text",
        single_choice: "Single Choice",
        multi_choice: "Multi Choice",
        user_agreement: "User Agreement",
      };
      return `${fieldTypes[this.extendedUserProfileField.field_type]}: ${
        this.name
      }`;
    },
    choices() {
      return this.extendedUserProfileField.choices;
    },
    links() {
      return this.extendedUserProfileField.links;
    },
    valid() {
      return !this.v$.$invalid;
    },
    checkboxLabelIsRequired() {
      return this.extendedUserProfileField.field_type === "user_agreement";
    },
  },
  validations() {
    // @vuelidate/core 2: array element validation uses helpers.forEach instead
    // of the removed `$each`. Per-element results are read from
    // v$.choices.$each.$response.$errors[index] in the template.
    return {
      name: {
        required,
      },
      checkbox_label: {
        required: requiredIf(this.checkboxLabelIsRequired),
      },
      choices: {
        $each: helpers.forEach({
          display_text: {
            required,
          },
        }),
      },
      links: {
        $each: helpers.forEach({
          label: {
            required,
          },
          url: {
            required,
          },
        }),
      },
    };
  },
  methods: {
    ...mapActions(useExtendedUserProfileStore, [
      "setName",
      "setCheckboxLabel",
      "setHelpText",
      "setRequired",
      "setOther",
      "addChoice",
      "updateChoiceDisplayText",
      "deleteChoice",
      "updateChoiceIndex",
      "addLink",
      "updateLinkLabel",
      "updateLinkURL",
      "updateLinkDisplayLink",
      "updateLinkDisplayInline",
      "deleteLink",
      "updateFieldIndex",
      "deleteField",
    ]),
    handleChoiceDisplayTextChanged(choice, display_text) {
      this.updateChoiceDisplayText({ choice, display_text });
      this.v$.choices.$touch();
    },
    handleChoiceDeleted(choice) {
      this.deleteChoice({ field: this.extendedUserProfileField, choice });
    },
    handleChoiceMoveUp(choice) {
      let index = this.extendedUserProfileField.choices.indexOf(choice);
      index--;
      this.updateChoiceIndex({
        field: this.extendedUserProfileField,
        choice,
        index,
      });
    },
    handleChoiceMoveDown(choice) {
      let index = this.extendedUserProfileField.choices.indexOf(choice);
      index++;
      this.updateChoiceIndex({
        field: this.extendedUserProfileField,
        choice,
        index,
      });
    },
    handleLinkLabelChanged(link, label) {
      this.updateLinkLabel({ link, label });
      this.v$.links.$touch();
    },
    handleLinkURLChanged(link, url) {
      this.updateLinkURL({ link, url });
      this.v$.links.$touch();
    },
    handleLinkDisplayLinkChanged(link, display_link) {
      this.updateLinkDisplayLink({ link, display_link });
    },
    handleLinkDisplayInlineChanged(link, display_inline) {
      this.updateLinkDisplayInline({ link, display_inline });
    },
    handleLinkDeleted(link) {
      this.deleteLink({ field: this.extendedUserProfileField, link });
    },
    handleMoveUp({ field }) {
      let index = this.extendedUserProfileFields.indexOf(field);
      index--;
      this.updateFieldIndex({ field, index });
    },
    handleMoveDown({ field }) {
      let index = this.extendedUserProfileFields.indexOf(field);
      index++;
      this.updateFieldIndex({ field, index });
    },
    handleDelete() {
      this.deleteField({
        field: this.extendedUserProfileField,
      });
    },
    validateState: errors.vuelidateHelpers.validateState,
    // Per-element validation state for helpers.forEach arrays (replaces the
    // removed `$each.$iter` per-item validation objects). Mirrors
    // vuelidateHelpers.validateState: null until the array is dirty, then false
    // when the element's named property has errors, true otherwise.
    elementState(arrayValidation, index, property) {
      if (!arrayValidation.$dirty) {
        return null;
      }
      const elementErrors = arrayValidation.$each.$response.$errors[index];
      const propertyErrors = elementErrors ? elementErrors[property] : [];
      return propertyErrors && propertyErrors.length > 0 ? false : true;
    },
    choiceDisplayTextState(index) {
      return this.elementState(this.v$.choices, index, "display_text");
    },
    linkLabelState(index) {
      return this.elementState(this.v$.links, index, "label");
    },
    linkUrlState(index) {
      return this.elementState(this.v$.links, index, "url");
    },
    touch() {
      this.v$.$touch();
    },
  },
  watch: {
    valid: {
      handler(valid) {
        this.$emit(valid ? "valid" : "invalid");
      },
      immediate: true,
    },
  },
};
</script>

<style></style>
