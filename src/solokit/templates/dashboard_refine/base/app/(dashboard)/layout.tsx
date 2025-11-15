import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";

/**
 * Dashboard layout
 * Provides consistent header and sidebar for all dashboard pages
 */
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
