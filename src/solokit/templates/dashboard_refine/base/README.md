# Dashboard Refine Template

A modern admin dashboard built with Refine.dev, Next.js 16 (App Router), and shadcn/ui components.

## What's Included

This template provides a complete foundation for building admin dashboards and CRUD applications:

- **Refine.dev**: Headless framework for building data-intensive applications
- **Next.js 16** with App Router
- **shadcn/ui**: High-quality, customizable React components
- **Tailwind CSS**: Utility-first CSS framework with comprehensive design system
- **TypeScript**: Full type safety across the stack
- **React Hook Form + Zod**: Type-safe form validation
- **Responsive Layout**: Pre-built header and sidebar components

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see your dashboard.

## Architecture Decisions

### Mock Data Provider

The template includes a **mock data provider** for demonstration purposes. This allows you to explore the dashboard features without setting up a backend.

⚠️ **Important**: Replace the mock provider with a real data provider before production:

1. Choose your backend type (REST, GraphQL, Strapi, Supabase, etc.)
2. Install the appropriate Refine data provider package
3. Update `lib/refine.tsx` with your configuration
4. See migration comments in `lib/refine.tsx` for detailed instructions

### shadcn/ui Integration

This template uses the comprehensive shadcn/ui theming system:

- **CSS Variables**: Defined in `app/globals.css`
- **Color Palette**: 16 semantic color tokens for light/dark modes
- **Components**: Button, Card, Table components included
- **Customizable**: Modify `tailwind.config.ts` and `components.json`

### Layout Structure

```
app/
├── (dashboard)/          # Route group for dashboard pages
│   ├── layout.tsx       # Dashboard layout with sidebar/header
│   ├── page.tsx         # Dashboard home page
│   └── users/           # Example resource page
├── layout.tsx           # Root layout
└── globals.css          # Global styles & theme variables
```

## Key Files

| File | Purpose |
|------|---------|
| `lib/refine.tsx` | Refine configuration and data provider |
| `lib/validations.ts` | Zod validation schemas for forms |
| `components/forms/user-form.tsx` | Example form with validation |
| `components/ui/*` | shadcn/ui components |
| `components/layout/*` | Header and sidebar components |

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Run TypeScript compiler |

## Next Steps

### 1. Set Up Your Backend

Replace the mock data provider with a real one:

- **REST API**: `@refinedev/simple-rest`
- **GraphQL**: `@refinedev/graphql`
- **Strapi**: `@refinedev/strapi-v4`
- **Supabase**: `@refinedev/supabase`

See `lib/refine.tsx` for migration guide.

### 2. Add Authentication

Refine supports multiple auth providers:

```typescript
import { AuthBindings } from "@refinedev/core";

const authProvider: AuthBindings = {
  login: async ({ email, password }) => { /* ... */ },
  logout: async () => { /* ... */ },
  check: async () => { /* ... */ },
  // ... other methods
};
```

### 3. Customize Your Resources

Add your own resources in `lib/refine.tsx`:

```typescript
export const refineResources = [
  {
    name: "your-resource",
    list: "/your-resource",
    create: "/your-resource/create",
    edit: "/your-resource/edit/:id",
  },
  // ... more resources
];
```

### 4. Add More UI Components

Install additional shadcn/ui components:

```bash
npx shadcn@latest add form input select
```

## Resources

- [Refine Documentation](https://refine.dev/docs/)
- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Zod Documentation](https://zod.dev/)

## Troubleshooting

### Mock Data Not Showing

Make sure you're viewing the dashboard pages under the `(dashboard)` route group. The home page is at `/`.

### Components Not Styled

Verify that `app/globals.css` is imported in your root layout and all CSS variables are defined.

### Type Errors

Run `npm run type-check` to see all TypeScript errors. The template is configured with strict mode enabled.
