import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function PageHeader({
  title,
  description,
  breadcrumb,
  actions,
}: {
  title: string;
  description?: string;
  breadcrumb?: { label: string; to: string };
  actions?: ReactNode;
}) {
  return (
    <header className="flex flex-col gap-3 border-b border-graphite-800 pb-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0 space-y-1">
        {breadcrumb ? (
          <p className="text-xs text-slate-500">
            <Link
              to={breadcrumb.to}
              className="transition-colors hover:text-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-indigo/50 rounded"
            >
              {breadcrumb.label}
            </Link>
          </p>
        ) : null}
        <h1 className="text-xl font-semibold tracking-tight text-slate-100 sm:text-2xl">{title}</h1>
        {description ? (
          <p className="max-w-3xl text-sm leading-relaxed text-slate-400">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </header>
  );
}