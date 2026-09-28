import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getInspection, reviewInspection, submitInspection } from "../api/inspections";
import { getAsset } from "../api/assets";
import { listDocuments, uploadDocument } from "../api/documents";
import { ConditionBadge, SeverityBadge } from "../components/Badge";
import { useAuth } from "../hooks/useAuth";
import type { FindingSeverity } from "../types";

interface DraftFinding {
  description: string;
  severity: FindingSeverity;
  recommends_maintenance: boolean;
}

export default function InspectionDetail() {
  const { id } = useParams<{ id: string }>();
  const { user, hasRole } = useAuth();
  const queryClient = useQueryClient();

  const { data: inspection, isLoading } = useQuery({ queryKey: ["inspection", id], queryFn: () => getInspection(id!), enabled: !!id });
  const { data: asset } = useQuery({ queryKey: ["asset", inspection?.asset_id], queryFn: () => getAsset(inspection!.asset_id), enabled: !!inspection });
  const { data: documents } = useQuery({ queryKey: ["inspection-documents", id], queryFn: () => listDocuments("inspection", id!), enabled: !!id });

  const [inspectionDate, setInspectionDate] = useState(new Date().toISOString().slice(0, 10));
  const [overallCondition, setOverallCondition] = useState("GOOD");
  const [remarks, setRemarks] = useState("");
  const [gps, setGps] = useState<{ lat: number; lon: number } | null>(null);
  const [findings, setFindings] = useState<DraftFinding[]>([]);
  const [reviewComments, setReviewComments] = useState("");

  const submitMutation = useMutation({
    mutationFn: () =>
      submitInspection(id!, {
        inspection_date: inspectionDate,
        overall_condition: overallCondition,
        remarks,
        gps_lat: gps?.lat,
        gps_lon: gps?.lon,
        findings,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspection", id] });
      queryClient.invalidateQueries({ queryKey: ["inspections"] });
    },
  });

  const reviewMutation = useMutation({
    mutationFn: (approve: boolean) => reviewInspection(id!, approve, reviewComments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspection", id] });
      queryClient.invalidateQueries({ queryKey: ["inspections"] });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument("PHOTOGRAPH", "inspection", id!, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inspection-documents", id] }),
  });

  function captureGps() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((pos) => setGps({ lat: pos.coords.latitude, lon: pos.coords.longitude }));
  }

  if (isLoading || !inspection) return <div className="text-slate-500">Loading…</div>;

  const canSubmit = inspection.inspector_id === user?.id && ["ASSIGNED", "IN_PROGRESS", "RETURNED"].includes(inspection.status);
  const canReview = inspection.status === "SUBMITTED" && hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN");

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Inspection — {asset?.name ?? "…"}</h1>
        <div className="text-sm text-slate-500">{asset?.asset_code} · Status: <span className="font-medium">{inspection.status}</span></div>
      </div>

      {inspection.status !== "ASSIGNED" && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-2">
          <h2 className="text-sm font-semibold text-slate-700">Submitted Findings</h2>
          {inspection.overall_condition && <ConditionBadge condition={inspection.overall_condition} />}
          <p className="text-sm text-slate-600">{inspection.remarks}</p>
          <ul className="space-y-1">
            {inspection.findings.map((f) => (
              <li key={f.id} className="text-sm flex gap-2 items-center">
                <SeverityBadge severity={f.severity} /> {f.description} {f.recommends_maintenance && <span className="text-xs text-amber-700">(recommends maintenance)</span>}
              </li>
            ))}
          </ul>
          {inspection.review_comments && <p className="text-xs text-slate-500 italic">Reviewer: {inspection.review_comments}</p>}
        </div>
      )}

      {canSubmit && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">Submit Inspection</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Inspection Date</label>
              <input type="date" value={inspectionDate} onChange={(e) => setInspectionDate(e.target.value)} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Overall Condition</label>
              <select value={overallCondition} onChange={(e) => setOverallCondition(e.target.value)} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm">
                {["GOOD", "FAIR", "POOR", "CRITICAL"].map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Remarks</label>
            <textarea value={remarks} onChange={(e) => setRemarks(e.target.value)} rows={2} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          </div>

          <div>
            <button type="button" onClick={captureGps} className="text-xs text-rb-teal hover:underline">
              {gps ? `GPS captured: ${gps.lat.toFixed(5)}, ${gps.lon.toFixed(5)}` : "Capture GPS location"}
            </button>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-600">Findings / Defects</label>
              <button
                type="button"
                onClick={() => setFindings((f) => [...f, { description: "", severity: "LOW", recommends_maintenance: false }])}
                className="text-xs text-rb-teal hover:underline"
              >
                + Add finding
              </button>
            </div>
            {findings.map((f, idx) => (
              <div key={idx} className="grid grid-cols-6 gap-2 mb-2 items-center">
                <input
                  className="col-span-3 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                  placeholder="Description"
                  value={f.description}
                  onChange={(e) => setFindings((arr) => arr.map((x, i) => (i === idx ? { ...x, description: e.target.value } : x)))}
                />
                <select
                  className="col-span-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                  value={f.severity}
                  onChange={(e) => setFindings((arr) => arr.map((x, i) => (i === idx ? { ...x, severity: e.target.value as FindingSeverity } : x)))}
                >
                  {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <label className="col-span-1 flex items-center gap-1 text-xs">
                  <input
                    type="checkbox"
                    checked={f.recommends_maintenance}
                    onChange={(e) => setFindings((arr) => arr.map((x, i) => (i === idx ? { ...x, recommends_maintenance: e.target.checked } : x)))}
                  />
                  Maintenance
                </label>
                <button type="button" onClick={() => setFindings((arr) => arr.filter((_, i) => i !== idx))} className="col-span-1 text-xs text-red-600">Remove</button>
              </div>
            ))}
          </div>

          <div>
            <label className="text-xs font-medium text-slate-600 mb-1 block">Photos</label>
            <input type="file" accept="image/*" onChange={(e) => e.target.files?.[0] && uploadMutation.mutate(e.target.files[0])} />
            <ul className="mt-1 text-xs text-slate-500">
              {documents?.map((d) => <li key={d.id}>{d.filename}</li>)}
            </ul>
          </div>

          <button
            disabled={submitMutation.isPending}
            onClick={() => submitMutation.mutate()}
            className="bg-rb-navy text-white text-sm px-4 py-2 rounded-md disabled:opacity-50"
          >
            {submitMutation.isPending ? "Submitting…" : "Submit Inspection"}
          </button>
        </div>
      )}

      {canReview && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-slate-700">Supervisor Review</h2>
          <textarea value={reviewComments} onChange={(e) => setReviewComments(e.target.value)} rows={2} placeholder="Comments" className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <div className="flex gap-2">
            <button onClick={() => reviewMutation.mutate(true)} className="bg-emerald-600 text-white text-sm px-4 py-2 rounded-md">Approve</button>
            <button onClick={() => reviewMutation.mutate(false)} className="bg-red-600 text-white text-sm px-4 py-2 rounded-md">Return</button>
          </div>
        </div>
      )}
    </div>
  );
}
