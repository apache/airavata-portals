<template>
  <div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <!-- TODO: Replace b-table with native table -->
            <table class="table">
              <thead>
                <tr>
                  <th>First Name</th>
                  <th>Last Name</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Email Verified</th>
                  <th>Created</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in items" :key="(item as Record<string, unknown>).user_id as string">
                  <td>{{ (item as Record<string, unknown>).first_name }}</td>
                  <td>{{ (item as Record<string, unknown>).last_name }}</td>
                  <td>{{ (item as Record<string, unknown>).user_id }}</td>
                  <td>{{ (item as Record<string, unknown>).email }}</td>
                  <td>{{ (item as Record<string, unknown>).email_verified }}</td>
                  <td>{{ (item as Record<string, unknown>).creation_time }}</td>
                  <td>
                    <enable-user-panel
                      v-if="!(item as Record<string, unknown>).enabled && !(item as Record<string, unknown>).email_verified"
                      :username="(item as Record<string, unknown>).user_id as string"
                      :email="(item as Record<string, unknown>).email as string"
                      @enable-user="enableUser"
                    />
                    <delete-user-panel
                      v-if="!(item as Record<string, unknown>).enabled && !(item as Record<string, unknown>).email_verified"
                      :username="(item as Record<string, unknown>).user_id as string"
                      @delete-user="deleteUser"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
            <pager :paginator="usersPaginator" @next="next" @previous="previous"></pager>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { services } from "django-airavata-api";
import EnableUserPanel from "./EnableUserPanel.vue";
import DeleteUserPanel from "./DeleteUserPanel.vue";

const usersPaginator = ref<{ results: unknown[]; next: () => void; previous: () => void } | null>(null);

const items = computed(() => usersPaginator.value?.results ?? []);

onMounted(() => {
  services.UnverifiedEmailUserProfileService.list({ limit: 10 }).then(
    (users: typeof usersPaginator.value) => (usersPaginator.value = users)
  );
});

function next() {
  usersPaginator.value!.next();
}

function previous() {
  usersPaginator.value!.previous();
}

function loadUnverifiedEmailUsers() {
  return services.UnverifiedEmailUserProfileService.list({ limit: 10 }).then(
    (users: typeof usersPaginator.value) => (usersPaginator.value = users)
  );
}

function enableUser(username: string) {
  services.IAMUserProfileService.enable({ lookup: username }).finally(() =>
    loadUnverifiedEmailUsers()
  );
}

function deleteUser(username: string) {
  services.IAMUserProfileService.delete({ lookup: username }).finally(() =>
    loadUnverifiedEmailUsers()
  );
}

</script>
