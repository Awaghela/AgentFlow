import { NavLink } from "react-router-dom";
import { LayoutGrid, GitBranch, ShieldCheck, FlaskConical, Radio } from "lucide-react";
import clsx from "clsx";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutGrid, end: true },
  { to: "/workflows", label: "Workflow runs", icon: GitBranch },
  { to: "/approvals", label: "Approvals", icon: ShieldCheck },
  { to: "/eval", label: "Eval suite", icon: FlaskConical },
];

export function Sidebar() {
  return (
    <aside className="flex h-full w-60 shrink-0 flex-col overflow-y-auto border-r border-border bg-ink-900">
      <div className="flex items-center gap-2.5 border-b border-border px-5 py-5">
        <span className="relative flex h-6 w-6 items-center justify-center rounded-sm border border-signal-amber/40 bg-signal-amberSoft">
          <Radio size={13} className="text-signal-amber" />
        </span>
        <div>
          <p className="font-display text-sm font-semibold leading-none text-text-primary">AgentFlow</p>
          <p className="mt-0.5 font-mono text-[9px] uppercase tracking-[0.14em] text-text-faint">
            Agent workflow console
          </p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4">
        <ul className="flex flex-col gap-0.5">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  clsx(
                    "flex items-center gap-2.5 rounded-sm px-3 py-2 font-mono text-xs uppercase tracking-wide transition-colors",
                    isActive
                      ? "border-l-2 border-signal-amber bg-surface text-signal-amber"
                      : "border-l-2 border-transparent text-text-secondary hover:bg-surface hover:text-text-primary"
                  )
                }
              >
                <item.icon size={14} />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t border-border px-5 py-4">
        <p className="font-mono text-[10px] leading-relaxed text-text-faint">
          FastAPI · LangGraph · RAG
          <br />
          PostgreSQL · Docker
        </p>
      </div>
    </aside>
  );
}
