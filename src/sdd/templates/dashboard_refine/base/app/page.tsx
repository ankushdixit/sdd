import { redirect } from "next/navigation";

/**
 * Root page - redirects to the dashboard
 * This allows the dashboard to be the default view
 */
export default function HomePage() {
  redirect("/dashboard");
}
