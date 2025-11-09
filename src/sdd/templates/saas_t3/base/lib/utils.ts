import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility function to merge Tailwind CSS classes
 *
 * @example
 * cn("px-2 py-1", "bg-blue-500") // "px-2 py-1 bg-blue-500"
 * cn("px-2", condition && "py-1") // "px-2 py-1" or "px-2"
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
