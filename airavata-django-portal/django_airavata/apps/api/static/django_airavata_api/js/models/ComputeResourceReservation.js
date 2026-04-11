import BaseModel from "./BaseModel";
import { v4 as uuidv4 } from "uuid";

function currentTimeTopOfHour() {
  const d = new Date();
  d.setMinutes(0);
  d.setSeconds(0);
  d.setMilliseconds(0);
  return d;
}
const FIELDS = [
  "reservation_id",
  "reservation_name",
  {
    name: "queue_names",
    type: "string",
    list: true,
  },
  {
    name: "start_time",
    type: Date,
    default: () => currentTimeTopOfHour(),
  },
  {
    name: "end_time",
    type: Date,
    default: () => currentTimeTopOfHour(),
  },
];

export default class ComputeResourceReservation extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
    this._key = data.key ? data.key : uuidv4();
  }
  get key() {
    return this._key;
  }
  validate() {
    let validationResults = {};
    if (this.isEmpty(this.reservation_name)) {
      validationResults["reservation_name"] =
        "Please provide the name of this reservation.";
    }
    if (this.start_time > this.end_time) {
      validationResults["end_time"] = "End time must be later than start time.";
    }
    if (this.isEmpty(this.queue_names)) {
      validationResults["queue_names"] = "Please select at least one queue.";
    }
    return validationResults;
  }
  get isExpired() {
    const now = new Date();
    return now > this.end_time;
  }
  get isActive() {
    const now = new Date();
    return this.start_time < now && now < this.end_time;
  }
  get isUpcoming() {
    const now = new Date();
    return now < this.start_time;
  }
}
