<template>
  <main-layout
    title="Manage Notices"
    subtitle="Create and manage notices shown to gateway users."
  >
    <template v-slot:actions>
      <Button :disabled="!isGatewayAdmin" @click="addNewNotice">
        New Notice
        <Plus class="size-4" aria-hidden="true" />
      </Button>
    </template>
    <div class="space-y-4">
      <Card v-if="showNewItemEditor">
        <CardContent>
          <notice-editor
            v-model="newNotice"
            ref="noticeEditor"
            @cancelNewNotice="cancelNewNotice"
            @saveNewNotice="saveNewNotice"
          >
            <template v-slot:title>
              <h2 class="mr-auto text-lg font-semibold">New Notice</h2>
            </template>
          </notice-editor>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead v-for="field in fields" :key="field.key">
                  {{ field.label }}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <template v-for="item in items" :key="item.notification_id">
                <TableRow>
                  <TableCell>{{ item.title }}</TableCell>
                  <TableCell>{{ item.notification_message }}</TableCell>
                  <TableCell
                    ><human-date :date="item.published_time"
                  /></TableCell>
                  <TableCell
                    ><human-date :date="item.expiration_time"
                  /></TableCell>
                  <TableCell>{{ item.priority.name }}</TableCell>
                  <TableCell>{{ item.show_in_dashboard }}</TableCell>
                  <TableCell>
                    <template v-if="item.user_has_write_access">
                      <a
                        href="#"
                        class="mr-2 inline-flex items-center gap-1 text-primary hover:underline"
                        @click.prevent="toggleDetails(item)"
                      >
                        Edit
                        <Pencil class="size-4" aria-hidden="true" />
                      </a>
                      <delete-link @delete="deleteNotice(item.notification_id)">
                        Are you sure you want to delete the notice?
                      </delete-link>
                    </template>
                  </TableCell>
                </TableRow>
                <TableRow v-if="isExpanded(item)">
                  <TableCell :colspan="fields.length">
                    <Card>
                      <CardContent>
                        <notice-editor
                          :value="item"
                          v-model="updatedNotice"
                          @userBeginsInput="isUserBeginInput = false"
                        >
                          <template v-slot:title>
                            <h2 class="mr-auto text-lg font-semibold">
                              Update Notice
                            </h2>
                          </template>
                        </notice-editor>
                        <div class="mt-2 flex gap-2">
                          <Button
                            size="sm"
                            @click="updateNotice()"
                            :disabled="isUserBeginInput"
                            >Update</Button
                          >
                          <Button
                            variant="secondary"
                            size="sm"
                            @click="toggleDetails(item)"
                            >Close</Button
                          >
                        </div>
                      </CardContent>
                    </Card>
                  </TableCell>
                </TableRow>
              </template>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  </main-layout>
</template>

<script>
import { Pencil, Plus } from "@lucide/vue";
import { models, services, session } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import NoticeEditor from "./NoticeEditor";

export default {
  name: "notice-management-container",
  data() {
    return {
      notices: null,
      isUserBeginInput: true,
      showNewItemEditor: false,
      showingDetails: {},
      expandedRows: {},
    };
  },
  components: {
    Pencil,
    Plus,
    "human-date": components.HumanDate,
    "delete-link": components.DeleteLink,
    "main-layout": components.MainLayout,
    NoticeEditor,
  },
  created() {
    services.ManageNotificationService.list().then(
      (notices) => (this.notices = notices),
    );
  },
  computed: {
    fields() {
      return [
        {
          label: "Notice",
          key: "title",
        },
        {
          label: "Message",
          key: "notification_message",
        },
        {
          label: "Publish Date",
          key: "published_time",
        },
        {
          label: "Expiry Date",
          key: "expiration_time",
        },
        {
          label: "Priority",
          key: "priority.name",
        },
        {
          label: "Show In Dashboard",
          key: "show_in_dashboard",
        },
        {
          label: "Action",
          key: "action",
        },
      ];
    },
    items() {
      return this.notices ? this.notices : [];
    },
    isGatewayAdmin() {
      return session.Session.isGatewayAdmin;
    },
  },
  methods: {
    saveNewNotice() {
      services.ManageNotificationService.create({ data: this.newNotice }).then(
        (sp) => {
          this.notices.push(sp);
        },
      );
      this.showNewItemEditor = true;
    },
    updateNotice() {
      const validation = this.updatedNotice.validate();
      if (Object.keys(validation).length === 0) {
        const index = this.notices.findIndex(
          (sp) => sp.notification_id === this.updatedNotice.notification_id,
        );
        services.ManageNotificationService.update({
          lookup: this.updatedNotice.notification_id,
          data: this.updatedNotice,
        }).then((sp) => {
          this.notices.splice(index, 1, sp);
        });
      }
    },
    cancelNewNotice() {
      this.showNewItemEditor = false;
    },
    addNewNotice() {
      this.newNotice = new models.Notification();
      this.showNewItemEditor = true;
    },
    deleteNotice(notificationId) {
      services.ManageNotificationService.delete({
        lookup: notificationId,
      }).then(() => {
        const index = this.notices.findIndex(
          (sp) => sp.notification_id === notificationId,
        );
        this.notices.splice(index, 1);
      });
    },
    isExpanded(item) {
      return Boolean(this.expandedRows[item.notification_id]);
    },
    toggleDetails(item) {
      this.updatedNotice = new models.Notification();
      this.updatedNotice = item;
      this.expandedRows[item.notification_id] =
        !this.expandedRows[item.notification_id];
      this.showingDetails[item.notification_id] =
        !this.showingDetails[item.notification_id];
    },
  },
};
</script>
