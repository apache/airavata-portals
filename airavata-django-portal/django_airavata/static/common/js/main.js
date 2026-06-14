import { Tooltip } from "bootstrap";

import "bootstrap/dist/css/bootstrap.css";
import "@fortawesome/fontawesome-free/css/all.css";
import "../scss/main.scss";

// Bootstrap 5 dropped the jQuery dependency. Initialize tooltips on
// server-rendered markup with the native API; Bootstrap 5 also renamed the data
// attribute from `data-toggle` to `data-bs-toggle`.
function initTooltips() {
  document
    .querySelectorAll('[data-bs-toggle="tooltip"]')
    .forEach((el) => Tooltip.getOrCreateInstance(el));
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTooltips);
} else {
  initTooltips();
}
