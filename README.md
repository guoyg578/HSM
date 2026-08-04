# HAM Station Manager fnOS V1.1

面向业余无线电爱好者的个人电台数字档案管理系统。一个电台一个档案空间，固定信息（呼号、QTH、设备、功率、天馈）只配置一次，每次通联自动继承本台信息。

## 功能

- 多电台档案管理（家庭台 / 车载台 / 便携台），设备、天馈、功率配置
- QSO 通联日志：新建时自动继承本台信息快照，RST 发送/收到分离
- 表格模式（搜索 / 排序 / 自定义列）与时间线模式（QSL 图片 / 录音 / 地图）自由切换，系统记忆选择
- 快速记录：只填呼号、频率、模式、RST，其余自动补充
- 距离自动计算（Maidenhead 网格 → 大圆距离）、频率自动换算波段
- 首页统计：累计 QSO、本月、最远距离、常用频段/模式
- ADIF 导入导出（兼容 LoTW / eQSL / QRZ / ClubLog）
- SQLite 自动备份（默认每 24 小时，保留 7 份）

## 部署（飞牛OS / 任意 Docker 环境）

```bash
docker compose up -d
```

访问 `http://NAS地址:8000` 即可。

数据全部保存在挂载的 `./data` 目录：

```
data/
├── database/   # SQLite 数据库 + backups/ 自动备份
├── audio/      # 通联录音
├── qsl/        # QSL 卡片图片
└── export/     # ADIF 导出文件
```

环境变量（docker-compose.yml 中可调）：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `BACKUP_INTERVAL_HOURS` | 24 | 自动备份间隔（小时） |
| `BACKUP_KEEP` | 7 | 备份保留份数 |

## 本地开发

后端（uv）：

```bash
uv sync
uv run uvicorn main:app --reload   # http://127.0.0.1:8000
uv run pytest                      # 冒烟测试
```

前端（pnpm，开发服务器已配置代理到 8000）：

```bash
cd frontend
pnpm install
pnpm dev                           # http://127.0.0.1:5173
pnpm build                         # 产物输出到 frontend/dist，由后端直接托管
```

## 技术栈

- 后端：Python 3.12 + FastAPI + SQLAlchemy + SQLite
- 前端：Vue3 + TypeScript + Vite + Tailwind v4 + @guoyg578/k-ui，地图 Leaflet + OpenStreetMap
- 部署：多阶段 Dockerfile + Docker Compose，数据经 `/data` Volume 持久化
