// Re-export the common shadcn-vue Button so common's source components (which
// import it via the package-local `@/components/ui/button` alias) resolve when
// common is linked as source and the `@` alias points at this app's js dir.
export * from "django-airavata-common-ui/js/components/ui/button";
