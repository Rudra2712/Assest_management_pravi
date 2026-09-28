import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import {
  Building2,
  TriangleAlert,
  IndianRupee,
  Wrench,
  ClipboardCheck,
  CalendarClock,
  ClipboardList,
  Banknote,
} from "lucide-react";
import { fetchDashboard } from "../api/reports";
import StatTile from "../components/StatTile";

const CONDITION_COLORS: Record<string, string> = {
  GOOD: "#6ecfa3",
  FAIR: "#f59e0b",
  POOR: "#ea580c",
  CRITICAL: "#ef4444",
  UNASSESSED: "#94a3b8",
};

export default function Dashboard() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });

  if (isLoading || !data) {
    return <div className="text-slate-400 animate-pulse">Loading dashboard…</div>;
  }

  const typeData = Object.entries(data.assets_by_type).map(([name, value]) => ({ name, value }));
  const conditionData = Object.entries(data.assets_by_condition).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Asset inventory overview across your jurisdiction.</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile label="Total Assets" value={data.total_assets} icon={Building2} tone="brand" />
        <StatTile label="Critical Assets" value={data.critical_assets} icon={TriangleAlert} tone="red" />
        <StatTile label="Total Asset Value" value={`₹${(data.total_asset_value / 1e7).toFixed(2)} Cr`} icon={IndianRupee} tone="blue" />
        <StatTile label="Active Maintenance" value={data.active_maintenance} icon={Wrench} tone="amber" />
        <StatTile label="Inspections Overdue" value={data.inspections_overdue} icon={ClipboardCheck} tone={data.inspections_overdue > 0 ? "red" : "slate"} />
        <StatTile label="Inspections Due (7d)" value={data.inspections_due_soon} icon={CalendarClock} tone="slate" />
        <StatTile label="Work Orders Overdue" value={data.overdue_work_orders} icon={ClipboardList} tone={data.overdue_work_orders > 0 ? "red" : "slate"} />
        <StatTile label="Maintenance Expenditure" value={`₹${(data.maintenance_expenditure / 1e5).toFixed(2)} L`} icon={Banknote} tone="brand" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h2 className="text-sm font-bold text-ink mb-4">Assets by Type</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={typeData}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#6b7280" }} interval={0} angle={-20} textAnchor="end" height={60} axisLine={{ stroke: "#f0f0f0" }} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#6b7280" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #f0f0f0", fontSize: 12 }} cursor={{ fill: "#fafafa" }} />
              <Bar dataKey="value" fill="#6ecfa3" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h2 className="text-sm font-bold text-ink mb-4">Condition Distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={conditionData} dataKey="value" nameKey="name" outerRadius={90} label>
                {conditionData.map((entry) => (
                  <Cell key={entry.name} fill={CONDITION_COLORS[entry.name] ?? "#94a3b8"} />
                ))}
              </Pie>
              <Legend />
              <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #f0f0f0", fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 p-5">
        <h2 className="text-sm font-bold text-ink mb-4">Assets by Administrative Unit</h2>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={Object.entries(data.assets_by_administrative_unit).map(([name, value]) => ({ name, value }))}>
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#6b7280" }} interval={0} angle={-20} textAnchor="end" height={60} axisLine={{ stroke: "#f0f0f0" }} tickLine={false} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#6b7280" }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #f0f0f0", fontSize: 12 }} cursor={{ fill: "#fafafa" }} />
            <Bar dataKey="value" fill="#111827" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
