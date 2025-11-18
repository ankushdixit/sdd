# Full-Stack Next.js Template

A modern full-stack Next.js application with Prisma ORM, PostgreSQL, and type-safe validation.

## What's Included

This template provides a minimal but complete full-stack foundation:

- **Next.js 16** with App Router
- **Prisma ORM**: Type-safe database access
- **PostgreSQL**: Production-ready database
- **Zod**: Runtime validation and type inference
- **Tailwind CSS**: Utility-first styling
- **TypeScript**: Full type safety
- **Environment Validation**: Runtime env var checking

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

### Prisma Client Export Name

This template exports the Prisma client as `prisma` (not `db`) to be explicit about what you're working with:

```typescript
import { prisma } from "@/lib/prisma";
const users = await prisma.user.findMany();
```

This follows the standard Prisma documentation pattern.

### Server Components First

The template demonstrates **Server Component** data fetching as the default pattern:

- Data fetched directly in components (see `app/page.tsx`)
- No unnecessary API routes for data fetching
- Better performance and SEO
- Reduced client-side JavaScript

Use API routes (`app/api/*`) only when needed for:
- Client-side mutations
- Webhook endpoints
- Third-party integrations

### Environment Validation

`lib/env.ts` validates environment variables at startup using Zod:

- Fail fast if vars are missing/invalid
- Type-safe env vars throughout the app
- Clear error messages

## Project Structure

```
├── app/
│   ├── api/              # API routes (use sparingly)
│   │   └── example/      # Example API endpoint
│   ├── globals.css       # Global styles
│   ├── layout.tsx        # Root layout
│   ├── page.tsx          # Home page (Server Component with data fetching)
│   ├── error.tsx         # Error boundary
│   └── loading.tsx       # Loading UI
├── components/           # React components
│   └── example-component.tsx
├── lib/
│   ├── prisma.ts        # Prisma client singleton
│   ├── utils.ts         # Utility functions (cn helper)
│   ├── validations.ts   # Zod schemas
│   └── env.ts           # Environment validation
├── prisma/
│   └── schema.prisma    # Database schema
└── components.json      # shadcn/ui config (optional)
```

## Key Files

| File | Purpose |
|------|---------|
| `lib/prisma.ts` | Prisma client with singleton pattern |
| `lib/env.ts` | Environment variable validation |
| `lib/validations.ts` | Zod schemas for API validation |
| `prisma/schema.prisma` | Database models and migrations |
| `app/api/example/route.ts` | Example API route with error handling |
| `app/page.tsx` | Server Component data fetching example |

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Run TypeScript compiler |

## Database Workflow

### Create a Migration

```bash
npx prisma migrate dev --name add_user_role
```

### Update Prisma Client

After schema changes:

```bash
npx prisma generate
```

### View Data in Prisma Studio

```bash
npx prisma studio
```

### Reset Database (Development Only!)

```bash
npx prisma migrate reset
```

## Common Patterns

### Server Component Data Fetching

```typescript
// app/users/page.tsx
import { prisma } from "@/lib/prisma";

export default async function UsersPage() {
  const users = await prisma.user.findMany();

  return (
    <div>
      {users.map(user => (
        <div key={user.id}>{user.name}</div>
      ))}
    </div>
  );
}
```

### API Route with Validation

```typescript
// app/api/users/route.ts
import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { userSchema } from "@/lib/validations";

export async function POST(request: Request) {
  try {
    const json = await request.json();
    const data = userSchema.parse(json);

    const user = await prisma.user.create({ data });
    return NextResponse.json(user, { status: 201 });
  } catch (error) {
    return NextResponse.json(
      { error: "Invalid request" },
      { status: 400 }
    );
  }
}
```

## Next Steps

### 1. Design Your Database Schema

Edit `prisma/schema.prisma` to add your models:

```prisma
model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  Int
}
```

### 2. Add Authentication

Consider using:
- **NextAuth.js**: Session-based auth
- **Clerk**: Hosted auth solution
- **Auth0**: Enterprise auth
- **Supabase Auth**: Open-source auth

### 3. Add UI Components

Install shadcn/ui components as needed:

```bash
npx shadcn@latest add button form input
```

The `components.json` is already configured.

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Prisma Documentation](https://www.prisma.io/docs)
- [Zod Documentation](https://zod.dev/)
- [Tailwind CSS](https://tailwindcss.com/docs)

## Troubleshooting

### Database Connection Errors

1. Verify PostgreSQL is running
2. Check `DATABASE_URL` in `.env`
3. Ensure database exists: `createdb mydb`

### Prisma Client Not Found

Run `npx prisma generate` to generate the client.

### Type Errors After Schema Changes

1. Run `npx prisma generate`
2. Restart TypeScript server in your editor
