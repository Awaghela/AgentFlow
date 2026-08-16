import { Outlet } from "react-router-dom";
import { Sidebar } from "@/components/layout/Sidebar";

export function AppShell() {
  return (
    // Lock the shell to the viewport height and let only the content pane
    // scroll internally, so the sidebar stays pinned in place regardless of
    // how tall a given page's content is.
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
