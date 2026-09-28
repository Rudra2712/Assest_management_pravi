import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { TriangleAlert, Wrench } from "lucide-react";
import {
  convertGrievanceToMaintenance,
  grievancePhotoUrl,
  listGrievances,
  updateGrievanceStatus,
} from "../api/grievances";
import { getAsset } from "../api/assets";
import { GrievanceStatusBadge, SeverityBadge } from "../components/Badge";
import { useAuth } from "../hooks/useAuth";
import { api, API_BASE_URL } from "../api/client";
import type { Grievance } from "../types";

const API_BASE = API_BASE_URL;
const STATUS_OPTIONS = ["OPEN", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED", "REJECTED"];
const NEXT_STATUS: Record<string, string[]> = {
  OPEN: ["ACKNOWLEDGED", "IN_PROGRESS", "REJECTED"],
  ACKNOWLEDGED: ["IN_PROGRESS", "REJECTED"],
  IN_PROGRESS: ["RESOLVED", "REJECTED"],
};
const CATEGORY_OPTIONS = ["", "STRUCTURAL_DAMAGE", "POTHOLE", "WATER_LOGGING", "TREE_HAZARD", "ENCROACHMENT", "SAFETY_HAZARD", "ELECTRICAL_HAZARD", "OTHER"];

function GrievanceCard({ g }: { g: Grievance }) {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const [expanded, setExpanded] = useState(false);
  const [nextStatus, setNextStatus] = useState("");
  const [notes, setNotes] = useState("");
  const { data: asset } = useQuery({ queryKey: ["asset", g.asset_id], queryFn: () => getAsset(g.asset_id!), enabled: expanded && !!g.asset_id });

  const statusMutation = useMutation({
    mutationFn: (status: string) => updateGrievanceStatus(g.id, status, notes || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grievances"] });
      setNextStatus("");
      setNotes("");
    },
  });
  const convertMutation = useMutation({
    mutationFn: () => convertGrievanceToMaintenance(g.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grievances"] });
      queryClient.invalidateQueries({ queryKey: ["maintenance-requests"] });
    },
  });

  const canTriage = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN", "FIELD_ENGINEER", "MAINTENANCE_OFFICER");
  const isOpen = !["RESOLVED", "REJECTED"].includes(g.status);
  const needsNotes = nextStatus === "RESOLVED" || nextStatus === "REJECTED";

  return (
    <article className="rounded-md border border-slate-200 bg-white px-4 py-3">
      <div className="flex items-start gap-3">
        <TriangleAlert size={16} className="mt-1 shrink-0 text-orange-600" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-500">
            <span className="font-mono">{g.grievance_code}</span>
            <span>{new Date(g.created_at).toLocaleDateString()}</span>
            <span className="rounded bg-slate-100 px-1.5 py-0.5">{g.category.replaceAll("_", " ")}</span>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <h2 className="min-w-0 flex-1 text-sm font-semibold text-slate-900">{g.title}</h2>
            <GrievanceStatusBadge status={g.status} />
            <SeverityBadge severity={g.severity} />
          </div>
          <p className="mt-1 line-clamp-1 text-sm text-slate-600">{g.description}</p>
        </div>
        <button type="button" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)} className="shrink-0 rounded border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50">
          {expanded ? "Hide details" : "Review"}
        </button>
      </div>

      {expanded && (
        <div className="ml-7 mt-3 space-y-3 border-t border-slate-100 pt-3">
          <p className="whitespace-pre-wrap text-sm text-slate-700">{g.description}</p>
          {g.has_photo && <img src={grievancePhotoUrl(g.id, API_BASE)} alt="Reported issue" className="h-20 w-28 rounded border border-slate-200 object-cover" />}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
            {asset && <Link to={`/assets/${asset.id}`} className="font-medium text-brand-ink hover:underline">{asset.asset_code} · {asset.name}</Link>}
            {g.reporter_name && <span>Reported by {g.reporter_name}</span>}
            {g.reporter_contact && <span>{g.reporter_contact}</span>}
          </div>
          {g.resolution_notes && <p className="rounded bg-emerald-50 px-3 py-2 text-sm text-emerald-800">Resolution: {g.resolution_notes}</p>}

          {canTriage && isOpen && (
            <div className="flex flex-wrap items-end gap-2 border-t border-slate-100 pt-3">
              <label className="min-w-48 flex-1 text-xs font-medium text-slate-600">
                Update status
                <select value={nextStatus} onChange={(e) => setNextStatus(e.target.value)} className="mt-1 block w-full rounded border border-slate-300 bg-white px-2 py-2 text-sm">
                  <option value="">Choose status…</option>
                  {(NEXT_STATUS[g.status] ?? []).map((status) => <option key={status} value={status}>{status.replaceAll("_", " ")}</option>)}
                </select>
              </label>
              {needsNotes && <label className="min-w-48 flex-1 text-xs font-medium text-slate-600">Resolution notes<input required value={notes} onChange={(e) => setNotes(e.target.value)} className="mt-1 block w-full rounded border border-slate-300 px-2 py-2 text-sm" /></label>}
              <button onClick={() => statusMutation.mutate(nextStatus)} disabled={!nextStatus || (needsNotes && !notes.trim()) || statusMutation.isPending} className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-40">
                {statusMutation.isPending ? "Saving…" : "Save status"}
              </button>
              {g.asset_id && !g.linked_maintenance_request_id && <button onClick={() => convertMutation.mutate()} disabled={convertMutation.isPending} className="flex items-center gap-1 rounded border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40"><Wrench size={14} /> Convert to maintenance</button>}
              {g.linked_maintenance_request_id && <span className="flex items-center gap-1 text-sm text-emerald-700"><Wrench size={14} /> Maintenance request created</span>}
            </div>
          )}
          {statusMutation.isError && <p role="alert" className="text-sm text-red-700">Could not update grievance. Refresh and try again.</p>}
          {convertMutation.isError && <p role="alert" className="text-sm text-red-700">Could not create a maintenance request.</p>}
        </div>
      )}
    </article>
  );
}

export default function Grievances() {
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const { data: grievances, isLoading } = useQuery({
    queryKey: ["grievances", status, category],
    queryFn: () => listGrievances({ status: status || undefined, category: category || undefined }),
  });

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Grievances</h1>
          <p className="page-subtitle">Citizen and field-reported defects — potholes, structural damage, hazards — triaged and resolved here.</p>
        </div>
        <Link to="/report" target="_blank" className="bg-orange-600 text-white text-sm font-semibold px-4 py-2 rounded-md hover:bg-orange-700 h-fit">
          + File a Grievance
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="rounded-md border border-slate-200 px-3 py-2 text-sm bg-white">
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}
        </select>
        <select value={category} onChange={(e) => setCategory(e.target.value)} className="rounded-md border border-slate-200 px-3 py-2 text-sm bg-white">
          {CATEGORY_OPTIONS.map((c) => <option key={c} value={c}>{c ? c.replaceAll("_", " ") : "All categories"}</option>)}
        </select>
        <span className="ml-auto text-sm text-slate-500">{grievances?.length ?? 0} reports</span>
      </div>

      <div className="space-y-2">
        {isLoading && <div className="py-8 text-center text-sm text-slate-400">Loading grievances…</div>}
        {grievances?.map((g) => <GrievanceCard key={g.id} g={g} />)}
        {!isLoading && !grievances?.length && <div className="rounded-md border border-dashed border-slate-300 py-10 text-center text-sm text-slate-500">No grievances match these filters.</div>}
      </div>
    </div>
  );
}
