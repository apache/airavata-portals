import { createStore } from "vuex";
import userProfile from "./modules/userProfile";
import extendedUserProfile from "./modules/extendedUserProfile";

const debug = process.env.NODE_ENV !== "production";

function makeStore() {
  return createStore({
    modules: {
      userProfile,
      extendedUserProfile,
    },
    strict: debug,
  });
}

export default makeStore;
