import { api } from "./client";

export interface ImportPreviewRow {
  row_number: number;
  asset_code: string;
  name: string;
  is_duplicate: boolean;
  errors: string[];
  importable: boolean;
}

export interface ImportPreview {
  total_rows: number;
  importable_count: number;
  duplicate_count: number;
  error_count: number;
  rows: ImportPreviewRow[];
}

export async function previewAssetImport(file: File): Promise<ImportPreview> {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post<ImportPreview>("/imports/assets/preview", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function commitAssetImport(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post("/imports/assets/commit", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data as { imported: number; skipped_duplicates: number; skipped_errors: number };
}
