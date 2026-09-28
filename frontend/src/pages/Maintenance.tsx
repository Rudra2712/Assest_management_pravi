import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createMaintenanceRequest, createWorkOrder, decideMaintenanceRequest, listMaintenanceRequests } from "../api/maintenance";
import { listAssets } from "../api/assets";
import { listContractors } from "../api/contractors";
import { useAuth } from "../hooks/useAuth";

const STATUS_COLORS: Record<string, string> = {
  OPEN: "bg-amber-100 text-amber-800",
  APPROVED: "bg-sky-100 text-sky-700",
  REJECTED: "bg-red-100 text-red-700",
  CONVERTED_TO_WORK_ORDER: "bg-emerald-100 text-emerald-700",
  CLOSED: "bg-slate-100 text-slate-600",
};

export default function Maintenance() {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [assetId, setAssetId] = useState("");
  const [type, setType] = useState("CORRECTIVE");
  const [priority, setPriority] = useState("MEDIUM");
  const [description, setDescription] = useState("");
  const [estimatedCost, setEstimatedCost] = useState("");

  const { data: requests, isLoading } = useQuery({ queryKey: ["maintenance-requests"], queryFn: () => listMaintenanceRequests({}) });
  const { data: assets } = useQuery({ queryKey: ["assets-for-maintenance"], queryFn: () => listAssets({ page_size: 200 }) });
  const { data: contractors } = useQuery({ queryKey: ["contractors"], queryFn: listContractors });

  const createMutation = useMutation({
    mutationFn: () =>
      createMaintenanceRequest({
        asset_id: assetId,
        maintenance_type: type,
        priority,
        description,
        estimated_cost: estimatedCost ? Number(estimatedCost) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["maintenance-requests"] });
      setShowCreate(false);
      setAssetId(""); setDescription(""); setEstimatedCost("");
    },
  });

  const decisionMutation = useMutation({
    mutationFn: ({ id, approve }: { id: string; approve: boolean }) => decideMaintenanceRequest(id, approve),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["maintenance-requests"] }),
  });

  const workOrderMutation = useMutation({
    mutationFn: ({ id, contractor_id }: { id: string; contractor_id?: string }) => createWorkOrder(id, { contractor_id }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["maintenance-requests"] }),
  });

  const canRequest = true;
  const canDecide = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN", "CIRCLE_DIVISION_OFFICER", "SUB_DIVISION_OFFICER");
  const canConvert = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN", "CIRCLE_DIVISION_OFFICER", "SUB_DIVISION_OFFICER", "MAINTENANCE_OFFICER");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Maintenance Requests</h1>
          <p className="text-sm text-slate-500">Preventive, corrective and emergency maintenance requests.</p>
        </div>
        {canRequest && (
          <button onClick={() => setShowCreate((s) => !s)} className="bg-rb-navy text-white text-sm font-medium px-4 py-2 rounded-md">
            + New Request
          </button>
        )}
      </div>

      {showCreate && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 grid grid-cols-5 gap-3 items-end">
          <select value={assetId} onChange={(e) => setAssetId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
            <option value="">Asset…</option>
            {assets?.items.map((a) => <option key={a.id} value={a.id}>{a.asset_code}</option>)}
          </select>
          <select value={type} onChange={(e) => setType(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
            {["PREVENTIVE", "CORRECTIVE", "EMERGENCY"].map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <select value={priority} onChange={(e) => setPriority(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
            {["LOW", "MEDIUM", "HIGH", "URGENT"].map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <input placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <input placeholder="Est. cost" type="number" value={estimatedCost} onChange={(e) => setEstimatedCost(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <button
            disabled={!assetId || !description || createMutation.isPending}
            onClick={() => createMutation.mutate()}
            className="bg-rb-teal text-white text-sm px-3 py-1.5 rounded-md disabled:opacity-50 col-span-5 w-fit"
          >
            Submit Request
          </button>
        </div>
      )}

      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-2">Description</th>
              <th className="text-left px-4 py-2">Type</th>
              <th className="text-left px-4 py-2">Priority</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400">Loading…</td></tr>}
            {requests?.map((r) => (
              <tr key={r.id} className="hover:bg-slate-50">
                <td className="px-4 py-2">{r.description}</td>
                <td className="px-4 py-2">{r.maintenance_type}</td>
                <td className="px-4 py-2">{r.priority}</td>
                <td className="px-4 py-2"><span className={`text-xs px-2 py-0.5 rounded ${STATUS_COLORS[r.status]}`}>{r.status.replaceAll("_", " ")}</span></td>
                <td className="px-4 py-2 space-x-2">
                  {canDecide && r.status === "OPEN" && (
                    <>
                      <button onClick={() => decisionMutation.mutate({ id: r.id, approve: true })} className="text-xs text-emerald-700 hover:underline">Approve</button>
                      <button onClick={() => decisionMutation.mutate({ id: r.id, approve: false })} className="text-xs text-red-700 hover:underline">Reject</button>
                    </>
                  )}
                  {canConvert && r.status === "APPROVED" && (
                    <select
                      onChange={(e) => e.target.value && workOrderMutation.mutate({ id: r.id, contractor_id: e.target.value })}
                      defaultValue=""
                      className="text-xs rounded border border-slate-300 px-1 py-0.5"
                    >
                      <option value="" disabled>Create work order with…</option>
                      {contractors?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  )}
                </td>
              </tr>
            ))}
            {!isLoading && !requests?.length && <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400">No maintenance requests.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
