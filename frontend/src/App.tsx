import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import ProtectedRoute from "./routes/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import AssetList from "./pages/AssetList";
import AssetForm from "./pages/AssetForm";
import AssetDetail from "./pages/AssetDetail";
import GisMap from "./pages/GisMap";
import Inspections from "./pages/Inspections";
import InspectionDetail from "./pages/InspectionDetail";
import Maintenance from "./pages/Maintenance";
import WorkOrders from "./pages/WorkOrders";
import WorkOrderDetail from "./pages/WorkOrderDetail";
import Projects from "./pages/Projects";
import Contractors from "./pages/Contractors";
import Reports from "./pages/Reports";
import Notifications from "./pages/Notifications";
import UserManagement from "./pages/UserManagement";
import AuditLogs from "./pages/AuditLogs";
import Grievances from "./pages/Grievances";
import ReportGrievance from "./pages/ReportGrievance";
import Tenders from "./pages/Tenders";
import { useAuth } from "./hooks/useAuth";

const PROCUREMENT_ROLES = ["STATE_ADMIN", "DEPARTMENT_ADMIN"];
const ASSET_ROLES = [...PROCUREMENT_ROLES, "FIELD_ENGINEER", "MAINTENANCE_OFFICER"];
const INSPECTION_ROLES = [...PROCUREMENT_ROLES, "FIELD_ENGINEER"];
const MAINTENANCE_ROLES = [...PROCUREMENT_ROLES, "FIELD_ENGINEER", "MAINTENANCE_OFFICER"];
const DASHBOARD_ROLES = ASSET_ROLES;

function DefaultHome() {
  const { hasRole } = useAuth();
  return <Navigate to={hasRole("CONTRACTOR") ? "/tenders" : "/dashboard"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/report" element={<ReportGrievance />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DefaultHome />} />
          <Route element={<ProtectedRoute roles={DASHBOARD_ROLES} />}>
            <Route path="/dashboard" element={<Dashboard />} />
          </Route>
          <Route element={<ProtectedRoute roles={ASSET_ROLES} />}>
            <Route path="/assets" element={<AssetList />} />
            <Route path="/assets/new" element={<AssetForm />} />
            <Route path="/assets/:id" element={<AssetDetail />} />
            <Route path="/gis" element={<GisMap />} />
          </Route>
          <Route element={<ProtectedRoute roles={ASSET_ROLES} />}>
            <Route path="/grievances" element={<Grievances />} />
          </Route>
          <Route element={<ProtectedRoute roles={[...PROCUREMENT_ROLES, "CONTRACTOR"]} />}>
            <Route path="/tenders" element={<Tenders />} />
          </Route>
          <Route element={<ProtectedRoute roles={INSPECTION_ROLES} />}>
            <Route path="/inspections" element={<Inspections />} />
            <Route path="/inspections/:id" element={<InspectionDetail />} />
          </Route>
          <Route element={<ProtectedRoute roles={MAINTENANCE_ROLES} />}>
            <Route path="/maintenance" element={<Maintenance />} />
          </Route>
          <Route element={<ProtectedRoute roles={[...PROCUREMENT_ROLES, "MAINTENANCE_OFFICER", "CONTRACTOR"]} />}>
            <Route path="/work-orders" element={<WorkOrders />} />
            <Route path="/work-orders/:id" element={<WorkOrderDetail />} />
          </Route>
          <Route element={<ProtectedRoute roles={[...PROCUREMENT_ROLES, "FIELD_ENGINEER", "MAINTENANCE_OFFICER"]} />}>
            <Route path="/projects" element={<Projects />} />
          </Route>
          <Route element={<ProtectedRoute roles={[...PROCUREMENT_ROLES, "MAINTENANCE_OFFICER"]} />}>
            <Route path="/contractors" element={<Contractors />} />
          </Route>
          <Route element={<ProtectedRoute roles={[...PROCUREMENT_ROLES, "MAINTENANCE_OFFICER"]} />}>
            <Route path="/reports" element={<Reports />} />
          </Route>
          <Route path="/notifications" element={<Notifications />} />
          <Route element={<ProtectedRoute roles={["STATE_ADMIN", "DEPARTMENT_ADMIN"]} />}>
            <Route path="/users" element={<UserManagement />} />
          </Route>
          <Route element={<ProtectedRoute roles={PROCUREMENT_ROLES} />}>
            <Route path="/audit-logs" element={<AuditLogs />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
