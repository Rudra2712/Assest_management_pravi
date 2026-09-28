import { api } from "./client";
import type { Contractor } from "../types";

export async function listContractors(): Promise<Contractor[]> {
  const res = await api.get<Contractor[]>("/contractors");
  return res.data;
}

export async function createContractor(payload: Record<string, unknown>): Promise<Contractor> {
  const res = await api.post<Contractor>("/contractors", payload);
  return res.data;
}
