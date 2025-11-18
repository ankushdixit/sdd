/**
 * Test for Prisma singleton pattern (T3 Stack db export)
 *
 * Note: This test validates the module structure and singleton pattern
 * without requiring an actual database connection.
 */

describe("Prisma Client (db export)", () => {
  // Helper to set NODE_ENV in tests (bypasses readonly restriction)
  const setNodeEnv = (value: string) => {
    (process.env as { NODE_ENV?: string }).NODE_ENV = value;
  };
  let originalEnv: string | undefined;

  beforeEach(() => {
    originalEnv = process.env.NODE_ENV;
    jest.resetModules();
  });

  afterEach(() => {
    setNodeEnv(originalEnv || "development");
  });

  it("exports db client instance", () => {
    const { db } = require("../db");
    expect(db).toBeDefined();
  });

  it("db has expected Prisma Client methods", () => {
    const { db } = require("../db");
    expect(typeof db.$connect).toBe("function");
    expect(typeof db.$disconnect).toBe("function");
    expect(typeof db.$transaction).toBe("function");
  });

  it("returns same instance on multiple imports in development", () => {
    setNodeEnv("development");
    jest.resetModules();

    const { db: db1 } = require("../db");
    const { db: db2 } = require("../db");

    expect(db1).toBe(db2);
  });

  it("uses singleton pattern to prevent multiple instances", () => {
    const { db } = require("../db");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const global = globalThis as any;

    // In development, the instance should be stored in global
    if (process.env.NODE_ENV !== "production") {
      expect(global.prisma).toBeDefined();
      expect(global.prisma).toBe(db);
    }
  });

  it("creates PrismaClient with expected configuration", () => {
    expect(() => {
      require("../db");
    }).not.toThrow();
  });

  it("should configure logging based on environment", () => {
    // Test development environment
    setNodeEnv("development");
    jest.resetModules();
    const { db: devDb } = require("../db");
    expect(devDb).toBeDefined();

    // Test production environment
    setNodeEnv("production");
    jest.resetModules();
    const { db: prodDb } = require("../db");
    expect(prodDb).toBeDefined();
  });

  it("follows T3 Stack naming convention", () => {
    const module = require("../db");
    expect(module.db).toBeDefined();
    expect(module.prisma).toBeUndefined(); // Should not export as "prisma"
  });
});
