import re
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

import schemas
from backup import backup_once
from config import AUDIO_DIR, QSL_DIR

router = APIRouter(prefix="/api", tags=["files"])

_ALLOWED = {
    "audio": (AUDIO_DIR, {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".opus"}),
    "qsl": (QSL_DIR, {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}),
}

_MAX_SIZE = 100 * 1024 * 1024  # 100MB


def _save(kind: str, file: UploadFile) -> schemas.UploadResult:
    target_dir, allowed_exts = _ALLOWED[kind]
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed_exts:
        raise HTTPException(400, f"不支持的文件类型: {suffix or '(无扩展名)'}")
    stem = re.sub(r"[^\w\-]", "_", Path(file.filename or "file").stem)[:50]
    name = f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
    dest = target_dir / name

    size = 0
    with dest.open("wb") as f:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > _MAX_SIZE:
                f.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(400, "文件超过 100MB 限制")
            f.write(chunk)
    rel = f"{kind}/{name}"
    return schemas.UploadResult(path=rel, url=f"/files/{rel}")


@router.post("/upload/audio", response_model=schemas.UploadResult)
def upload_audio(file: UploadFile):
    return _save("audio", file)


@router.post("/upload/qsl", response_model=schemas.UploadResult)
def upload_qsl(file: UploadFile):
    return _save("qsl", file)


@router.post("/backup", response_model=schemas.Message)
def trigger_backup():
    dest = backup_once()
    if not dest:
        raise HTTPException(500, "数据库文件不存在，备份失败")
    return schemas.Message(message=f"已备份: {dest}")
