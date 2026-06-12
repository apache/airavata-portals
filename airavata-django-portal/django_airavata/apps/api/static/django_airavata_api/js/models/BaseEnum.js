export default class BaseEnum {
  constructor(name, value, writeName = false) {
    this.name = name;
    this.value = value;
    this.writeName = writeName;
    // immutable
    Object.freeze(this);
  }
  toJSON() {
    // Serialize the proto member NAME on the wire, symmetric with the read
    // contract (the portal renders enums to NAMES via MessageToDict). The SDK
    // resolves the NAME back to the proto int — the proto enum is the type-truth.
    return this.name;
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

  // Strip the enum's SCREAMING_SNAKE prefix when present so
  // `ExperimentState.EXECUTING` resolves alongside the full
  // `ExperimentState.EXPERIMENT_STATE_EXECUTING`. The prefix is derived from the
  // 0-sentinel member name (see init) — NOT from this.name (the class name),
  // because minified production builds mangle class names, which previously left
  // every short alias unregistered (e.g. `ExperimentState.CREATED === undefined`).
  static shortAlias(name) {
    const prefix = this._prefix || "";
    return prefix && name.startsWith(prefix) ? name.slice(prefix.length) : name;
  }

  // names: full proto member names in proto order. Each value is registered
  // under its full name AND aliased to its stripped short name on the class, so
  // both byName(fullName)/this[fullName] and this[shortName] resolve. The prefix
  // is taken from the 0-sentinel (always carries the full prefix, e.g.
  // "EXPERIMENT_STATE_UNKNOWN") minus its trailing segment — a string literal
  // that survives minification, unlike the class name.
  static init(names, writeName = false) {
    const enums = names.map((name, index) => new this(name, index, writeName));
    Object.freeze(enums);
    Object.defineProperty(this, "values", { get: () => enums });
    const sentinel = names[0] || "";
    const lastUnderscore = sentinel.lastIndexOf("_");
    const prefix = lastUnderscore >= 0 ? sentinel.slice(0, lastUnderscore + 1) : "";
    Object.defineProperty(this, "_prefix", { value: prefix, configurable: true });
    this.values.forEach((v) => {
      this[v.name] = v;
      const short = this.shortAlias(v.name);
      if (short !== v.name) this[short] = v;
    });
  }
}
