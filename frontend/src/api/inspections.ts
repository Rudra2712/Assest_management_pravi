import { api } from "./client";
import type { Inspection } from "../types";

export async function listInspections(params: Record<string, string | boolean | undefined>): Promise<Inspection[]> {
  const res = await api.get<Inspection[]>("/inspections", { params });
  return res.data;
}

export async function getInspection(id: string): Promise<Inspection> {
  const res = await api.get<Inspection>(`/inspections/${id}`);
  return res.data;
}

export async function assignInspection(payload: {
  asset_id: string;
  inspector_id: string;
  template_id?: string;
  assigned_date?: string;
}): Promise<Inspection> {
  const res = await api.post<Inspection>("/inspections", payload);
  return res.data;
}

export async function submitInspection(id: string, payload: Record<string, unknown>): Promise<Inspection> {
  const res = await api.post<Inspection>(`/inspections/${id}/submit`, payload);
  return res.data;
}

export async function reviewInspection(id: string, approve: boolean, comments?: string): Promise<Inspection> {
  const res = await api.post<Inspection>(`/inspections/${id}/review`, { approve, comments });
  return res.data;
}
