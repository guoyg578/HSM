"""全局配置：数据目录结构与数据库位置。

Docker 中通过环境变量 DATA_DIR=/data 挂载 Volume；本地开发默认 ./data。
"""
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))

DATABASE_DIR = DATA_DIR / "database"
AUDIO_DIR = DATA_DIR / "audio"
QSL_DIR = DATA_DIR / "qsl"
EXPORT_DIR = DATA_DIR / "export"
BACKUP_DIR = DATABASE_DIR / "backups"

DATABASE_PATH = DATABASE_DIR / "hsm.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# 自动备份：间隔（小时）与保留份数
BACKUP_INTERVAL_HOURS = int(os.environ.get("BACKUP_INTERVAL_HOURS", "24"))
BACKUP_KEEP = int(os.environ.get("BACKUP_KEEP", "7"))


def ensure_dirs() -> None:
    for d in (DATABASE_DIR, AUDIO_DIR, QSL_DIR, EXPORT_DIR, BACKUP_DIR):
        d.mkdir(parents=True, exist_ok=True)
