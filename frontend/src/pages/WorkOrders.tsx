import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listWorkOrders } from "../api/maintenance";

const STATUS_COLORS: Record<string, string> = {
  CREATED: "bg-slate-100 text-slate-600",
  ASSIGNED: "bg-sky-100 text-sky-700",
  IN_PROGRESS: "bg-amber-100 text-amber-800",
  COMPLETED: "bg-indigo-100 text-indigo-700",
  VERIFIED: "bg-emerald-100 text-emerald-700",
  CLOSED: "bg-emerald-100 text-emerald-700",
  CANCELLED: "bg-red-100 text-red-700",
};

export default function WorkOrders() {
  const { data, isLoading } = useQuery({ queryKey: ["work-orders"], queryFn: () => listWorkOrders({}) });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Work Orders</h1>
        <p className="text-sm text-slate-500">Assignment, execution and verification of maintenance work.</p>
      </div>
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-2">Work Order</th>
              <th className="text-left px-4 py-2">Priority</th>
              <th className="text-left px-4 py-2">SLA Due</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400">Loading…</td></tr>}
            {data?.map((w) => (
              <tr key={w.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-mono text-xs">{w.work_order_code}</td>
                <td className="px-4 py-2">{w.priority}</td>
                <td className="px-4 py-2">{w.sla_due_date ?? "—"}</td>
                <td className="px-4 py-2"><span className={`text-xs px-2 py-0.5 rounded ${STATUS_COLORS[w.status]}`}>{w.status}</span></td>
                <td className="px-4 py-2"><Link to={`/work-orders/${w.id}`} className="text-rb-navy hover:underline">Open →</Link></td>
              </tr>
            ))}
            {!isLoading && !data?.length && <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400">No work orders.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
