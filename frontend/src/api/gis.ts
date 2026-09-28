import { api } from "./client";

export interface AssetFeatureCollection {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: GeoJSON.Geometry;
    properties: {
      id: string;
      asset_code: string;
      name: string;
      asset_type_code: string;
      lifecycle_status: string;
      current_condition: string | null;
      administrative_unit_id: string;
    };
  }>;
}

export async function fetchAssetsGeoJSON(params: Record<string, string | undefined>): Promise<AssetFeatureCollection> {
  const res = await api.get<AssetFeatureCollection>("/gis/assets.geojson", { params });
  return res.data;
}

export async function fetchNearbyGeoJSON(lat: number, lon: number, radius_m = 1000): Promise<AssetFeatureCollection> {
  const res = await api.get<AssetFeatureCollection>("/gis/nearby.geojson", { params: { lat, lon, radius_m } });
  return res.data;
}
