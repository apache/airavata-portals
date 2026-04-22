/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const component: DefineComponent<object, object, any>;
  export default component;
}

// django-airavata-api is JS-only; declare minimal module typing.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare module "django-airavata-api" {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const services: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const models: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const errors: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const utils: any;
  export { services, models, errors, utils };
}

// django-airavata-common-ui entry point is JS; declare minimal module typing.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare module "django-airavata-common-ui" {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const components: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const errors: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const layouts: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mixins: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const notifications: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const utils: any;
  export { components, errors, layouts, mixins, notifications, utils };
}

// bootstrap (Modal class only)
declare module "bootstrap" {
  export class Modal {
    constructor(el: Element, options?: Record<string, unknown>);
    show(): void;
    hide(): void;
    static getInstance(el: Element): Modal | null;
  }
}
