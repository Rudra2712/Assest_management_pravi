import { api } from "./client";
import type { MaintenanceRequest, WorkOrder } from "../types";

export async function listMaintenanceRequests(params: Record<string, string | undefined>): Promise<MaintenanceRequest[]> {
  const res = await api.get<MaintenanceRequest[]>("/maintenance/requests", { params });
  return res.data;
}

export async function createMaintenanceRequest(payload: Record<string, unknown>): Promise<MaintenanceRequest> {
  const res = await api.post<MaintenanceRequest>("/maintenance/requests", payload);
  return res.data;
}

export async function decideMaintenanceRequest(id: string, approve: boolean, comments?: string): Promise<MaintenanceRequest> {
  const res = await api.post<MaintenanceRequest>(`/maintenance/requests/${id}/decision`, { approve, comments });
  return res.data;
}

export async function createWorkOrder(requestId: string, payload: Record<string, unknown>): Promise<WorkOrder> {
  const res = await api.post<WorkOrder>(`/maintenance/requests/${requestId}/work-order`, payload);
  return res.data;
}

export async function listWorkOrders(params: Record<string, string | undefined>): Promise<WorkOrder[]> {
  const res = await api.get<WorkOrder[]>("/work-orders", { params });
  return res.data;
}

export async function getWorkOrder(id: string): Promise<WorkOrder> {
  const res = await api.get<WorkOrder>(`/work-orders/${id}`);
  return res.data;
}

export async function assignWorkOrder(id: string, payload: Record<string, unknown>): Promise<WorkOrder> {
  const res = await api.post<WorkOrder>(`/work-orders/${id}/assign`, payload);
  return res.data;
}

export async function startWorkOrder(id: string): Promise<WorkOrder> {
  const res = await api.post<WorkOrder>(`/work-orders/${id}/start`);
  return res.data;
}

export async function completeWorkOrder(id: string, payload: Record<string, unknown>): Promise<WorkOrder> {
  const res = await api.post<WorkOrder>(`/work-orders/${id}/complete`, payload);
  return res.data;
}

export async function verifyWorkOrder(id: string, verified: boolean, comments?: string): Promise<WorkOrder> {
  const res = await api.post<WorkOrder>(`/work-orders/${id}/verify`, { verified, comments });
  return res.data;
}

export async function getWorkOrderHistory(id: string) {
  const res = await api.get(`/work-orders/${id}/history`);
  return res.data as Array<{ id: string; event: string; notes: string | null; recorded_by: string; created_at: string }>;
}
