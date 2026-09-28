import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { assignInspection, listInspections } from "../api/inspections";
import { listAssets } from "../api/assets";
import { listUsers } from "../api/admin";
import { ConditionBadge } from "../components/Badge";
import { useAuth } from "../hooks/useAuth";

export default function Inspections() {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [mineOnly, setMineOnly] = useState(hasRole("FIELD_ENGINEER"));
  const [showAssign, setShowAssign] = useState(false);
  const [assetId, setAssetId] = useState("");
  const [inspectorId, setInspectorId] = useState("");
  const [assignedDate, setAssignedDate] = useState("");

  const { data: inspections, isLoading } = useQuery({
    queryKey: ["inspections", mineOnly],
    queryFn: () => listInspections({ mine: mineOnly }),
  });
  const { data: assets } = useQuery({ queryKey: ["assets-for-assign"], queryFn: () => listAssets({ page_size: 200 }) });
  const { data: users } = useQuery({ queryKey: ["users-for-assign"], queryFn: listUsers, enabled: showAssign });

  const assignMutation = useMutation({
    mutationFn: () => assignInspection({ asset_id: assetId, inspector_id: inspectorId, assigned_date: assignedDate || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspections"] });
      setShowAssign(false);
      setAssetId("");
      setInspectorId("");
      setAssignedDate("");
    },
  });

  const canAssign = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Inspections</h1>
          <p className="text-sm text-slate-500">Field inspection assignments, submissions and supervisor review.</p>
        </div>
        {canAssign && (
          <button onClick={() => setShowAssign((s) => !s)} className="bg-rb-navy text-white text-sm font-medium px-4 py-2 rounded-md">
            + Assign Inspection
          </button>
        )}
      </div>

      {showAssign && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 grid grid-cols-4 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Asset</label>
            <select value={assetId} onChange={(e) => setAssetId(e.target.value)} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm">
              <option value="">Select asset…</option>
              {assets?.items.map((a) => <option key={a.id} value={a.id}>{a.asset_code} — {a.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Inspector</label>
            <select value={inspectorId} onChange={(e) => setInspectorId(e.target.value)} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm">
              <option value="">Select inspector…</option>
              {users?.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Assigned Date</label>
            <input type="date" value={assignedDate} onChange={(e) => setAssignedDate(e.target.value)} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          </div>
          <button
            disabled={!assetId || !inspectorId || assignMutation.isPending}
            onClick={() => assignMutation.mutate()}
            className="bg-rb-teal text-white text-sm px-3 py-1.5 rounded-md disabled:opacity-50"
          >
            Assign
          </button>
        </div>
      )}

      <label className="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" checked={mineOnly} onChange={(e) => setMineOnly(e.target.checked)} /> Show only my inspections
      </label>

      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-2">Assigned Date</th>
              <th className="text-left px-4 py-2">Inspection Date</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2">Condition</th>
              <th className="text-left px-4 py-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400">Loading…</td></tr>}
            {inspections?.map((i) => (
              <tr key={i.id} className="hover:bg-slate-50">
                <td className="px-4 py-2">{i.assigned_date ?? "—"}</td>
                <td className="px-4 py-2">{i.inspection_date ?? "—"}</td>
                <td className="px-4 py-2"><span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">{i.status}</span></td>
                <td className="px-4 py-2">{i.overall_condition ? <ConditionBadge condition={i.overall_condition} /> : "—"}</td>
                <td className="px-4 py-2"><Link to={`/inspections/${i.id}`} className="text-rb-navy hover:underline">Open →</Link></td>
              </tr>
            ))}
            {!isLoading && !inspections?.length && <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400">No inspections found.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
