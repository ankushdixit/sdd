import { z } from "zod";
import { createTRPCRouter, publicProcedure } from "@/server/api/trpc";
import { db } from "@/server/db";

export const exampleRouter = createTRPCRouter({
  hello: publicProcedure.input(z.object({ text: z.string() })).query(({ input }) => {
    return {
      greeting: `Hello ${input.text}`,
    };
  }),

  create: publicProcedure
    .input(z.object({ name: z.string().min(1), email: z.string().email() }))
    .mutation(async ({ input }) => {
      // Example: Create a new user in the database
      const user = await db.user.create({
        data: {
          name: input.name,
          email: input.email,
        },
      });
      return user;
    }),

  getAll: publicProcedure.query(async () => {
    // Example: Fetch all users from the database
    const users = await db.user.findMany({
      orderBy: { createdAt: "desc" },
    });
    return users;
  }),
});
