import Link from "next/link";
import ExampleComponent from "@/components/example-component";
import { prisma } from "@/lib/prisma";

/**
 * Server Component with Data Fetching
 *
 * This is a Next.js Server Component that fetches data directly from the database.
 * Server Components run on the server and can directly access databases, file systems, etc.
 *
 * Benefits:
 * - No client-side JavaScript for data fetching
 * - Direct database access (no API route needed)
 * - Automatic caching and revalidation
 * - Better performance and SEO
 */
export default async function Home() {
  // Server-side data fetching - this runs on the server only
  const userCount = await prisma.user.count();
  const latestUser = await prisma.user.findFirst({
    orderBy: { createdAt: "desc" },
  });

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-[#2e026d] to-[#15162c] text-white">
      <div className="container flex flex-col items-center justify-center gap-12 px-4 py-16">
        <h1 className="text-5xl font-extrabold tracking-tight sm:text-[5rem]">
          Full-Stack <span className="text-[hsl(280,100%,70%)]">Next.js</span>
        </h1>

        {/* Server-side data display */}
        <div className="rounded-xl bg-white/10 p-6">
          <h3 className="mb-2 text-xl font-bold">Server-Side Data Fetching Example</h3>
          <p className="text-sm text-white/70">
            This data is fetched directly in the Server Component:
          </p>
          <div className="mt-4 space-y-2 text-lg">
            <p>Total Users: {userCount}</p>
            {latestUser && (
              <p className="text-sm text-white/80">
                Latest: {latestUser.name} ({latestUser.email})
              </p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-8">
          <Link
            href="/api/example"
            className="flex max-w-xs flex-col gap-4 rounded-xl bg-white/10 p-4 hover:bg-white/20"
          >
            <h3 className="text-2xl font-bold">API Routes →</h3>
            <div className="text-lg">Check out the example API route at /api/example</div>
          </Link>
          <div className="flex max-w-xs flex-col gap-4 rounded-xl bg-white/10 p-4">
            <h3 className="text-2xl font-bold">Database →</h3>
            <div className="text-lg">Prisma ORM with PostgreSQL for type-safe database queries</div>
          </div>
        </div>
        <ExampleComponent />
      </div>
    </main>
  );
}
