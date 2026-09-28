export default function StatTile({ label, value, tone }: { label: string; value: string | number; tone?: "default" | "warn" | "critical" }) {
  const toneClass =
    tone === "critical" ? "text-red-600" : tone === "warn" ? "text-amber-600" : "text-slate-900";
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-semibold mt-1 ${toneClass}`}>{value}</div>
    </div>
  );
}
