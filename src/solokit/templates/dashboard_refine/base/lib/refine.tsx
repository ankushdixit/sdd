import routerProvider from "@refinedev/nextjs-router";
import type { DataProvider, BaseKey } from "@refinedev/core";

/**
 * Refine configuration
 * This file centralizes all Refine-related configuration
 */

/**
 * Mock data provider for development/testing
 *
 * ⚠️ IMPORTANT: This is a mock data provider for demonstration purposes only.
 * Replace with a real data provider when you have a backend API.
 *
 * Migration Path:
 *
 * 1. Choose a data provider based on your backend:
 *    - REST API: @refinedev/simple-rest
 *    - GraphQL: @refinedev/graphql
 *    - Strapi: @refinedev/strapi-v4
 *    - Supabase: @refinedev/supabase
 *    - Custom: Implement your own DataProvider interface
 *
 * 2. Install the data provider package:
 *    npm install @refinedev/simple-rest
 *
 * 3. Replace the mock provider:
 *    import dataProvider from "@refinedev/simple-rest";
 *    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000/api";
 *    export const refineDataProvider = dataProvider(API_URL);
 *
 * 4. Update your resources to match your API endpoints
 *
 * 5. Remove the mockDataProvider code below
 *
 * Documentation: https://refine.dev/docs/data/data-provider/
 */
/* eslint-disable @typescript-eslint/no-explicit-any */
const mockDataProvider: DataProvider = {
  getList: async ({ resource }) => {
    // Mock user data
    if (resource === "users") {
      return {
        data: [
          { id: 1, name: "John Doe", email: "john@example.com" },
          { id: 2, name: "Jane Smith", email: "jane@example.com" },
          { id: 3, name: "Bob Johnson", email: "bob@example.com" },
        ] as any,
        total: 3,
      };
    }
    return { data: [] as any, total: 0 };
  },
  getOne: async ({ resource, id }) => {
    if (resource === "users") {
      return {
        data: { id, name: "John Doe", email: "john@example.com" } as any,
      };
    }
    return { data: {} as any };
  },
  create: async ({ variables }: { variables: any }) => {
    return { data: { id: 1, ...variables } as any };
  },
  update: async ({ id, variables }: { id: BaseKey; variables: any }) => {
    return { data: { id, ...variables } as any };
  },
  deleteOne: async ({ id }: { id: BaseKey }) => {
    return { data: { id } as any };
  },
  getApiUrl: () => "",
};
/* eslint-enable @typescript-eslint/no-explicit-any */

export const refineDataProvider = mockDataProvider;

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
    list: "/users",
    create: "/users/create",
    edit: "/users/edit/:id",
    show: "/users/show/:id",
    meta: {
      canDelete: true,
    },
  },
  {
    name: "orders",
    list: "/orders",
    create: "/orders/create",
    edit: "/orders/edit/:id",
    show: "/orders/show/:id",
  },
  {
    name: "products",
    list: "/products",
    create: "/products/create",
    edit: "/products/edit/:id",
    show: "/products/show/:id",
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
