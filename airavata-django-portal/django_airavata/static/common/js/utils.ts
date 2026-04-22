export function getProperty(
  obj: Record<string, unknown>,
  props: string | string[]
): unknown {
  if (typeof props === "string") {
    return obj[props];
  } else if (Array.isArray(props)) {
    return props.reduce<unknown>(
      (o, prop) =>
        o && typeof o === "object" && prop in (o as Record<string, unknown>)
          ? (o as Record<string, unknown>)[prop]
          : undefined,
      obj
    );
  }
}

export function sanitizeHTMLId(id: string): string {
  // Replace anything that isn't an HTML safe id character with underscore
  // Here safe means allowable by HTML5 and also safe to use in a jQuery selector
  return id.replace(/[^a-zA-Z0-9_-]/g, "_");
}

export const dateFormatters: {
  dateTimeInMinutesWithTimeZone: Intl.DateTimeFormat;
} = {
  dateTimeInMinutesWithTimeZone: new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "numeric",
    minute: "numeric",
    timeZoneName: "short",
  }),
};
