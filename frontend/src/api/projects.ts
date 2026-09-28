import { api } from "./client";
import type { Project } from "../types";

export async function listProjects(): Promise<Project[]> {
  const res = await api.get<Project[]>("/projects");
  return res.data;
}

export async function getProject(id: string): Promise<Project> {
  const res = await api.get<Project>(`/projects/${id}`);
  return res.data;
}

export async function createProject(payload: Record<string, unknown>): Promise<Project> {
  const res = await api.post<Project>("/projects", payload);
  return res.data;
}

export async function updateProject(id: string, payload: Record<string, unknown>): Promise<Project> {
  const res = await api.patch<Project>(`/projects/${id}`, payload);
  return res.data;
}

export async function linkProjectAsset(id: string, assetId: string) {
  const res = await api.post(`/projects/${id}/assets`, { asset_id: assetId });
  return res.data;
}

export async function listProjectAssets(id: string) {
  const res = await api.get(`/projects/${id}/assets`);
  return res.data as Array<{ id: string; asset_code: string; name: string }>;
}
