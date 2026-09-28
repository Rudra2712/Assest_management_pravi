"""GeoJSON validation and geometry-kind helpers."""

from typing import Any

from shapely.geometry import shape

from app.models.enums import GeometryKind

GEOJSON_TYPE_TO_KIND = {
    "Point": GeometryKind.POINT,
    "LineString": GeometryKind.LINESTRING,
    "Polygon": GeometryKind.POLYGON,
}
KIND_TO_GEOJSON_TYPE = {v: k for k, v in GEOJSON_TYPE_TO_KIND.items()}


def geojson_to_geometry_kind(geojson: dict[str, Any]) -> GeometryKind:
    geom_type = geojson.get("type")
    if geom_type not in GEOJSON_TYPE_TO_KIND:
        raise ValueError(f"Unsupported geometry type '{geom_type}'. Expected Point, LineString or Polygon.")
    return GEOJSON_TYPE_TO_KIND[geom_type]


def geojson_to_geometry(geojson: dict[str, Any]) -> dict[str, Any]:
    shape(geojson)
    return geojson


def geometry_to_geojson(geometry: dict[str, Any] | None) -> dict[str, Any] | None:
    return geometry
