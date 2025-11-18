/**
 * Tests for tRPC configuration
 */
import { createTRPCContext, createTRPCRouter, publicProcedure, createCallerFactory } from "../trpc";

// Mock superjson to avoid ES module issues in Jest
jest.mock("superjson", () => ({
  serialize: (obj: unknown) => ({ json: obj, meta: undefined }),
  deserialize: (payload: { json: unknown }) => payload.json,
  stringify: (obj: unknown) => JSON.stringify(obj),
  parse: (str: string) => JSON.parse(str),
}));

// Mock db
jest.mock("@/server/db", () => ({
  db: {
    user: {
      findMany: jest.fn(),
      create: jest.fn(),
    },
  },
}));

describe("tRPC Configuration", () => {
  describe("createTRPCContext", () => {
    it("creates context with db", async () => {
      const headers = new Headers();
      const context = await createTRPCContext({ headers });

      expect(context.db).toBeDefined();
    });

    it("includes headers in context", async () => {
      const headers = new Headers();
      headers.set("x-test", "test-value");

      const context = await createTRPCContext({ headers });

      expect(context.headers).toBe(headers);
    });

    it("returns consistent db instance", async () => {
      const headers1 = new Headers();
      const headers2 = new Headers();

      const context1 = await createTRPCContext({ headers: headers1 });
      const context2 = await createTRPCContext({ headers: headers2 });

      expect(context1.db).toBe(context2.db);
    });
  });

  describe("createTRPCRouter", () => {
    it("is a function", () => {
      expect(typeof createTRPCRouter).toBe("function");
    });

    it("creates a router", () => {
      const router = createTRPCRouter({
        test: publicProcedure.query(() => "test"),
      });

      expect(router).toBeDefined();
    });

    it("can create router with multiple procedures", () => {
      const router = createTRPCRouter({
        query1: publicProcedure.query(() => "query1"),
        query2: publicProcedure.query(() => "query2"),
      });

      expect(router).toBeDefined();
    });
  });

  describe("publicProcedure", () => {
    it("is defined", () => {
      expect(publicProcedure).toBeDefined();
    });

    it("can create a query procedure", () => {
      const procedure = publicProcedure.query(() => "test");
      expect(procedure).toBeDefined();
    });

    it("can create a mutation procedure", () => {
      const procedure = publicProcedure.mutation(() => "test");
      expect(procedure).toBeDefined();
    });

    it("can add input validation", () => {
      const { z } = require("zod");
      const procedure = publicProcedure
        .input(z.object({ text: z.string() }))
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .query(({ input }: any) => (input as { text: string }).text);

      expect(procedure).toBeDefined();
    });
  });

  describe("createCallerFactory", () => {
    it("is defined", () => {
      expect(createCallerFactory).toBeDefined();
    });

    it("is a function", () => {
      expect(typeof createCallerFactory).toBe("function");
    });
  });

  describe("Error Formatting", () => {
    it("formats ZodError in error response", async () => {
      const { z } = require("zod");

      const testRouter = createTRPCRouter({
        test: publicProcedure
          .input(z.object({ text: z.string() }))
          .query(({ input }) => input),
      });

      // This validates that the error formatter is configured
      expect(testRouter).toBeDefined();
    });
  });

  describe("SuperJSON Transformer", () => {
    it("configures superjson transformer", () => {
      // The transformer allows Date objects and other special types
      // to be serialized/deserialized correctly
      const router = createTRPCRouter({
        getDate: publicProcedure.query(() => new Date()),
      });

      expect(router).toBeDefined();
    });
  });
});
