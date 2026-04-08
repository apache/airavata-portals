import { createStore } from "vuex";
import viewExperiment from "./modules/view-experiment";

const debug = process.env.NODE_ENV !== "production";

function makeStore() {
  return createStore({
    modules: {
      viewExperiment,
    },
    strict: debug,
  });
}

export default makeStore;
