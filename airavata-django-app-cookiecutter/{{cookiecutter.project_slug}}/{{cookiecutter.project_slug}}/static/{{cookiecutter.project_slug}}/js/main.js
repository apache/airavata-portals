// Minimal Vite entry for {{ cookiecutter.project_name }}. The portal loads this
// bundle via {% raw %}{% vite_js 'main' vite_app %}{% endraw %} in home.html.
const el = document.getElementById("app");
if (el) {
  el.textContent = "Hello from {{ cookiecutter.project_name }}";
}

// Example: talk to the Airavata REST API from the browser. The portal ships the
// JS SDK as the "django-airavata-api" package; add it to devDependencies and
// import what you need:
//
//   import { services, session } from "django-airavata-api";
//
//   services.ExperimentSearchService
//     .list({ limit: 5, USERNAME: session.Session.username })
//     .then((data) => console.log(data.results));
