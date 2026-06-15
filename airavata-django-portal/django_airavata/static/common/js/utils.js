export function getProperty(obj, props) {
  if (typeof props === "string") {
    return obj[props];
  } else if (typeof props === "object" && props instanceof Array) {
    // Array
    return props.reduce(
      (o, prop) => (o && prop in o ? o[prop] : undefined),
      obj
    );
  }
}
export function sanitizeHTMLId(id) {
  // Replace anything that isn't an HTML safe id character with underscore
  // Here safe means allowable by HTML5 and also safe to use in a jQuery selector
  return id.replace(/[^a-zA-Z0-9_-]/g, "_");
}
export const dateFormatters = {
  dateTimeInMinutesWithTimeZone: new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "numeric",
    minute: "numeric",
    timeZoneName: "short",
  }),
};

// Tracks app-initiated (intentional) navigations so UnsavedChangesGuard does not
// pop the native "Leave site?" dialog when the portal itself sends the user to
// another page (e.g. after Save / Save and Launch). The guard should still warn
// on genuinely accidental leaves (closing the tab, browser back/forward, editing
// the URL bar, following an unrelated link) while there are unsaved edits.
let intentionalNavigation = false;

export function isIntentionalNavigation() {
  return intentionalNavigation;
}

// Send the browser to `url` as an intentional, app-initiated navigation. Use this
// instead of window.location.assign for in-portal navigations (e.g. redirecting
// after a successful save) so the unsaved-changes guard stays silent.
export function navigateTo(url) {
  intentionalNavigation = true;
  window.location.assign(url);
}
