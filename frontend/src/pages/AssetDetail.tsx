import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import * as turf from "@turf/turf";
import { TriangleAlert } from "lucide-react";
import { getAsset, getLifecycleHistory, transitionLifecycle } from "../api/assets";
import { listInspections } from "../api/inspections";
import { listMaintenanceRequests, listWorkOrders } from "../api/maintenance";
import { listDocuments, uploadDocument } from "../api/documents";
import { listGrievances } from "../api/grievances";
import { api } from "../api/client";
import { LifecycleBadge, ConditionBadge, SeverityBadge, GrievanceStatusBadge } from "../components/Badge";
import AssetMiniMap from "../components/AssetMiniMap";
import { useAuth } from "../hooks/useAuth";
import type { GeoJSONGeometry, LifecycleStatus } from "../types";

function formatCoord([lon, lat]: [number, number]): string {
  return `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
}

function useGpsInfo(geometry: GeoJSONGeometry | null) {
  return useMemo(() => {
    if (!geometry) return null;
    if (geometry.type === "Point") {
      const coord = geometry.coordinates as [number, number];
      return { kind: "point" as const, point: coord };
    }
    if (geometry.type === "LineString") {
      const coords = geometry.coordinates as [number, number][];
      const lengthKm = turf.length(turf.lineString(coords), { units: "kilometers" });
      return { kind: "line" as const, start: coords[0], end: coords[coords.length - 1], lengthKm };
    }
    const centroid = turf.centroid(turf.polygon(geometry.coordinates as number[][][])).geometry.coordinates as [number, number];
    const areaSqm = turf.area(turf.polygon(geometry.coordinates as number[][][]));
    return { kind: "polygon" as const, centroid, areaSqm };
  }, [geometry]);
}

const NEXT_STATUS_HINTS: Record<string, LifecycleStatus[]> = {
  PLANNED: ["SANCTIONED"],
  SANCTIONED: ["UNDER_CONSTRUCTION"],
  UNDER_CONSTRUCTION: ["COMMISSIONED"],
  COMMISSIONED: ["OPERATIONAL"],
  OPERATIONAL: ["INSPECTION_REQUIRED", "MAINTENANCE_REQUIRED", "RENOVATION_UPGRADATION", "RETIRED"],
  INSPECTION_REQUIRED: ["OPERATIONAL", "MAINTENANCE_REQUIRED"],
  MAINTENANCE_REQUIRED: ["UNDER_MAINTENANCE"],
  UNDER_MAINTENANCE: ["OPERATIONAL"],
  RENOVATION_UPGRADATION: ["OPERATIONAL"],
  RETIRED: ["DECOMMISSIONED"],
  DECOMMISSIONED: [],
};

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between py-1.5 border-b border-slate-100 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-900 font-medium">{value ?? "—"}</span>
    </div>
  );
}

export default function AssetDetail() {
  const { id } = useParams<{ id: string }>();
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [reason, setReason] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");

  const { data: asset, isLoading } = useQuery({ queryKey: ["asset", id], queryFn: () => getAsset(id!), enabled: !!id });
  const { data: history } = useQuery({ queryKey: ["asset-lifecycle", id], queryFn: () => getLifecycleHistory(id!), enabled: !!id });
  const { data: inspections } = useQuery({ queryKey: ["asset-inspections", id], queryFn: () => listInspections({ asset_id: id }), enabled: !!id });
  const { data: maintenanceRequests } = useQuery({ queryKey: ["asset-maintenance", id], queryFn: () => listMaintenanceRequests({ asset_id: id }), enabled: !!id });
  const { data: workOrders } = useQuery({ queryKey: ["asset-work-orders", id], queryFn: () => listWorkOrders({ asset_id: id }), enabled: !!id });
  const { data: documents } = useQuery({ queryKey: ["asset-documents", id], queryFn: () => listDocuments("asset", id!), enabled: !!id });
  const { data: grievances } = useQuery({ queryKey: ["asset-grievances", id], queryFn: () => listGrievances({ asset_id: id }), enabled: !!id });

  const gps = useGpsInfo(asset?.geometry ?? null);

  const transitionMutation = useMutation({
    mutationFn: () => transitionLifecycle(id!, selectedStatus as LifecycleStatus, reason || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["asset", id] });
      queryClient.invalidateQueries({ queryKey: ["asset-lifecycle", id] });
      setReason("");
      setSelectedStatus("");
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument("OTHER", "asset", id!, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["asset-documents", id] }),
  });

  async function downloadDoc(docId: string, filename: string) {
    const res = await api.get(`/documents/${docId}/download`, { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (isLoading || !asset) return <div className="text-slate-500">Loading asset…</div>;

  const canEdit = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN");
  const nextOptions = NEXT_STATUS_HINTS[asset.lifecycle_status] ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-mono text-slate-500">{asset.asset_code}</div>
          <h1 className="text-xl font-semibold text-slate-900">{asset.name}</h1>
          <div className="flex gap-2 mt-2">
            <LifecycleBadge status={asset.lifecycle_status} />
            <ConditionBadge condition={asset.current_condition} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <section className="bg-white rounded-lg border border-slate-200 p-4">
            <h2 className="text-sm font-semibold text-slate-700 mb-2">Identity &amp; Location</h2>
            <DetailRow label="Ownership" value={asset.ownership} />
            <DetailRow label="Address" value={asset.address} />
            <DetailRow label="Acquisition Date" value={asset.acquisition_date} />
            <DetailRow label="Commissioning Date" value={asset.commissioning_date} />
            <DetailRow label="Original Cost" value={asset.original_cost ? `₹${asset.original_cost.toLocaleString()}` : null} />
            <DetailRow label="Current Value" value={asset.current_value ? `₹${asset.current_value.toLocaleString()}` : null} />
            <DetailRow label="Useful Life" value={asset.useful_life_years ? `${asset.useful_life_years} years` : null} />
            <DetailRow label="Expected End of Life" value={asset.expected_end_of_life} />
          </section>

          {(asset.road || asset.bridge || asset.culvert || asset.building || asset.structure) && (
            <section className="bg-white rounded-lg border border-slate-200 p-4">
              <h2 className="text-sm font-semibold text-slate-700 mb-2">{asset.asset_type_code.replaceAll("_", " ")} Details</h2>
              {Object.entries(asset.road ?? asset.bridge ?? asset.culvert ?? asset.building ?? asset.structure ?? {}).map(([k, v]) => (
                <DetailRow key={k} label={k.replaceAll("_", " ")} value={v == null ? null : typeof v === "object" ? JSON.stringify(v) : String(v)} />
              ))}
            </section>
          )}

          <section className="bg-white rounded-lg border border-slate-200 p-4">
            <h2 className="text-sm font-semibold text-slate-700 mb-2">Lifecycle History</h2>
            {canEdit && nextOptions.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3 items-center">
                <select value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
                  <option value="">Transition to…</option>
                  {nextOptions.map((s) => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}
                </select>
                <input
                  placeholder="Reason (optional)"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="rounded-md border border-slate-300 px-2 py-1.5 text-sm flex-1 min-w-[160px]"
                />
                <button
                  disabled={!selectedStatus || transitionMutation.isPending}
                  onClick={() => transitionMutation.mutate()}
                  className="bg-rb-navy text-white text-sm px-3 py-1.5 rounded-md disabled:opacity-50"
                >
                  Apply
                </button>
              </div>
            )}
            <ul className="space-y-2">
              {history?.map((h) => (
                <li key={h.id} className="text-sm flex items-center gap-2">
                  <span className="text-slate-400 w-40 shrink-0">{new Date(h.created_at).toLocaleString()}</span>
                  <span className="text-slate-500">{h.old_status ?? "—"}</span>
                  <span>→</span>
                  <LifecycleBadge status={h.new_status} />
                  {h.reason && <span className="text-slate-500 italic">"{h.reason}"</span>}
                </li>
              ))}
              {!history?.length && <li className="text-sm text-slate-400">No lifecycle events yet.</li>}
            </ul>
          </section>

          <section className="bg-white rounded-lg border border-slate-200 p-4">
            <h2 className="text-sm font-semibold text-slate-700 mb-2">Inspections</h2>
            <ul className="space-y-2">
              {inspections?.map((i) => (
                <li key={i.id} className="text-sm border-b border-slate-100 pb-2">
                  <div className="flex justify-between">
                    <span>{i.inspection_date ?? `Assigned ${i.assigned_date ?? ""}`}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">{i.status}</span>
                  </div>
                  {i.overall_condition && <ConditionBadge condition={i.overall_condition} />}
                  {i.findings.length > 0 && (
                    <ul className="mt-1 space-y-1">
                      {i.findings.map((f) => (
                        <li key={f.id} className="text-xs text-slate-600 flex gap-2 items-center">
                          <SeverityBadge severity={f.severity} /> {f.description}
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
              {!inspections?.length && <li className="text-sm text-slate-400">No inspections recorded.</li>}
            </ul>
          </section>

          <section className="bg-white rounded-lg border border-slate-200 p-4">
            <h2 className="text-sm font-semibold text-slate-700 mb-2">Maintenance &amp; Work Orders</h2>
            <ul className="space-y-2">
              {maintenanceRequests?.map((r) => (
                <li key={r.id} className="text-sm border-b border-slate-100 pb-2">
                  <div className="flex justify-between">
                    <span>{r.maintenance_type} — {r.description}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">{r.status}</span>
                  </div>
                </li>
              ))}
              {!maintenanceRequests?.length && <li className="text-sm text-slate-400">No maintenance requests.</li>}
            </ul>
            {!!workOrders?.length && (
              <>
                <div className="text-xs font-semibold text-slate-500 mt-3 mb-1">Work Orders</div>
                <ul className="space-y-1">
                  {workOrders.map((w) => (
                    <li key={w.id} className="text-sm flex justify-between">
                      <span className="font-mono text-xs">{w.work_order_code}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">{w.status}</span>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </section>

          <section className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-semibold text-slate-700">Documents</h2>
              <label className="text-xs text-rb-teal cursor-pointer hover:underline">
                Upload
                <input type="file" className="hidden" onChange={(e) => e.target.files?.[0] && uploadMutation.mutate(e.target.files[0])} />
              </label>
            </div>
            <ul className="space-y-1">
              {documents?.map((d) => (
                <li key={d.id} className="text-sm flex justify-between items-center">
                  <span>{d.filename} <span className="text-xs text-slate-400">v{d.current_version}</span></span>
                  <button onClick={() => downloadDoc(d.id, d.filename)} className="text-xs text-rb-navy hover:underline">Download</button>
                </li>
              ))}
              {!documents?.length && <li className="text-sm text-slate-400">No documents uploaded.</li>}
            </ul>
          </section>
        </div>

        <div className="space-y-6">
          {asset.geometry && (
            <section className="bg-white rounded-lg border border-slate-200 p-4">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-sm font-semibold text-slate-700">Location</h2>
                <Link to={`/report?asset_id=${asset.id}`} className="text-xs text-orange-600 hover:underline flex items-center gap-1">
                  <TriangleAlert size={12} /> Report an issue
                </Link>
              </div>
              <AssetMiniMap geometry={asset.geometry} />

              {gps?.kind === "line" && (
                <div className="mt-3 text-sm space-y-1">
                  <DetailRow label="Start (GPS)" value={<span className="font-mono text-xs">{formatCoord(gps.start)}</span>} />
                  <DetailRow label="End (GPS)" value={<span className="font-mono text-xs">{formatCoord(gps.end)}</span>} />
                  <DetailRow label="Measured Length" value={`${gps.lengthKm.toFixed(2)} km`} />
                </div>
              )}
              {gps?.kind === "point" && (
                <div className="mt-3 text-sm">
                  <DetailRow label="GPS Coordinates" value={<span className="font-mono text-xs">{formatCoord(gps.point)}</span>} />
                </div>
              )}
              {gps?.kind === "polygon" && (
                <div className="mt-3 text-sm space-y-1">
                  <DetailRow label="Centroid (GPS)" value={<span className="font-mono text-xs">{formatCoord(gps.centroid)}</span>} />
                  <DetailRow label="Footprint Area" value={`${gps.areaSqm.toLocaleString(undefined, { maximumFractionDigits: 0 })} m²`} />
                </div>
              )}
            </section>
          )}

          <section className="bg-white rounded-lg border border-slate-200 p-4">
            <h2 className="text-sm font-semibold text-slate-700 mb-2">Grievances</h2>
            <ul className="space-y-2">
              {grievances?.map((g) => (
                <li key={g.id} className="text-sm border-b border-slate-100 pb-2">
                  <div className="flex justify-between items-start gap-2">
                    <span className="font-medium text-slate-800">{g.title}</span>
                    <GrievanceStatusBadge status={g.status} />
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">{g.category.replaceAll("_", " ")} · <SeverityBadge severity={g.severity} /></div>
                </li>
              ))}
              {!grievances?.length && <li className="text-sm text-slate-400">No grievances reported for this asset.</li>}
            </ul>
            <Link to="/grievances" className="text-xs text-rb-navy hover:underline mt-2 inline-block">View all grievances →</Link>
          </section>
        </div>
      </div>
    </div>
  );
}
