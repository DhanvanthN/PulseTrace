import { NavLink } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";
import type { NavItem } from "@/types/navigation";
import { Activity } from "lucide-react";

interface SidebarProps {
  items: NavItem[];
}

export function Sidebar({ items }: SidebarProps) {
  return (
    <aside
      data-testid="app-sidebar"
      className="flex w-56 shrink-0 flex-col border-r border-graphite-800 bg-graphite-900"
      aria-label="Main navigation"
    >
      <div className="flex items-center gap-2 border-b border-graphite-800 px-4 py-4">
        <div className="rounded-md bg-accent-indigo/15 p-1.5 ring-1 ring-accent-indigo/30">
          <Activity className="h-4 w-4 text-accent-cyan" aria-hidden />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-100">PulseTrace</p>
          <p className="text-[10px] text-slate-500">Observability</p>
        </div>
      </div>

      <div className="flex-1 space-y-0.5 p-2">
        {items.map((item, index) => {
          const Icon = item.icon;
          const content = (
            <>
              <Icon className="h-4 w-4 shrink-0" aria-hidden />
              <span className="truncate">{item.label}</span>
              {item.disabled ? (
                <Badge variant="muted" className="ml-auto normal-case">
                  Soon
                </Badge>
              ) : null}
            </>
          );

          const baseClass =
            "flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-sm transition-colors";

          if (item.disabled) {
            return (
              <div
                key={`${item.path}-${item.label}-${index}`}
                aria-disabled
                className={cn(
                  baseClass,
                  "cursor-not-allowed text-slate-600 opacity-80"
                )}
                title="Available in a future phase"
              >
                {content}
              </div>
            );
          }

          return (
            <NavLink
              key={`${item.path}-${item.label}-${index}`}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                cn(
                  baseClass,
                  isActive
                    ? "bg-graphite-800 text-slate-100 ring-1 ring-graphite-700"
                    : "text-slate-400 hover:bg-graphite-850 hover:text-slate-200"
                )
              }
            >
              {content}
            </NavLink>
          );
        })}
      </div>

      <div className="border-t border-graphite-800 p-3">
        <p className="text-[10px] leading-relaxed text-slate-600">
          Evidence-based incident intelligence — ingest logs, correlate, investigate.
        </p>
      </div>
    </aside>
  );
}