<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Manage Notices</h1>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <list-layout
              title="Notice"
              new-item-button-text="New Notice"
              :new-button-disabled="!isGatewayAdmin"
              @add-new-item="addNewNotice"
            >
              <template #new-item-editor>
                <div v-if="showNewItemEditor" class="card">
                  <notice-editor
                    ref="noticeEditor"
                    v-model="newNotice"
                    @cancel-new-notice="cancelNewNotice"
                    @save-new-notice="saveNewNotice"
                  >
                    <template #title>
                      <h1 class="h4 mb-4 me-auto">New Notice</h1>
                    </template>
                  </notice-editor>
                </div>
              </template>
              <template #item-list>
                <table class="table">
                  <thead>
                    <tr>
                      <th>Published Time</th>
                      <th>Expiration Time</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in items" :key="item.notificationId">
                      <td><human-date :date="item.publishedTime" /></td>
                      <td><human-date :date="item.expirationTime" /></td>
                      <td>
                        <template v-if="item.user_has_write_access">
                          <a class="action-link" @click="editNotice(item)">
                            Edit
                            <i class="fa fa-edit" aria-hidden="true"></i>
                          </a>
                          <delete-link @delete="deleteNotice(item.notificationId)">
                            Are you sure you want to delete the notice?
                          </delete-link>
                        </template>
                      </td>
                    </tr>
                    <tr v-if="items && items.length === 0">
                      <td colspan="3" class="text-center text-muted py-4">
                        <i class="fa fa-bell fa-2x d-block mb-2 text-muted"></i>
                        No notices yet. Click "New Notice" to publish one.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </template>
            </list-layout>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { models, services, session } from "django-airavata-api";
import NoticeEditor from "./NoticeEditor.vue";

const notices = ref<InstanceType<typeof models.Notification>[] | null>(null);
const showNewItemEditor = ref(false);
const newNotice = ref<InstanceType<typeof models.Notification>>(new models.Notification());

const items = computed(() => notices.value ?? []);
const isGatewayAdmin = computed(() => session.Session.is_gateway_admin);

onMounted(() => {
  services.ManageNotificationService.list().then(
    (n: InstanceType<typeof models.Notification>[]) => (notices.value = n)
  );
});

function saveNewNotice() {
  services.ManageNotificationService.create({ data: newNotice.value }).then(
    (sp: InstanceType<typeof models.Notification>) => {
      notices.value!.push(sp);
    }
  );
  showNewItemEditor.value = false;
}

function cancelNewNotice() {
  showNewItemEditor.value = false;
}

function addNewNotice() {
  newNotice.value = new models.Notification();
  showNewItemEditor.value = true;
}

function deleteNotice(notificationId: string) {
  services.ManageNotificationService.delete({ lookup: notificationId }).then(() => {
    const index = notices.value!.findIndex((sp) => sp.notificationId === notificationId);
    notices.value!.splice(index, 1);
  });
}

function editNotice(item: InstanceType<typeof models.Notification>) {
  newNotice.value = item;
  showNewItemEditor.value = true;
}
</script>
