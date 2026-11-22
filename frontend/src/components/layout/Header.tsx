import { useQuery } from "@tanstack/react-query";
import { Bell, ChevronDown, LogOut, Search, UserCircle2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "@/features/auth/AuthProvider";
import { listProjects } from "@/services/projects";

export function Header() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const projectsQuery = useQuery({
    queryKey: ["projects", "header"],
    queryFn: () => listProjects(0, 5),
    enabled: isAuthenticated,
  });

  const firstProject = projectsQuery.data?.items[0];

  return (
    <header className="flex h-14 items-center gap-4 border-b border-graphite-800 bg-graphite-900/80 px-4 backdrop-blur">
      <div className="hidden min-w-0 sm:block">
        <p className="text-xs text-slate-500">Workspace</p>
        {firstProject ? (
          <Link
            to={`/projects/${firstProject.id}`}
            className="flex items-center gap-1 text-sm font-medium text-slate-200 hover:text-white"
          >
            {firstProject.name}
            <ChevronDown className="h-4 w-4 opacity-50" aria-hidden />
          </Link>
        ) : (
          <Link to="/projects" className="text-sm font-medium text-slate-400 hover:text-slate-200">
            Select or create a project
          </Link>
        )}
      </div>

      <div className="ml-auto flex max-w-md flex-1 items-center justify-end gap-2 sm:justify-center">
        <label className="relative hidden w-full max-w-sm md:block">
          <Search
            className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600"
            aria-hidden
          />
          <input
            type="search"
            disabled
            placeholder="Search logs, incidents, services…"
            aria-label="Global search — not available yet"
            className="w-full rounded-md border border-graphite-700 bg-graphite-850 py-1.5 pl-8 pr-3 text-sm text-slate-500 placeholder:text-slate-600"
            title="Search will be enabled after log ingestion"
          />
        </label>
      </div>

      <div className="flex items-center gap-1">
        <button
          type="button"
          disabled
          className="rounded-md p-2 text-slate-600"
          aria-label="Notifications — not configured"
          title="Notifications not configured"
        >
          <Bell className="h-4 w-4" aria-hidden />
        </button>
        <div className="flex items-center gap-2 rounded-md border border-graphite-700 bg-graphite-850 px-2 py-1 text-slate-300">
          <UserCircle2 className="h-5 w-5" aria-hidden />
          <span className="hidden max-w-[10rem] truncate text-xs sm:inline">
            {user?.full_name ?? "Account"}
          </span>
          <button
            type="button"
            onClick={() => {
              void (async () => {
                await logout();
                void navigate("/login", { replace: true });
              })();
            }}
            className="rounded p-1 text-slate-500 hover:bg-graphite-800 hover:text-slate-200"
            aria-label="Sign out"
            title="Sign out"
          >
            <LogOut className="h-4 w-4" aria-hidden />
          </button>
        </div>
      </div>
    </header>
  );
}