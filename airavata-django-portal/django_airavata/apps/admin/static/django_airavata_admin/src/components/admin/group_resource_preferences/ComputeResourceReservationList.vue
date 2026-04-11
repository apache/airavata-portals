<template>
  <list-layout
    @add-new-item="addNewReservation"
    :items="decoratedReservations"
    title="Reservations"
    new-item-button-text="New Reservation"
    :newButtonDisabled="readonly"
  >
    <template #additional-buttons>
      <delete-button
        class="me-2"
        @delete="deleteAllExpiredReservations"
        label="Delete All Expired"
        :disabled="expiredReservations.length === 0"
      >
        Are you sure you want to delete all expired reservations?
      </delete-button>
    </template>
    <template #new-item-editor>
      <div class="card" v-if="showNewItemEditor">
        <div class="card-header">New Reservation</div>
        <div class="card-body">
          <compute-resource-reservation-editor
            v-model="newReservation"
            :queues="queues"
            @valid="
              newReservationValid = true;
              validate();
            "
            @invalid="
              newReservationValid = false;
              validate();
            "
          />
          <div class="row">
            <div class="col">
              <button class="btn btn-primary btn-sm"
                @click="saveNewReservation"
                :disabled="isSaveDisabled"
              >
                Add
              </button>
              <button class="btn btn-secondary btn-sm" @click="cancelNewReservation">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #item-list="slotProps">
      <table class="table">
        <thead>
          <tr>
            <th>Reservation Name</th>
            <th>Queue Names</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in slotProps.items" :key="item.key">
            <td>
              {{ item.reservationName }}
              <span class="badge bg-secondary" v-if="item.isExpired">Expired</span>
              <span class="badge bg-success" v-if="item.isActive">Active</span>
              <span class="badge bg-info" v-if="item.isUpcoming">Upcoming</span>
            </td>
            <td>
              <ul>
                <li v-for="queueName in item.queueNames" :key="queueName">{{ queueName }}</li>
              </ul>
            </td>
            <td>
              <a
                v-if="!readonly"
                class="action-link"
                @click="editReservation(item)"
              >
                Edit
                <i class="fa fa-edit" aria-hidden="true"></i>
              </a>
              <delete-link
                v-if="!readonly"
                class="action-link"
                @delete="deleteReservation(item)"
              >
                Are you sure you want to delete reservation
                <strong>{{ item.reservationName }}</strong>?
              </delete-link>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
  </list-layout>
</template>

<script>
import { models } from "django-airavata-api";
import { components, layouts, utils } from "django-airavata-common-ui";
import ComputeResourceReservationEditor from "./ComputeResourceReservationEditor";

export default {
  name: "compute-resource-reservation-list",
  components: {
    "delete-link": components.DeleteLink,
    "list-layout": layouts.ListLayout,
    ComputeResourceReservationEditor,
    "delete-button": components.DeleteButton,
  },
  props: {
    reservations: {
      type: Array,
      required: true,
    },
    queues: {
      type: Array,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      showingDetails: {},
      showNewItemEditor: false,
      newReservation: null,
      newReservationValid: false,
      invalidReservations: [], // list of ComputeResourceReservation.key
    };
  },
  computed: {
    fields() {
      return [
        {
          label: "Name",
          key: "reservationName",
        },
        {
          label: "Queues",
          key: "queueNames",
        },
        {
          label: "Start Time",
          key: "startTime",
          formatter: (value) =>
            utils.dateFormatters.dateTimeInMinutesWithTimeZone.format(value),
        },
        {
          label: "End Time",
          key: "endTime",
          formatter: (value) =>
            utils.dateFormatters.dateTimeInMinutesWithTimeZone.format(value),
        },
        {
          label: "Action",
          key: "action",
        },
      ];
    },
    decoratedReservations() {
      return this.reservations
        ? this.reservations.map((res) => {
            const resClone = res.clone();
            resClone._showDetails = this.showingDetails[resClone.key];
            return resClone;
          })
        : [];
    },
    isSaveDisabled() {
      return !this.newReservationValid;
    },
    valid() {
      return (
        (!this.showNewItemEditor || this.newReservationValid) &&
        this.invalidReservations.length === 0
      );
    },
    expiredReservations() {
      return this.reservations
        ? this.reservations.filter((r) => r.isExpired)
        : [];
    },
  },
  created() {},
  methods: {
    updatedReservation(newValue) {
      this.$emit("updated", newValue);
    },
    toggleDetails(row) {
      row.toggleDetails();
      this.showingDetails[row.item.key] = !this.showingDetails[row.item.key];
    },
    deleteReservation(reservation) {
      this.removeInvalidReservation(reservation.key);
      this.$emit("deleted", reservation);
    },
    addNewReservation() {
      this.newReservation = new models.ComputeResourceReservation();
      this.newReservationValid = false;
      this.newReservation.queueNames = this.queues.slice();
      this.showNewItemEditor = true;
    },
    saveNewReservation() {
      this.$emit("added", this.newReservation);
      this.showNewItemEditor = false;
    },
    cancelNewReservation() {
      this.showNewItemEditor = false;
    },
    recordInvalidReservation(reservationKey) {
      if (this.invalidReservations.indexOf(reservationKey) < 0) {
        this.invalidReservations.push(reservationKey);
      }
      this.validate();
    },
    removeInvalidReservation(reservationKey) {
      const index = this.invalidReservations.indexOf(reservationKey);
      if (index >= 0) {
        this.invalidReservations.splice(index, 1);
      }
      this.validate();
    },
    isReservationInvalid(reservationKey) {
      return this.invalidReservations.indexOf(reservationKey) >= 0;
    },
    validate() {
      if (this.valid) {
        this.$emit("valid");
      } else {
        this.$emit("invalid");
      }
    },
    deleteAllExpiredReservations() {
      this.expiredReservations.forEach(this.deleteReservation);
    },
  },
};
</script>
