import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function Input({ label, error, className, id, ...props }: InputProps) {
  const fieldId = id ?? props.name;
  return (
    <label className="block space-y-1.5" htmlFor={fieldId}>
      <span className="text-xs font-medium text-slate-400">{label}</span>
      <input
        id={fieldId}
        className={cn(
          "w-full rounded-md border border-graphite-700 bg-graphite-850 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-accent-indigo/50 focus:outline-none focus:ring-1 focus:ring-accent-indigo/40",
          error && "border-red-800/80 focus:border-red-700 focus:ring-red-700/30",
          className
        )}
        {...props}
      />
      {error ? <span className="text-xs text-red-400">{error}</span> : null}
    </label>
  );
}