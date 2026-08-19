from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
import schemas
from app_settings import get_bands
from database import get_db
from hamutils import freq_to_band, grid_distance_km
from qthgrid import qth_to_grid
from routers.stations import build_defaults

router = APIRouter(prefix="/api/qsos", tags=["qsos"])

_SORT_COLUMNS = {
    "date": models.QSO.datetime_utc,
    "freq": models.QSO.freq_mhz,
    "distance": models.QSO.distance_km,
}


@router.get("", response_model=schemas.QSOPage)
def list_qsos(
    station_id: int | None = None,
    q: str | None = Query(None, description="呼号/QTH/备注模糊搜索"),
    call: str | None = None,
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to: str | None = Query(None, description="YYYY-MM-DD"),
    freq_min: float | None = None,
    freq_max: float | None = None,
    band: str | None = None,
    mode: str | None = None,
    sort_by: str = Query("date", pattern="^(date|freq|distance)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(models.QSO)
    if station_id is not None:
        query = query.filter(models.QSO.station_id == station_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                models.QSO.call.ilike(like),
                models.QSO.qth.ilike(like),
                models.QSO.remark.ilike(like),
            )
        )
    if call:
        query = query.filter(models.QSO.call.ilike(f"%{call}%"))
    if date_from:
        query = query.filter(models.QSO.datetime_utc >= _parse_date(date_from))
    if date_to:
        query = query.filter(
            models.QSO.datetime_utc < _parse_date(date_to, end_of_day=True)
        )
    if freq_min is not None:
        query = query.filter(models.QSO.freq_mhz >= freq_min)
    if freq_max is not None:
        query = query.filter(models.QSO.freq_mhz <= freq_max)
    if band:
        query = query.filter(models.QSO.band == band)
    if mode:
        query = query.filter(models.QSO.mode == mode)

    total = query.count()
    col = _SORT_COLUMNS[sort_by]
    query = query.order_by(col.desc() if order == "desc" else col.asc())
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return schemas.QSOPage(total=total, page=page, page_size=page_size, items=items)


def _parse_date(value: str, end_of_day: bool = False) -> datetime:
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, f"日期格式应为 YYYY-MM-DD: {value}")
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt


@router.post("", response_model=schemas.QSOOut)
def create_qso(data: schemas.QSOCreate, db: Session = Depends(get_db)):
    station = db.get(models.Station, data.station_id)
    if not station:
        raise HTTPException(404, "电台不存在")

    fields = data.model_dump()
    # 快照字段：未显式传入时从电台配置继承
    defaults = build_defaults(station)
    for key in (
        "my_callsign",
        "my_qth",
        "my_grid",
        "my_equipment",
        "my_antenna",
        "my_power",
    ):
        if fields.get(key) is None:
            fields[key] = getattr(defaults, key)

    if fields.get("datetime_utc") is None:
        fields["datetime_utc"] = datetime.now(timezone.utc)
    _autofill(fields, get_bands(db))

    qso = models.QSO(**fields)
    db.add(qso)
    db.commit()
    return qso


@router.get("/{qso_id}", response_model=schemas.QSOOut)
def get_qso(qso_id: int, db: Session = Depends(get_db)):
    qso = db.get(models.QSO, qso_id)
    if not qso:
        raise HTTPException(404, "QSO 不存在")
    return qso


@router.put("/{qso_id}", response_model=schemas.QSOOut)
def update_qso(qso_id: int, data: schemas.QSOUpdate, db: Session = Depends(get_db)):
    qso = db.get(models.QSO, qso_id)
    if not qso:
        raise HTTPException(404, "QSO 不存在")
    changes = data.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(qso, key, value)

    # 频率变了但未显式给波段 → 重算；网格变了但未显式给距离 → 重算
    if "freq_mhz" in changes and "band" not in changes:
        qso.band = freq_to_band(qso.freq_mhz, get_bands(db))
    # QTH 变了而网格仍为空 → 按地名估算，视同网格变化以触发距离重算
    grid_filled = False
    if "qth" in changes and not qso.grid:
        hit = qth_to_grid(qso.qth)
        if hit:
            qso.grid = hit[0]
            grid_filled = True
    if (
        "grid" in changes or "my_grid" in changes or grid_filled
    ) and "distance_km" not in changes:
        qso.distance_km = grid_distance_km(qso.my_grid, qso.grid)
    db.commit()
    return qso


@router.delete("/{qso_id}", response_model=schemas.Message)
def delete_qso(qso_id: int, db: Session = Depends(get_db)):
    qso = db.get(models.QSO, qso_id)
    if not qso:
        raise HTTPException(404, "QSO 不存在")
    db.delete(qso)
    db.commit()
    return schemas.Message()


def _autofill(fields: dict, bands: list[tuple[float, float, str]] | None = None) -> None:
    """波段、网格与距离的自动推导（不覆盖显式传入值）。"""
    if not fields.get("band"):
        fields["band"] = freq_to_band(fields.get("freq_mhz"), bands)
    # 只填了 QTH 没填网格时按地名估算 4 位网格，让距离能算出来
    if not fields.get("grid"):
        hit = qth_to_grid(fields.get("qth") or "")
        if hit:
            fields["grid"] = hit[0]
    if fields.get("distance_km") is None:
        fields["distance_km"] = grid_distance_km(
            fields.get("my_grid") or "", fields.get("grid") or ""
        )
