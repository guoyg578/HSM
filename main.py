"""HAM Station Manager — FastAPI 应用入口。

启动：uv run uvicorn main:app --reload
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import models  # noqa: F401  确保建表前模型已注册
from backup import start_backup_thread, stop_backup_thread
from config import AUDIO_DIR, QSL_DIR, ensure_dirs
from database import Base, engine, run_migrations
from routers import adif_router, files, qsos, stations, stats

logging.basicConfig(level=logging.INFO)

FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    Base.metadata.create_all(engine)
    run_migrations()
    start_backup_thread()
    yield
    stop_backup_thread()


app = FastAPI(title="HAM Station Manager", version="1.1", lifespan=lifespan)

app.include_router(stations.router)
app.include_router(qsos.router)
app.include_router(stats.router)
app.include_router(files.router)
app.include_router(adif_router.router)

# 上传文件访问（只暴露 audio / qsl，不暴露 database）
app.mount("/files/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
app.mount("/files/qsl", StaticFiles(directory=QSL_DIR), name="qsl")


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 前端静态文件（构建产物存在时托管，SPA 路由回退到 index.html）
if FRONTEND_DIST.exists():
    app.mount(
        "/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets"
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file() and candidate.resolve().is_relative_to(
            FRONTEND_DIST.resolve()
        ):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
