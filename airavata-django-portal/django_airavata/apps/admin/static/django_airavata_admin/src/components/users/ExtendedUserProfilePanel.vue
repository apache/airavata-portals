<template>
  <div class="card">
    <div class="card-header">Extended User Profile</div>
    <div class="card-body">
      <template v-if="items.length === 0">
        <a href="/admin/extended-user-profile"
          >Add additional user profile fields for gateway users to complete</a
        >
      </template>
      <table v-else class="table table-sm table-borderless mb-0">
        <thead>
          <tr>
            <th>name</th>
            <th>value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.name">
            <td>{{ item.name }}</td>
            <td>
              <!-- only show a valid checkmark when there is a user provided value -->
              <i v-if="item.value && item.valid" class="fas fa-check text-success"></i>
              <i v-if="!item.valid" class="fas fa-times text-danger"></i>
              <template v-if="Array.isArray(item.value)">
                <ul>
                  <li v-for="result in item.value" :key="result">
                    {{ result }}
                  </li>
                </ul>
              </template>
              <template v-else> {{ item.value }} </template>
            </td>
          </tr>
        </tbody>
      </table>
      <a v-if="items.length > 0" href="/admin/extended-user-profile" class="text-muted small"
        >Add or edit these field definitions</a
      >
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { models } from "django-airavata-api";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";
import type { ExtendedUserProfileField } from "django-airavata-common-ui/js/types/user";

// The model has `valid` and `value_display` fields beyond the interface
type ExtendedUserProfileValueModel = {
  ext_user_profile_field: number;
  valid?: boolean;
  value_display?: unknown;
  [key: string]: unknown;
};

const props = defineProps<{
  iamUserProfile: InstanceType<typeof models.IAMUserProfile>;
}>();

const userStore = useUserStore();

const extendedUserProfileFields = computed(() => userStore.extendedUserProfileFields);
const extendedUserProfileValues = computed(
  () => userStore.extendedUserProfileValues as ExtendedUserProfileValueModel[]
);

function getValue(field: ExtendedUserProfileField): ExtendedUserProfileValueModel | undefined {
  return extendedUserProfileValues.value?.find(
    (v) => v.ext_user_profile_field === field.id
  );
}

const items = computed(() => {
  if (extendedUserProfileFields.value && extendedUserProfileValues.value) {
    return extendedUserProfileFields.value.map((field) => {
      const value = getValue(field);
      return {
        name: field.name,
        value: value ? value.value_display : null,
        // if no value, consider it invalid only if it is required
        valid: value ? value.valid : !field.required,
      };
    });
  }
  return [];
});

onMounted(() => {
  userStore.loadExtendedUserProfileFields();
  userStore.loadExtendedUserProfileValues({ username: props.iamUserProfile.user_id });
});
</script>

<style scoped>
ul {
  display: inline-block;
  padding-left: 20px;
}
</style>
