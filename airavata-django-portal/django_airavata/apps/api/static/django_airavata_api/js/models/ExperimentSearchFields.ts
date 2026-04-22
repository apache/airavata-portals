import BaseEnum from "./BaseEnum";

export default class ExperimentSearchFields extends BaseEnum {
  static EXPERIMENT_NAME: ExperimentSearchFields;
  static EXPERIMENT_DESC: ExperimentSearchFields;
  static APPLICATION_ID: ExperimentSearchFields;
  static FROM_DATE: ExperimentSearchFields;
  static TO_DATE: ExperimentSearchFields;
  static STATUS: ExperimentSearchFields;
  static PROJECT_ID: ExperimentSearchFields;
  static USER_NAME: ExperimentSearchFields;
  static JOB_ID: ExperimentSearchFields;
  static values: ExperimentSearchFields[];
}
ExperimentSearchFields.init([
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
