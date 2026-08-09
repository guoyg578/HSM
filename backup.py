"""SQLite 自动备份：后台线程定时把数据库复制到 backups 目录，保留最近 N 份。

间隔与保留份数从运行时配置读取（后台管理页可改），
配置变更后线程被唤醒并按新间隔重新计时。
"""
import logging
import sqlite3
import threading
from datetime import datetime, timezone

from config import BACKUP_DIR, DATABASE_PATH

logger = logging.getLogger(__name__)

_stop_event = threading.Event()
_settings_changed = threading.Event()


def notify_settings_changed() -> None:
    """后台管理修改了备份配置：唤醒线程重新计时。"""
    _settings_changed.set()


def backup_once() -> str | None:
    from app_settings import backup_settings

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
    _, keep = backup_settings()
    _prune(keep)
    logger.info("数据库已备份到 %s", dest)
    return str(dest)


def _prune(keep: int) -> None:
    backups = sorted(BACKUP_DIR.glob("hsm_*.db"))
    for old in backups[:-keep]:
        try:
            old.unlink()
        except OSError:
            pass


def _worker() -> None:
    from app_settings import backup_settings

    while not _stop_event.is_set():
        interval_hours, _ = backup_settings()
        changed = _settings_changed.wait(interval_hours * 3600)
        if _stop_event.is_set():
            break
        if changed:
            _settings_changed.clear()  # 按新间隔重新计时
            continue
        try:
            backup_once()
        except Exception:
            logger.exception("自动备份失败")


def start_backup_thread() -> None:
    t = threading.Thread(target=_worker, name="db-backup", daemon=True)
    t.start()


def stop_backup_thread() -> None:
    _stop_event.set()
    _settings_changed.set()
