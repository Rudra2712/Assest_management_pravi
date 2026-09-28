import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { fetchDashboard } from "../api/reports";
import StatTile from "../components/StatTile";

const CONDITION_COLORS: Record<string, string> = {
  GOOD: "#059669",
  FAIR: "#d97706",
  POOR: "#ea580c",
  CRITICAL: "#dc2626",
  UNASSESSED: "#94a3b8",
};

export default function Dashboard() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });

  if (isLoading || !data) {
    return <div className="text-slate-500">Loading dashboard…</div>;
  }

  const typeData = Object.entries(data.assets_by_type).map(([name, value]) => ({ name, value }));
  const conditionData = Object.entries(data.assets_by_condition).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500">Asset inventory overview across your jurisdiction.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile label="Total Assets" value={data.total_assets} />
        <StatTile label="Critical Assets" value={data.critical_assets} tone="critical" />
        <StatTile label="Total Asset Value" value={`₹${(data.total_asset_value / 1e7).toFixed(2)} Cr`} />
        <StatTile label="Active Maintenance" value={data.active_maintenance} />
        <StatTile label="Inspections Overdue" value={data.inspections_overdue} tone={data.inspections_overdue > 0 ? "warn" : "default"} />
        <StatTile label="Inspections Due (7d)" value={data.inspections_due_soon} />
        <StatTile label="Work Orders Overdue" value={data.overdue_work_orders} tone={data.overdue_work_orders > 0 ? "critical" : "default"} />
        <StatTile label="Maintenance Expenditure" value={`₹${(data.maintenance_expenditure / 1e5).toFixed(2)} L`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Assets by Type</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={typeData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#0f766e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Condition Distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={conditionData} dataKey="value" nameKey="name" outerRadius={90} label>
                {conditionData.map((entry) => (
                  <Cell key={entry.name} fill={CONDITION_COLORS[entry.name] ?? "#94a3b8"} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">Assets by Administrative Unit</h2>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={Object.entries(data.assets_by_administrative_unit).map(([name, value]) => ({ name, value }))}>
            <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="value" fill="#0b3d63" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
