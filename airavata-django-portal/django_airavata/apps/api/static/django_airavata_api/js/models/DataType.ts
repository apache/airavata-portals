import BaseEnum from "./BaseEnum";

export default class DataType extends BaseEnum {
  static STRING: DataType;
  static INTEGER: DataType;
  static FLOAT: DataType;
  static URI: DataType;
  static URI_COLLECTION: DataType;
  static STDOUT: DataType;
  static STDERR: DataType;
  static values: DataType[];

  get isSimpleValueType() {
    return [DataType.STRING, DataType.INTEGER, DataType.FLOAT].indexOf(this) >= 0;
  }
  get isFileValueType() {
    return (
      [DataType.URI, DataType.URI_COLLECTION, DataType.STDOUT, DataType.STDERR].indexOf(this) >= 0
    );
  }
}
// NOTE: Serialize enum as its name (writeName=true) so that the backend's
// protobuf ParseDict maps values by enum name rather than ordinal. The
// frontend ordinals DO NOT match the real protobuf enum values (which
// include DATA_TYPE_UNKNOWN=0 and start STRING at 1), so sending numeric
// values would silently corrupt the data type (e.g. STDOUT would be read
// as URI_COLLECTION). See application_io.proto.
DataType.init(["STRING", "INTEGER", "FLOAT", "URI", "URI_COLLECTION", "STDOUT", "STDERR"], true);
