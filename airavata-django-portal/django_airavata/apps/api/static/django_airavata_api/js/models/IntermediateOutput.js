import BaseModel from "./BaseModel";
import ProcessStatus from "./ProcessStatus";
import DataProduct from "./DataProduct";

// Portal-composed (not a proto): the experiments ViewSet's
// _add_intermediate_output_information emits process_status + data_products.
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
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
