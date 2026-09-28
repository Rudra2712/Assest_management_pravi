import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Layers, LocateFixed, MapPin, TriangleAlert } from "lucide-react";
import { fetchAssetsGeoJSON } from "../api/gis";
import { fetchGrievancesGeoJSON } from "../api/grievances";
import { listAssetTypes } from "../api/admin";
import { styleFor, type BasemapKind } from "../lib/mapStyle";

const CONDITION_COLOR: Record<string, string> = {
  GOOD: "#059669", FAIR: "#d97706", POOR: "#ea580c", CRITICAL: "#dc2626",
};
const SEVERITY_COLOR: Record<string, string> = {
  LOW: "#eab308", MEDIUM: "#f97316", HIGH: "#ef4444", CRITICAL: "#b91c1c",
};
const EMPTY_FC: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };

function collectCoordinates(value: unknown, coordinates: [number, number][]) {
  if (!Array.isArray(value)) return;
  if (typeof value[0] === "number" && typeof value[1] === "number") {
    coordinates.push([value[0], value[1]]);
    return;
  }
  value.forEach((item) => collectCoordinates(item, coordinates));
}

function addDataLayers(map: maplibregl.Map) {
  if (!map.getSource("assets")) {
    map.addSource("assets", { type: "geojson", data: EMPTY_FC });
    map.addLayer({
      id: "asset-polygons", type: "fill", source: "assets",
      filter: ["==", ["geometry-type"], "Polygon"],
      paint: { "fill-color": "#0f766e", "fill-opacity": 0.45 },
    });
    map.addLayer({
      id: "asset-polygons-outline", type: "line", source: "assets",
      filter: ["==", ["geometry-type"], "Polygon"],
      paint: { "line-color": "#0b3d63", "line-width": 2 },
    });
    map.addLayer({
      id: "asset-lines-casing", type: "line", source: "assets",
      filter: ["==", ["geometry-type"], "LineString"],
      paint: { "line-color": "#ffffff", "line-width": 6.5 },
      layout: { "line-cap": "round", "line-join": "round" },
    });
    map.addLayer({
      id: "asset-lines", type: "line", source: "assets",
      filter: ["==", ["geometry-type"], "LineString"],
      paint: {
        "line-color": [
          "match", ["get", "current_condition"],
          "GOOD", CONDITION_COLOR.GOOD, "FAIR", CONDITION_COLOR.FAIR,
          "POOR", CONDITION_COLOR.POOR, "CRITICAL", CONDITION_COLOR.CRITICAL,
          "#0b3d63",
        ],
        "line-width": 4,
      },
      layout: { "line-cap": "round", "line-join": "round" },
    });
    map.addLayer({
      id: "asset-points", type: "circle", source: "assets",
      filter: ["==", ["geometry-type"], "Point"],
      paint: {
        "circle-radius": 8,
        "circle-color": [
          "match", ["get", "current_condition"],
          "GOOD", CONDITION_COLOR.GOOD, "FAIR", CONDITION_COLOR.FAIR,
          "POOR", CONDITION_COLOR.POOR, "CRITICAL", CONDITION_COLOR.CRITICAL,
          "#64748b",
        ],
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    });
  }

  if (!map.getSource("grievances")) {
    map.addSource("grievances", { type: "geojson", data: EMPTY_FC });
    map.addLayer({
      id: "grievance-points", type: "circle", source: "grievances",
      paint: {
        "circle-radius": 9,
        "circle-color": [
          "match", ["get", "severity"],
          "LOW", SEVERITY_COLOR.LOW, "MEDIUM", SEVERITY_COLOR.MEDIUM,
          "HIGH", SEVERITY_COLOR.HIGH, "CRITICAL", SEVERITY_COLOR.CRITICAL,
          "#f97316",
        ],
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
        "circle-opacity": ["match", ["get", "status"], "RESOLVED", 0.35, "REJECTED", 0.35, 1],
      },
    });
    map.addLayer({
      id: "grievance-labels", type: "symbol", source: "grievances",
      layout: { "text-field": "!", "text-size": 12, "text-allow-overlap": true },
      paint: { "text-color": "#ffffff" },
    });
  }
}

export default function GisMap() {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [basemap, setBasemap] = useState<BasemapKind>("satellite");
  const [showAssets, setShowAssets] = useState(true);
  const [showGrievances, setShowGrievances] = useState(true);
  const [assetType, setAssetType] = useState("");
  const [lifecycleStatus, setLifecycleStatus] = useState("");
  const [condition, setCondition] = useState("");
  const [mapReady, setMapReady] = useState(false);

  const { data: assetTypes } = useQuery({ queryKey: ["asset-types"], queryFn: listAssetTypes });
  const { data: geojson } = useQuery({
    queryKey: ["gis-assets", assetType, lifecycleStatus, condition],
    queryFn: () =>
      fetchAssetsGeoJSON({
        asset_type_code: assetType || undefined,
        lifecycle_status: lifecycleStatus || undefined,
        current_condition: condition || undefined,
      }),
  });
  const { data: grievancesGeojson } = useQuery({
    queryKey: ["gis-grievances"],
    queryFn: () => fetchGrievancesGeoJSON({}),
  });

  function zoomToAssets() {
    const map = mapRef.current;
    if (!map || !geojson?.features.length) return;
    const coordinates: [number, number][] = [];
    geojson.features.forEach((feature) => {
      if (feature.geometry) {
        collectCoordinates((feature.geometry as { coordinates?: unknown }).coordinates, coordinates);
      }
    });
    if (!coordinates.length) return;
    const bounds = coordinates.reduce(
      (result, coordinate) => result.extend(coordinate),
      new maplibregl.LngLatBounds(coordinates[0], coordinates[0]),
    );
    map.fitBounds(bounds, { padding: 72, maxZoom: 15, duration: 700 });
  }

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleFor("satellite"),
      center: [72.5714, 23.0225],
      zoom: 11,
      pitch: 30,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(new maplibregl.GeolocateControl({
      positionOptions: { enableHighAccuracy: true },
      trackUserLocation: false,
    }), "top-right");
    map.addControl(new maplibregl.FullscreenControl(), "top-right");
    map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");
    mapRef.current = map;

    const wireInteractions = () => {
      for (const layerId of ["asset-points", "asset-lines", "asset-polygons"]) {
        map.on("click", layerId, (e) => {
          const feature = e.features?.[0];
          if (!feature) return;
          const props = feature.properties as Record<string, string>;
          const content = document.createElement("div");
          const title = document.createElement("strong");
          title.textContent = props.name || "Asset";
          const detail = document.createElement("div");
          detail.className = "mt-1 text-xs text-slate-600";
          detail.textContent = `${props.asset_code} · ${props.asset_type_code} · ${props.lifecycle_status}${props.current_condition ? ` · ${props.current_condition}` : ""}`;
          const open = document.createElement("button");
          open.type = "button";
          open.className = "mt-2 block text-xs font-medium text-blue-700 underline";
          open.textContent = "Open asset record";
          open.addEventListener("click", () => navigate(`/assets/${props.id}`));
          content.append(title, detail, open);
          new maplibregl.Popup({ closeButton: true }).setLngLat(e.lngLat).setDOMContent(content).addTo(map);
        });
        map.on("mouseenter", layerId, () => (map.getCanvas().style.cursor = "pointer"));
        map.on("mouseleave", layerId, () => (map.getCanvas().style.cursor = ""));
      }

      map.on("click", "grievance-points", (e) => {
        const feature = e.features?.[0];
        if (!feature) return;
        const props = feature.properties as Record<string, string>;
        const content = document.createElement("div");
        const title = document.createElement("strong");
        title.textContent = `Grievance · ${props.title || "Reported issue"}`;
        const detail = document.createElement("div");
        detail.className = "mt-1 text-xs text-slate-600";
        detail.textContent = `${props.grievance_code} · ${props.category.replaceAll("_", " ")} · ${props.severity} · ${props.status}`;
        const open = document.createElement("button");
        open.type = "button";
        open.className = "mt-2 block text-xs font-medium text-blue-700 underline";
        open.textContent = "View grievances";
        open.addEventListener("click", () => navigate("/grievances"));
        content.append(title, detail, open);
        new maplibregl.Popup({ closeButton: true }).setLngLat(e.lngLat).setDOMContent(content).addTo(map);
      });
      map.on("mouseenter", "grievance-points", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "grievance-points", () => (map.getCanvas().style.cursor = ""));
    };

    map.on("load", () => {
      addDataLayers(map);
      wireInteractions();
      setMapReady(true);
    });

    map.getContainer().addEventListener("click", (e) => {
      const target = e.target as HTMLElement;
      const assetId = target.getAttribute?.("data-nav-asset");
      if (assetId) {
        e.preventDefault();
        navigate(`/assets/${assetId}`);
        return;
      }
      if (target.getAttribute?.("data-nav-grievances")) {
        e.preventDefault();
        navigate("/grievances");
      }
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Basemap switch: setStyle() wipes custom sources/layers, so re-add them once the new style loads.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;
    map.setStyle(styleFor(basemap));
    map.once("style.load", () => {
      addDataLayers(map);
      if (geojson) (map.getSource("assets") as maplibregl.GeoJSONSource | undefined)?.setData(geojson as GeoJSON.FeatureCollection);
      if (grievancesGeojson) (map.getSource("grievances") as maplibregl.GeoJSONSource | undefined)?.setData(grievancesGeojson as GeoJSON.FeatureCollection);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [basemap]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !geojson) return;
    const source = map.getSource("assets") as maplibregl.GeoJSONSource | undefined;
    source?.setData(geojson as GeoJSON.FeatureCollection);
  }, [geojson, mapReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !grievancesGeojson) return;
    const source = map.getSource("grievances") as maplibregl.GeoJSONSource | undefined;
    source?.setData(grievancesGeojson as GeoJSON.FeatureCollection);
  }, [grievancesGeojson, mapReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;
    const visibility = showAssets ? "visible" : "none";
    for (const id of ["asset-points", "asset-lines", "asset-lines-casing", "asset-polygons", "asset-polygons-outline"]) {
      if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", visibility);
    }
  }, [showAssets, mapReady, basemap]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;
    const visibility = showGrievances ? "visible" : "none";
    for (const id of ["grievance-points", "grievance-labels"]) {
      if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", visibility);
    }
  }, [showGrievances, mapReady, basemap]);

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">GIS Asset Map</h1>
        <p className="text-sm text-slate-500">Satellite view of roads, bridges, culverts, buildings, structures and citizen-reported grievances.</p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex rounded-md border border-slate-300 overflow-hidden text-sm">
          <button
            onClick={() => setBasemap("satellite")}
            className={`px-3 py-2 flex items-center gap-1.5 ${basemap === "satellite" ? "bg-rb-navy text-white" : "bg-white text-slate-600 hover:bg-slate-50"}`}
          >
            <Layers size={14} /> Satellite
          </button>
          <button
            onClick={() => setBasemap("streets")}
            className={`px-3 py-2 flex items-center gap-1.5 border-l border-slate-300 ${basemap === "streets" ? "bg-rb-navy text-white" : "bg-white text-slate-600 hover:bg-slate-50"}`}
          >
            <MapPin size={14} /> Streets
          </button>
        </div>

        <select value={assetType} onChange={(e) => setAssetType(e.target.value)} className="rounded-md border border-slate-300 px-3 py-2 text-sm">
          <option value="">All types</option>
          {assetTypes?.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
        </select>
        <select value={lifecycleStatus} onChange={(e) => setLifecycleStatus(e.target.value)} className="rounded-md border border-slate-300 px-3 py-2 text-sm">
          <option value="">All lifecycle statuses</option>
          <option value="OPERATIONAL">Operational</option>
          <option value="UNDER_CONSTRUCTION">Under Construction</option>
          <option value="MAINTENANCE_REQUIRED">Maintenance Required</option>
          <option value="UNDER_MAINTENANCE">Under Maintenance</option>
        </select>
        <select value={condition} onChange={(e) => setCondition(e.target.value)} className="rounded-md border border-slate-300 px-3 py-2 text-sm">
          <option value="">All conditions</option>
          <option value="GOOD">Good</option>
          <option value="FAIR">Fair</option>
          <option value="POOR">Poor</option>
          <option value="CRITICAL">Critical</option>
        </select>

        <label className="flex items-center gap-1.5 text-sm text-slate-600 ml-2">
          <input type="checkbox" checked={showAssets} onChange={(e) => setShowAssets(e.target.checked)} /> Assets
        </label>
        <label className="flex items-center gap-1.5 text-sm text-slate-600">
          <input type="checkbox" checked={showGrievances} onChange={(e) => setShowGrievances(e.target.checked)} />
          <TriangleAlert size={14} className="text-orange-500" /> Grievances
        </label>
        <button type="button" onClick={zoomToAssets} disabled={!geojson?.features.length} className="flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50">
          <LocateFixed size={14} /> Zoom to assets
        </button>

        <div className="ml-auto text-sm text-slate-500 self-center">
          {geojson?.features.length ?? 0} assets &middot; {grievancesGeojson?.features.length ?? 0} grievances
        </div>
      </div>
      <div className="relative flex-1 min-h-[520px] rounded-lg overflow-hidden border border-slate-200 shadow-sm">
        <div ref={containerRef} className="absolute inset-0" />
        <div className="absolute bottom-3 right-3 bg-white/95 backdrop-blur rounded-md shadow px-3 py-2 text-xs space-y-1 pointer-events-none">
          <div className="font-semibold text-slate-700 mb-1">Condition</div>
          {Object.entries(CONDITION_COLOR).map(([label, color]) => (
            <div key={label} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: color }} />
              <span className="text-slate-600">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
