from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.asset import Asset
from app.models.enums import SystemRole
from app.models.project import Project, ProjectAsset
from app.models.user import User
from app.schemas.project import ProjectAssetLink, ProjectCreate, ProjectRead, ProjectUpdate
from app.utils.audit import record_audit

router = APIRouter(prefix="/projects", tags=["projects"])

_WRITE_ROLES = [r.value for r in [SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.CIRCLE_DIVISION_OFFICER]]


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(*_WRITE_ROLES))):
    if db.query(Project).filter(Project.project_code == payload.project_code).first():
        raise HTTPException(status_code=409, detail="Project code already exists")
    project = Project(**payload.model_dump(), created_by=user.id)
    db.add(project)
    db.flush()
    record_audit(db, actor_id=user.id, action="PROJECT_CREATE", entity_type="project", entity_id=project.id, new_value={"name": project.name})
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: UUID, payload: ProjectUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(*_WRITE_ROLES))):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(project, field, value)
    record_audit(db, actor_id=user.id, action="PROJECT_UPDATE", entity_type="project", entity_id=project.id, new_value=changes)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/assets", status_code=201)
def link_asset(project_id: UUID, payload: ProjectAssetLink, db: Session = Depends(get_db), user: User = Depends(require_roles(*_WRITE_ROLES))):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    asset = db.get(Asset, payload.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    exists = db.query(ProjectAsset).filter(ProjectAsset.project_id == project_id, ProjectAsset.asset_id == payload.asset_id).first()
    if not exists:
        db.add(ProjectAsset(project_id=project_id, asset_id=payload.asset_id))
    asset.linked_project_id = project_id

    record_audit(db, actor_id=user.id, action="PROJECT_ASSET_LINK", entity_type="project", entity_id=project.id, new_value={"asset_id": str(payload.asset_id)})
    db.commit()
    return {"status": "linked"}


@router.get("/{project_id}/assets")
def list_project_assets(project_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = (
        db.query(Asset)
        .join(ProjectAsset, ProjectAsset.asset_id == Asset.id)
        .filter(ProjectAsset.project_id == project_id)
        .all()
    )
    return [{"id": a.id, "asset_code": a.asset_code, "name": a.name} for a in rows]
