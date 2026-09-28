import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listAssets } from "../api/assets";
import { listAssetTypes } from "../api/admin";
import { LifecycleBadge, ConditionBadge } from "../components/Badge";
import { useAuth } from "../hooks/useAuth";

const LIFECYCLE_OPTIONS = [
  "PLANNED", "SANCTIONED", "UNDER_CONSTRUCTION", "COMMISSIONED", "OPERATIONAL", "INSPECTION_REQUIRED",
  "MAINTENANCE_REQUIRED", "UNDER_MAINTENANCE", "RENOVATION_UPGRADATION", "RETIRED", "DECOMMISSIONED",
];
const CONDITION_OPTIONS = ["GOOD", "FAIR", "POOR", "CRITICAL"];

export default function AssetList() {
  const { hasRole } = useAuth();
  const [q, setQ] = useState("");
  const [assetType, setAssetType] = useState("");
  const [lifecycle, setLifecycle] = useState("");
  const [condition, setCondition] = useState("");
  const [page, setPage] = useState(1);

  const { data: assetTypes } = useQuery({ queryKey: ["asset-types"], queryFn: listAssetTypes });
  const { data, isLoading } = useQuery({
    queryKey: ["assets", q, assetType, lifecycle, condition, page],
    queryFn: () =>
      listAssets({
        q: q || undefined,
        asset_type_code: assetType || undefined,
        lifecycle_status: lifecycle || undefined,
        current_condition: condition || undefined,
        page,
        page_size: 20,
      }),
  });

  const canCreate = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Asset Registry</h1>
          <p className="text-sm text-slate-500">Search and manage roads, bridges, culverts, buildings and other fixed assets.</p>
        </div>
        {canCreate && (
          <Link to="/assets/new" className="bg-rb-navy text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-rb-navy/90">
            + Add Asset
          </Link>
        )}
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-4 grid grid-cols-1 md:grid-cols-4 gap-3">
        <input
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="Search by name or asset code…"
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
        />
        <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={assetType} onChange={(e) => { setAssetType(e.target.value); setPage(1); }}>
          <option value="">All types</option>
          {assetTypes?.map((t) => (
            <option key={t.code} value={t.code}>{t.name}</option>
          ))}
        </select>
        <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={lifecycle} onChange={(e) => { setLifecycle(e.target.value); setPage(1); }}>
          <option value="">All lifecycle statuses</option>
          {LIFECYCLE_OPTIONS.map((s) => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}
        </select>
        <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={condition} onChange={(e) => { setCondition(e.target.value); setPage(1); }}>
          <option value="">All conditions</option>
          {CONDITION_OPTIONS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-2">Asset Code</th>
              <th className="text-left px-4 py-2">Name</th>
              <th className="text-left px-4 py-2">Type</th>
              <th className="text-left px-4 py-2">Lifecycle</th>
              <th className="text-left px-4 py-2">Condition</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400">Loading…</td></tr>
            )}
            {!isLoading && data?.items.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400">No assets match your filters.</td></tr>
            )}
            {data?.items.map((a) => (
              <tr key={a.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-mono text-xs text-slate-600">{a.asset_code}</td>
                <td className="px-4 py-2">
                  <Link to={`/assets/${a.id}`} className="text-rb-navy font-medium hover:underline">{a.name}</Link>
                </td>
                <td className="px-4 py-2 text-slate-600">{a.asset_type_code}</td>
                <td className="px-4 py-2"><LifecycleBadge status={a.lifecycle_status} /></td>
                <td className="px-4 py-2"><ConditionBadge condition={a.current_condition} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data && data.pages > 1 && (
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span>Page {data.page} of {data.pages} ({data.total} assets)</span>
          <div className="space-x-2">
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1 rounded border border-slate-300 disabled:opacity-40">Previous</button>
            <button disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)} className="px-3 py-1 rounded border border-slate-300 disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
