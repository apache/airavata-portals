<template>
  <div class="card">
    <div class="card-header">{{ title }}</div>
    <div class="card-body">
      <div class="mb-3">
        <label class="form-label">Name</label>
        <input
          v-model="name"
          :class="['form-control', validateState(v$.nameState) === false ? 'is-invalid' : '']"
        />
        <div v-if="v$.nameState.$dirty && v$.nameState.$error" class="invalid-feedback">
          This field is required.
        </div>
      </div>
      <form-group
        v-if="extendedUserProfileField.field_type === 'user_agreement'"
        label="Checkbox Label"
        :disabled="disabled"
      >
        <input
          v-model="checkbox_label"
          :class="['form-control', validateState(v$.checkboxLabelState) === false ? 'is-invalid' : '']"
          placeholder="E.g. I accept the Terms of Service listed above"
        />
        <div v-if="v$.checkboxLabelState.$dirty && v$.checkboxLabelState.$error" class="invalid-feedback">
          This field is required.
        </div>
      </form-group>
      <div class="mb-3">
        <label class="form-label">Help text <small class="text-muted">(Optional)</small></label>
        <input v-model="help_text" class="form-control" />
      </div>
      <div class="mb-3">
        <div class="form-check">
          <input id="required-check" v-model="fieldRequired" class="form-check-input" type="checkbox" />
          <label class="form-check-label" for="required-check">Required</label>
        </div>
      </div>
      <div v-if="extendedUserProfileField.supportsChoices" class="card mb-3">
        <div class="card-header">Options</div>
        <div class="card-body">
          <transition-group name="fade">
            <template v-for="(choice, index) in extendedUserProfileField.choices" :key="choice.key">
              <div :class="['mb-3', { 'opacity-50': disabled }]">
                <div class="input-group">
                  <input
                    :class="['form-control', !choice.display_text ? 'is-invalid' : '']"
                    :value="choice.display_text"
                    @input="handleChoiceDisplayTextChanged(choice, $event)"
                  />
                  <span class="input-group-text">
                    <button
                      class="btn btn-sm"
                      :disabled="index === 0"
                      title="Move Up"
                      @click="handleChoiceMoveUp(choice)"
                    >
                      <i class="fa fa-arrow-up" aria-hidden="true"></i>
                    </button>
                    <button
                      class="btn btn-sm"
                      :disabled="index === extendedUserProfileField.choices.length - 1"
                      title="Move Down"
                      @click="handleChoiceMoveDown(choice)"
                    >
                      <i class="fa fa-arrow-down" aria-hidden="true"></i>
                    </button>
                    <button
                      class="btn btn-sm btn-danger"
                      title="Delete Option"
                      @click="handleChoiceDeleted(choice)"
                    >
                      <i class="fa fa-trash" aria-hidden="true"></i>
                    </button>
                  </span>
                </div>
                <div v-if="!choice.display_text" class="invalid-feedback d-block">
                  This field is required.
                </div>
              </div>
            </template>
            <div v-if="extendedUserProfileField.other" :key="'other'" class="mb-3">
              <div class="input-group">
                <input
                  class="form-control"
                  placeholder="User will see: Other (please specify)"
                  disabled
                />
                <span class="input-group-text">
                  <button class="btn btn-sm" disabled>
                    <i class="fa fa-arrow-up" aria-hidden="true"></i>
                  </button>
                  <button class="btn btn-sm" disabled>
                    <i class="fa fa-arrow-down" aria-hidden="true"></i>
                  </button>
                  <button
                    class="btn btn-sm btn-danger"
                    title="Remove Other option"
                    @click="other = false"
                  >
                    <i class="fa fa-trash" aria-hidden="true"></i>
                  </button>
                </span>
              </div>
            </div>
          </transition-group>
          <div class="mb-3">
            <button
              class="btn btn-sm btn-secondary"
              @click="userStore.addFieldChoice({ field: extendedUserProfileField })"
            >
              Add Option
            </button>
          </div>
          <div class="mb-3">
            <div class="form-check form-switch">
              <input id="other-check" v-model="other" class="form-check-input" type="checkbox" />
              <label class="form-check-label" for="other-check">
                Allow user to type in an "Other" option
              </label>
            </div>
          </div>
        </div>
      </div>

      <template v-if="links && links.length > 0">
        <transition-group name="fade">
          <div v-for="(link, linkIdx) in links" :key="link.id ?? link.label" class="card mb-2">
            <div class="card-header">Link: {{ link.label }}</div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">Label</label>
                <input
                  :class="['form-control', !link.label ? 'is-invalid' : '']"
                  :value="link.label"
                  @input="handleLinkLabelChanged(link, $event)"
                />
                <div v-if="!link.label" class="invalid-feedback">This field is required.</div>
              </div>
              <div class="mb-3">
                <label class="form-label">URL</label>
                <input
                  :class="['form-control', !link.url ? 'is-invalid' : '']"
                  :value="link.url"
                  @input="handleLinkURLChanged(link, $event)"
                />
                <div v-if="!link.url" class="invalid-feedback">This field is required.</div>
              </div>
              <div class="row mb-2">
                <div class="col">
                  <div class="form-check form-switch">
                    <input
                      :id="`display-link-${linkIdx}`"
                      class="form-check-input"
                      type="checkbox"
                      :checked="link.display_link"
                      @change="handleLinkDisplayLinkChanged(link, ($event.target as HTMLInputElement).checked)"
                    />
                    <label class="form-check-label" :for="`display-link-${linkIdx}`"
                      >Show as link?</label
                    >
                  </div>
                </div>
                <div class="col">
                  <div class="form-check form-switch">
                    <input
                      :id="`display-inline-${linkIdx}`"
                      class="form-check-input"
                      type="checkbox"
                      :checked="link.display_inline"
                      @change="handleLinkDisplayInlineChanged(link, ($event.target as HTMLInputElement).checked)"
                    />
                    <label class="form-check-label" :for="`display-inline-${linkIdx}`"
                      >Show inline?</label
                    >
                  </div>
                </div>
              </div>
              <button
                class="btn btn-sm btn-danger"
                :disabled="disabled"
                @click="handleLinkDeleted(link)"
              >
                Delete Link
              </button>
            </div>
          </div>
        </transition-group>
      </template>
      <div class="d-flex gap-2 mt-2">
        <button
          class="btn btn-sm btn-secondary"
          :disabled="disabled"
          @click="userStore.addFieldLink({ field: extendedUserProfileField })"
        >
          Add Link
        </button>
        <button
          class="btn btn-sm btn-secondary"
          :disabled="disabled || (extendedUserProfileFields ?? []).indexOf(extendedUserProfileField) === 0"
          @click="handleMoveUp({ field: extendedUserProfileField })"
        >
          Move Up
        </button>
        <button
          class="btn btn-sm btn-secondary"
          :disabled="
            disabled ||
            (extendedUserProfileFields ?? []).indexOf(extendedUserProfileField) ===
              (extendedUserProfileFields ?? []).length - 1
          "
          @click="handleMoveDown({ field: extendedUserProfileField })"
        >
          Move Down
        </button>
        <button class="btn btn-sm btn-danger" :disabled="disabled" @click="handleDelete">
          Delete
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { useVuelidate } from "@vuelidate/core";
import { required, requiredIf } from "@vuelidate/validators";
import { errors } from "django-airavata-common-ui";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";
import type {
  ExtendedUserProfileField,
  ExtendedUserProfileFieldChoice,
  ExtendedUserProfileFieldLink,
} from "django-airavata-common-ui/js/types/user";

const props = defineProps<{
  extendedUserProfileField: ExtendedUserProfileField;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  valid: [];
  invalid: [];
}>();

const userStore = useUserStore();

const extendedUserProfileFields = computed(() => userStore.extendedUserProfileFields);

const checkboxLabelIsRequired = computed(
  () => props.extendedUserProfileField.field_type === "user_agreement"
);

// Computed state for vuelidate — read from store, write back to store
const nameState = computed(() => props.extendedUserProfileField.name);
const checkboxLabelState = computed(() => props.extendedUserProfileField.checkbox_label ?? "");

const rules = computed(() => ({
  nameState: { required },
  checkboxLabelState: {
    required: requiredIf(() => checkboxLabelIsRequired.value),
  },
}));

const v$ = useVuelidate(rules, { nameState, checkboxLabelState });

// Two-way computed for v-model bindings (touch vuelidate after store update)
const name = computed({
  get: () => props.extendedUserProfileField.name,
  set: (value: string) => {
    userStore.setFieldName({ value, field: props.extendedUserProfileField });
    v$.value.nameState.$touch();
  },
});

const checkbox_label = computed({
  get: () => props.extendedUserProfileField.checkbox_label ?? "",
  set: (value: string) => {
    userStore.setFieldCheckboxLabel({ value, field: props.extendedUserProfileField });
    v$.value.checkboxLabelState.$touch();
  },
});

const help_text = computed({
  get: () => props.extendedUserProfileField.help_text ?? "",
  set: (value: string) => {
    userStore.setFieldHelpText({ value, field: props.extendedUserProfileField });
  },
});

const fieldRequired = computed({
  get: () => props.extendedUserProfileField.required ?? false,
  set: (value: boolean) => {
    userStore.setFieldRequired({ value, field: props.extendedUserProfileField });
  },
});

const other = computed({
  get: () => props.extendedUserProfileField.other ?? false,
  set: (value: boolean) => {
    userStore.setFieldOther({ value, field: props.extendedUserProfileField });
  },
});

const fieldTypeLabels: Record<string, string> = {
  text: "Text",
  single_choice: "Single Choice",
  multi_choice: "Multi Choice",
  user_agreement: "User Agreement",
};

const title = computed(
  () => `${fieldTypeLabels[props.extendedUserProfileField.field_type]}: ${name.value}`
);

const links = computed(() => props.extendedUserProfileField.links);
const valid = computed(() => !v$.value.$invalid);

const validateState = errors.vuelidateHelpers.validateState;

watch(
  valid,
  (isValid) => {
    if (isValid) {
      emit("valid");
    } else {
      emit("invalid");
    }
  },
  { immediate: true }
);

function handleChoiceDisplayTextChanged(choice: ExtendedUserProfileFieldChoice, event: Event) {
  userStore.updateFieldChoiceDisplayText({
    choice,
    display_text: (event.target as HTMLInputElement).value,
  });
}

function handleChoiceDeleted(choice: ExtendedUserProfileFieldChoice) {
  userStore.deleteFieldChoice({ field: props.extendedUserProfileField, choice });
}

function handleChoiceMoveUp(choice: ExtendedUserProfileFieldChoice) {
  let index = props.extendedUserProfileField.choices.indexOf(choice);
  index--;
  userStore.updateFieldChoiceIndex({ field: props.extendedUserProfileField, choice, index });
}

function handleChoiceMoveDown(choice: ExtendedUserProfileFieldChoice) {
  let index = props.extendedUserProfileField.choices.indexOf(choice);
  index++;
  userStore.updateFieldChoiceIndex({ field: props.extendedUserProfileField, choice, index });
}

function handleLinkLabelChanged(link: ExtendedUserProfileFieldLink, event: Event) {
  userStore.updateFieldLinkLabel({ link, label: (event.target as HTMLInputElement).value });
}

function handleLinkURLChanged(link: ExtendedUserProfileFieldLink, event: Event) {
  userStore.updateFieldLinkURL({ link, url: (event.target as HTMLInputElement).value });
}

function handleLinkDisplayLinkChanged(link: ExtendedUserProfileFieldLink, display_link: boolean) {
  userStore.updateFieldLinkDisplayLink({ link, display_link });
}

function handleLinkDisplayInlineChanged(link: ExtendedUserProfileFieldLink, display_inline: boolean) {
  userStore.updateFieldLinkDisplayInline({ link, display_inline });
}

function handleLinkDeleted(link: ExtendedUserProfileFieldLink) {
  userStore.deleteFieldLink({ field: props.extendedUserProfileField, link });
}

function handleMoveUp({ field }: { field: ExtendedUserProfileField }) {
  let index = (extendedUserProfileFields.value ?? []).indexOf(field);
  index--;
  userStore.updateFieldIndex({ field, index });
}

function handleMoveDown({ field }: { field: ExtendedUserProfileField }) {
  let index = (extendedUserProfileFields.value ?? []).indexOf(field);
  index++;
  userStore.updateFieldIndex({ field, index });
}

function handleDelete() {
  userStore.deleteExtendedUserProfileField({ field: props.extendedUserProfileField });
}

function touch() {
  v$.value.$touch();
}

defineExpose({ touch });
</script>

<style></style>
