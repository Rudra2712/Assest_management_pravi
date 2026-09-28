import random
import string
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.contractor import Contractor
from app.models.enums import SystemRole, TenderBidStatus, TenderStatus
from app.models.tender import Tender, TenderBid
from app.models.user import User
from app.schemas.tender import TenderAward, TenderBidCreate, TenderBidRead, TenderCreate, TenderRead
from app.utils.audit import record_audit
from app.permissions.jurisdiction import user_role_codes

router = APIRouter(prefix="/tenders", tags=["tenders"])

_PROCUREMENT_ROLES = [r.value for r in [SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN]]


def _generate_tender_number() -> str:
    year = date.today().year
    suffix = "".join(random.choices(string.digits, k=6))
    return f"GEM/{year}/RB/{suffix}"


def _bid_to_read(bid: TenderBid) -> TenderBidRead:
    return TenderBidRead.model_validate(bid).model_copy(update={"contractor_name": bid.contractor.name})


def _to_read(t: Tender, *, can_review_bids: bool, contractor_id: UUID | None) -> TenderRead:
    data = TenderRead.model_validate(t)
    visible_bids = []
    if can_review_bids:
        visible_bids = t.bids
    else:
        if contractor_id:
            visible_bids.extend(b for b in t.bids if b.contractor_id == contractor_id)
        if t.status == TenderStatus.AWARDED and t.awarded_bid:
            visible_bids.append(t.awarded_bid)
    data.bid_count = len(t.bids) if can_review_bids or t.status != TenderStatus.PUBLISHED else 0
    data.bids = [_bid_to_read(bid) for bid in {bid.id: bid for bid in visible_bids}.values()]
    return data


def _tender_query(db: Session):
    return db.query(Tender).options(joinedload(Tender.bids).joinedload(TenderBid.contractor), joinedload(Tender.awarded_bid).joinedload(TenderBid.contractor))


@router.get("", response_model=list[TenderRead])
def list_tenders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status: TenderStatus | None = None,
    asset_id: UUID | None = None,
):
    roles = user_role_codes(user)
    can_review_bids = bool(roles & set(_PROCUREMENT_ROLES))
    contractor = db.query(Contractor).filter(Contractor.user_id == user.id).first() if SystemRole.CONTRACTOR.value in roles else None
    query = _tender_query(db)
    if SystemRole.CONTRACTOR.value in roles:
        query = query.filter(Tender.status != TenderStatus.DRAFT)
    if status:
        query = query.filter(Tender.status == status)
    if asset_id:
        query = query.filter(Tender.asset_id == asset_id)
    rows = query.order_by(Tender.created_at.desc()).all()
    return [_to_read(t, can_review_bids=can_review_bids, contractor_id=contractor.id if contractor else None) for t in rows]


@router.post("", response_model=TenderRead, status_code=201)
def create_tender(
    payload: TenderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_PROCUREMENT_ROLES)),
):
    tender = Tender(
        tender_number=_generate_tender_number(),
        status=TenderStatus.PUBLISHED,
        published_date=date.today(),
        created_by=user.id,
        **payload.model_dump(),
    )
    db.add(tender)
    db.flush()
    record_audit(db, actor_id=user.id, action="TENDER_PUBLISH", entity_type="tender", entity_id=tender.id, new_value={"tender_number": tender.tender_number, "title": tender.title})
    db.commit()
    db.refresh(tender)
    tender = _tender_query(db).filter(Tender.id == tender.id).first()
    return _to_read(tender, can_review_bids=True, contractor_id=None)


@router.get("/my-bids", response_model=list[TenderRead])
def list_my_bids(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(SystemRole.CONTRACTOR)),
):
    contractor = db.query(Contractor).filter(Contractor.user_id == user.id).first()
    if not contractor:
        return []
    tender_ids = [row[0] for row in db.query(TenderBid.tender_id).filter(TenderBid.contractor_id == contractor.id).all()]
    if not tender_ids:
        return []
    tenders = _tender_query(db).filter(Tender.id.in_(tender_ids)).order_by(Tender.created_at.desc()).all()
    return [_to_read(tender, can_review_bids=False, contractor_id=contractor.id) for tender in tenders]


@router.get("/{tender_id}", response_model=TenderRead)
def get_tender(tender_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tender = _tender_query(db).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    roles = user_role_codes(user)
    if tender.status == TenderStatus.DRAFT and not roles & set(_PROCUREMENT_ROLES):
        raise HTTPException(status_code=404, detail="Tender not found")
    contractor = db.query(Contractor).filter(Contractor.user_id == user.id).first() if SystemRole.CONTRACTOR.value in roles else None
    return _to_read(tender, can_review_bids=bool(roles & set(_PROCUREMENT_ROLES)), contractor_id=contractor.id if contractor else None)


@router.post("/{tender_id}/bids", response_model=TenderBidRead, status_code=201)
def submit_bid(
    tender_id: UUID,
    payload: TenderBidCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(SystemRole.CONTRACTOR)),
):
    tender = db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    if tender.status != TenderStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Bidding is not open for this tender")
    if tender.submission_deadline and date.today() > tender.submission_deadline:
        raise HTTPException(status_code=400, detail="Submission deadline has passed")

    contractor = db.query(Contractor).filter(Contractor.user_id == user.id).first()
    if not contractor:
        raise HTTPException(status_code=400, detail="No contractor profile linked to this account")
    if db.query(TenderBid).filter(TenderBid.tender_id == tender_id, TenderBid.contractor_id == contractor.id).first():
        raise HTTPException(status_code=409, detail="You have already submitted a bid for this tender")

    bid = TenderBid(tender_id=tender_id, contractor_id=contractor.id, bid_amount=payload.bid_amount, remarks=payload.remarks)
    db.add(bid)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="You have already submitted a bid for this tender") from exc
    record_audit(db, actor_id=user.id, action="TENDER_BID_SUBMIT", entity_type="tender", entity_id=tender.id, new_value={"contractor_id": str(contractor.id), "bid_amount": payload.bid_amount})
    db.commit()
    db.refresh(bid)
    bid = db.query(TenderBid).options(joinedload(TenderBid.contractor)).filter(TenderBid.id == bid.id).one()
    return _bid_to_read(bid)


@router.post("/{tender_id}/close", response_model=TenderRead)
def close_bidding(
    tender_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_PROCUREMENT_ROLES)),
):
    tender = _tender_query(db).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    if tender.status != TenderStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Only a published tender can be closed for bidding")
    tender.status = TenderStatus.BIDDING_CLOSED
    record_audit(db, actor_id=user.id, action="TENDER_CLOSE", entity_type="tender", entity_id=tender.id)
    db.commit()
    db.refresh(tender)
    tender = _tender_query(db).filter(Tender.id == tender.id).first()
    return _to_read(tender, can_review_bids=True, contractor_id=None)


@router.post("/{tender_id}/award", response_model=TenderRead)
def award_tender(
    tender_id: UUID,
    payload: TenderAward,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_PROCUREMENT_ROLES)),
):
    tender = _tender_query(db).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    if tender.status != TenderStatus.BIDDING_CLOSED:
        raise HTTPException(status_code=400, detail=f"Cannot award a tender in status {tender.status.value}")
    if not tender.bids:
        raise HTTPException(status_code=400, detail="A tender needs at least one bid before it can be awarded")

    bid = next((b for b in tender.bids if b.id == payload.bid_id), None)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found for this tender")

    for b in tender.bids:
        b.status = TenderBidStatus.AWARDED if b.id == bid.id else TenderBidStatus.REJECTED

    tender.awarded_bid_id = bid.id
    tender.awarded_at = datetime.now(timezone.utc)
    tender.status = TenderStatus.AWARDED

    record_audit(db, actor_id=user.id, action="TENDER_AWARD", entity_type="tender", entity_id=tender.id, new_value={"bid_id": str(bid.id), "contractor_id": str(bid.contractor_id), "bid_amount": float(bid.bid_amount)})
    db.commit()
    db.refresh(tender)
    tender = _tender_query(db).filter(Tender.id == tender.id).first()
    return _to_read(tender, can_review_bids=True, contractor_id=None)


@router.post("/{tender_id}/cancel", response_model=TenderRead)
def cancel_tender(
    tender_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_PROCUREMENT_ROLES)),
):
    tender = _tender_query(db).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    if tender.status == TenderStatus.AWARDED:
        raise HTTPException(status_code=400, detail="Cannot cancel an already-awarded tender")
    tender.status = TenderStatus.CANCELLED
    record_audit(db, actor_id=user.id, action="TENDER_CANCEL", entity_type="tender", entity_id=tender.id)
    db.commit()
    db.refresh(tender)
    tender = _tender_query(db).filter(Tender.id == tender.id).first()
    return _to_read(tender, can_review_bids=True, contractor_id=None)
