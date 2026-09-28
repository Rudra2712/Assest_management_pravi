import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listAuditLogs } from "../api/audit";

export default function AuditLogs() {
  const [entityType, setEntityType] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs", entityType],
    queryFn: () => listAuditLogs({ entity_type: entityType || undefined }),
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Audit Logs</h1>
        <p className="text-sm text-slate-500">Immutable record of who changed what, when — for government accountability.</p>
      </div>
      <select value={entityType} onChange={(e) => setEntityType(e.target.value)} className="rounded-md border border-slate-300 px-3 py-2 text-sm">
        <option value="">All entity types</option>
        {["asset", "inspection", "maintenance_request", "work_order", "project", "contractor", "document", "user", "csv_import_batch"].map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="min-w-full text-xs">
          <thead className="bg-slate-50 text-slate-500 uppercase">
            <tr>
              <th className="text-left px-3 py-2">Timestamp</th>
              <th className="text-left px-3 py-2">Action</th>
              <th className="text-left px-3 py-2">Entity</th>
              <th className="text-left px-3 py-2">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && <tr><td colSpan={4} className="px-3 py-6 text-center text-slate-400">Loading…</td></tr>}
            {data?.map((entry) => (
              <tr key={entry.id}>
                <td className="px-3 py-2 whitespace-nowrap">{new Date(entry.created_at).toLocaleString()}</td>
                <td className="px-3 py-2 font-medium">{entry.action}</td>
                <td className="px-3 py-2">{entry.entity_type}</td>
                <td className="px-3 py-2 font-mono text-[11px] text-slate-500 max-w-md truncate" title={JSON.stringify(entry.new_value)}>
                  {JSON.stringify(entry.new_value)}
                </td>
              </tr>
            ))}
            {!isLoading && !data?.length && <tr><td colSpan={4} className="px-3 py-6 text-center text-slate-400">No audit entries.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
