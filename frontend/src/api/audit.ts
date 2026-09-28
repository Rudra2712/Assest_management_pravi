import { api } from "./client";
import type { AuditLogEntry } from "../types";

export async function listAuditLogs(params: Record<string, string | number | undefined>): Promise<AuditLogEntry[]> {
  const res = await api.get<AuditLogEntry[]>("/audit-logs", { params });
  return res.data;
}
