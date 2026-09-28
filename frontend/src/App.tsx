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
import CsvImport from "./pages/CsvImport";
import Reports from "./pages/Reports";
import Notifications from "./pages/Notifications";
import UserManagement from "./pages/UserManagement";
import AuditLogs from "./pages/AuditLogs";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/assets" element={<AssetList />} />
          <Route path="/assets/new" element={<AssetForm />} />
          <Route path="/assets/:id" element={<AssetDetail />} />
          <Route path="/gis" element={<GisMap />} />
          <Route path="/inspections" element={<Inspections />} />
          <Route path="/inspections/:id" element={<InspectionDetail />} />
          <Route path="/maintenance" element={<Maintenance />} />
          <Route path="/work-orders" element={<WorkOrders />} />
          <Route path="/work-orders/:id" element={<WorkOrderDetail />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/contractors" element={<Contractors />} />
          <Route path="/imports" element={<CsvImport />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route element={<ProtectedRoute roles={["STATE_ADMIN", "DEPARTMENT_ADMIN"]} />}>
            <Route path="/users" element={<UserManagement />} />
          </Route>
          <Route element={<ProtectedRoute roles={["STATE_ADMIN", "DEPARTMENT_ADMIN", "AUDITOR"]} />}>
            <Route path="/audit-logs" element={<AuditLogs />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
