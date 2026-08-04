# ---------- 阶段 1：构建前端 ----------
FROM node:22-alpine AS frontend
WORKDIR /build
RUN npm install -g pnpm@10
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

# ---------- 阶段 2：后端运行镜像 ----------
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# 先装依赖（利用 Docker 层缓存）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 后端代码 + 前端构建产物
COPY *.py ./
COPY routers/ ./routers/
COPY --from=frontend /build/dist ./frontend/dist

ENV DATA_DIR=/data \
    PATH="/app/.venv/bin:$PATH"

VOLUME /data
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
