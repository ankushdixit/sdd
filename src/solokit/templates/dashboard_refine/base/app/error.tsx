"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md space-y-4 rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold">Something went wrong!</h2>
          <p className="text-sm text-muted-foreground">
            {error.message || "An unexpected error occurred"}
          </p>
        </div>
        <button
          onClick={reset}
          className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
