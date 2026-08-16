import type { ReactNode } from "react";

export function TopBar({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <header className="flex items-center justify-between border-b border-border px-8 py-5">
      <div>
        <h1 className="font-display text-lg font-medium text-text-primary">{title}</h1>
        {description && <p className="mt-0.5 text-sm text-text-secondary">{description}</p>}
      </div>
      {action}
    </header>
  );
}
