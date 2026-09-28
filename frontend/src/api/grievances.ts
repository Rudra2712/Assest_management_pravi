import { api } from "./client";
import type { GeoJSONGeometry, Grievance } from "../types";

export interface PublicAssetContext {
  id: string;
  asset_code: string;
  name: string;
  geometry: GeoJSONGeometry | null;
}

/** Public (no auth) — used by the anonymous /report page to show "Reporting
 * against X" and re-center the map. Does NOT use the staff-only GET
 * /assets/{id} endpoint, which requires a login the citizen doesn't have. */
export async function getPublicAssetContext(assetId: string): Promise<PublicAssetContext> {
  const res = await api.get<PublicAssetContext>(`/grievances/asset-lookup/${assetId}`);
  return res.data;
}

export interface FileGrievancePayload {
  title: string;
  description: string;
  category: string;
  severity: string;
  lat: number;
  lon: number;
  asset_id?: string;
  reporter_name?: string;
  reporter_contact?: string;
  photo?: File;
}

export async function fileGrievance(payload: FileGrievancePayload): Promise<Grievance> {
  const form = new FormData();
  form.append("title", payload.title);
  form.append("description", payload.description);
  form.append("category", payload.category);
  form.append("severity", payload.severity);
  form.append("lat", String(payload.lat));
  form.append("lon", String(payload.lon));
  if (payload.asset_id) form.append("asset_id", payload.asset_id);
  if (payload.reporter_name) form.append("reporter_name", payload.reporter_name);
  if (payload.reporter_contact) form.append("reporter_contact", payload.reporter_contact);
  if (payload.photo) form.append("photo", payload.photo);

  const res = await api.post<Grievance>("/grievances", form, { headers: { "Content-Type": "multipart/form-data" } });
  return res.data;
}

export async function listGrievances(params: Record<string, string | undefined> = {}): Promise<Grievance[]> {
  const res = await api.get<Grievance[]>("/grievances", { params });
  return res.data;
}

export async function getGrievance(id: string): Promise<Grievance> {
  const res = await api.get<Grievance>(`/grievances/${id}`);
  return res.data;
}

export async function fetchGrievancesGeoJSON(params: Record<string, string | undefined> = {}) {
  const res = await api.get("/grievances/geojson", { params });
  return res.data as {
    type: "FeatureCollection";
    features: Array<{ type: "Feature"; geometry: GeoJSON.Geometry; properties: Record<string, string | null> }>;
  };
}

export async function updateGrievanceStatus(id: string, status: string, notes?: string): Promise<Grievance> {
  const res = await api.patch<Grievance>(`/grievances/${id}/status`, { status, notes });
  return res.data;
}

export async function assignGrievance(id: string, assignedTo: string): Promise<Grievance> {
  const res = await api.post<Grievance>(`/grievances/${id}/assign`, { assigned_to: assignedTo });
  return res.data;
}

export async function linkGrievanceAsset(id: string, assetId: string): Promise<Grievance> {
  const res = await api.post<Grievance>(`/grievances/${id}/link-asset`, { asset_id: assetId });
  return res.data;
}

export async function convertGrievanceToMaintenance(id: string): Promise<{ maintenance_request_id: string }> {
  const res = await api.post(`/grievances/${id}/convert-to-maintenance`);
  return res.data;
}

export function grievancePhotoUrl(id: string, apiBase: string): string {
  return `${apiBase}/grievances/${id}/photo`;
}
