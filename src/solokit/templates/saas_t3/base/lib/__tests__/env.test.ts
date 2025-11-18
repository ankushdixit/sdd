/**
 * Environment validation tests for saas_t3 stack
 */

/// <reference types="node" />

describe("Environment Validation", () => {
  // Helper to set NODE_ENV in tests (bypasses readonly restriction)
  const setNodeEnv = (value: string) => {
    (process.env as { NODE_ENV?: string }).NODE_ENV = value;
  };
  let originalEnv: NodeJS.ProcessEnv;

  beforeAll(() => {
    originalEnv = { ...process.env };
  });

  afterEach(() => {
    process.env = { ...originalEnv };
    jest.resetModules();
  });

  it("validates when DATABASE_URL is present", () => {
    process.env.DATABASE_URL = "postgresql://localhost:5432/test";
    setNodeEnv("development");

    expect(() => {
      require("../env");
    }).not.toThrow();
  });

  it("exports env object with DATABASE_URL", () => {
    process.env.DATABASE_URL = "postgresql://localhost:5432/test";
    setNodeEnv("development");
    jest.resetModules();

    const { env } = require("../env");
    expect(env.DATABASE_URL).toBe("postgresql://localhost:5432/test");
  });

  it("exports env object with NODE_ENV", () => {
    process.env.DATABASE_URL = "postgresql://localhost:5432/test";
    setNodeEnv("production");
    jest.resetModules();

    const { env } = require("../env");
    expect(env.NODE_ENV).toBe("production");
  });

  it("defaults NODE_ENV to development when not set", () => {
    process.env.DATABASE_URL = "postgresql://localhost:5432/test";
    (process.env as { NODE_ENV?: string }).NODE_ENV = undefined;
    jest.resetModules();

    const { env } = require("../env");
    expect(env.NODE_ENV).toBe("development");
  });

  it("accepts development NODE_ENV", () => {
    process.env.DATABASE_URL = "postgresql://localhost:5432/test";
    setNodeEnv("development");
    jest.resetModules();

    expect(() => {
      require("../env");
    }).not.toThrow();
  });

  it("accepts production NODE_ENV", () => {
    process.env.DATABASE_URL = "postgresql://localhost:5432/test";
    setNodeEnv("production");
    jest.resetModules();

    expect(() => {
      require("../env");
    }).not.toThrow();
  });

  it("accepts test NODE_ENV", () => {
    process.env.DATABASE_URL = "postgresql://localhost:5432/test";
    setNodeEnv("test");
    jest.resetModules();

    expect(() => {
      require("../env");
    }).not.toThrow();
  });

  it("validates various DATABASE_URL formats", () => {
    const validUrls = [
      "postgresql://localhost:5432/test",
      "postgresql://user:password@localhost:5432/db",
      "mysql://localhost:3306/test",
      "mongodb://localhost:27017/test",
      "https://example.com/db",
    ];

    validUrls.forEach((url) => {
      process.env.DATABASE_URL = url;
      setNodeEnv("development");
      jest.resetModules();

      expect(() => {
        require("../env");
      }).not.toThrow();
    });
  });

  it("throws error when DATABASE_URL is missing", () => {
    delete process.env.DATABASE_URL;
    setNodeEnv("development");

    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    jest.resetModules();

    expect(() => {
      require("../env");
    }).toThrow("Invalid environment variables");

    consoleErrorSpy.mockRestore();
  });

  it("throws error when DATABASE_URL is empty string", () => {
    process.env.DATABASE_URL = "";
    setNodeEnv("development");

    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    jest.resetModules();

    expect(() => {
      require("../env");
    }).toThrow("Invalid environment variables");

    consoleErrorSpy.mockRestore();
  });

  it("throws error when DATABASE_URL is not a valid URL", () => {
    process.env.DATABASE_URL = "not-a-url";
    setNodeEnv("development");

    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    jest.resetModules();

    expect(() => {
      require("../env");
    }).toThrow("Invalid environment variables");

    consoleErrorSpy.mockRestore();
  });

  it("logs error details when validation fails", () => {
    delete process.env.DATABASE_URL;
    setNodeEnv("development");

    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    jest.resetModules();

    try {
      require("../env");
    } catch {
      // Expected to throw
    }

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      expect.stringContaining("Invalid environment variables")
    );

    consoleErrorSpy.mockRestore();
  });
});
