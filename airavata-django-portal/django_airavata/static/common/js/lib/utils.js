import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge class names with Tailwind-aware conflict resolution (the shadcn `cn`
 * helper). Accepts the same inputs as clsx; later Tailwind classes win.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
