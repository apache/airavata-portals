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
              @add-new-item="addNewNotice"
              title="Notice"
              new-item-button-text="New Notice"
              :new-button-disabled="!isGatewayAdmin"
            >
              <template slot="new-item-editor">
                <b-card v-if="showNewItemEditor">
                  <notice-editor
                    v-model="newNotice"
                    ref="noticeEditor"
                    @cancelNewNotice="cancelNewNotice"
                    @saveNewNotice="saveNewNotice"
                  >
                    <template slot="title">
                      <h1 class="h4 mb-4 mr-auto">New Notice</h1>
                    </template>
                  </notice-editor>
                </b-card>
              </template>
              <template slot="item-list">
                <b-table hover :fields="fields" :items="items">
                  <template slot="cell(published_time)" slot-scope="data">
                    <human-date :date="data.value" /> </template
                  >row
                  <template slot="cell(expiration_time)" slot-scope="data">
                    <human-date :date="data.value" />
                  </template>
                  <template slot="cell(action)" slot-scope="data">
                    <template v-if="data.item.user_has_write_access">
                      <b-link class="action-link" @click="toggleDetails(data)">
                        Edit
                        <i class="fa fa-edit" aria-hidden="true"></i>
                      </b-link>
                      <delete-link
                        @delete="deleteNotice(data.item.notification_id)"
                      >
                        Are you sure you want to delete the notice?
                      </delete-link>
                    </template>
                  </template>
                  <template slot="row-details" slot-scope="row">
                    <b-card>
                      <notice-editor
                        :value="row.item"
                        v-model="updatedNotice"
                        @userBeginsInput="isUserBeginInput = false"
                      >
                        <template slot="title">
                          <h1 class="h4 mb-4 mr-auto">Update Notice</h1>
                        </template>
                      </notice-editor>
                      <b-button
                        variant="success"
                        size="sm"
                        @click="updateNotice()"
                        :disabled="isUserBeginInput"
                        >Update</b-button
                      >
                      <b-button
                        variant="primary"
                        size="sm"
                        @click="toggleDetails(row)"
                        >Close</b-button
                      >
                    </b-card>
                  </template>
                </b-table>
              </template>
            </list-layout>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
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
    };
  },
  components: {
    "human-date": components.HumanDate,
    "delete-link": components.DeleteLink,
    "list-layout": layouts.ListLayout,
    NoticeEditor,
  },
  created() {
    services.ManageNotificationService.list().then(
      (notices) => (this.notices = notices)
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
        }
      );
      this.showNewItemEditor = true;
    },
    updateNotice() {
      const validation = this.updatedNotice.validate();
      if (Object.keys(validation).length === 0) {
        const index = this.notices.findIndex(
          (sp) => sp.notification_id === this.updatedNotice.notification_id
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
          (sp) => sp.notification_id === notificationId
        );
        this.notices.splice(index, 1);
      });
    },
    toggleDetails(row) {
      (this.updatedNotice = new models.Notification()),
        (this.updatedNotice = row.item);
      row.toggleDetails();
      this.showingDetails[row.item.notification_id] = !this.showingDetails[
        row.item.notification_id
      ];
    },
  },
};
</script>
