import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { createAsset } from "../api/assets";
import { listAdminUnits, listAssetTypes, listDepartments } from "../api/admin";
import type { AssetTypeCode } from "../types";

const TYPE_FIELDS: Record<AssetTypeCode, { key: string; label: string; type: "text" | "number" }[]> = {
  ROAD: [
    { key: "length_km", label: "Length (km)", type: "number" },
    { key: "width_m", label: "Width (m)", type: "number" },
    { key: "number_of_lanes", label: "Number of lanes", type: "number" },
    { key: "surface_type", label: "Surface type", type: "text" },
  ],
  BRIDGE: [
    { key: "length_m", label: "Length (m)", type: "number" },
    { key: "width_m", label: "Width (m)", type: "number" },
    { key: "number_of_spans", label: "Number of spans", type: "number" },
    { key: "bridge_type", label: "Bridge type", type: "text" },
    { key: "material", label: "Material", type: "text" },
    { key: "load_capacity_tonnes", label: "Load capacity (tonnes)", type: "number" },
  ],
  CULVERT: [
    { key: "culvert_type", label: "Culvert type", type: "text" },
    { key: "length_m", label: "Length (m)", type: "number" },
    { key: "opening_width_m", label: "Opening width (m)", type: "number" },
    { key: "material", label: "Material", type: "text" },
  ],
  BUILDING: [
    { key: "plot_area_sqm", label: "Plot area (sqm)", type: "number" },
    { key: "built_up_area_sqm", label: "Built-up area (sqm)", type: "number" },
    { key: "number_of_floors", label: "Number of floors", type: "number" },
    { key: "construction_year", label: "Construction year", type: "number" },
    { key: "building_type", label: "Building type", type: "text" },
    { key: "occupancy_use", label: "Occupancy / use", type: "text" },
  ],
  PUBLIC_STRUCTURE: [{ key: "structure_subtype", label: "Structure subtype", type: "text" }],
  OTHER_FIXED_ASSET: [{ key: "structure_subtype", label: "Subtype", type: "text" }],
};

const DETAIL_FIELD_KEY: Record<AssetTypeCode, "road" | "bridge" | "culvert" | "building" | "structure"> = {
  ROAD: "road",
  BRIDGE: "bridge",
  CULVERT: "culvert",
  BUILDING: "building",
  PUBLIC_STRUCTURE: "structure",
  OTHER_FIXED_ASSET: "structure",
};

export default function AssetForm() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: departments } = useQuery({ queryKey: ["departments"], queryFn: listDepartments });
  const { data: adminUnits } = useQuery({ queryKey: ["admin-units"], queryFn: listAdminUnits });
  const { data: assetTypes } = useQuery({ queryKey: ["asset-types"], queryFn: listAssetTypes });

  const [assetCode, setAssetCode] = useState("");
  const [name, setName] = useState("");
  const [assetTypeCode, setAssetTypeCode] = useState<AssetTypeCode>("ROAD");
  const [departmentId, setDepartmentId] = useState("");
  const [administrativeUnitId, setAdministrativeUnitId] = useState("");
  const [detail, setDetail] = useState<Record<string, string>>({});
  const [geometryText, setGeometryText] = useState('{"type":"Point","coordinates":[73.85,18.52]}');
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: createAsset,
    onSuccess: (asset) => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      navigate(`/assets/${asset.id}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || "Failed to create asset.");
    },
  });

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    let geometry: unknown = undefined;
    if (geometryText.trim()) {
      try {
        geometry = JSON.parse(geometryText);
      } catch {
        setError("Geometry must be valid GeoJSON (e.g. a Point, LineString or Polygon).");
        return;
      }
    }

    const detailFieldKey = DETAIL_FIELD_KEY[assetTypeCode];
    const detailPayload: Record<string, unknown> = {};
    for (const field of TYPE_FIELDS[assetTypeCode]) {
      const raw = detail[field.key];
      if (raw === undefined || raw === "") continue;
      detailPayload[field.key] = field.type === "number" ? Number(raw) : raw;
    }

    mutation.mutate({
      asset_code: assetCode,
      name,
      asset_type_code: assetTypeCode,
      department_id: departmentId,
      administrative_unit_id: administrativeUnitId,
      geometry,
      [detailFieldKey]: Object.keys(detailPayload).length ? detailPayload : undefined,
    });
  }

  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold text-slate-900">Add Asset</h1>

      <form onSubmit={onSubmit} className="bg-white rounded-lg border border-slate-200 p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Asset Code</label>
            <input required value={assetCode} onChange={(e) => setAssetCode(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="RB-ROAD-0003" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Asset Type</label>
            <select value={assetTypeCode} onChange={(e) => { setAssetTypeCode(e.target.value as AssetTypeCode); setDetail({}); }} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
              {assetTypes?.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
          <input required value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Department</label>
            <select required value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
              <option value="">Select…</option>
              {departments?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Administrative Unit</label>
            <select required value={administrativeUnitId} onChange={(e) => setAdministrativeUnitId(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
              <option value="">Select…</option>
              {adminUnits?.map((u) => <option key={u.id} value={u.id}>{u.name} ({u.level})</option>)}
            </select>
          </div>
        </div>

        <div className="border-t pt-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">{assetTypeCode.replaceAll("_", " ")} Details</h2>
          <div className="grid grid-cols-2 gap-4">
            {TYPE_FIELDS[assetTypeCode].map((field) => (
              <div key={field.key}>
                <label className="block text-sm font-medium text-slate-700 mb-1">{field.label}</label>
                <input
                  type={field.type}
                  value={detail[field.key] ?? ""}
                  onChange={(e) => setDetail((d) => ({ ...d, [field.key]: e.target.value }))}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            ))}
          </div>
        </div>

        <div className="border-t pt-4">
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Geometry (GeoJSON — Point for bridges/culverts/structures, LineString for roads, Polygon for buildings)
          </label>
          <textarea
            rows={3}
            value={geometryText}
            onChange={(e) => setGeometryText(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm font-mono text-xs"
          />
        </div>

        {error && <div className="text-sm text-red-600">{error}</div>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={() => navigate(-1)} className="px-4 py-2 text-sm rounded-md border border-slate-300">Cancel</button>
          <button type="submit" disabled={mutation.isPending} className="px-4 py-2 text-sm rounded-md bg-rb-navy text-white disabled:opacity-50">
            {mutation.isPending ? "Saving…" : "Create Asset"}
          </button>
        </div>
      </form>
    </div>
  );
}
