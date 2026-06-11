import BaseModel from "./BaseModel";
import UserStatus from "./UserStatus";

const FIELDS = [
  "user_model_version",
  "airavata_internal_user_id",
  "user_id",
  "gateway_id",
  "emails",
  "first_name",
  "last_name",
  "middle_name",
  "name_prefix",
  "name_suffix",
  "orcid_id",
  "phones",
  "country",
  "nationality",
  "home_organization",
  // proto field is spelled origination_affiliation (the old camel orgination* was a typo).
  "origination_affiliation",
  {
    name: "creation_time",
    type: "date",
  },
  {
    name: "last_access_time",
    type: "date",
  },
  "valid_until",
  {
    name: "state",
    type: UserStatus,
  },
  "comments",
  "labeled_uri",
  "gpg_key",
  "time_zone",
  "nsf_demographics",
  "custom_dashboard",
];

export default class UserProfile extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  get email() {
    return this.emails != null && this.emails.length > 0
      ? this.emails[0]
      : null;
  }
}
