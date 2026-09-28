from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.asset import AssetCategory, AssetType
from app.models.enums import AssetTypeCode, GeometryKind
from app.schemas.common import ORMModel

router = APIRouter(prefix="/asset-types", tags=["asset-types"])


class AssetTypeRead(ORMModel):
    id: UUID
    code: AssetTypeCode
    name: str
    default_geometry_kind: GeometryKind
    category_id: UUID | None = None


class AssetCategoryRead(ORMModel):
    id: UUID
    code: str
    name: str


@router.get("", response_model=list[AssetTypeRead])
def list_asset_types(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(AssetType).order_by(AssetType.name).all()


@router.get("/categories", response_model=list[AssetCategoryRead])
def list_categories(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(AssetCategory).order_by(AssetCategory.name).all()
