"""ADIF (Amateur Data Interchange Format) 导入/导出。

按 ADIF 规范以字节长度读写字段（UTF-8 编码），兼容中文 QTH/备注；
字段映射覆盖 LoTW / eQSL / QRZ / ClubLog 通用字段。
"""
import re
from datetime import datetime, timezone

ADIF_HEADER = (
    "HAM Station Manager ADIF Export\n"
    "<ADIF_VER:5>3.1.4\n"
    "<PROGRAMID:19>HAM Station Manager\n"
    "<EOH>\n"
)

_FIELD_RE = re.compile(rb"<([A-Za-z0-9_]+):(\d+)(?::[A-Za-z])?>")
_EOR_RE = re.compile(rb"<[Ee][Oo][Rr]>")
_EOH_RE = re.compile(rb"<[Ee][Oo][Hh]>")


def _field(name: str, value: str) -> str:
    if value is None or value == "":
        return ""
    b = value.encode("utf-8")
    return f"<{name}:{len(b)}>{value} "


def qso_to_adif(q) -> str:
    """models.QSO → 一条 ADIF 记录。"""
    dt: datetime = q.datetime_utc
    parts = [
        _field("CALL", q.call),
        _field("QSO_DATE", dt.strftime("%Y%m%d")),
        _field("TIME_ON", dt.strftime("%H%M%S")),
        _field("FREQ", f"{q.freq_mhz:.6f}".rstrip("0").rstrip(".") if q.freq_mhz else ""),
        _field("BAND", q.band),
        _field("MODE", q.mode.upper() if q.mode else ""),
        _field("RST_SENT", q.rst_sent),
        _field("RST_RCVD", q.rst_rcvd),
        _field("QTH", q.qth),
        _field("GRIDSQUARE", q.grid),
        _field("DISTANCE", str(q.distance_km) if q.distance_km is not None else ""),
        # 对方台站：RIG / RX_PWR 为 ADIF 标准字段，天线无标准字段用 APP 自定义
        _field("RIG", q.their_equipment),
        _field("RX_PWR", re.sub(r"[^0-9.]", "", q.their_power) if q.their_power else ""),
        _field("APP_HSM_THEIR_ANTENNA", q.their_antenna),
        _field("COMMENT", q.remark),
        _field("STATION_CALLSIGN", q.my_callsign),
        _field("MY_GRIDSQUARE", q.my_grid),
        _field("MY_CITY", q.my_qth),
        _field("MY_RIG", q.my_equipment),
        _field("MY_ANTENNA", q.my_antenna),
        _field("TX_PWR", re.sub(r"[^0-9.]", "", q.my_power) if q.my_power else ""),
    ]
    return "".join(p for p in parts if p) + "<EOR>\n"


def export_adif(qsos) -> str:
    return ADIF_HEADER + "".join(qso_to_adif(q) for q in qsos)


def parse_adif(content: bytes) -> list[dict]:
    """解析 ADIF 字节流 → 记录字典列表（字段名统一大写）。"""
    m = _EOH_RE.search(content)
    body = content[m.end():] if m else content

    records: list[dict] = []
    current: dict = {}
    pos = 0
    while True:
        fm = _FIELD_RE.search(body, pos)
        em = _EOR_RE.search(body, pos)
        # <EOR> 在下一个字段之前 → 当前记录结束
        if em and (not fm or em.start() < fm.start()):
            if current:
                records.append(current)
                current = {}
            pos = em.end()
            continue
        if not fm:
            break
        name = fm.group(1).decode("ascii").upper()
        length = int(fm.group(2))
        value = body[fm.end(): fm.end() + length].decode("utf-8", errors="replace")
        current[name] = value.strip()
        pos = fm.end() + length
    if current:
        records.append(current)
    return records


def adif_record_to_qso_fields(rec: dict) -> dict:
    """ADIF 记录 → QSOCreate 字段字典（不含 station_id）。"""
    date = rec.get("QSO_DATE", "")
    time = rec.get("TIME_ON", "000000").ljust(6, "0")[:6]
    dt = None
    if re.fullmatch(r"\d{8}", date):
        try:
            dt = datetime.strptime(date + time, "%Y%m%d%H%M%S").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            dt = None

    def _float(key: str) -> float | None:
        try:
            return float(rec[key])
        except (KeyError, ValueError):
            return None

    return {
        "datetime_utc": dt,
        "call": rec.get("CALL", ""),
        "freq_mhz": _float("FREQ"),
        "band": rec.get("BAND", "").lower(),
        "mode": rec.get("MODE", ""),
        "rst_sent": rec.get("RST_SENT", ""),
        "rst_rcvd": rec.get("RST_RCVD", ""),
        "qth": rec.get("QTH", ""),
        "grid": rec.get("GRIDSQUARE", ""),
        "distance_km": _float("DISTANCE"),
        "their_equipment": rec.get("RIG", ""),
        "their_antenna": rec.get("APP_HSM_THEIR_ANTENNA", ""),
        "their_power": (rec.get("RX_PWR", "") + "W" if rec.get("RX_PWR") else ""),
        "remark": rec.get("COMMENT", rec.get("NOTES", "")),
        "my_callsign": rec.get("STATION_CALLSIGN", rec.get("OPERATOR", "")) or None,
        "my_grid": rec.get("MY_GRIDSQUARE", "") or None,
        "my_qth": rec.get("MY_CITY", "") or None,
        "my_equipment": rec.get("MY_RIG", "") or None,
        "my_antenna": rec.get("MY_ANTENNA", "") or None,
        "my_power": (rec.get("TX_PWR", "") + "W" if rec.get("TX_PWR") else None),
    }
