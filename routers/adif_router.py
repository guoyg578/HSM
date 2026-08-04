from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from adif import adif_record_to_qso_fields, export_adif, parse_adif
from config import EXPORT_DIR
from database import get_db
from routers.qsos import _autofill
from routers.stations import build_defaults

router = APIRouter(prefix="/api/adif", tags=["adif"])


@router.get("/export")
def adif_export(station_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.QSO).order_by(models.QSO.datetime_utc)
    if station_id is not None:
        if not db.get(models.Station, station_id):
            raise HTTPException(404, "电台不存在")
        query = query.filter(models.QSO.station_id == station_id)
    qsos = query.all()

    content = export_adif(qsos)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = f"_station{station_id}" if station_id is not None else ""
    filename = f"hsm_export{suffix}_{stamp}.adi"
    path = EXPORT_DIR / filename
    path.write_text(content, encoding="utf-8")
    return FileResponse(path, filename=filename, media_type="application/octet-stream")


class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str] = []


@router.post("/import", response_model=ImportResult)
async def adif_import(
    station_id: int, file: UploadFile, db: Session = Depends(get_db)
):
    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "电台不存在")

    content = await file.read()
    records = parse_adif(content)
    if not records:
        raise HTTPException(400, "未解析到任何 ADIF 记录")

    defaults = build_defaults(station)
    imported, skipped, errors = 0, 0, []
    for i, rec in enumerate(records, 1):
        try:
            fields = adif_record_to_qso_fields(rec)
            if not fields["call"]:
                skipped += 1
                continue
            # 快照字段：ADIF 未提供时从当前电台继承
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
            if fields["datetime_utc"] is None:
                fields["datetime_utc"] = datetime.now(timezone.utc)
            _autofill(fields)
            db.add(models.QSO(station_id=station_id, **fields))
            imported += 1
        except Exception as e:  # 单条失败不阻断整体导入
            errors.append(f"第{i}条: {e}")
    db.commit()
    return ImportResult(imported=imported, skipped=skipped, errors=errors[:20])
