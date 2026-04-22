/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const component: DefineComponent<object, object, any>;
  export default component;
}

// bootstrap is a JavaScript package without full TypeScript declarations in this version.
declare module "bootstrap" {
  export class Modal {
    constructor(el: Element, options?: Record<string, unknown>);
    show(): void;
    hide(): void;
    static getInstance(el: Element): Modal | null;
  }
}

// django-airavata-api is a JavaScript package without TypeScript declarations.
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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const session: any;
  export { services, models, errors, utils, session };
}
