import type { ReactNode } from "react";
import clsx from "clsx";

export function Panel({
  title,
  eyebrow,
  action,
  children,
  className,
}: {
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={clsx(
        "rounded-md border border-border bg-surface shadow-panel",
        className
      )}
    >
      {(title || eyebrow || action) && (
        <div className="flex items-center justify-between border-b border-border px-5 py-3.5">
          <div>
            {eyebrow && (
              <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-faint">
                {eyebrow}
              </p>
            )}
            {title && <h2 className="font-display text-sm font-medium text-text-primary">{title}</h2>}
          </div>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}
