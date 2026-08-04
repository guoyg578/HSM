from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/stations", tags=["stations"])


def _get_station(db: Session, station_id: int) -> models.Station:
    station = db.get(models.Station, station_id)
    if not station:
        raise HTTPException(404, "电台不存在")
    return station


@router.get("", response_model=list[schemas.StationOut])
def list_stations(db: Session = Depends(get_db)):
    return db.query(models.Station).order_by(models.Station.id).all()


@router.post("", response_model=schemas.StationDetail)
def create_station(data: schemas.StationCreate, db: Session = Depends(get_db)):
    station = models.Station(**data.model_dump())
    db.add(station)
    db.commit()
    return station


@router.get("/{station_id}", response_model=schemas.StationDetail)
def get_station(station_id: int, db: Session = Depends(get_db)):
    return _get_station(db, station_id)


@router.put("/{station_id}", response_model=schemas.StationDetail)
def update_station(
    station_id: int, data: schemas.StationUpdate, db: Session = Depends(get_db)
):
    station = _get_station(db, station_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(station, key, value)
    db.commit()
    return station


@router.delete("/{station_id}", response_model=schemas.Message)
def delete_station(station_id: int, db: Session = Depends(get_db)):
    db.delete(_get_station(db, station_id))
    db.commit()
    return schemas.Message()


# ---------- 设备 ----------
@router.post("/{station_id}/equipments", response_model=schemas.EquipmentOut)
def add_equipment(
    station_id: int, data: schemas.EquipmentBase, db: Session = Depends(get_db)
):
    _get_station(db, station_id)
    item = models.Equipment(station_id=station_id, **data.model_dump())
    db.add(item)
    db.commit()
    return item


@router.put("/{station_id}/equipments/{item_id}", response_model=schemas.EquipmentOut)
def update_equipment(
    station_id: int,
    item_id: int,
    data: schemas.EquipmentBase,
    db: Session = Depends(get_db),
):
    item = db.get(models.Equipment, item_id)
    if not item or item.station_id != station_id:
        raise HTTPException(404, "设备不存在")
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    return item


@router.delete("/{station_id}/equipments/{item_id}", response_model=schemas.Message)
def delete_equipment(station_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Equipment, item_id)
    if not item or item.station_id != station_id:
        raise HTTPException(404, "设备不存在")
    db.delete(item)
    db.commit()
    return schemas.Message()


# ---------- 天线 ----------
@router.post("/{station_id}/antennas", response_model=schemas.AntennaOut)
def add_antenna(
    station_id: int, data: schemas.AntennaBase, db: Session = Depends(get_db)
):
    _get_station(db, station_id)
    item = models.Antenna(station_id=station_id, **data.model_dump())
    db.add(item)
    db.commit()
    return item


@router.put("/{station_id}/antennas/{item_id}", response_model=schemas.AntennaOut)
def update_antenna(
    station_id: int,
    item_id: int,
    data: schemas.AntennaBase,
    db: Session = Depends(get_db),
):
    item = db.get(models.Antenna, item_id)
    if not item or item.station_id != station_id:
        raise HTTPException(404, "天线不存在")
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    return item


@router.delete("/{station_id}/antennas/{item_id}", response_model=schemas.Message)
def delete_antenna(station_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Antenna, item_id)
    if not item or item.station_id != station_id:
        raise HTTPException(404, "天线不存在")
    db.delete(item)
    db.commit()
    return schemas.Message()


# ---------- 功率配置 ----------
@router.post("/{station_id}/power-profiles", response_model=schemas.PowerProfileOut)
def add_power_profile(
    station_id: int, data: schemas.PowerProfileBase, db: Session = Depends(get_db)
):
    _get_station(db, station_id)
    item = models.PowerProfile(station_id=station_id, **data.model_dump())
    db.add(item)
    db.commit()
    return item


@router.put(
    "/{station_id}/power-profiles/{item_id}", response_model=schemas.PowerProfileOut
)
def update_power_profile(
    station_id: int,
    item_id: int,
    data: schemas.PowerProfileBase,
    db: Session = Depends(get_db),
):
    item = db.get(models.PowerProfile, item_id)
    if not item or item.station_id != station_id:
        raise HTTPException(404, "功率配置不存在")
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    return item


@router.delete("/{station_id}/power-profiles/{item_id}", response_model=schemas.Message)
def delete_power_profile(station_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.PowerProfile, item_id)
    if not item or item.station_id != station_id:
        raise HTTPException(404, "功率配置不存在")
    db.delete(item)
    db.commit()
    return schemas.Message()


# ---------- 新建 QSO 时的继承信息 ----------
@router.get("/{station_id}/qso-defaults", response_model=schemas.QSODefaults)
def qso_defaults(station_id: int, db: Session = Depends(get_db)):
    station = _get_station(db, station_id)
    return build_defaults(station)


def build_defaults(station: models.Station) -> schemas.QSODefaults:
    equipment = ""
    if station.equipments:
        e = station.equipments[0]
        equipment = " ".join(x for x in (e.brand, e.model) if x)
    antenna = station.antennas[0].name if station.antennas else ""
    power = ""
    if station.power_profiles:
        p = station.power_profiles[0]
        power = f"{p.power_watts:g}W"
    return schemas.QSODefaults(
        my_callsign=station.callsign,
        my_qth=station.qth,
        my_grid=station.grid,
        my_equipment=equipment,
        my_antenna=antenna,
        my_power=power,
        power_profiles=station.power_profiles,
    )
