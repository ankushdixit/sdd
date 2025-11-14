/**
 * @jest-environment jsdom
 */
import { render, screen } from "@testing-library/react";

// Example component for testing
function ExampleComponent({ text }: { text: string }) {
  return <div data-testid="example">{text}</div>;
}

describe("ExampleComponent", () => {
  it("should render the text prop", () => {
    render(<ExampleComponent text="Hello World" />);
    const element = screen.getByTestId("example");
    expect(element).toBeInTheDocument();
    expect(element).toHaveTextContent("Hello World");
  });

  it("should render different text when prop changes", () => {
    const { rerender } = render(<ExampleComponent text="First" />);
    expect(screen.getByTestId("example")).toHaveTextContent("First");

    rerender(<ExampleComponent text="Second" />);
    expect(screen.getByTestId("example")).toHaveTextContent("Second");
  });
});
