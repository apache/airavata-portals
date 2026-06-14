<template>
  <list-layout
    @add-new-item="addNewReservation"
    :items="decoratedReservations"
    title="Reservations"
    new-item-button-text="New Reservation"
    :newButtonDisabled="readonly"
  >
    <template v-slot:additional-buttons>
      <delete-button
        class="mr-2"
        @delete="deleteAllExpiredReservations"
        label="Delete All Expired"
        :disabled="expiredReservations.length === 0"
      >
        Are you sure you want to delete all expired reservations?
      </delete-button>
    </template>
    <template v-slot:new-item-editor>
      <Card v-if="showNewItemEditor">
        <CardHeader>
          <CardTitle>New Reservation</CardTitle>
        </CardHeader>
        <CardContent>
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
          <div class="mt-4 flex gap-2">
            <Button
              variant="default"
              @click="saveNewReservation"
              :disabled="isSaveDisabled"
            >
              Add
            </Button>
            <Button variant="secondary" @click="cancelNewReservation">
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </template>
    <template v-slot:item-list="slotProps">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead v-for="field in fields" :key="field.key">
              {{ field.label }}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <template v-for="item in slotProps.items" :key="item.key">
            <TableRow>
              <TableCell>
                {{ item.reservation_name }}
                <Badge v-if="item.isExpired">Expired</Badge>
                <Badge
                  v-if="item.isActive"
                  class="border-transparent bg-success text-success-foreground"
                  >Active</Badge
                >
                <Badge v-if="item.isUpcoming" variant="secondary"
                  >Upcoming</Badge
                >
              </TableCell>
              <TableCell>
                <ul class="list-disc pl-5">
                  <li v-for="queueName in item.queue_names" :key="queueName">
                    {{ queueName }}
                  </li>
                </ul>
              </TableCell>
              <TableCell>{{ formatDate(item.start_time) }}</TableCell>
              <TableCell>{{ formatDate(item.end_time) }}</TableCell>
              <TableCell>
                <a
                  href="#"
                  v-if="!readonly"
                  class="mr-2 inline-flex items-center gap-1 text-primary hover:underline"
                  :class="{
                    'pointer-events-none opacity-50': isReservationInvalid(
                      item.key,
                    ),
                  }"
                  @click.prevent="toggleDetails(item)"
                >
                  Edit
                  <Pencil class="size-4" aria-hidden="true" />
                </a>
                <delete-link
                  v-if="!readonly"
                  @delete="deleteReservation(item)"
                >
                  Are you sure you want to delete reservation
                  <strong>{{ item.reservation_name }}</strong
                  >?
                </delete-link>
              </TableCell>
            </TableRow>
            <TableRow v-if="item._showDetails">
              <TableCell :colspan="fields.length">
                <Card>
                  <CardContent>
                    <compute-resource-reservation-editor
                      :value="item"
                      @input="updatedReservation"
                      :queues="queues"
                      @valid="removeInvalidReservation(item.key)"
                      @invalid="recordInvalidReservation(item.key)"
                    />
                    <Button
                      class="mt-2"
                      size="sm"
                      @click="toggleDetails(item)"
                      :disabled="isReservationInvalid(item.key)"
                      >Close</Button
                    >
                  </CardContent>
                </Card>
              </TableCell>
            </TableRow>
          </template>
        </TableBody>
      </Table>
    </template>
  </list-layout>
</template>

<script>
import { Pencil } from "@lucide/vue";
import { models } from "django-airavata-api";
import { components, layouts, utils } from "django-airavata-common-ui";
import ComputeResourceReservationEditor from "./ComputeResourceReservationEditor";

export default {
  name: "compute-resource-reservation-list",
  components: {
    Pencil,
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
          key: "reservation_name",
        },
        {
          label: "Queues",
          key: "queue_names",
        },
        {
          label: "Start Time",
          key: "start_time",
          formatter: (value) =>
            utils.dateFormatters.dateTimeInMinutesWithTimeZone.format(value),
        },
        {
          label: "End Time",
          key: "end_time",
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
    formatDate(value) {
      return utils.dateFormatters.dateTimeInMinutesWithTimeZone.format(value);
    },
    updatedReservation(newValue) {
      this.$emit("updated", newValue);
    },
    toggleDetails(item) {
      this.showingDetails[item.key] = !this.showingDetails[item.key];
    },
    deleteReservation(reservation) {
      this.removeInvalidReservation(reservation.key);
      this.$emit("deleted", reservation);
    },
    addNewReservation() {
      this.newReservation = new models.ComputeResourceReservation();
      this.newReservationValid = false;
      this.newReservation.queue_names = this.queues.slice();
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
