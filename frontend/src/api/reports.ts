import { api } from "./client";
import type { DashboardData } from "../types";

export async function fetchDashboard(): Promise<DashboardData> {
  const res = await api.get<DashboardData>("/reports/dashboard");
  return res.data;
}

export async function fetchFieldDashboard() {
  const res = await api.get("/reports/field-dashboard");
  return res.data as {
    assigned_inspections: number;
    overdue_inspections: number;
    assigned_work_orders: number;
    critical_findings_reported: number;
  };
}
