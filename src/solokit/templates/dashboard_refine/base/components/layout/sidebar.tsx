"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  ShoppingCart,
  Package,
  Settings,
} from "lucide-react";

/**
 * Dashboard sidebar navigation
 * Provides links to main sections of the application
 */
export function Sidebar() {
  const pathname = usePathname();

  const routes = [
    {
      label: "Dashboard",
      icon: LayoutDashboard,
      href: "/dashboard",
      active: pathname === "/dashboard",
    },
    {
      label: "Users",
      icon: Users,
      href: "/dashboard/users",
      active: pathname === "/dashboard/users",
    },
    {
      label: "Orders",
      icon: ShoppingCart,
      href: "/dashboard/orders",
      active: pathname === "/dashboard/orders",
    },
    {
      label: "Products",
      icon: Package,
      href: "/dashboard/products",
      active: pathname === "/dashboard/products",
    },
    {
      label: "Settings",
      icon: Settings,
      href: "/dashboard/settings",
      active: pathname === "/dashboard/settings",
    },
  ];

  return (
    <aside className="hidden md:flex w-64 flex-col border-r bg-background">
      <div className="flex h-14 items-center border-b px-4">
        <Link
          href="/dashboard"
          className="flex items-center gap-2 font-semibold"
        >
          <LayoutDashboard className="h-6 w-6" />
          <span>Dashboard</span>
        </Link>
      </div>
      <nav className="flex-1 space-y-1 p-4" aria-label="Main navigation">
        {routes.map((route) => (
          <Link
            key={route.href}
            href={route.href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all hover:bg-accent",
              route.active
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground",
            )}
            aria-current={route.active ? "page" : undefined}
          >
            <route.icon className="h-4 w-4" />
            {route.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
