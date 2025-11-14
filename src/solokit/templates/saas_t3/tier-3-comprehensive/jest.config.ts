import type { Config } from "jest";
import nextJest from "next/jest.js";

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: "./",
});

// Add any custom config to be passed to Jest
const config: Config = {
  coverageProvider: "v8",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],

  // Only run unit and integration tests with Jest
  testMatch: [
    "**/tests/unit/**/*.test.{ts,tsx}",
    "**/tests/integration/**/*.test.{ts,tsx}",
  ],

  // Exclude e2e tests (run separately with Playwright)
  testPathIgnorePatterns: ["/node_modules/", "/.next/", "/tests/e2e/"],

  // Allow testing of app, components, lib directories
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
  },

  // ESM transformation for dependencies that need it
  transformIgnorePatterns: ["node_modules/(?!(superjson|@trpc)/)"],
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
export default createJestConfig(config);
