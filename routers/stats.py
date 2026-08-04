from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=schemas.Stats)
def get_stats(station_id: int | None = None, db: Session = Depends(get_db)):
    def base(query):
        if station_id is not None:
            query = query.filter(models.QSO.station_id == station_id)
        return query

    total = base(db.query(func.count(models.QSO.id))).scalar() or 0

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month = (
        base(db.query(func.count(models.QSO.id)))
        .filter(models.QSO.datetime_utc >= month_start.replace(tzinfo=None))
        .scalar()
        or 0
    )

    max_distance = base(db.query(func.max(models.QSO.distance_km))).scalar()

    def top(column) -> str:
        row = (
            base(db.query(column, func.count(models.QSO.id).label("c")))
            .filter(column != "")
            .group_by(column)
            .order_by(func.count(models.QSO.id).desc())
            .first()
        )
        return row[0] if row else ""

    return schemas.Stats(
        total_qso=total,
        month_qso=month,
        max_distance_km=max_distance,
        top_band=top(models.QSO.band),
        top_mode=top(models.QSO.mode),
    )
