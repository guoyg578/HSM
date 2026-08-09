"""业余无线电相关工具：Maidenhead 网格定位、大圆距离、频率→波段。"""
import math
import re

_GRID_RE = re.compile(r"^[A-Ra-r]{2}[0-9]{2}([A-Xa-x]{2})?([0-9]{2})?$")

# (下限 MHz, 上限 MHz, 波段名) —— 常用业余频段，可在后台管理中覆盖
DEFAULT_BANDS = [
    (0.1357, 0.1378, "2190m"),
    (0.472, 0.479, "630m"),
    (1.8, 2.0, "160m"),
    (3.5, 4.0, "80m"),
    (5.06, 5.45, "60m"),
    (7.0, 7.3, "40m"),
    (10.1, 10.15, "30m"),
    (14.0, 14.35, "20m"),
    (18.068, 18.168, "17m"),
    (21.0, 21.45, "15m"),
    (24.89, 24.99, "12m"),
    (28.0, 29.7, "10m"),
    (50.0, 54.0, "6m"),
    (70.0, 71.0, "4m"),
    (144.0, 148.0, "2m"),
    (219.0, 225.0, "1.25m"),
    (420.0, 450.0, "70cm"),
    (902.0, 928.0, "33cm"),
    (1240.0, 1300.0, "23cm"),
    (2300.0, 2450.0, "13cm"),
]


def is_valid_grid(grid: str) -> bool:
    return bool(grid) and bool(_GRID_RE.match(grid.strip()))


def grid_to_latlon(grid: str) -> tuple[float, float]:
    """Maidenhead 网格 → 网格中心点 (纬度, 经度)。支持 4/6/8 位。"""
    g = grid.strip()
    if not is_valid_grid(g):
        raise ValueError(f"无效的网格定位: {grid}")
    g = g[:2].upper() + g[2:4] + (g[4:6].lower() if len(g) >= 6 else "")

    lon = (ord(g[0]) - ord("A")) * 20.0 - 180.0
    lat = (ord(g[1]) - ord("A")) * 10.0 - 90.0
    lon += int(g[2]) * 2.0
    lat += int(g[3]) * 1.0
    if len(g) >= 6:
        lon += (ord(g[4]) - ord("a")) * (2.0 / 24.0)
        lat += (ord(g[5]) - ord("a")) * (1.0 / 24.0)
        lon += 2.0 / 24.0 / 2.0
        lat += 1.0 / 24.0 / 2.0
    else:
        lon += 1.0
        lat += 0.5
    return lat, lon


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def grid_distance_km(grid1: str, grid2: str) -> float | None:
    """两个网格间的大圆距离（公里），网格无效返回 None。"""
    if not (is_valid_grid(grid1) and is_valid_grid(grid2)):
        return None
    lat1, lon1 = grid_to_latlon(grid1)
    lat2, lon2 = grid_to_latlon(grid2)
    return round(haversine_km(lat1, lon1, lat2, lon2), 1)


def freq_to_band(
    freq_mhz: float | None, bands: list[tuple[float, float, str]] | None = None
) -> str:
    if freq_mhz is None:
        return ""
    for low, high, name in bands if bands is not None else DEFAULT_BANDS:
        if low <= freq_mhz <= high:
            return name
    return ""
