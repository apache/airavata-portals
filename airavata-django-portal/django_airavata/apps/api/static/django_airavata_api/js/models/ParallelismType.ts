import BaseEnum from "./BaseEnum";

export default class ParallelismType extends BaseEnum {
  static SERIAL: ParallelismType;
  static MPI: ParallelismType;
  static OPENMP: ParallelismType;
  static OPENMP_MPI: ParallelismType;
  static CCM: ParallelismType;
  static CRAY_MPI: ParallelismType;
  static values: ParallelismType[];
}
ParallelismType.init(["SERIAL", "MPI", "OPENMP", "OPENMP_MPI", "CCM", "CRAY_MPI"]);
