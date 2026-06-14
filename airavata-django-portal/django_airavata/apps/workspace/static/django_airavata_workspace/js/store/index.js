// The Vuex `viewExperiment` namespaced module is now a Pinia store. Re-export it
// so existing imports (`import { useViewExperimentStore } from "../store"`)
// continue to resolve. The Pinia instance itself is created in the entry point.
export { useViewExperimentStore, default } from "./modules/view-experiment";
