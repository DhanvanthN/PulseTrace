import { Activity } from "lucide-react";
import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/features/auth/AuthProvider";

export function AuthLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-graphite-950 text-sm text-slate-400">
        Loading…
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-graphite-950 px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <div className="flex items-center gap-2">
          <div className="rounded-md bg-accent-indigo/15 p-2 ring-1 ring-accent-indigo/30">
            <Activity className="h-5 w-5 text-accent-cyan" aria-hidden />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-100">PulseTrace</h1>
            <p className="text-xs text-slate-500">Observability platform</p>
          </div>
        </div>
        <Outlet />
      </div>
    </div>
  );
}