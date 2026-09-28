import { api } from "./client";
import type { Asset, AssetListItem, LifecycleEvent, LifecycleStatus, Page } from "../types";

export interface AssetListParams {
  q?: string;
  asset_type_code?: string;
  lifecycle_status?: string;
  current_condition?: string;
  administrative_unit_id?: string;
  department_id?: string;
  page?: number;
  page_size?: number;
}

export async function listAssets(params: AssetListParams): Promise<Page<AssetListItem>> {
  const res = await api.get<Page<AssetListItem>>("/assets", { params });
  return res.data;
}

export async function getAsset(id: string): Promise<Asset> {
  const res = await api.get<Asset>(`/assets/${id}`);
  return res.data;
}

export async function createAsset(payload: Record<string, unknown>): Promise<Asset> {
  const res = await api.post<Asset>("/assets", payload);
  return res.data;
}

export async function updateAsset(id: string, payload: Record<string, unknown>): Promise<Asset> {
  const res = await api.patch<Asset>(`/assets/${id}`, payload);
  return res.data;
}

export async function getLifecycleHistory(id: string): Promise<LifecycleEvent[]> {
  const res = await api.get<LifecycleEvent[]>(`/assets/${id}/lifecycle-history`);
  return res.data;
}

export async function transitionLifecycle(id: string, new_status: LifecycleStatus, reason?: string): Promise<Asset> {
  const res = await api.post<Asset>(`/assets/${id}/lifecycle-transitions`, { new_status, reason });
  return res.data;
}
