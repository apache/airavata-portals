<template>
  <ul class="nav nav-tabs mt-3 px-2" content->
    <li class="nav-item" title="User Profile" :active="iamUserProfile.airavata_user_profile_exists">
      <div v-if="!iamUserProfile.userProfileComplete" class="alert alert-warning">
        This user has not completed their user profile. An incomplete user profile is shown below.
      </div>
      <div v-if="isUsernameInvalid" class="alert alert-danger">
        The user has an invalid username. Please use
        <strong>Change Username</strong> under the <strong>Troubleshooting</strong> tab to fix the
        user's username.
      </div>
      <user-profile-panel :iam-user-profile="iamUserProfile" />
      <extended-user-profile-panel :iam-user-profile="iamUserProfile" />
      <external-idp-user-info-panel
        v-if="hasExternalIDPUserInfo"
        :external-i-d-p-user-info="localIAMUserProfile.external_idp_user_info"
      />
    </li>
    <li
      class="nav-item"
      title="Troubleshooting"
      :active="!iamUserProfile.airavata_user_profile_exists"
    >
      <activate-user-panel
        v-if="
          iamUserProfile.enabled &&
          iamUserProfile.email_verified &&
          iamUserProfile.userProfileComplete &&
          !iamUserProfile.airavata_user_profile_exists
        "
        :username="iamUserProfile.user_id"
        @activate-user="$emit('enable-user', $event)"
      />
      <enable-user-panel
        v-if="!iamUserProfile.enabled && !iamUserProfile.email_verified"
        :username="iamUserProfile.user_id"
        :email="iamUserProfile.email"
        @enable-user="$emit('enable-user', $event)"
      />
      <delete-user-panel
        v-if="!iamUserProfile.enabled && !iamUserProfile.email_verified"
        :username="iamUserProfile.user_id"
        @delete-user="$emit('delete-user', $event)"
      />
      <div v-if="isUsernameInvalid" class="alert alert-danger">
        The user has an invalid username. Please fix the user's username so that they can complete
        their user profile.
      </div>
      <change-username-panel
        :username="iamUserProfile.user_id"
        :email="iamUserProfile.email"
        :airavata-user-profile-exists="iamUserProfile.airavata_user_profile_exists"
        @update-username="$emit('update-username', $event)"
      />
    </li>
  </ul>
</template>
<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { models } from "django-airavata-api";
import ActivateUserPanel from "./ActivateUserPanel.vue";
import EnableUserPanel from "./EnableUserPanel.vue";
import DeleteUserPanel from "./DeleteUserPanel.vue";
import ChangeUsernamePanel from "./ChangeUsernamePanel.vue";
import ExternalIdpUserInfoPanel from "./ExternalIDPUserInfoPanel.vue";
import UserProfilePanel from "./UserProfilePanel.vue";
import ExtendedUserProfilePanel from "./ExtendedUserProfilePanel.vue";

const props = defineProps<{
  iamUserProfile: InstanceType<typeof models.IAMUserProfile>;
}>();

defineEmits<{
  "enable-user": [username: string];
  "delete-user": [username: string];
  "update-username": [args: [string, string]];
}>();

const localIAMUserProfile = ref(props.iamUserProfile.clone());

watch(
  () => props.iamUserProfile,
  (newValue) => {
    localIAMUserProfile.value = newValue.clone();
  }
);

const hasExternalIDPUserInfo = computed(
  () => Object.keys(localIAMUserProfile.value.external_idp_user_info).length !== 0
);

const isUsernameInvalid = computed(
  () => props.iamUserProfile.user_profile_invalid_fields.indexOf("username") >= 0
);
</script>
