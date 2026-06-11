export default class BaseEnum {
  constructor(name, value, writeName = false) {
    this.name = name;
    this.value = value;
    this.writeName = writeName;
    // immutable
    Object.freeze(this);
  }
  toJSON() {
    return this.writeName ? this.name : this.value;
  }
  // Wire enum values are full proto member names ("EXPERIMENT_STATE_EXECUTING");
  // byName also accepts the stripped short alias ("EXECUTING") so component-level
  // constant lookups keep resolving.
  static byName(name) {
    return (
      this.values.find((x) => x.name === name) ||
      this.values.find((x) => this.shortAlias(x.name) === name)
    );
  }
  static byValue(value) {
    return this.values.find((x) => x.value === value);
  }

  // The 0-sentinel is the only member that always carries the full
  // SCREAMING_SNAKE(className) prefix; non-zero members carry it inconsistently
  // (ExperimentState.EXPERIMENT_STATE_CREATED, but DataType.STRING). Strip the
  // prefix when present so `ExperimentState.EXECUTING` resolves either way.
  static shortAlias(name) {
    const prefix = this.name.replace(/([a-z0-9])([A-Z])/g, "$1_$2").toUpperCase() + "_";
    return name.startsWith(prefix) ? name.slice(prefix.length) : name;
  }

  // names: full proto member names in proto order. Each value is registered
  // under its full name AND aliased to its stripped short name on the class, so
  // both byName(fullName)/this[fullName] and this[shortName] resolve.
  static init(names, writeName = false) {
    const enums = names.map((name, index) => new this(name, index, writeName));
    Object.freeze(enums);
    Object.defineProperty(this, "values", { get: () => enums });
    this.values.forEach((v) => {
      this[v.name] = v;
      this[this.shortAlias(v.name)] = v;
    });
  }
}
