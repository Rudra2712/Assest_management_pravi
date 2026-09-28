import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { fetchAssetsGeoJSON } from "../api/gis";
import { listAssetTypes } from "../api/admin";

const STYLE = "https://demotiles.maplibre.org/style.json";
const CONDITION_COLOR: Record<string, string> = {
  GOOD: "#059669", FAIR: "#d97706", POOR: "#ea580c", CRITICAL: "#dc2626",
};

export default function GisMap() {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [assetType, setAssetType] = useState("");
  const [lifecycleStatus, setLifecycleStatus] = useState("");
  const [condition, setCondition] = useState("");

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

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE,
      center: [73.87, 18.52],
      zoom: 10,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      map.addSource("assets", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "asset-points",
        type: "circle",
        source: "assets",
        filter: ["==", ["geometry-type"], "Point"],
        paint: {
          "circle-radius": 7,
          "circle-color": [
            "match", ["get", "current_condition"],
            "GOOD", CONDITION_COLOR.GOOD, "FAIR", CONDITION_COLOR.FAIR,
            "POOR", CONDITION_COLOR.POOR, "CRITICAL", CONDITION_COLOR.CRITICAL,
            "#64748b",
          ],
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "#ffffff",
        },
      });
      map.addLayer({
        id: "asset-lines",
        type: "line",
        source: "assets",
        filter: ["==", ["geometry-type"], "LineString"],
        paint: { "line-color": "#0b3d63", "line-width": 4 },
      });
      map.addLayer({
        id: "asset-polygons",
        type: "fill",
        source: "assets",
        filter: ["==", ["geometry-type"], "Polygon"],
        paint: { "fill-color": "#0f766e", "fill-opacity": 0.45 },
      });

      for (const layerId of ["asset-points", "asset-lines", "asset-polygons"]) {
        map.on("click", layerId, (e) => {
          const feature = e.features?.[0];
          if (!feature) return;
          const props = feature.properties as Record<string, string>;
          new maplibregl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(
              `<div style="font-size:13px"><strong>${props.name}</strong><br/>${props.asset_code}<br/>${props.asset_type_code} · ${props.lifecycle_status}${
                props.current_condition ? ` · ${props.current_condition}` : ""
              }<br/><a href="/assets/${props.id}" style="color:#0b3d63" data-asset-id="${props.id}">View details →</a></div>`
            )
            .addTo(map);
        });
        map.on("mouseenter", layerId, () => (map.getCanvas().style.cursor = "pointer"));
        map.on("mouseleave", layerId, () => (map.getCanvas().style.cursor = ""));
      }

      map.getContainer().addEventListener("click", (e) => {
        const target = e.target as HTMLElement;
        const assetId = target.getAttribute?.("data-asset-id");
        if (assetId) {
          e.preventDefault();
          navigate(`/assets/${assetId}`);
        }
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !geojson) return;
    const source = map.getSource("assets") as maplibregl.GeoJSONSource | undefined;
    source?.setData(geojson as GeoJSON.FeatureCollection);
  }, [geojson]);

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">GIS Asset Map</h1>
        <p className="text-sm text-slate-500">Spatial view of roads, bridges, culverts, buildings and structures.</p>
      </div>
      <div className="flex gap-3">
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
        <div className="ml-auto text-sm text-slate-500 self-center">{geojson?.features.length ?? 0} assets shown</div>
      </div>
      <div ref={containerRef} className="flex-1 min-h-[500px] rounded-lg overflow-hidden border border-slate-200" />
    </div>
  );
}
