/**
 * Prisma Client Instance
 *
 * This file implements the singleton pattern for Prisma Client to prevent
 * multiple instances during development (due to hot-reloading).
 *
 * Export name: "db"
 * This template follows the T3 Stack convention of exporting as "db" for brevity
 * and consistency with the T3 ecosystem. This is the standard pattern used in
 * create-t3-app and throughout the T3 community.
 *
 * Usage:
 * import { db } from "@/server/db";
 * const users = await db.user.findMany();
 */

import { PrismaClient } from "@prisma/client";

const createPrismaClient = () =>
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["query", "error", "warn"] : ["error"],
  });

const globalForPrisma = globalThis as unknown as {
  prisma: ReturnType<typeof createPrismaClient> | undefined;
};

export const db = globalForPrisma.prisma ?? createPrismaClient();

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = db;
