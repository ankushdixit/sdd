"use client";

import { api } from "@/lib/api";

export default function ExampleComponent() {
  const hello = api.example.hello.useQuery({ text: "from tRPC" });

  return (
    <div className="flex flex-col items-center gap-4 rounded-xl bg-white/10 p-6">
      <h3 className="text-2xl font-bold">tRPC Example Component</h3>
      {hello.data ? (
        <p className="text-lg">{hello.data.greeting}</p>
      ) : (
        <p className="text-lg">Loading tRPC query...</p>
      )}
      <p className="text-sm text-white/60">
        This component demonstrates tRPC usage with type-safe API calls
      </p>
    </div>
  );
}
