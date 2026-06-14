// The shared shadcn-vue component library lives in the common package and its
// source `.vue` files import the `cn` helper via the package-local `@/lib/utils`
// alias. Because Vite resolves the `@` alias against the *consuming* app, those
// imports land here when common is linked as source. Re-export the canonical
// helper from common so there is a single implementation.
export * from "django-airavata-common-ui/js/lib/utils";

// Canonical styling for a NATIVE control (a <select> that must stay native, or a
// native <input> inside a standalone web component where the shadcn <Input> /
// <Select> components are not registered) so it matches a shadcn <Input> (h-9).
// Keep every such control on this exact class — no ad-hoc styling.
export const NATIVE_SELECT_CLASS =
  "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50";

// Alias for native <input> elements that cannot use the shadcn <Input> component
// (e.g. inside web-component builds). Same canonical, Input-matching class.
export const NATIVE_INPUT_CLASS = NATIVE_SELECT_CLASS;
