/**
 * Aggregate validation state of child components. Child components should
 * dispatch 'valid' and 'invalid' events and component using this mixin should
 * call recordValidChildComponent or recordInvalidChildComponent, respectively.
 */

type ValidationParentInstance = {
  invalidChildComponents: string[];
};

export default {
  data(): { invalidChildComponents: string[] } {
    return {
      invalidChildComponents: [],
    };
  },
  computed: {
    childComponentsAreValid(this: ValidationParentInstance): boolean {
      return this.invalidChildComponents.length === 0;
    },
  },
  methods: {
    recordInvalidChildComponent(
      this: ValidationParentInstance,
      childComponentId: string
    ): void {
      if (!this.invalidChildComponents.includes(childComponentId)) {
        this.invalidChildComponents.push(childComponentId);
      }
    },
    recordValidChildComponent(
      this: ValidationParentInstance,
      childComponentId: string
    ): void {
      if (this.invalidChildComponents.includes(childComponentId)) {
        const index = this.invalidChildComponents.indexOf(childComponentId);
        this.invalidChildComponents.splice(index, 1);
      }
    },
  },
};
