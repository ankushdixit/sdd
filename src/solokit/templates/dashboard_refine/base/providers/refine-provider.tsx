"use client";

import { Refine } from "@refinedev/core";
import {
  refineDataProvider,
  refineRouterProvider,
  refineResources,
  refineOptions,
} from "@/lib/refine";

/**
 * Refine Provider Component
 * Wraps the application with Refine context and configuration
 */
export function RefineProvider({ children }: { children: React.ReactNode }) {
  return (
    <Refine
      dataProvider={refineDataProvider}
      routerProvider={refineRouterProvider}
      resources={refineResources}
      options={refineOptions}
    >
      {children}
    </Refine>
  );
}
