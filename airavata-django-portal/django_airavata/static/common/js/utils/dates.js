// Thin wrappers around native Intl APIs. Replaces moment across the portal.
// Ordinal-day format ("Apr 21st") is not supported by Intl and is not
// preserved — callers that used "MMM Do YYYY" now render "MMM d, yyyy".

const EN = "en-US";
const UNITS = [
  { limit: 60, unit: "second", div: 1 },
  { limit: 3600, unit: "minute", div: 60 },
  { limit: 86400, unit: "hour", div: 3600 },
  { limit: 2592000, unit: "day", div: 86400 },
  { limit: 31536000, unit: "month", div: 2592000 },
  { limit: Infinity, unit: "year", div: 31536000 },
];

/** "3 hours ago" / "in 5 minutes". Replaces moment(x).fromNow(). */
export function relativeTime(date, now = new Date()) {
  const deltaSec = (new Date(date).getTime() - now.getTime()) / 1000;
  const abs = Math.abs(deltaSec);
  const u = UNITS.find((u) => abs < u.limit) ?? UNITS[UNITS.length - 1];
  const value = Math.round(deltaSec / u.div);
  return new Intl.RelativeTimeFormat(EN, { numeric: "auto" }).format(value, u.unit);
}

/** "Apr 21, 2026, 2:30 PM". Replaces moment(x).format("lll"). */
export function formatShort(date) {
  return new Intl.DateTimeFormat(EN, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(date));
}

/** "Apr 21, 2026". Replaces moment(x).format("MMM Do YYYY") — loses ordinal. */
export function formatDate(date) {
  return new Intl.DateTimeFormat(EN, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(date));
}

/** "2026-04-21". Replaces moment(x).format("YYYY-MM-DD"). */
export function formatIsoDate(date) {
  return new Date(date).toISOString().slice(0, 10);
}

/** "2026-04-21T14:30:00Z". Replaces moment(x).utc().format(). */
export function formatUtc(date) {
  return new Date(date).toISOString().replace(/\.\d{3}Z$/, "Z");
}
