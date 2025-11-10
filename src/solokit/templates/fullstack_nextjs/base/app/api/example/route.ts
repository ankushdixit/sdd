import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { createUserSchema } from "@/lib/validations";
import { z } from "zod";

/**
 * GET /api/example
 * Returns a simple greeting message
 */
export async function GET() {
  try {
    // Example: Fetch users from database
    const users = await prisma.user.findMany({
      take: 10,
      orderBy: { createdAt: "desc" },
    });

    return NextResponse.json({
      message: "Hello from Next.js API!",
      users,
    });
  } catch (error) {
    console.error("Error fetching users:", error);
    return NextResponse.json(
      { error: "Failed to fetch users" },
      { status: 500 }
    );
  }
}

/**
 * POST /api/example
 * Creates a new user
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate request body
    const validatedData = createUserSchema.parse(body);

    // Create user in database
    const user = await prisma.user.create({
      data: {
        name: validatedData.name,
        email: validatedData.email,
      },
    });

    return NextResponse.json(user, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "Validation failed", details: error.issues },
        { status: 400 }
      );
    }

    console.error("Error creating user:", error);
    return NextResponse.json(
      { error: "Failed to create user" },
      { status: 500 }
    );
  }
}
