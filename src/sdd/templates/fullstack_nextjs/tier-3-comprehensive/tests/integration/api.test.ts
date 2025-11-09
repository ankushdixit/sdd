import { describe, it, expect, jest, beforeEach } from "@jest/globals";
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

describe("API Integration Tests", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("GET /api/example", () => {
    it("should successfully fetch users from database", async () => {
      const mockUsers = [
        {
          id: 1,
          name: "John Doe",
          email: "john@example.com",
          createdAt: new Date("2024-01-01"),
          updatedAt: new Date("2024-01-01"),
        },
        {
          id: 2,
          name: "Jane Smith",
          email: "jane@example.com",
          createdAt: new Date("2024-01-02"),
          updatedAt: new Date("2024-01-02"),
        },
      ];

      (prisma.user.findMany as jest.Mock).mockResolvedValue(mockUsers);

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data).toHaveProperty("message");
      expect(data.users).toEqual(mockUsers);
      expect(prisma.user.findMany).toHaveBeenCalledWith({
        take: 10,
        orderBy: { createdAt: "desc" },
      });
    });

    it("should handle empty user list", async () => {
      (prisma.user.findMany as jest.Mock).mockResolvedValue([]);

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.users).toEqual([]);
    });

    it("should handle database connection errors", async () => {
      (prisma.user.findMany as jest.Mock).mockRejectedValue(
        new Error("Database connection failed")
      );

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data).toHaveProperty("error", "Failed to fetch users");
    });
  });

  describe("POST /api/example", () => {
    it("should create user with valid input", async () => {
      const mockUser = {
        id: 1,
        name: "New User",
        email: "newuser@example.com",
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      (prisma.user.create as jest.Mock).mockResolvedValue(mockUser);

      const request = new NextRequest("http://localhost:3000/api/example", {
        method: "POST",
        body: JSON.stringify({
          name: "New User",
          email: "newuser@example.com",
        }),
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(201);
      expect(data).toEqual(mockUser);
      expect(prisma.user.create).toHaveBeenCalledWith({
        data: {
          name: "New User",
          email: "newuser@example.com",
        },
      });
    });

    it("should reject invalid email format", async () => {
      const request = new NextRequest("http://localhost:3000/api/example", {
        method: "POST",
        body: JSON.stringify({
          name: "Test User",
          email: "invalid-email",
        }),
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data).toHaveProperty("error", "Validation failed");
      expect(data).toHaveProperty("details");
    });

    it("should reject empty name", async () => {
      const request = new NextRequest("http://localhost:3000/api/example", {
        method: "POST",
        body: JSON.stringify({
          name: "",
          email: "test@example.com",
        }),
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data).toHaveProperty("error", "Validation failed");
    });

    it("should handle database creation errors", async () => {
      (prisma.user.create as jest.Mock).mockRejectedValue(
        new Error("Duplicate email")
      );

      const request = new NextRequest("http://localhost:3000/api/example", {
        method: "POST",
        body: JSON.stringify({
          name: "Test User",
          email: "test@example.com",
        }),
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data).toHaveProperty("error", "Failed to create user");
    });
  });
});
