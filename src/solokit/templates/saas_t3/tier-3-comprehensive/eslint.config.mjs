import js from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import globals from "globals";
import jestDomPlugin from "eslint-plugin-jest-dom";
import testingLibraryPlugin from "eslint-plugin-testing-library";

export default [
  js.configs.recommended,
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        React: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tseslint,
      "jest-dom": jestDomPlugin,
      "testing-library": testingLibraryPlugin,
    },
    rules: {
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn",
      // jest-dom rules
      "jest-dom/prefer-checked": "error",
      "jest-dom/prefer-enabled-disabled": "error",
      "jest-dom/prefer-required": "error",
      "jest-dom/prefer-to-have-attribute": "error",
      // testing-library rules
      "testing-library/await-async-queries": "error",
      "testing-library/no-await-sync-queries": "error",
      "testing-library/no-debugging-utils": "warn",
      "testing-library/prefer-screen-queries": "error",
    },
  },
  {
    files: ["**/*.test.{js,jsx,ts,tsx}", "tests/**/*.{js,jsx,ts,tsx}"],
    languageOptions: {
      globals: {
        ...globals.jest,
      },
    },
  },
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      "out/**",
      "dist/**",
      "build/**",
      ".session/**",
      "coverage/**",
    ],
  },
];
