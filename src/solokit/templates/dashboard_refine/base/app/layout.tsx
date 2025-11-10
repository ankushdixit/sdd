import type { Metadata } from "next";
import type { ReactNode } from "react";
import ClientRefineWrapper from "@/components/client-refine-wrapper";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dashboard - Refine Admin",
  description: "Modern admin dashboard built with Refine and Next.js",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ClientRefineWrapper>{children}</ClientRefineWrapper>
      </body>
    </html>
  );
}
