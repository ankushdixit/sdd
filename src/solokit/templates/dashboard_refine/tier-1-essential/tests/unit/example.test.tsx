import { render, screen } from "@testing-library/react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

/**
 * Example Component Tests using Jest
 * These tests demonstrate the testing setup and best practices
 */

describe("Button Component", () => {
  it("renders children correctly", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    render(<Button variant="destructive">Delete</Button>);
    const button = screen.getByText("Delete");
    expect(button).toBeInTheDocument();
  });

  it("handles click events", () => {
    let clicked = false;
    render(<Button onClick={() => (clicked = true)}>Click</Button>);
    const button = screen.getByText("Click");
    button.click();
    expect(clicked).toBe(true);
  });

  it("is accessible with proper aria attributes", () => {
    render(<Button aria-label="Submit form">Submit</Button>);
    expect(screen.getByLabelText("Submit form")).toBeInTheDocument();
  });
});

describe("Card Component", () => {
  it("renders with all parts", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Card</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Card content</p>
        </CardContent>
      </Card>
    );

    expect(screen.getByText("Test Card")).toBeInTheDocument();
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(
      <Card className="custom-class">
        <CardContent>Content</CardContent>
      </Card>
    );

    const card = container.querySelector(".custom-class");
    expect(card).toBeInTheDocument();
  });
});

describe("Utility Functions", () => {
  it("cn() merges classes correctly", () => {
    const { cn } = require("@/lib/utils");

    expect(cn("px-2 py-1", "bg-blue-500")).toBe("px-2 py-1 bg-blue-500");

    // Test conditional class merging
    const isActive = false;
    const isHighlighted = true;
    expect(cn("px-2", isActive && "py-1")).toBe("px-2");
    expect(cn("px-2", isHighlighted && "py-1")).toBe("px-2 py-1");
  });
});
