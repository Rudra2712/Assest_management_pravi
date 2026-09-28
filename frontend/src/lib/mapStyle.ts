import type { StyleSpecification } from "maplibre-gl";

/** Esri World Imagery — free, no API key, standard choice for demo/prototype
 * satellite basemaps. Attribution is required and included below. */
export const SATELLITE_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    satellite: {
      type: "raster",
      tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
      tileSize: 256,
      maxzoom: 19,
      attribution: "Esri, Maxar, Earthstar Geographics",
    },
    "satellite-labels": {
      type: "raster",
      tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"],
      tileSize: 256,
      maxzoom: 19,
      attribution: "Esri",
    },
    transportation: {
      type: "raster",
      tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Transportation/MapServer/tile/{z}/{y}/{x}"],
      tileSize: 256,
      maxzoom: 19,
      attribution: "Esri transportation data",
    },
  },
  layers: [
    { id: "satellite", type: "raster", source: "satellite" },
    { id: "transportation", type: "raster", source: "transportation", paint: { "raster-opacity": 0.85 } },
    { id: "satellite-labels", type: "raster", source: "satellite-labels" },
  ],
};

/** Plain OSM raster tiles as the alternate "streets" basemap for the toggle. */
export const STREETS_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      maxzoom: 19,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

export type BasemapKind = "satellite" | "streets";

export function styleFor(kind: BasemapKind): StyleSpecification {
  return kind === "satellite" ? SATELLITE_STYLE : STREETS_STYLE;
}
