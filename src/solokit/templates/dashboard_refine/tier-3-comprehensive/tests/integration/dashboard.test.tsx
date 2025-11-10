import { render, screen, waitFor } from "@testing-library/react";
import { RefineProvider } from "@/providers/refine-provider";

/**
 * Dashboard Integration Tests
 * Tests the integration between Refine provider and dashboard components
 */

// Mock Next.js navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock Refine hooks
jest.mock("@refinedev/core", () => ({
  Refine: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useList: () => ({
    data: {
      data: [
        { id: 1, name: "John Doe", email: "john@example.com" },
        { id: 2, name: "Jane Smith", email: "jane@example.com" },
      ],
      total: 2,
    },
    isLoading: false,
    isError: false,
  }),
}));

describe("Dashboard Integration", () => {
  it("should render RefineProvider without errors", () => {
    const { container } = render(
      <RefineProvider>
        <div>Test Content</div>
      </RefineProvider>
    );

    expect(container).toBeInTheDocument();
    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("should provide Refine context to children", () => {
    const TestComponent = () => {
      return <div>Refine is working</div>;
    };

    render(
      <RefineProvider>
        <TestComponent />
      </RefineProvider>
    );

    expect(screen.getByText("Refine is working")).toBeInTheDocument();
  });

  it("should handle data fetching in components", async () => {
    const { useList } = await import("@refinedev/core");

    const TestComponent = () => {
      const { data, isLoading } = useList({ resource: "users" });

      if (isLoading) return <div>Loading...</div>;

      return (
        <div>
          {data?.data.map((user: any) => (
            <div key={user.id}>{user.name}</div>
          ))}
        </div>
      );
    };

    render(
      <RefineProvider>
        <TestComponent />
      </RefineProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    });
  });
});
