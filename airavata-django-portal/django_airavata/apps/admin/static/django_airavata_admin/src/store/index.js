import { createStore } from "vuex";
import extendedUserProfile from "./modules/extendedUserProfile";

const debug = process.env.NODE_ENV !== "production";

function makeStore() {
  return createStore({
    modules: {
      extendedUserProfile,
    },
    strict: debug,
  });
}

export default makeStore;
