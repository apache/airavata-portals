export default class BaseEnum {
  name: string;
  value: number | string;
  writeName: boolean;

  // TODO: add parameter
  constructor(name: string, value: number | string, writeName = false) {
    this.name = name;
    this.value = value;
    this.writeName = writeName;
    // immutable
    Object.freeze(this);
  }
  toJSON() {
    return this.writeName ? this.name : this.value;
  }
  static byName(this: typeof BaseEnum & { values: BaseEnum[] }, name: string): BaseEnum | undefined {
    return this.values.find((x) => x.name === name);
  }
  static byValue(this: typeof BaseEnum & { values: BaseEnum[] }, value: number | string): BaseEnum | undefined {
    return this.values.find((x) => x.value === value);
  }
  // This must be called to initialize static methods on the Enum subclass
  static init(this: new (name: string, index: number, writeName?: boolean) => BaseEnum, names: string[], writeName = false) {
    const enums = names.map((name, index) => new this(name, index, writeName));
    Object.freeze(enums);
    Object.defineProperty(this, "values", {
      get: function () {
        return enums;
      },
    });
    (enums as (BaseEnum & Record<string, unknown>)[]).forEach((v) => ((this as unknown as Record<string, unknown>)[v.name] = v));
  }
}
