import { api } from "./client";
import type { DocumentMeta } from "../types";

export async function listDocuments(linkedEntityType: string, linkedEntityId: string): Promise<DocumentMeta[]> {
  const res = await api.get<DocumentMeta[]>("/documents", {
    params: { linked_entity_type: linkedEntityType, linked_entity_id: linkedEntityId },
  });
  return res.data;
}

export async function uploadDocument(
  documentType: string,
  linkedEntityType: string,
  linkedEntityId: string,
  file: File
): Promise<DocumentMeta> {
  const form = new FormData();
  form.append("document_type", documentType);
  form.append("linked_entity_type", linkedEntityType);
  form.append("linked_entity_id", linkedEntityId);
  form.append("file", file);
  const res = await api.post<DocumentMeta>("/documents", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export function downloadUrl(documentId: string, apiBase: string): string {
  return `${apiBase}/documents/${documentId}/download`;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`);
}
