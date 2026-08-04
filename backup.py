"""SQLite 自动备份：后台线程定时把数据库复制到 backups 目录，保留最近 N 份。"""
import logging
import shutil
import sqlite3
import threading
from datetime import datetime, timezone

from config import BACKUP_DIR, BACKUP_INTERVAL_HOURS, BACKUP_KEEP, DATABASE_PATH

logger = logging.getLogger(__name__)

_stop_event = threading.Event()


def backup_once() -> str | None:
    if not DATABASE_PATH.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"hsm_{stamp}.db"
    # 用 sqlite backup API 保证一致性（避免直接复制正在写入的文件）
    src = sqlite3.connect(DATABASE_PATH)
    try:
        dst = sqlite3.connect(dest)
        with dst:
            src.backup(dst)
        dst.close()
    finally:
        src.close()
    _prune()
    logger.info("数据库已备份到 %s", dest)
    return str(dest)


def _prune() -> None:
    backups = sorted(BACKUP_DIR.glob("hsm_*.db"))
    for old in backups[:-BACKUP_KEEP]:
        try:
            old.unlink()
        except OSError:
            pass


def _worker() -> None:
    while not _stop_event.wait(BACKUP_INTERVAL_HOURS * 3600):
        try:
            backup_once()
        except Exception:
            logger.exception("自动备份失败")


def start_backup_thread() -> None:
    t = threading.Thread(target=_worker, name="db-backup", daemon=True)
    t.start()


def stop_backup_thread() -> None:
    _stop_event.set()
