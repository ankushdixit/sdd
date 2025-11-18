import { createUserSchema, updateUserSchema } from "../validations";
import { z } from "zod";

describe("createUserSchema", () => {
  it("validates correct user data", () => {
    const validData = {
      name: "John Doe",
      email: "john@example.com",
    };
    expect(() => createUserSchema.parse(validData)).not.toThrow();
    const result = createUserSchema.parse(validData);
    expect(result).toEqual(validData);
  });

  it("rejects user with empty name", () => {
    const invalidData = {
      name: "",
      email: "john@example.com",
    };
    expect(() => createUserSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects user with name too long", () => {
    const invalidData = {
      name: "a".repeat(101),
      email: "john@example.com",
    };
    expect(() => createUserSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects user with invalid email", () => {
    const invalidData = {
      name: "John Doe",
      email: "not-an-email",
    };
    expect(() => createUserSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects user with missing name", () => {
    const invalidData = {
      email: "john@example.com",
    };
    expect(() => createUserSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects user with missing email", () => {
    const invalidData = {
      name: "John Doe",
    };
    expect(() => createUserSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("accepts name with exactly 100 characters", () => {
    const validData = {
      name: "a".repeat(100),
      email: "john@example.com",
    };
    expect(() => createUserSchema.parse(validData)).not.toThrow();
  });

  it("accepts name with 1 character", () => {
    const validData = {
      name: "J",
      email: "john@example.com",
    };
    expect(() => createUserSchema.parse(validData)).not.toThrow();
  });

  it("validates various email formats", () => {
    const emails = [
      "test@example.com",
      "test.name@example.co.uk",
      "test+tag@example.com",
      "test_123@sub.example.com",
    ];

    emails.forEach((email) => {
      const data = { name: "Test", email };
      expect(() => createUserSchema.parse(data)).not.toThrow();
    });
  });

  it("rejects invalid email formats", () => {
    const emails = ["test", "test@", "@example.com", "test @example.com", "test@.com"];

    emails.forEach((email) => {
      const data = { name: "Test", email };
      expect(() => createUserSchema.parse(data)).toThrow(z.ZodError);
    });
  });
});

describe("updateUserSchema", () => {
  it("validates user data with both fields", () => {
    const validData = {
      name: "John Doe",
      email: "john@example.com",
    };
    expect(() => updateUserSchema.parse(validData)).not.toThrow();
  });

  it("validates user data with only name", () => {
    const validData = {
      name: "John Doe",
    };
    expect(() => updateUserSchema.parse(validData)).not.toThrow();
  });

  it("validates user data with only email", () => {
    const validData = {
      email: "john@example.com",
    };
    expect(() => updateUserSchema.parse(validData)).not.toThrow();
  });

  it("validates empty object (all fields optional)", () => {
    const validData = {};
    expect(() => updateUserSchema.parse(validData)).not.toThrow();
  });

  it("rejects empty name when provided", () => {
    const invalidData = {
      name: "",
    };
    expect(() => updateUserSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects name too long when provided", () => {
    const invalidData = {
      name: "a".repeat(101),
    };
    expect(() => updateUserSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects invalid email when provided", () => {
    const invalidData = {
      email: "not-an-email",
    };
    expect(() => updateUserSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("accepts name with exactly 100 characters", () => {
    const validData = {
      name: "a".repeat(100),
    };
    expect(() => updateUserSchema.parse(validData)).not.toThrow();
  });

  it("accepts name with 1 character", () => {
    const validData = {
      name: "J",
    };
    expect(() => updateUserSchema.parse(validData)).not.toThrow();
  });

  it("allows undefined fields", () => {
    const validData = {
      name: undefined,
      email: undefined,
    };
    expect(() => updateUserSchema.parse(validData)).not.toThrow();
  });
});
