import { userSchema, productSchema, orderSchema } from "../validations";
import { z } from "zod";

describe("userSchema", () => {
  it("validates correct user data", () => {
    const validData = {
      name: "John Doe",
      email: "john@example.com",
    };
    expect(() => userSchema.parse(validData)).not.toThrow();
    const result = userSchema.parse(validData);
    expect(result).toEqual(validData);
  });

  it("rejects user with name too short", () => {
    const invalidData = {
      name: "J",
      email: "john@example.com",
    };
    expect(() => userSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects user with name too long", () => {
    const invalidData = {
      name: "a".repeat(101),
      email: "john@example.com",
    };
    expect(() => userSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects user with invalid email", () => {
    const invalidData = {
      name: "John Doe",
      email: "not-an-email",
    };
    expect(() => userSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects user with missing name", () => {
    const invalidData = {
      email: "john@example.com",
    };
    expect(() => userSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects user with missing email", () => {
    const invalidData = {
      name: "John Doe",
    };
    expect(() => userSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("provides correct error message for short name", () => {
    const invalidData = {
      name: "J",
      email: "john@example.com",
    };
    try {
      userSchema.parse(invalidData);
    } catch (error) {
      if (error instanceof z.ZodError) {
        expect(error.issues[0]?.message).toBe("Name must be at least 2 characters");
      }
    }
  });
});

describe("productSchema", () => {
  it("validates correct product data with all fields", () => {
    const validData = {
      name: "Widget",
      price: 29.99,
      description: "A great widget for all your needs",
      inStock: true,
    };
    expect(() => productSchema.parse(validData)).not.toThrow();
  });

  it("validates correct product data without optional fields", () => {
    const validData = {
      name: "Widget",
      price: 29.99,
    };
    const result = productSchema.parse(validData);
    expect(result.inStock).toBe(true); // default value
  });

  it("rejects product with empty name", () => {
    const invalidData = {
      name: "",
      price: 29.99,
    };
    expect(() => productSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects product with negative price", () => {
    const invalidData = {
      name: "Widget",
      price: -10,
    };
    expect(() => productSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects product with zero price", () => {
    const invalidData = {
      name: "Widget",
      price: 0,
    };
    expect(() => productSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects product with description too short", () => {
    const invalidData = {
      name: "Widget",
      price: 29.99,
      description: "Short",
    };
    expect(() => productSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("accepts product with description exactly 10 characters", () => {
    const validData = {
      name: "Widget",
      price: 29.99,
      description: "1234567890",
    };
    expect(() => productSchema.parse(validData)).not.toThrow();
  });

  it("handles inStock boolean correctly", () => {
    const data1 = { name: "Widget", price: 29.99, inStock: false };
    const result1 = productSchema.parse(data1);
    expect(result1.inStock).toBe(false);

    const data2 = { name: "Widget", price: 29.99, inStock: true };
    const result2 = productSchema.parse(data2);
    expect(result2.inStock).toBe(true);
  });
});

describe("orderSchema", () => {
  it("validates correct order data with all fields", () => {
    const validData = {
      userId: 1,
      productId: 2,
      quantity: 5,
      notes: "Please deliver by Friday",
    };
    expect(() => orderSchema.parse(validData)).not.toThrow();
  });

  it("validates correct order data without optional notes", () => {
    const validData = {
      userId: 1,
      productId: 2,
      quantity: 5,
    };
    expect(() => orderSchema.parse(validData)).not.toThrow();
  });

  it("rejects order with negative userId", () => {
    const invalidData = {
      userId: -1,
      productId: 2,
      quantity: 5,
    };
    expect(() => orderSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects order with zero productId", () => {
    const invalidData = {
      userId: 1,
      productId: 0,
      quantity: 5,
    };
    expect(() => orderSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects order with negative quantity", () => {
    const invalidData = {
      userId: 1,
      productId: 2,
      quantity: -5,
    };
    expect(() => orderSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects order with zero quantity", () => {
    const invalidData = {
      userId: 1,
      productId: 2,
      quantity: 0,
    };
    expect(() => orderSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects order with decimal quantity", () => {
    const invalidData = {
      userId: 1,
      productId: 2,
      quantity: 5.5,
    };
    expect(() => orderSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("rejects order with notes too long", () => {
    const invalidData = {
      userId: 1,
      productId: 2,
      quantity: 5,
      notes: "a".repeat(501),
    };
    expect(() => orderSchema.parse(invalidData)).toThrow(z.ZodError);
  });

  it("accepts order with notes exactly 500 characters", () => {
    const validData = {
      userId: 1,
      productId: 2,
      quantity: 5,
      notes: "a".repeat(500),
    };
    expect(() => orderSchema.parse(validData)).not.toThrow();
  });
});
