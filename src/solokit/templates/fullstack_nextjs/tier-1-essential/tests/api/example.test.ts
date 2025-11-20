/**
 * @jest-environment node
 */
import { NextRequest } from "next/server";
import { GET, POST } from "@/app/api/example/route";

// Mock Prisma client
jest.mock("@/lib/prisma", () => ({
  prisma: {
    user: {
      findMany: jest.fn(),
      create: jest.fn(),
    },
  },
}));

// Import the mocked prisma after mocking
import { prisma } from "@/lib/prisma";

describe("API Route: /api/example", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("GET", () => {
    it("should return a greeting message and users", async () => {
      const mockDate = new Date("2024-01-01T00:00:00.000Z");
      const mockUsers = [
        {
          id: 1,
          name: "John Doe",
          email: "john@example.com",
          createdAt: mockDate,
          updatedAt: mockDate,
        },
      ];

      (prisma.user.findMany as jest.Mock).mockResolvedValue(mockUsers);

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data).toHaveProperty("message");
      expect(data).toHaveProperty("users");
      // Date objects are serialized to ISO strings in JSON
      expect(data.users).toEqual([
        {
          id: 1,
          name: "John Doe",
          email: "john@example.com",
          createdAt: mockDate.toISOString(),
          updatedAt: mockDate.toISOString(),
        },
      ]);
    });

    it("should handle database errors", async () => {
      (prisma.user.findMany as jest.Mock).mockRejectedValue(new Error("Database error"));

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data).toHaveProperty("error");
    });
  });

  describe("POST", () => {
    it("should create a new user with valid data", async () => {
      const mockDate = new Date("2024-01-01T00:00:00.000Z");
      const mockUser = {
        id: 1,
        name: "Jane Doe",
        email: "jane@example.com",
        createdAt: mockDate,
        updatedAt: mockDate,
      };

      (prisma.user.create as jest.Mock).mockResolvedValue(mockUser);

      const request = new NextRequest("http://localhost:3000/api/example", {
        method: "POST",
        body: JSON.stringify({ name: "Jane Doe", email: "jane@example.com" }),
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(201);
      // Date objects are serialized to ISO strings in JSON
      expect(data).toEqual({
        id: 1,
        name: "Jane Doe",
        email: "jane@example.com",
        createdAt: mockDate.toISOString(),
        updatedAt: mockDate.toISOString(),
      });
    });

    it("should return validation error for invalid data", async () => {
      const request = new NextRequest("http://localhost:3000/api/example", {
        method: "POST",
        body: JSON.stringify({ name: "", email: "invalid-email" }),
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data).toHaveProperty("error", "Validation failed");
    });

    it("should handle database errors during creation", async () => {
      const { prisma } = require("@/lib/prisma");
      prisma.user.create.mockRejectedValue(new Error("Database connection failed"));

      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

      const request = new NextRequest("http://localhost:3000/api/example", {
        method: "POST",
        body: JSON.stringify({ name: "John Doe", email: "john@example.com" }),
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data).toHaveProperty("error", "Failed to create user");
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });
  });
});
