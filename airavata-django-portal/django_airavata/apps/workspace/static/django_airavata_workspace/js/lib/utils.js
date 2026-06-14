// The shared shadcn-vue component library lives in the common package and its
// source `.vue` files import the `cn` helper via the package-local `@/lib/utils`
// alias. Because Vite resolves the `@` alias against the *consuming* app, those
// imports land here when common is linked as source. Re-export the canonical
// helper from common so there is a single implementation.
export * from "django-airavata-common-ui/js/lib/utils";
