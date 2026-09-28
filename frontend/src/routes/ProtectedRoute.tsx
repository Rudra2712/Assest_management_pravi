import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function ProtectedRoute({ roles }: { roles?: string[] }) {
  const { user, loading, hasRole } = useAuth();

  if (loading) {
    return <div className="p-8 text-slate-500">Loading…</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (roles && !hasRole(...roles)) {
    return <div className="p-8 text-red-600">You do not have permission to view this page.</div>;
  }
  return <Outlet />;
}
