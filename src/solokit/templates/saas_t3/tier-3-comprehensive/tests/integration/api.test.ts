import { describe, it, expect, beforeAll, afterAll } from "@jest/globals";
import { appRouter } from "@/server/api/root";
import { createTRPCContext } from "@/server/api/trpc";
import { createCallerFactory } from "@/server/api/trpc";

describe("tRPC API Integration Tests", () => {
  let caller: ReturnType<typeof createCallerFactory<typeof appRouter>>;

  beforeAll(async () => {
    // Create a mock context
    const ctx = await createTRPCContext({
      headers: new Headers(),
    });

    // Create a caller with the mock context
    const createCaller = createCallerFactory(appRouter);
    caller = createCaller(ctx);
  });

  describe("example router", () => {
    it("should return a greeting from hello query", async () => {
      const result = await caller.example.hello({ text: "world" });

      expect(result).toBeDefined();
      expect(result.greeting).toBe("Hello world");
    });

    it("should create an item", async () => {
      const result = await caller.example.create({ name: "Test Item" });

      expect(result).toBeDefined();
      expect(result.name).toBe("Test Item");
      expect(result.id).toBeDefined();
      expect(result.createdAt).toBeInstanceOf(Date);
    });

    it("should get all items", async () => {
      const result = await caller.example.getAll();

      expect(result).toBeDefined();
      expect(Array.isArray(result)).toBe(true);
    });
  });
});
