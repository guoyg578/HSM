from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import app_settings
import schemas
from backup import notify_settings_changed
from database import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=schemas.SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    return app_settings.get_all(db)


@router.get("/defaults", response_model=schemas.SettingsOut)
def get_defaults():
    """内置默认值（前端「恢复默认」用）。"""
    return app_settings.DEFAULTS


@router.put("", response_model=schemas.SettingsOut)
def update_settings(data: schemas.SettingsUpdate, db: Session = Depends(get_db)):
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    result = app_settings.update(db, changes)
    if changes.keys() & {"backup_interval_hours", "backup_keep"}:
        notify_settings_changed()
    return result
