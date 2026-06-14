import AppShell from "./components/AppShell.vue";
import entry from "./entry";

// The Django base template renders the page-shell data (brand, nav items, app
// switcher entries, user menu) into a JSON <script> tag. Read it before Vue
// mounts so the shell can render the sidebar without any business logic.
function readShellData() {
  const el = document.getElementById("app-shell-data");
  if (!el) {
    return {};
  }
  try {
    return JSON.parse(el.textContent) || {};
  } catch {
    return {};
  }
}

const mountPoint = document.getElementById("app-shell");
if (mountPoint) {
  entry(AppShell, readShellData()).mount(mountPoint);
}
