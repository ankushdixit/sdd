"use client";

import { useState } from "react";

export default function ExampleComponent() {
  const [count, setCount] = useState(0);

  return (
    <div className="flex flex-col items-center gap-4 rounded-xl bg-white/10 p-6">
      <h3 className="text-2xl font-bold">Client Component Example</h3>
      <p className="text-lg">Count: {count}</p>
      <button
        onClick={() => setCount(count + 1)}
        className="rounded-lg bg-white/20 px-6 py-2 font-semibold transition hover:bg-white/30"
      >
        Increment
      </button>
    </div>
  );
}
