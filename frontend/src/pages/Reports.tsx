import { useQuery } from "@tanstack/react-query";
import { fetchDashboard } from "../api/reports";
import StatTile from "../components/StatTile";

export default function Reports() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });

  if (isLoading || !data) return <div className="text-slate-500">Loading reports…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Reports &amp; Analytics</h1>
        <p className="text-sm text-slate-500">Lifecycle distribution, maintenance expenditure and project progress.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile label="Projects In Progress" value={data.projects_in_progress} />
        <StatTile label="Projects Completed" value={data.projects_completed} />
        <StatTile label="Maintenance Expenditure" value={`₹${(data.maintenance_expenditure / 1e5).toFixed(2)} L`} />
        <StatTile label="Total Asset Value" value={`₹${(data.total_asset_value / 1e7).toFixed(2)} Cr`} />
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">Lifecycle Status Distribution</h2>
        <table className="min-w-full text-sm">
          <tbody className="divide-y divide-slate-100">
            {Object.entries(data.assets_by_lifecycle_status).map(([status, count]) => (
              <tr key={status}>
                <td className="py-1.5 text-slate-600">{status.replaceAll("_", " ")}</td>
                <td className="py-1.5 text-right font-medium">{count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">Assets by Administrative Unit</h2>
        <table className="min-w-full text-sm">
          <tbody className="divide-y divide-slate-100">
            {Object.entries(data.assets_by_administrative_unit).map(([unit, count]) => (
              <tr key={unit}>
                <td className="py-1.5 text-slate-600">{unit}</td>
                <td className="py-1.5 text-right font-medium">{count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
