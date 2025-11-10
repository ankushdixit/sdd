import { z } from "zod";
import { createTRPCRouter, publicProcedure } from "@/server/api/trpc";

export const exampleRouter = createTRPCRouter({
  hello: publicProcedure
    .input(z.object({ text: z.string() }))
    .query(({ input }) => {
      return {
        greeting: `Hello ${input.text}`,
      };
    }),

  create: publicProcedure
    .input(z.object({ name: z.string().min(1) }))
    .mutation(async ({ ctx, input }) => {
      // This is a placeholder - you'll need to implement your database logic
      return {
        id: "1",
        name: input.name,
        createdAt: new Date(),
      };
    }),

  getAll: publicProcedure.query(async ({ ctx }) => {
    // This is a placeholder - you'll need to implement your database logic
    return [];
  }),
});
