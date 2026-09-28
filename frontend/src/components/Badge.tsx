import clsx from "clsx";

const PILL = "inline-flex items-center rounded-full px-2.5 py-0.5 text-[0.72rem] font-bold whitespace-nowrap";

const LIFECYCLE_COLORS: Record<string, string> = {
  PLANNED: "bg-slate-100 text-slate-600",
  SANCTIONED: "bg-blue-50 text-blue-700",
  UNDER_CONSTRUCTION: "bg-amber-50 text-amber-700",
  COMMISSIONED: "bg-indigo-50 text-indigo-700",
  OPERATIONAL: "bg-emerald-50 text-emerald-700",
  INSPECTION_REQUIRED: "bg-amber-50 text-amber-700",
  MAINTENANCE_REQUIRED: "bg-orange-50 text-orange-700",
  UNDER_MAINTENANCE: "bg-orange-50 text-orange-700",
  RENOVATION_UPGRADATION: "bg-purple-50 text-purple-700",
  RETIRED: "bg-slate-100 text-slate-600",
  DECOMMISSIONED: "bg-slate-200 text-slate-700",
};

const CONDITION_COLORS: Record<string, string> = {
  GOOD: "bg-emerald-50 text-emerald-700",
  FAIR: "bg-amber-50 text-amber-700",
  POOR: "bg-orange-50 text-orange-700",
  CRITICAL: "bg-red-50 text-red-700",
  UNASSESSED: "bg-slate-100 text-slate-500",
};

export function LifecycleBadge({ status }: { status: string }) {
  return (
    <span className={clsx(PILL, LIFECYCLE_COLORS[status] ?? "bg-slate-100 text-slate-600")}>
      {status.replaceAll("_", " ")}
    </span>
  );
}

export function ConditionBadge({ condition }: { condition: string | null }) {
  const key = condition ?? "UNASSESSED";
  return <span className={clsx(PILL, CONDITION_COLORS[key])}>{key}</span>;
}

export function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    LOW: "bg-slate-100 text-slate-600",
    MEDIUM: "bg-amber-50 text-amber-700",
    HIGH: "bg-orange-50 text-orange-700",
    CRITICAL: "bg-red-50 text-red-700",
  };
  return <span className={clsx(PILL, colors[severity])}>{severity}</span>;
}

const GRIEVANCE_STATUS_COLORS: Record<string, string> = {
  OPEN: "bg-red-50 text-red-700",
  ACKNOWLEDGED: "bg-amber-50 text-amber-700",
  IN_PROGRESS: "bg-blue-50 text-blue-700",
  RESOLVED: "bg-emerald-50 text-emerald-700",
  REJECTED: "bg-slate-100 text-slate-600",
};

export function GrievanceStatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx(PILL, GRIEVANCE_STATUS_COLORS[status] ?? "bg-slate-100 text-slate-600")}>
      {status.replaceAll("_", " ")}
    </span>
  );
}

const TENDER_STATUS_COLORS: Record<string, string> = {
  DRAFT: "bg-slate-100 text-slate-600",
  PUBLISHED: "bg-blue-50 text-blue-700",
  BIDDING_CLOSED: "bg-amber-50 text-amber-700",
  AWARDED: "bg-emerald-50 text-emerald-700",
  CANCELLED: "bg-red-50 text-red-700",
};

export function TenderStatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx(PILL, TENDER_STATUS_COLORS[status] ?? "bg-slate-100 text-slate-600")}>
      {status.replaceAll("_", " ")}
    </span>
  );
}
