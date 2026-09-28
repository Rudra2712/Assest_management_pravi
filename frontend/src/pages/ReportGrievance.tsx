import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { CheckCircle2, Crosshair, TriangleAlert } from "lucide-react";
import { fileGrievance, getPublicAssetContext } from "../api/grievances";
import { SATELLITE_STYLE } from "../lib/mapStyle";

const CATEGORIES = [
  { value: "POTHOLE", label: "Pothole" },
  { value: "STRUCTURAL_DAMAGE", label: "Structural damage (bridge/building)" },
  { value: "WATER_LOGGING", label: "Water logging / drainage" },
  { value: "TREE_HAZARD", label: "Tree / vegetation hazard" },
  { value: "ENCROACHMENT", label: "Encroachment" },
  { value: "SAFETY_HAZARD", label: "Safety hazard" },
  { value: "ELECTRICAL_HAZARD", label: "Electrical hazard" },
  { value: "OTHER", label: "Other" },
];

const DEFAULT_CENTER: [number, number] = [72.5714, 23.0225];

function assetCenter(geometry: { type: string; coordinates: unknown } | null | undefined): [number, number] | null {
  if (!geometry) return null;
  if (geometry.type === "Point") return geometry.coordinates as [number, number];
  if (geometry.type === "LineString") {
    const coords = geometry.coordinates as [number, number][];
    return coords[Math.floor(coords.length / 2)];
  }
  if (geometry.type === "Polygon") {
    const coords = geometry.coordinates as [number, number][][];
    return coords[0][0];
  }
  return null;
}

export default function ReportGrievance() {
  const [searchParams] = useSearchParams();
  const assetId = searchParams.get("asset_id") ?? undefined;
  const { data: linkedAsset } = useQuery({ queryKey: ["public-asset-context", assetId], queryFn: () => getPublicAssetContext(assetId!), enabled: !!assetId });

  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  const [manualCoords, setManualCoords] = useState<[number, number] | null>(null);
  const coords = manualCoords ?? assetCenter(linkedAsset?.geometry) ?? DEFAULT_CENTER;
  const [mapReady, setMapReady] = useState(false);
  const [locationStatus, setLocationStatus] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("POTHOLE");
  const [severity, setSeverity] = useState("MEDIUM");
  const [reporterName, setReporterName] = useState("");
  const [reporterContact, setReporterContact] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);

  // Initialize the map once.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({ container: containerRef.current, style: SATELLITE_STYLE, center: DEFAULT_CENTER, zoom: 12 });
    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("load", () => {
      const marker = new maplibregl.Marker({ color: "#ea580c", draggable: true }).setLngLat(DEFAULT_CENTER).addTo(map);
      marker.on("dragend", () => {
        const { lng, lat } = marker.getLngLat();
        setManualCoords([lng, lat]);
      });
      map.on("click", (e) => {
        marker.setLngLat(e.lngLat);
        setManualCoords([e.lngLat.lng, e.lngLat.lat]);
      });
      markerRef.current = marker;
      setMapReady(true);
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
  }, []);

  // Keep the map's marker/camera in sync with `coords`, whatever the source
  // (manual lat/lon fields, "use my location", map click/drag, or the
  // asset pre-fill above) — runs once more as soon as the map finishes
  // loading, in case coords was already set before mapReady flipped.
  useEffect(() => {
    if (!mapReady) return;
    markerRef.current?.setLngLat(coords);
    mapRef.current?.jumpTo({ center: coords, zoom: mapRef.current.getZoom() < 13 ? 15 : mapRef.current.getZoom() });
  }, [coords, mapReady]);

  function useMyLocation() {
    if (!navigator.geolocation) {
      setLocationStatus("Your browser doesn't support location — please pin the spot on the map manually.");
      return;
    }
    setLocationStatus("Locating…");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        // The coords→map sync effect below picks this up and recenters the map.
        setManualCoords([pos.coords.longitude, pos.coords.latitude]);
        setLocationStatus(null);
      },
      (err) => {
        setLocationStatus(
          err.code === err.PERMISSION_DENIED
            ? "Location permission denied — pin the spot on the map or type coordinates below instead."
            : "Couldn't get your location — pin the spot on the map or type coordinates below instead."
        );
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  const mutation = useMutation({
    mutationFn: () =>
      fileGrievance({
        title, description, category, severity,
        lat: coords[1], lon: coords[0],
        asset_id: assetId,
        reporter_name: reporterName || undefined,
        reporter_contact: reporterContact || undefined,
        photo: photo || undefined,
      }),
  });

  if (mutation.isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center space-y-3">
          <CheckCircle2 className="mx-auto text-emerald-600" size={40} />
          <h1 className="text-lg font-semibold text-ink">Report submitted</h1>
          <p className="text-sm text-slate-500">
            Reference code <span className="font-mono font-medium">{mutation.data.grievance_code}</span>. The concerned
            department will review and take action.
          </p>
          <button onClick={() => mutation.reset()} className="text-sm text-brand-ink font-medium hover:underline">File another report</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8 flex justify-center">
      <div className="max-w-2xl w-full space-y-4">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 text-orange-600 font-semibold">
            <TriangleAlert size={20} /> Report a Road / Infrastructure Issue
          </div>
          <p className="text-sm text-slate-500 mt-1">
            No login needed. Pin the location on the map, describe the issue, and submit — e.g. a pothole, a damaged
            railing, or a tree root damaging the road surface.
          </p>
          {linkedAsset && <p className="text-xs text-slate-400 mt-1">Reporting against {linkedAsset.asset_code} — {linkedAsset.name}</p>}
        </div>

        <div className="bg-white rounded-xl border border-slate-100 p-4 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-medium text-slate-700">Location — click or drag the pin</label>
              <button type="button" onClick={useMyLocation} className="text-xs text-brand-ink hover:underline flex items-center gap-1">
                <Crosshair size={12} /> Use my location
              </button>
            </div>
            <div ref={containerRef} className="w-full h-64 rounded-md overflow-hidden border border-slate-200 bg-slate-100" />
            {locationStatus && <div className="text-xs text-amber-600 mt-1">{locationStatus}</div>}

            <div className="grid grid-cols-2 gap-2 mt-2">
              <label className="text-xs text-slate-500">
                Latitude
                <input
                  type="number" step="0.00001" value={coords[1]}
                  onChange={(e) => { const lat = Number(e.target.value); if (!Number.isNaN(lat)) setManualCoords([coords[0], lat]); }}
                  className="w-full rounded-md border border-slate-200 px-2 py-1.5 text-xs font-mono mt-0.5"
                />
              </label>
              <label className="text-xs text-slate-500">
                Longitude
                <input
                  type="number" step="0.00001" value={coords[0]}
                  onChange={(e) => { const lon = Number(e.target.value); if (!Number.isNaN(lon)) setManualCoords([lon, coords[1]]); }}
                  className="w-full rounded-md border border-slate-200 px-2 py-1.5 text-xs font-mono mt-0.5"
                />
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Short summary, e.g. Pothole near bus stop" />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="What's wrong, and anything that might help staff (e.g. a tree root lifting the asphalt after rain)" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
                {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Severity</label>
              <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
                {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Your name (optional)</label>
              <input value={reporterName} onChange={(e) => setReporterName(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Phone (optional)</label>
              <input value={reporterContact} onChange={(e) => setReporterContact(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Photo (optional)</label>
            <input type="file" accept="image/*" onChange={(e) => setPhoto(e.target.files?.[0] ?? null)} />
          </div>

          {mutation.isError && <div className="text-sm text-red-600">Something went wrong submitting your report. Please try again.</div>}

          <button
            disabled={!title || !description || mutation.isPending}
            onClick={() => mutation.mutate()}
            className="w-full bg-orange-600 text-white rounded-md py-2.5 text-sm font-semibold hover:bg-orange-700 disabled:opacity-50"
          >
            {mutation.isPending ? "Submitting…" : "Submit Report"}
          </button>
        </div>
      </div>
    </div>
  );
}
