import { NavLink, Outlet, useNavigate } from "react-router-dom";
import clsx from "clsx";
import {
  Landmark,
  LayoutDashboard,
  Building2,
  Map as MapIcon,
  TriangleAlert,
  ClipboardCheck,
  Wrench,
  ClipboardList,
  FolderKanban,
  Gavel,
  HardHat,
  BarChart3,
  Bell,
  Users,
  History,
  LogOut,
  type LucideIcon,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";

const PROCUREMENT_ROLES = ["STATE_ADMIN", "DEPARTMENT_ADMIN"];
const ASSET_ROLES = [...PROCUREMENT_ROLES, "FIELD_ENGINEER", "MAINTENANCE_OFFICER"];

const NAV_ITEMS: { to: string; label: string; icon: LucideIcon; roles?: string[] }[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ASSET_ROLES },
  { to: "/assets", label: "Asset Registry", icon: Building2, roles: ASSET_ROLES },
  { to: "/gis", label: "GIS Map", icon: MapIcon, roles: ASSET_ROLES },
  { to: "/grievances", label: "Grievances", icon: TriangleAlert, roles: ASSET_ROLES },
  { to: "/inspections", label: "Inspections", icon: ClipboardCheck, roles: [...PROCUREMENT_ROLES, "FIELD_ENGINEER"] },
  { to: "/maintenance", label: "Maintenance", icon: Wrench, roles: [...PROCUREMENT_ROLES, "FIELD_ENGINEER", "MAINTENANCE_OFFICER"] },
  { to: "/work-orders", label: "Work Orders", icon: ClipboardList, roles: [...PROCUREMENT_ROLES, "MAINTENANCE_OFFICER", "CONTRACTOR"] },
  { to: "/projects", label: "Projects", icon: FolderKanban, roles: [...PROCUREMENT_ROLES, "FIELD_ENGINEER", "MAINTENANCE_OFFICER"] },
  { to: "/tenders", label: "Tenders", icon: Gavel, roles: [...PROCUREMENT_ROLES, "CONTRACTOR"] },
  { to: "/contractors", label: "Contractors", icon: HardHat, roles: [...PROCUREMENT_ROLES, "MAINTENANCE_OFFICER"] },
  { to: "/reports", label: "Reports", icon: BarChart3, roles: [...PROCUREMENT_ROLES, "MAINTENANCE_OFFICER"] },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/users", label: "User Management", icon: Users, roles: ["STATE_ADMIN", "DEPARTMENT_ADMIN"] },
  { to: "/audit-logs", label: "Audit Logs", icon: History, roles: PROCUREMENT_ROLES },
];

function initials(name: string | undefined): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase();
}

export default function AppLayout() {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex h-screen bg-slate-50">
      <aside className="w-64 shrink-0 bg-white border-r border-slate-100 flex flex-col shadow-[1px_0_0_0_#f0f0f0]">
        <div className="flex items-center gap-2.5 px-4 py-5 border-b border-slate-100 min-h-16">
          <div className="w-[34px] h-[34px] rounded-[10px] bg-brand flex items-center justify-center shrink-0 animate-pulseBrand">
            <Landmark size={17} className="text-brand-ink" />
          </div>
          <div className="overflow-hidden">
            <div className="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">Govt. of Gujarat</div>
            <div className="font-extrabold text-[0.95rem] leading-tight text-ink tracking-tight whitespace-nowrap">R&amp;B Asset Inventory</div>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {NAV_ITEMS.filter((item) => !item.roles || hasRole(...item.roles)).map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  clsx(
                    "relative flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[0.835rem] font-medium transition-colors",
                    isActive ? "bg-brand-light text-brand-ink font-semibold" : "text-slate-500 hover:bg-slate-50 hover:text-ink"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && <span className="absolute left-0 top-1/5 bottom-1/5 w-[3px] rounded-r bg-brand" />}
                    <Icon size={16} className="shrink-0" />
                    {item.label}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
        <div className="px-2 py-3 border-t border-slate-100">
          <div className="flex items-center gap-2.5 rounded-lg p-2.5 hover:bg-slate-50 transition-colors">
            <div className="w-[34px] h-[34px] rounded-full bg-brand flex items-center justify-center text-[0.85rem] font-bold text-brand-ink shrink-0">
              {initials(user?.full_name)}
            </div>
            <div className="overflow-hidden flex-1 min-w-0">
              <div className="text-sm font-semibold text-ink truncate">{user?.full_name}</div>
              <div className="text-xs text-slate-400 truncate">{user?.roles.join(", ")}</div>
            </div>
            <button
              title="Sign out"
              className="text-slate-400 hover:text-ink shrink-0"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto bg-slate-50">
        <div className="p-6 max-w-[1400px] mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
