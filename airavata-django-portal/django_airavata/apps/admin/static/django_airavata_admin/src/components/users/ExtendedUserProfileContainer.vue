<template>
  <div class="has-fixed-footer">
    <div class="row mb-2">
      <div class="col-auto me-auto">
        <h1 class="h4">Extended User Profile Editor</h1>
        <p class="text-muted small">
          Add and edit additional user profile fields for gateway users to complete.
        </p>
      </div>
    </div>
    <transition-group name="fade">
      <div v-for="field in extendedUserProfileFields" :key="field.id ?? field.name" class="row">
        <div class="col">
          <extended-user-profile-field-editor
            ref="extendedUserProfileFieldEditors"
            :extended-user-profile-field="field"
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
          <a class="dropdown-item" @click="addField('single_choice')">Single Choice</a>
          <a class="dropdown-item" @click="addField('multi_choice')">Multi Choice</a>
          <a class="dropdown-item" @click="addField('user_agreement')">User Agreement</a>
        </div>
        <button class="btn btn-primary btn-sm ms-2" :disabled="!isGatewayAdmin" @click="save">
          Save
        </button>
        <button class="btn btn-secondary btn-sm ms-auto" href="/admin/users">
          Return to Manage Users
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from "vue";
import { session } from "django-airavata-api";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";
import type { ExtendedUserProfileField } from "django-airavata-common-ui/js/types/user";
import ExtendedUserProfileFieldEditor from "./field-editors/ExtendedUserProfileFieldEditor.vue";

const userStore = useUserStore();

// ValidationParent logic inlined — tracks invalid fields by object reference
const invalidChildComponents = ref<ExtendedUserProfileField[]>([]);
const childComponentsAreValid = computed(() => invalidChildComponents.value.length === 0);

function recordValidChildComponent(field: ExtendedUserProfileField) {
  const index = invalidChildComponents.value.indexOf(field);
  if (index >= 0) {
    invalidChildComponents.value.splice(index, 1);
  }
}

function recordInvalidChildComponent(field: ExtendedUserProfileField) {
  if (!invalidChildComponents.value.includes(field)) {
    invalidChildComponents.value.push(field);
  }
}

const bottom = ref<HTMLElement | null>(null);
const extendedUserProfileFieldEditors = ref<{ touch: () => void }[]>([]);

const extendedUserProfileFields = computed(() => userStore.extendedUserProfileFields);
const valid = computed(() => childComponentsAreValid.value);
const isGatewayAdmin = computed(() => session.Session.is_gateway_admin);

onMounted(() => {
  userStore.loadExtendedUserProfileFields();
});

async function addField(field_type: string) {
  userStore.addExtendedUserProfileField({ field_type });
  await nextTick();
  bottom.value?.scrollIntoView();
}

function save() {
  if (valid.value) {
    userStore.saveExtendedUserProfileFields();
  } else {
    extendedUserProfileFieldEditors.value.forEach((c) => c.touch());
  }
}
</script>
