import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { commitAssetImport, previewAssetImport, type ImportPreview } from "../api/imports";

export default function CsvImport() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [result, setResult] = useState<{ imported: number; skipped_duplicates: number; skipped_errors: number } | null>(null);

  const previewMutation = useMutation({
    mutationFn: () => previewAssetImport(file!),
    onSuccess: (data) => { setPreview(data); setResult(null); },
  });
  const commitMutation = useMutation({
    mutationFn: () => commitAssetImport(file!),
    onSuccess: (data) => setResult(data),
  });

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">CSV Asset Import</h1>
        <p className="text-sm text-slate-500">
          Upload &rarr; Validate &rarr; Preview &rarr; Duplicate Detection &rarr; Import &rarr; Audit. Duplicates (by asset code) are always
          skipped — this import never overwrites existing records.
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
        <p className="text-xs text-slate-500">
          Required columns: <code>asset_code, name, asset_type_code, department_code, administrative_unit_code</code>. Optional:
          <code> ownership, address, lifecycle_status, acquisition_date, commissioning_date, original_cost, current_value, useful_life_years</code>.
        </p>
        <input type="file" accept=".csv" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setPreview(null); setResult(null); }} />
        <div className="flex gap-2">
          <button disabled={!file || previewMutation.isPending} onClick={() => previewMutation.mutate()} className="bg-rb-teal text-white text-sm px-4 py-2 rounded-md disabled:opacity-50">
            {previewMutation.isPending ? "Validating…" : "Preview"}
          </button>
          {preview && preview.importable_count > 0 && (
            <button disabled={commitMutation.isPending} onClick={() => commitMutation.mutate()} className="bg-rb-navy text-white text-sm px-4 py-2 rounded-md disabled:opacity-50">
              {commitMutation.isPending ? "Importing…" : `Import ${preview.importable_count} rows`}
            </button>
          )}
        </div>
      </div>

      {preview && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
          <div className="flex gap-4 text-sm">
            <span>Total: <strong>{preview.total_rows}</strong></span>
            <span className="text-emerald-700">Importable: <strong>{preview.importable_count}</strong></span>
            <span className="text-amber-700">Duplicates: <strong>{preview.duplicate_count}</strong></span>
            <span className="text-red-700">Errors: <strong>{preview.error_count}</strong></span>
          </div>
          <table className="min-w-full text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase">
              <tr>
                <th className="text-left px-2 py-1">Row</th>
                <th className="text-left px-2 py-1">Asset Code</th>
                <th className="text-left px-2 py-1">Name</th>
                <th className="text-left px-2 py-1">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {preview.rows.map((r) => (
                <tr key={r.row_number}>
                  <td className="px-2 py-1">{r.row_number}</td>
                  <td className="px-2 py-1 font-mono">{r.asset_code}</td>
                  <td className="px-2 py-1">{r.name}</td>
                  <td className="px-2 py-1">
                    {r.importable && <span className="text-emerald-700">Ready to import</span>}
                    {r.is_duplicate && <span className="text-amber-700">Duplicate — skipped</span>}
                    {r.errors.length > 0 && <span className="text-red-700">{r.errors.join("; ")}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {result && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-sm text-emerald-800">
          Imported {result.imported} assets. Skipped {result.skipped_duplicates} duplicates and {result.skipped_errors} rows with errors.
        </div>
      )}
    </div>
  );
}
