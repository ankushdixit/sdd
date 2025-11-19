import { render, screen, fireEvent } from "@testing-library/react";
import ExampleComponent from "@/components/example-component";

describe("ExampleComponent", () => {
  it("should render the component with initial count", () => {
    render(<ExampleComponent />);
    expect(screen.getByText(/Count:/i)).toBeInTheDocument();
    expect(screen.getByText(/0/)).toBeInTheDocument();
  });

  it("should have an increment button", () => {
    render(<ExampleComponent />);
    const button = screen.getByRole("button", { name: /increment/i });
    expect(button).toBeInTheDocument();
  });

  it("should render the title", () => {
    render(<ExampleComponent />);
    expect(screen.getByText(/Client Component Example/i)).toBeInTheDocument();
  });

  it("should increment count when button is clicked", () => {
    render(<ExampleComponent />);
    const button = screen.getByRole("button", { name: /increment/i });

    // Initial count should be 0
    expect(screen.getByText(/Count: 0/)).toBeInTheDocument();

    // Click the button
    fireEvent.click(button);

    // Count should now be 1
    expect(screen.getByText(/Count: 1/)).toBeInTheDocument();
  });
});
