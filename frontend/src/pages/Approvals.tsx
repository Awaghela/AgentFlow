import { api } from "@/api/client";
import { useAsync } from "@/hooks/useAsync";
import { TopBar } from "@/components/layout/TopBar";
import { Loading, ErrorState, EmptyState } from "@/components/common/Loading";
import { ApprovalCard } from "@/components/approvals/ApprovalCard";

export function Approvals() {
  const { data, loading, error, refetch } = useAsync(() => api.listApprovals("pending"), []);

  async function decide(approvalId: string, decision: "approved" | "rejected", notes?: string) {
    await api.decideApproval(approvalId, decision, "console-reviewer", notes);
    refetch();
  }

  return (
    <>
      <TopBar
        title="Approvals"
        description="Recommendations below the auto-approve confidence threshold, or flagged as high risk, wait here for a human decision."
      />
      <div className="px-8 py-6">
        {loading && <Loading label="Loading approval queue" />}
        {error && <ErrorState message={error} onRetry={refetch} />}
        {data && data.length === 0 && (
          <EmptyState
            title="Queue is clear"
            description="No workflow runs are currently waiting on a human decision."
          />
        )}
        {data && data.length > 0 && (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {data.map((approval) => (
              <ApprovalCard
                key={approval.id}
                approval={approval}
                onDecide={(decision, notes) => decide(approval.id, decision, notes)}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
