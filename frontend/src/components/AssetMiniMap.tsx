import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GeoJSONGeometry } from "../types";

const STYLE = "https://demotiles.maplibre.org/style.json";

function centerOf(geometry: GeoJSONGeometry): [number, number] {
  if (geometry.type === "Point") return geometry.coordinates as [number, number];
  if (geometry.type === "LineString") {
    const coords = geometry.coordinates as [number, number][];
    return coords[Math.floor(coords.length / 2)];
  }
  const rings = geometry.coordinates as [number, number][][];
  return rings[0][0];
}

export default function AssetMiniMap({ geometry }: { geometry: GeoJSONGeometry }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const center = centerOf(geometry);
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE,
      center,
      zoom: geometry.type === "Point" ? 14 : 12,
      interactive: true,
    });

    map.on("load", () => {
      map.addSource("asset-geom", { type: "geojson", data: geometry as GeoJSON.Geometry });
      if (geometry.type === "Point") {
        map.addLayer({ id: "asset-point", type: "circle", source: "asset-geom", paint: { "circle-radius": 8, "circle-color": "#0f766e" } });
      } else if (geometry.type === "LineString") {
        map.addLayer({ id: "asset-line", type: "line", source: "asset-geom", paint: { "line-color": "#0b3d63", "line-width": 4 } });
      } else {
        map.addLayer({ id: "asset-poly", type: "fill", source: "asset-geom", paint: { "fill-color": "#0f766e", "fill-opacity": 0.4 } });
        map.addLayer({ id: "asset-poly-outline", type: "line", source: "asset-geom", paint: { "line-color": "#0b3d63", "line-width": 2 } });
      }
    });

    return () => map.remove();
  }, [geometry]);

  return <div ref={containerRef} className="w-full h-64 rounded-md overflow-hidden border border-slate-200" />;
}
