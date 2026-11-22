import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-accent-indigo text-white hover:bg-indigo-500 border border-indigo-400/30",
  secondary:
    "bg-graphite-800 text-slate-200 hover:bg-graphite-700 border border-graphite-600",
  ghost: "bg-transparent text-slate-300 hover:bg-graphite-800 border border-transparent",
  danger:
    "bg-red-950/40 text-red-300 hover:bg-red-950/70 border border-red-900/50",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  isLoading?: boolean;
}

export function Button({
  children,
  className,
  variant = "primary",
  isLoading = false,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      disabled={disabled ?? isLoading}
      {...props}
    >
      {isLoading ? "Working…" : children}
    </button>
  );
}