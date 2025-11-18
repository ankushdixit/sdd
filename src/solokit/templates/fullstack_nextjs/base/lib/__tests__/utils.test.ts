import { cn } from "../utils";

describe("cn utility function", () => {
  it("merges class names correctly", () => {
    expect(cn("px-2 py-1", "bg-blue-500")).toBe("px-2 py-1 bg-blue-500");
  });

  it("handles conditional classes", () => {
    const isActive = false;
    const isHighlighted = true;
    expect(cn("px-2", isActive && "py-1")).toBe("px-2");
    expect(cn("px-2", isHighlighted && "py-1")).toBe("px-2 py-1");
  });

  it("handles undefined and null values", () => {
    expect(cn("px-2", undefined, null, "py-1")).toBe("px-2 py-1");
  });

  it("merges conflicting Tailwind classes correctly", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  it("handles empty inputs", () => {
    expect(cn()).toBe("");
    expect(cn("")).toBe("");
  });

  it("handles array inputs", () => {
    expect(cn(["px-2", "py-1"])).toBe("px-2 py-1");
  });

  it("handles object inputs with boolean values", () => {
    expect(cn({ "px-2": true, "py-1": false, "bg-blue": true })).toBe("px-2 bg-blue");
  });

  it("combines multiple types of inputs", () => {
    const isHidden = false;
    expect(cn("px-2", { "py-1": true }, ["bg-blue"], isHidden && "hidden")).toBe(
      "px-2 py-1 bg-blue"
    );
  });
});
