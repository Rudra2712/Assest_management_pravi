import clsx from "clsx";

const LIFECYCLE_COLORS: Record<string, string> = {
  PLANNED: "bg-slate-100 text-slate-700",
  SANCTIONED: "bg-sky-100 text-sky-700",
  UNDER_CONSTRUCTION: "bg-amber-100 text-amber-800",
  COMMISSIONED: "bg-indigo-100 text-indigo-700",
  OPERATIONAL: "bg-emerald-100 text-emerald-700",
  INSPECTION_REQUIRED: "bg-amber-100 text-amber-800",
  MAINTENANCE_REQUIRED: "bg-orange-100 text-orange-800",
  UNDER_MAINTENANCE: "bg-orange-100 text-orange-800",
  RENOVATION_UPGRADATION: "bg-purple-100 text-purple-700",
  RETIRED: "bg-slate-200 text-slate-600",
  DECOMMISSIONED: "bg-slate-300 text-slate-700",
};

const CONDITION_COLORS: Record<string, string> = {
  GOOD: "bg-emerald-100 text-emerald-700",
  FAIR: "bg-amber-100 text-amber-800",
  POOR: "bg-orange-100 text-orange-800",
  CRITICAL: "bg-red-100 text-red-700",
  UNASSESSED: "bg-slate-100 text-slate-500",
};

export function LifecycleBadge({ status }: { status: string }) {
  return (
    <span className={clsx("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", LIFECYCLE_COLORS[status] ?? "bg-slate-100 text-slate-700")}>
      {status.replaceAll("_", " ")}
    </span>
  );
}

export function ConditionBadge({ condition }: { condition: string | null }) {
  const key = condition ?? "UNASSESSED";
  return (
    <span className={clsx("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", CONDITION_COLORS[key])}>
      {key}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    LOW: "bg-slate-100 text-slate-700",
    MEDIUM: "bg-amber-100 text-amber-800",
    HIGH: "bg-orange-100 text-orange-800",
    CRITICAL: "bg-red-100 text-red-700",
  };
  return <span className={clsx("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", colors[severity])}>{severity}</span>;
}
