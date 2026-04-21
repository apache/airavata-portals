import * as bootstrap from "bootstrap";

import "bootstrap/dist/css/bootstrap.css";
import "@fortawesome/fontawesome-free/css/all.css";
import "../scss/main.scss";

// Initialize Bootstrap tooltips
document.addEventListener("DOMContentLoaded", () => {
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggerList.forEach((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl));
});
