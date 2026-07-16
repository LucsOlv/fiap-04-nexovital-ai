import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonVariant = "default" | "secondary" | "outline" | "ghost" | "destructive";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variantClasses: Record<ButtonVariant, string> = {
  default:
    "bg-slate-900 text-white hover:bg-slate-800 dark:bg-brand dark:hover:bg-blue-500 focus-visible:ring-slate-400",
  secondary:
    "bg-slate-100 text-slate-900 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 focus-visible:ring-slate-300",
  outline:
    "border app-border bg-[var(--app-surface)] text-[var(--app-text)] hover:bg-[var(--app-surface-muted)] focus-visible:ring-slate-300",
  ghost: "bg-transparent text-[var(--app-text)] hover:bg-[var(--app-surface-muted)] focus-visible:ring-slate-300",
  destructive: "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-300",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50",
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  ),
);

Button.displayName = "Button";
