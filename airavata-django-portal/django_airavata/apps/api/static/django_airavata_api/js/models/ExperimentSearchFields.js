import BaseEnum from "./BaseEnum";

export default class ExperimentSearchFields extends BaseEnum {}
ExperimentSearchFields.init([
  "EXPERIMENT_SEARCH_FIELDS_UNKNOWN",
  "EXPERIMENT_NAME",
  "EXPERIMENT_DESC",
  "APPLICATION_ID",
  "FROM_DATE",
  "TO_DATE",
  "STATUS",
  "PROJECT_ID",
  "USER_NAME",
  "JOB_ID",
]);
