<template>
  <div>
    <template
      v-for="extendedUserProfileField in extendedUserProfileFields"
      :key="extendedUserProfileField.id"
    >
      <component
        :is="getEditor(extendedUserProfileField)"
        ref="extendedUserProfileFieldComponents"
        :extended-user-profile-field="extendedUserProfileField"
        @valid="recordValidChildComponent(extendedUserProfileField.id)"
        @invalid="recordInvalidChildComponent(extendedUserProfileField.id)"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { storeToRefs } from "pinia";
import type { Component } from "vue";
import type { ExtendedUserProfileField } from "django-airavata-common-ui/js/types/user";
import ExtendedUserProfileMultiChoiceValueEditor from "./ExtendedUserProfileMultiChoiceValueEditor.vue";
import ExtendedUserProfileSingleChoiceValueEditor from "./ExtendedUserProfileSingleChoiceValueEditor.vue";
import ExtendedUserProfileTextValueEditor from "./ExtendedUserProfileTextValueEditor.vue";
import ExtendedUserProfileUserAgreementValueEditor from "./ExtendedUserProfileUserAgreementValueEditor.vue";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";

const userStore = useUserStore();
const { extendedUserProfileFields } = storeToRefs(userStore);

// Inline ValidationParent mixin logic
const invalidChildComponents = ref<number[]>([]);
const childComponentsAreValid = computed(() => invalidChildComponents.value.length === 0);

function recordInvalidChildComponent(id: number | undefined): void {
  if (id === undefined || id === null) return;
  if (!invalidChildComponents.value.includes(id)) {
    invalidChildComponents.value.push(id);
  }
}

function recordValidChildComponent(id: number | undefined): void {
  if (id === undefined || id === null) return;
  const index = invalidChildComponents.value.indexOf(id);
  if (index !== -1) {
    invalidChildComponents.value.splice(index, 1);
  }
}

const valid = computed(() => childComponentsAreValid.value);

type FieldEditor = Component;
const fieldTypeEditors: Record<string, FieldEditor> = {
  text: ExtendedUserProfileTextValueEditor,
  single_choice: ExtendedUserProfileSingleChoiceValueEditor,
  multi_choice: ExtendedUserProfileMultiChoiceValueEditor,
  user_agreement: ExtendedUserProfileUserAgreementValueEditor,
};

function getEditor(extendedUserProfileField: ExtendedUserProfileField): FieldEditor | undefined {
  if (extendedUserProfileField.field_type in fieldTypeEditors) {
    return fieldTypeEditors[extendedUserProfileField.field_type];
  } else {
    // eslint-disable-next-line no-console
    console.error("Unexpected field_type", extendedUserProfileField.field_type);
    return undefined;
  }
}

// Template ref: array of child component instances
const extendedUserProfileFieldComponents = ref<Array<{ touch: () => void }>>([]);

function touch(): void {
  extendedUserProfileFieldComponents.value.forEach((c) => c.touch());
}

defineExpose({ valid, touch });
</script>

<style></style>
