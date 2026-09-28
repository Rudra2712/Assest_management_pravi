"""GeoJSON <-> PostGIS conversion helpers. Keeps Shapely/GeoAlchemy2 details
out of routers and services, which only ever see plain GeoJSON dicts."""

from typing import Any

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry

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


def geojson_to_wkb(geojson: dict[str, Any], srid: int = 4326):
    geom: BaseGeometry = shape(geojson)
    return from_shape(geom, srid=srid)


def wkb_to_geojson(wkb_element) -> dict[str, Any] | None:
    if wkb_element is None:
        return None
    geom = to_shape(wkb_element)
    return mapping(geom)
