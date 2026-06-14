<template>
  <div>
    <div>
      <h1 class="mb-4 text-xl font-semibold">Manage Notices</h1>
    </div>
    <Card>
      <CardContent>
        <list-layout
          @add-new-item="addNewNotice"
          title="Notice"
          new-item-button-text="New Notice"
          :new-button-disabled="!isGatewayAdmin"
        >
          <template v-slot:new-item-editor>
            <Card v-if="showNewItemEditor">
              <CardContent>
                <notice-editor
                  v-model="newNotice"
                  ref="noticeEditor"
                  @cancelNewNotice="cancelNewNotice"
                  @saveNewNotice="saveNewNotice"
                >
                  <template v-slot:title>
                    <h1 class="mr-auto mb-4 text-xl font-semibold">
                      New Notice
                    </h1>
                  </template>
                </notice-editor>
              </CardContent>
            </Card>
          </template>
          <template v-slot:item-list>
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
                        <delete-link
                          @delete="deleteNotice(item.notification_id)"
                        >
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
                              <h1 class="mr-auto mb-4 text-xl font-semibold">
                                Update Notice
                              </h1>
                            </template>
                          </notice-editor>
                          <div class="mt-2 flex gap-2">
                            <Button
                              variant="default"
                              size="sm"
                              class="bg-success text-success-foreground hover:bg-success/90"
                              @click="updateNotice()"
                              :disabled="isUserBeginInput"
                              >Update</Button
                            >
                            <Button
                              variant="default"
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
          </template>
        </list-layout>
      </CardContent>
    </Card>
  </div>
</template>

<script>
import { Pencil } from "@lucide/vue";
import { models, services, session } from "django-airavata-api";
import { components, layouts } from "django-airavata-common-ui";
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
    "human-date": components.HumanDate,
    "delete-link": components.DeleteLink,
    "list-layout": layouts.ListLayout,
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
