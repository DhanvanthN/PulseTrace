import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type BadgeVariant = "default" | "muted" | "accent";

const variantClasses: Record<BadgeVariant, string> = {
  default: "border-graphite-600 bg-graphite-800 text-slate-300",
  muted: "border-graphite-700 bg-graphite-850 text-slate-500",
  accent: "border-accent-indigo/40 bg-accent-indigo/10 text-accent-cyan",
};

export function Badge({
  children,
  variant = "default",
  className,
}: {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide",
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}