import { createPinia } from "pinia";

// Pinia replaces Vuex. Stores are defined with defineStore (see
// ./modules/extendedUserProfile.js); the entry point installs this Pinia
// instance on the app.
export default function createStore() {
  return createPinia();
}
