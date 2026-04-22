<template>
  <div>
    <h1 class="h4 mb-4">User Profile Editor</h1>
    <div v-if="user && !user.username_valid" class="alert alert-danger">
      <p>
        Unfortunately the username on your profile is invalid, which prevents creating or updating
        your user profile. The administrators have been notified and will be able to update your
        user account with a valid username. An administrator will notify you once your username has
        been updated to a valid value.
      </p>
      <p>In the meantime, please complete as much of your profile as possible.</p>
    </div>
    <div v-else-if="mustComplete" class="alert alert-info">
      Please complete your user profile before continuing.
    </div>
    <div class="card">
      <div class="card-body">
        <user-profile-editor
          ref="userProfileEditor"
          @save="onSave"
          @resend-email-verification="handleResendEmailVerification"
        />
        <!-- include extended-user-profile-editor if there are extendedUserProfileFields -->
        <template v-if="hasExtendedUserProfileFields">
          <hr />
          <extended-user-profile-editor ref="extendedUserProfileEditor" />
        </template>

        <button class="btn btn-primary" @click="onSave">Save</button>
        <button v-if="!mustComplete" class="btn btn-success" href="/workspace/applications">
          Go to Applications
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { storeToRefs } from "pinia";
import UserProfileEditor from "../components/UserProfileEditor.vue";
import ExtendedUserProfileEditor from "../components/ExtendedUserProfileEditor.vue";
import { notifications } from "django-airavata-common-ui";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";

const userStore = useUserStore();
const { user, hasExtendedUserProfileFields } = storeToRefs(userStore);

const userProfileEditor = ref<InstanceType<typeof UserProfileEditor> | null>(null);
const extendedUserProfileEditor = ref<InstanceType<typeof ExtendedUserProfileEditor> | null>(null);

const mustComplete = computed(
  () => user.value && (!user.value.complete || !user.value.ext_user_profile_valid),
);

onMounted(async () => {
  await userStore.loadCurrentUser();
  await userStore.loadExtendedUserProfileFields();
  if (hasExtendedUserProfileFields.value) {
    await userStore.loadExtendedUserProfileValues();
  }

  const queryParams = new URLSearchParams(window.location.search);
  if (queryParams.has("code")) {
    const code = queryParams.get("code");
    if (code) {
      await userStore.verifyEmailChange({ code });
    }
    notifications.NotificationList.add(
      new notifications.Notification({
        type: "SUCCESS",
        message: "Email address verified and updated",
        duration: 5,
      }),
    );
    // Update URL, removing the code from the query string
    window.history.replaceState({}, "", "/auth/user-profile/");
  }
});

async function onSave(): Promise<void> {
  if (
    userProfileEditor.value?.valid &&
    (!hasExtendedUserProfileFields.value || extendedUserProfileEditor.value?.valid)
  ) {
    await userStore.updateUser();
    if (hasExtendedUserProfileFields.value) {
      await userStore.saveExtendedUserProfileValues();
    }
    // Reload current user to get updated 'complete' and 'ext_user_profile_valid'
    await userStore.loadCurrentUser();
    notifications.NotificationList.add(
      new notifications.Notification({
        type: "SUCCESS",
        message: "User profile saved",
        duration: 5,
      }),
    );
  } else if (hasExtendedUserProfileFields.value) {
    extendedUserProfileEditor.value?.touch();
  }
}

async function handleResendEmailVerification(): Promise<void> {
  await userStore.resendEmailVerification();
  notifications.NotificationList.add(
    new notifications.Notification({
      type: "SUCCESS",
      message: "Verification link sent",
      duration: 5,
    }),
  );
}
</script>

<style></style>
