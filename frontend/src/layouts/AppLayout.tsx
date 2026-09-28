import { NavLink, Outlet, useNavigate } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "../hooks/useAuth";

const NAV_ITEMS: { to: string; label: string; roles?: string[] }[] = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/assets", label: "Asset Registry" },
  { to: "/gis", label: "GIS Map" },
  { to: "/inspections", label: "Inspections" },
  { to: "/maintenance", label: "Maintenance" },
  { to: "/work-orders", label: "Work Orders" },
  { to: "/projects", label: "Projects" },
  { to: "/contractors", label: "Contractors" },
  { to: "/imports", label: "CSV Import" },
  { to: "/reports", label: "Reports" },
  { to: "/notifications", label: "Notifications" },
  { to: "/users", label: "User Management", roles: ["STATE_ADMIN", "DEPARTMENT_ADMIN"] },
  { to: "/audit-logs", label: "Audit Logs", roles: ["STATE_ADMIN", "DEPARTMENT_ADMIN", "AUDITOR"] },
];

export default function AppLayout() {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex h-screen">
      <aside className="w-64 shrink-0 bg-rb-navy text-white flex flex-col">
        <div className="px-4 py-5 border-b border-white/10">
          <div className="text-sm uppercase tracking-wide text-white/60">Government of Pravinagar</div>
          <div className="font-semibold text-lg leading-tight">R&amp;B Asset Inventory</div>
        </div>
        <nav className="flex-1 overflow-y-auto py-3">
          {NAV_ITEMS.filter((item) => !item.roles || hasRole(...item.roles)).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                clsx(
                  "block px-4 py-2 text-sm rounded-md mx-2 my-0.5",
                  isActive ? "bg-white/15 text-white font-medium" : "text-white/80 hover:bg-white/10"
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-3 border-t border-white/10 text-xs text-white/60">
          <div className="font-medium text-white/90">{user?.full_name}</div>
          <div>{user?.roles.join(", ")}</div>
          <button
            className="mt-2 text-white/80 hover:text-white underline underline-offset-2"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Sign out
          </button>
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
