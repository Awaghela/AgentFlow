import { Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { Dashboard } from "@/pages/Dashboard";
import { Workflows } from "@/pages/Workflows";
import { WorkflowDetail } from "@/pages/WorkflowDetail";
import { Approvals } from "@/pages/Approvals";
import { EvalResults } from "@/pages/EvalResults";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/workflows" element={<Workflows />} />
        <Route path="/workflows/:id" element={<WorkflowDetail />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/eval" element={<EvalResults />} />
      </Route>
    </Routes>
  );
}
