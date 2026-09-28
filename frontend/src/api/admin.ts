import { api } from "./client";
import type { AdministrativeUnit, AssetType, CurrentUser, Department } from "../types";

export async function listDepartments(): Promise<Department[]> {
  const res = await api.get<Department[]>("/departments");
  return res.data;
}

export async function listAdminUnits(): Promise<AdministrativeUnit[]> {
  const res = await api.get<AdministrativeUnit[]>("/admin-units");
  return res.data;
}

export async function listAssetTypes(): Promise<AssetType[]> {
  const res = await api.get<AssetType[]>("/asset-types");
  return res.data;
}

export async function listAssetCategories() {
  const res = await api.get("/asset-types/categories");
  return res.data as Array<{ id: string; code: string; name: string }>;
}

export async function listUsers(): Promise<CurrentUser[]> {
  const res = await api.get<CurrentUser[]>("/users");
  return res.data;
}

export async function createUser(payload: Record<string, unknown>): Promise<CurrentUser> {
  const res = await api.post<CurrentUser>("/users", payload);
  return res.data;
}

export async function assignUserRole(userId: string, roleCode: string, jurisdictionUnitId?: string): Promise<CurrentUser> {
  const res = await api.post<CurrentUser>(`/users/${userId}/roles`, { role_code: roleCode, jurisdiction_unit_id: jurisdictionUnitId });
  return res.data;
}
