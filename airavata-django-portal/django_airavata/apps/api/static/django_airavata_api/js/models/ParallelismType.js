import BaseEnum from "./BaseEnum";

// Proto enum is `ApplicationParallelismType`; members below are the bare proto
// names. The 0-sentinel registers only under its full name.
export default class ParallelismType extends BaseEnum {}
ParallelismType.init([
  "APPLICATION_PARALLELISM_TYPE_UNKNOWN",
  "SERIAL",
  "MPI",
  "OPENMP",
  "OPENMP_MPI",
  "CCM",
  "CRAY_MPI",
]);
