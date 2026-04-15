import { redirect } from "next/navigation";

// Root route — redirect based on auth state.
// Token check happens client-side in the target pages,
// so we default to /dashboard and let the dashboard
// redirect to /login if no token is found.
export default function RootPage() {
  redirect("/dashboard");
}
