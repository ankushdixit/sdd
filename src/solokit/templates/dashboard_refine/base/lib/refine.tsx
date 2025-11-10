import routerProvider from "@refinedev/nextjs-router";

/**
 * Refine configuration
 * This file centralizes all Refine-related configuration
 */

/**
 * Data provider configuration
 * TODO: Add a data provider when you have a backend API
 * Example: import dataProvider from "@refinedev/simple-rest";
 * Then: export const refineDataProvider = dataProvider(API_URL);
 */
export const refineDataProvider = undefined;

/**
 * Router provider configuration
 * Integrates Refine with Next.js App Router
 */
export const refineRouterProvider = routerProvider;

/**
 * Resource definitions
 * Define all resources that will be managed in the dashboard
 */
export const refineResources = [
  {
    name: "users",
    list: "/dashboard/users",
    create: "/dashboard/users/create",
    edit: "/dashboard/users/edit/:id",
    show: "/dashboard/users/show/:id",
    meta: {
      canDelete: true,
    },
  },
  {
    name: "orders",
    list: "/dashboard/orders",
    create: "/dashboard/orders/create",
    edit: "/dashboard/orders/edit/:id",
    show: "/dashboard/orders/show/:id",
  },
  {
    name: "products",
    list: "/dashboard/products",
    create: "/dashboard/products/create",
    edit: "/dashboard/products/edit/:id",
    show: "/dashboard/products/show/:id",
    meta: {
      canDelete: true,
    },
  },
];

/**
 * Refine options
 * Global configuration for Refine behavior
 */
export const refineOptions = {
  syncWithLocation: true,
  warnWhenUnsavedChanges: true,
  useNewQueryKeys: true,
  projectId: "refine-dashboard",
};
