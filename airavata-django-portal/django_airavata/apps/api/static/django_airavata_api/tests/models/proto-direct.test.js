// Foundation contract for proto-direct snake_case consumption: the BaseEnum
// full-name + short-alias mechanism, BaseModel.convertDateField on epoch-millis
// strings, and a reference Experiment built from a contract-shaped object.
import BaseEnum from "../../js/models/BaseEnum";
import BaseModel from "../../js/models/BaseModel";
import Experiment from "../../js/models/Experiment";
import ExperimentState from "../../js/models/ExperimentState";

describe("BaseEnum full proto name + short alias", () => {
  test("byName resolves the full proto member name", () => {
    expect(ExperimentState.byName("EXPERIMENT_STATE_EXECUTING")).toBe(
      ExperimentState.EXPERIMENT_STATE_EXECUTING
    );
    expect(ExperimentState.byName("EXPERIMENT_STATE_EXECUTING").name).toBe(
      "EXPERIMENT_STATE_EXECUTING"
    );
  });

  test("short alias constant resolves to the same value", () => {
    expect(ExperimentState.EXECUTING).toBe(
      ExperimentState.EXPERIMENT_STATE_EXECUTING
    );
    expect(ExperimentState.byName("EXECUTING")).toBe(ExperimentState.EXECUTING);
  });

  test("0-sentinel is representable", () => {
    expect(ExperimentState.byName("EXPERIMENT_STATE_UNKNOWN")).toBe(
      ExperimentState.UNKNOWN
    );
  });

  test("bare-named members (no prefix) register as-is", () => {
    class DataType extends BaseEnum {}
    DataType.init(["DATA_TYPE_UNKNOWN", "STRING", "INTEGER", "URI"]);
    expect(DataType.STRING).toBe(DataType.byName("STRING"));
    expect(DataType.STRING.name).toBe("STRING");
    // 0-sentinel still carries the prefix and gets a stripped UNKNOWN alias.
    expect(DataType.UNKNOWN).toBe(DataType.byName("DATA_TYPE_UNKNOWN"));
  });

  test("per-member inconsistent prefixing yields correct short aliases", () => {
    // DataMovementProtocol keeps the prefix on LOCAL but not on SCP/SFTP.
    class DataMovementProtocol extends BaseEnum {}
    DataMovementProtocol.init([
      "DATA_MOVEMENT_PROTOCOL_UNKNOWN",
      "DATA_MOVEMENT_PROTOCOL_LOCAL",
      "SCP",
      "SFTP",
    ]);
    expect(DataMovementProtocol.LOCAL).toBe(
      DataMovementProtocol.byName("DATA_MOVEMENT_PROTOCOL_LOCAL")
    );
    expect(DataMovementProtocol.SFTP.name).toBe("SFTP");
  });
});

describe("BaseModel.convertDateField on epoch-millis", () => {
  const bm = Object.create(BaseModel.prototype);

  test("epoch-millis string parses to the right Date", () => {
    const d = bm.convertDateField("1705320000000", null);
    expect(d).toBeInstanceOf(Date);
    expect(d.getTime()).toBe(1705320000000);
  });

  test("epoch-millis number parses to the right Date", () => {
    expect(bm.convertDateField(1705320000000, null).getTime()).toBe(
      1705320000000
    );
  });

  test("'0' parses to the epoch, not Invalid Date", () => {
    expect(bm.convertDateField("0", null).getTime()).toBe(0);
  });

  test("null/undefined fall back to the default", () => {
    expect(bm.convertDateField(undefined, "DFLT")).toBe("DFLT");
    expect(bm.convertDateField(null, "DFLT")).toBe("DFLT");
  });
});

describe("Experiment from a snake_case contract-shaped object", () => {
  const data = {
    experiment_id: "exp-1",
    project_id: "proj-1",
    gateway_id: "default",
    experiment_type: "SINGLE_APPLICATION",
    user_name: "alice",
    experiment_name: "Contract Experiment",
    creation_time: "1705320000000",
    description: "desc",
    execution_id: "iface-1",
    email_addresses: ["a@x.org"],
    user_has_write_access: true,
    experiment_status: [
      {
        state: "EXPERIMENT_STATE_EXECUTING",
        time_of_state_change: "1705320004000",
        reason: "running",
        status_id: "es-1",
      },
    ],
  };

  test("snake_case scalar properties are exposed", () => {
    const exp = new Experiment(data);
    expect(exp.experiment_name).toBe("Contract Experiment");
    expect(exp.project_id).toBe("proj-1");
    expect(exp.user_name).toBe("alice");
    expect(exp.experiment_type).toBe("SINGLE_APPLICATION");
    expect(exp.user_has_write_access).toBe(true);
  });

  test("creation_time parses from the epoch-millis string", () => {
    expect(new Experiment(data).creation_time.getTime()).toBe(1705320000000);
  });

  test("nested experiment_status state resolves via the full wire enum name", () => {
    const exp = new Experiment(data);
    expect(exp.experiment_status[0].state).toBe(
      ExperimentState.EXPERIMENT_STATE_EXECUTING
    );
    expect(exp.latestStatus.state).toBe(ExperimentState.EXECUTING);
    expect(exp.isProgressing).toBe(true);
    expect(exp.experiment_status[0].time_of_state_change.getTime()).toBe(
      1705320004000
    );
  });
});
