import type { LucideIcon } from "lucide-react";
import { TrendingDown, TrendingUp } from "lucide-react";

type Tone = "brand" | "blue" | "amber" | "red" | "slate";

const TONE_STYLES: Record<Tone, { bg: string; text: string }> = {
  brand: { bg: "bg-brand-light", text: "text-brand-ink" },
  blue: { bg: "bg-blue-50", text: "text-blue-700" },
  amber: { bg: "bg-amber-50", text: "text-amber-700" },
  red: { bg: "bg-red-50", text: "text-red-700" },
  slate: { bg: "bg-slate-100", text: "text-slate-600" },
};

export default function StatTile({
  label,
  value,
  icon: Icon,
  tone = "brand",
  trend,
}: {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  tone?: Tone;
  /** Positive = up/good (shown in emerald), negative = down/attention (shown in red). */
  trend?: number;
}) {
  const toneStyle = TONE_STYLES[tone];

  return (
    <div className="kpi-card group relative overflow-hidden animate-fadeUp">
      <span className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-brand to-brand-dark opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="flex items-start justify-between">
        {Icon && (
          <div className={`w-11 h-11 rounded-[11px] flex items-center justify-center shrink-0 ${toneStyle.bg}`}>
            <Icon size={20} className={toneStyle.text} />
          </div>
        )}
        {trend !== undefined && (
          <span
            className={`inline-flex items-center gap-1 text-[0.72rem] font-bold px-2 py-0.5 rounded-full ${
              trend >= 0 ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
            }`}
          >
            {trend >= 0 ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
            {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div>
        <div className="text-[2rem] font-extrabold text-ink leading-none tracking-tight tabular-nums animate-countUp">{value}</div>
        <div className="text-[0.78rem] text-slate-500 font-medium mt-1.5">{label}</div>
      </div>
    </div>
  );
}
