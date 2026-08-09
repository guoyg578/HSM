"""运行时可配置项：模式选项、新建 QSO 默认值、波段表、备份参数。

存 settings 表（key + JSON value），后台管理页编辑，保存即生效。
环境变量 BACKUP_INTERVAL_HOURS / BACKUP_KEEP 仅作初始默认值，
在后台保存过之后以数据库为准。
"""
import json

from sqlalchemy.orm import Session

import models
from config import BACKUP_INTERVAL_HOURS, BACKUP_KEEP
from hamutils import DEFAULT_BANDS

DEFAULTS: dict = {
    "mode_options": [
        "FM",
        "FMO",
        "SSB",
        "CW",
        "AM",
        "FT8",
        "FT4",
        "RTTY",
        "DMR",
        "C4FM",
        "D-STAR",
        "Digital",
    ],
    "default_mode": "FM",
    "default_rst": "59",
    "bands": [
        {"low_mhz": low, "high_mhz": high, "name": name}
        for low, high, name in DEFAULT_BANDS
    ],
    "backup_interval_hours": BACKUP_INTERVAL_HOURS,
    "backup_keep": BACKUP_KEEP,
}


def get_all(db: Session) -> dict:
    """默认值与数据库覆盖项合并后的完整配置。"""
    result = {k: v for k, v in DEFAULTS.items()}
    for row in db.query(models.Setting).all():
        if row.key in DEFAULTS:
            try:
                result[row.key] = json.loads(row.value)
            except ValueError:
                pass  # 损坏的值回退默认
    return result


def update(db: Session, changes: dict) -> dict:
    for key, value in changes.items():
        if key not in DEFAULTS:
            continue
        row = db.get(models.Setting, key)
        if row is None:
            db.add(models.Setting(key=key, value=json.dumps(value)))
        else:
            row.value = json.dumps(value)
    db.commit()
    return get_all(db)


def get_bands(db: Session) -> list[tuple[float, float, str]]:
    """配置后的波段表 → freq_to_band 使用的 (low, high, name) 列表。"""
    return [
        (b["low_mhz"], b["high_mhz"], b["name"]) for b in get_all(db)["bands"]
    ]


def backup_settings() -> tuple[int, int]:
    """(备份间隔小时, 保留份数) —— 供备份线程使用，自带会话。"""
    from database import SessionLocal

    db = SessionLocal()
    try:
        s = get_all(db)
        return int(s["backup_interval_hours"]), int(s["backup_keep"])
    finally:
        db.close()
