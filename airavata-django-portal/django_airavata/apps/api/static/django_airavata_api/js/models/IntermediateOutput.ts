import BaseModel from "./BaseModel";
import ProcessStatus from "./ProcessStatus";
import DataProduct from "./DataProduct";

const FIELDS = [
  {
    name: "process_status",
    type: ProcessStatus,
  },
  {
    name: "data_products",
    type: DataProduct,
    list: true,
  },
];

export default class IntermediateOutput extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
