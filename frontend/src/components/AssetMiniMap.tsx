import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GeoJSONGeometry } from "../types";
import { SATELLITE_STYLE } from "../lib/mapStyle";

function boundsOf(geometry: GeoJSONGeometry): maplibregl.LngLatBounds {
  const bounds = new maplibregl.LngLatBounds();
  const extend = (coords: unknown): void => {
    if (Array.isArray(coords) && typeof coords[0] === "number") {
      bounds.extend(coords as [number, number]);
    } else if (Array.isArray(coords)) {
      coords.forEach(extend);
    }
  };
  extend(geometry.coordinates);
  return bounds;
}

export default function AssetMiniMap({ geometry }: { geometry: GeoJSONGeometry }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const bounds = boundsOf(geometry);
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: SATELLITE_STYLE,
      center: bounds.getCenter(),
      zoom: geometry.type === "Point" ? 15 : 13,
      interactive: true,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    map.on("load", () => {
      map.addSource("asset-geom", { type: "geojson", data: geometry as GeoJSON.Geometry });
      if (geometry.type === "Point") {
        map.addLayer({ id: "asset-point-halo", type: "circle", source: "asset-geom", paint: { "circle-radius": 14, "circle-color": "#0f766e", "circle-opacity": 0.25 } });
        map.addLayer({ id: "asset-point", type: "circle", source: "asset-geom", paint: { "circle-radius": 7, "circle-color": "#0f766e", "circle-stroke-width": 2, "circle-stroke-color": "#ffffff" } });
      } else if (geometry.type === "LineString") {
        map.addLayer({ id: "asset-line-casing", type: "line", source: "asset-geom", paint: { "line-color": "#ffffff", "line-width": 7 }, layout: { "line-cap": "round" } });
        map.addLayer({ id: "asset-line", type: "line", source: "asset-geom", paint: { "line-color": "#0b3d63", "line-width": 4 }, layout: { "line-cap": "round" } });

        const coords = geometry.coordinates as [number, number][];
        const start = coords[0];
        const end = coords[coords.length - 1];
        new maplibregl.Marker({ color: "#059669" }).setLngLat(start).setPopup(new maplibregl.Popup({ offset: 12 }).setText("Start")).addTo(map);
        new maplibregl.Marker({ color: "#dc2626" }).setLngLat(end).setPopup(new maplibregl.Popup({ offset: 12 }).setText("End")).addTo(map);
      } else {
        map.addLayer({ id: "asset-poly", type: "fill", source: "asset-geom", paint: { "fill-color": "#0f766e", "fill-opacity": 0.4 } });
        map.addLayer({ id: "asset-poly-outline", type: "line", source: "asset-geom", paint: { "line-color": "#0b3d63", "line-width": 2 } });
      }

      if (!bounds.isEmpty() && geometry.type !== "Point") {
        map.fitBounds(bounds, { padding: 40, maxZoom: 16, duration: 0 });
      }
    });

    return () => map.remove();
  }, [geometry]);

  return <div ref={containerRef} className="w-full h-64 rounded-md overflow-hidden border border-slate-200" />;
}
