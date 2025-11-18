# T3 Stack Template

A typesafe full-stack SaaS template built with the T3 Stack: Next.js, tRPC, Prisma, and PostgreSQL.

## What's Included

This template provides the complete T3 Stack experience:

- **Next.js 16** with App Router
- **tRPC**: End-to-end typesafe APIs
- **Prisma ORM**: Type-safe database access
- **PostgreSQL**: Production-ready database
- **Zod**: Runtime validation and type inference
- **Tailwind CSS**: Utility-first styling
- **TypeScript**: Full stack type safety
- **TanStack Query**: Powerful data fetching
- **SuperJSON**: Enhanced data serialization

## Quick Start

### 1. Set Up Database

Create a PostgreSQL database and add the connection string to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL="postgresql://user:password@localhost:5432/mydb"
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Initialize Database

```bash
npx prisma migrate dev --name init
npx prisma generate
```

### 4. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see your app.

## Architecture Decisions

### tRPC for API Layer

This template uses **tRPC** instead of traditional REST/GraphQL APIs:

**Benefits:**
- Full stack type safety (no code generation needed)
- Automatic TypeScript inference
- Better DX with autocomplete everywhere
- No need to keep API docs in sync

**Trade-offs:**
- TypeScript only (no other language clients)
- Requires shared code (monorepo or fullstack repo)

### Prisma Client Export Name

Following T3 Stack conventions, the Prisma client is exported as `db`:

```typescript
import { db } from "@/server/db";
const users = await db.user.findMany();
```

This is the standard pattern in create-t3-app and the T3 community.

### Server Directory

All server-side code lives in `server/`:
- `server/api/` - tRPC routers and procedures
- `server/db.ts` - Prisma client

This separation makes it clear what runs server-side only.

### Environment Validation

`lib/env.ts` validates environment variables using Zod:
- Type-safe env vars
- Fail fast on misconfiguration
- Clear error messages

## Project Structure

```
├── app/
│   ├── api/trpc/[trpc]/ # tRPC HTTP handler
│   ├── globals.css      # Global styles
│   ├── layout.tsx       # Root layout with tRPC provider
│   ├── page.tsx         # Home page using tRPC
│   ├── error.tsx        # Error boundary
│   └── loading.tsx      # Loading UI
├── components/          # React components
│   └── example-component.tsx  # Example using tRPC
├── lib/
│   ├── api.tsx          # tRPC React provider
│   ├── utils.ts         # Utility functions
│   └── env.ts           # Environment validation
├── server/
│   ├── api/
│   │   ├── root.ts      # Root tRPC router
│   │   ├── trpc.ts      # tRPC initialization
│   │   └── routers/
│   │       └── example.ts  # Example router with procedures
│   └── db.ts            # Prisma client
├── prisma/
│   └── schema.prisma    # Database schema
└── components.json      # shadcn/ui config (optional)
```

## Key Files

| File | Purpose |
|------|---------|
| `server/api/trpc.ts` | tRPC initialization and context |
| `server/api/root.ts` | Root router combining all routers |
| `server/api/routers/example.ts` | Example router with queries/mutations |
| `server/db.ts` | Prisma client singleton |
| `lib/api.tsx` | tRPC React provider and client |
| `lib/env.ts` | Environment validation |
| `prisma/schema.prisma` | Database models |

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Run TypeScript compiler |

## tRPC Patterns

### Creating a Procedure

```typescript
// server/api/routers/posts.ts
import { z } from "zod";
import { createTRPCRouter, publicProcedure } from "@/server/api/trpc";
import { db } from "@/server/db";

export const postsRouter = createTRPCRouter({
  getAll: publicProcedure.query(async () => {
    return await db.post.findMany({
      orderBy: { createdAt: "desc" },
    });
  }),

  create: publicProcedure
    .input(z.object({ title: z.string(), content: z.string() }))
    .mutation(async ({ input }) => {
      return await db.post.create({
        data: input,
      });
    }),
});
```

### Using tRPC in Components

```typescript
// components/posts-list.tsx
"use client";

import { api } from "@/lib/api";

export function PostsList() {
  const posts = api.posts.getAll.useQuery();
  const createPost = api.posts.create.useMutation();

  if (posts.isLoading) return <div>Loading...</div>;
  if (posts.error) return <div>Error: {posts.error.message}</div>;

  return (
    <div>
      {posts.data?.map(post => (
        <div key={post.id}>{post.title}</div>
      ))}
    </div>
  );
}
```

### Server-Side tRPC Calls

```typescript
// app/posts/page.tsx
import { api } from "@/lib/api";

export default async function PostsPage() {
  // Server-side tRPC call
  const posts = await api.posts.getAll();

  return (
    <div>
      {posts.map(post => (
        <div key={post.id}>{post.title}</div>
      ))}
    </div>
  );
}
```

## Database Workflow

### Create a Migration

```bash
npx prisma migrate dev --name add_post_model
```

### Generate Prisma Client

```bash
npx prisma generate
```

### View Data in Prisma Studio

```bash
npx prisma studio
```

## Next Steps

### 1. Design Your Database Schema

Edit `prisma/schema.prisma`:

```prisma
model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String
  author    User     @relation(fields: [authorId], references: [id])
  authorId  Int
  createdAt DateTime @default(now())

  @@index([authorId])
}
```

### 2. Create tRPC Routers

Add new routers in `server/api/routers/` and register them in `server/api/root.ts`:

```typescript
// server/api/root.ts
import { postsRouter } from "./routers/posts";

export const appRouter = createTRPCRouter({
  example: exampleRouter,
  posts: postsRouter,  // Add your router
});
```

### 3. Add Authentication

The T3 Stack recommends **NextAuth.js**:

```bash
npm install next-auth @next-auth/prisma-adapter
```

Update Prisma schema with NextAuth models and configure providers.

### 4. Add UI Components

Install shadcn/ui components:

```bash
npx shadcn@latest add button form input
```

## Resources

- [T3 Stack Documentation](https://create.t3.gg/)
- [tRPC Documentation](https://trpc.io/docs)
- [Prisma Documentation](https://www.prisma.io/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [TanStack Query](https://tanstack.com/query/latest)

## Troubleshooting

### tRPC Type Errors

1. Make sure all routers are registered in `server/api/root.ts`
2. Restart TypeScript server in your editor
3. Check that tRPC provider wraps your app in `app/layout.tsx`

### Database Connection Errors

1. Verify PostgreSQL is running
2. Check `DATABASE_URL` in `.env`
3. Run `npx prisma generate`

### Serialization Errors

SuperJSON handles Date, Map, Set, BigInt automatically. If you see serialization errors:
1. Check if you're returning unsupported types
2. Consider transforming data before returning

## Why T3 Stack?

The T3 Stack is optimized for:
- **Type Safety**: End-to-end TypeScript
- **Developer Experience**: Amazing autocomplete and intellisense
- **Performance**: Optimal data fetching with TanStack Query
- **Scalability**: Modular router architecture
- **Modern**: Uses latest Next.js and React features

Perfect for building SaaS applications, admin panels, and typesafe full-stack apps.
