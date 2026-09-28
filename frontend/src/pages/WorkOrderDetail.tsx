import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { assignWorkOrder, completeWorkOrder, getWorkOrder, getWorkOrderHistory, startWorkOrder, verifyWorkOrder } from "../api/maintenance";
import { listContractors } from "../api/contractors";
import { listUsers } from "../api/admin";
import { uploadDocument } from "../api/documents";
import { useAuth } from "../hooks/useAuth";

export default function WorkOrderDetail() {
  const { id } = useParams<{ id: string }>();
  const { hasRole, user } = useAuth();
  const queryClient = useQueryClient();

  const { data: wo, isLoading } = useQuery({ queryKey: ["work-order", id], queryFn: () => getWorkOrder(id!), enabled: !!id });
  const { data: history } = useQuery({ queryKey: ["work-order-history", id], queryFn: () => getWorkOrderHistory(id!), enabled: !!id });
  const canManage = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN", "MAINTENANCE_OFFICER");
  const { data: contractors } = useQuery({ queryKey: ["contractors"], queryFn: listContractors, enabled: canManage });
  const { data: users } = useQuery({ queryKey: ["users-for-assign"], queryFn: listUsers, enabled: hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN") });

  const [contractorId, setContractorId] = useState("");
  const [officerId, setOfficerId] = useState("");
  const [actualCost, setActualCost] = useState("");
  const [completionRemarks, setCompletionRemarks] = useState("");

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["work-order", id] });
    queryClient.invalidateQueries({ queryKey: ["work-order-history", id] });
    queryClient.invalidateQueries({ queryKey: ["work-orders"] });
  };

  const assignMutation = useMutation({
    mutationFn: () => assignWorkOrder(id!, { contractor_id: contractorId || undefined, assigned_officer_id: officerId || undefined }),
    onSuccess: invalidate,
  });
  const startMutation = useMutation({ mutationFn: () => startWorkOrder(id!), onSuccess: invalidate });
  const completeMutation = useMutation({
    mutationFn: () => completeWorkOrder(id!, { actual_cost: actualCost ? Number(actualCost) : undefined, completion_remarks: completionRemarks }),
    onSuccess: invalidate,
  });
  const verifyMutation = useMutation({ mutationFn: (verified: boolean) => verifyWorkOrder(id!, verified), onSuccess: invalidate });
  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument("MAINTENANCE_REPORT", "work_order", id!, file),
    onSuccess: invalidate,
  });

  const canVerify = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN");

  if (isLoading || !wo) return <div className="text-slate-500">Loading…</div>;
  const canExecute = canManage || (hasRole("CONTRACTOR") && user?.contractor_id === wo.contractor_id);

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900 font-mono">{wo.work_order_code}</h1>
        <div className="text-sm text-slate-500">Status: <span className="font-medium">{wo.status}</span> · Priority: {wo.priority}</div>
      </div>

      {canManage && (wo.status === "CREATED" || wo.status === "ASSIGNED") && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-slate-700">Assign</h2>
          <div className="grid grid-cols-2 gap-3">
            <select value={contractorId} onChange={(e) => setContractorId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
              <option value="">Contractor…</option>
              {contractors?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <select value={officerId} onChange={(e) => setOfficerId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
              <option value="">Assigned officer…</option>
              {users?.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
            </select>
          </div>
          <button onClick={() => assignMutation.mutate()} className="bg-rb-navy text-white text-sm px-4 py-2 rounded-md">Assign</button>
        </div>
      )}

      {canExecute && wo.status === "ASSIGNED" && (
        <button onClick={() => startMutation.mutate()} className="bg-amber-600 text-white text-sm px-4 py-2 rounded-md">Start Work</button>
      )}

      {canExecute && wo.status === "IN_PROGRESS" && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-slate-700">Complete Work Order</h2>
          <input placeholder="Actual cost" type="number" value={actualCost} onChange={(e) => setActualCost(e.target.value)} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <textarea placeholder="Completion remarks" value={completionRemarks} onChange={(e) => setCompletionRemarks(e.target.value)} rows={2} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <div>
            <label className="text-xs text-rb-teal cursor-pointer hover:underline">
              Upload before/after photo
              <input type="file" className="hidden" onChange={(e) => e.target.files?.[0] && uploadMutation.mutate(e.target.files[0])} />
            </label>
          </div>
          <button onClick={() => completeMutation.mutate()} className="bg-indigo-600 text-white text-sm px-4 py-2 rounded-md">Mark Completed</button>
        </div>
      )}

      {canVerify && wo.status === "COMPLETED" && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-slate-700">Verification</h2>
          <p className="text-sm text-slate-600">{wo.completion_remarks}</p>
          <div className="flex gap-2">
            <button onClick={() => verifyMutation.mutate(true)} className="bg-emerald-600 text-white text-sm px-4 py-2 rounded-md">Verify &amp; Close</button>
            <button onClick={() => verifyMutation.mutate(false)} className="bg-red-600 text-white text-sm px-4 py-2 rounded-md">Reject</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-2">History</h2>
        <ul className="space-y-1">
          {history?.map((h) => (
            <li key={h.id} className="text-sm flex gap-2">
              <span className="text-slate-400 w-40 shrink-0">{new Date(h.created_at).toLocaleString()}</span>
              <span className="font-medium">{h.event}</span>
              {h.notes && <span className="text-slate-500">— {h.notes}</span>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
