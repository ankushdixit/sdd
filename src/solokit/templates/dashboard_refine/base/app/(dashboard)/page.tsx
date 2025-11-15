"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, Users, ShoppingCart, TrendingUp } from "lucide-react";

/**
 * Dashboard home page
 * Displays key metrics and statistics
 */
export default function DashboardPage() {
  const stats = [
    {
      title: "Total Users",
      value: "2,543",
      icon: Users,
      trend: "+12.5%",
    },
    {
      title: "Total Orders",
      value: "1,234",
      icon: ShoppingCart,
      trend: "+8.2%",
    },
    {
      title: "Revenue",
      value: "$45,231",
      icon: TrendingUp,
      trend: "+23.1%",
    },
    {
      title: "Products",
      value: "456",
      icon: BarChart3,
      trend: "+4.3%",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Welcome to your admin dashboard</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">{stat.trend}</span> from last month
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
