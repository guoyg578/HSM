"""核心流程冒烟测试：电台配置 → QSO 继承 → 搜索/统计 → ADIF 往返。"""
import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="hsm_test_")

from fastapi.testclient import TestClient  # noqa: E402

from database import Base, engine  # noqa: E402
from main import app  # noqa: E402

Base.metadata.create_all(engine)
client = TestClient(app)


def _create_station() -> int:
    resp = client.post(
        "/api/stations",
        json={
            "name": "家庭电台",
            "callsign": "BG5TEST",
            "qth": "安徽合肥",
            "grid": "OM81",
        },
    )
    assert resp.status_code == 200, resp.text
    sid = resp.json()["id"]
    assert (
        client.post(
            f"/api/stations/{sid}/equipments",
            json={"brand": "八重洲", "model": "FTM-150R", "type": "车载电台"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/stations/{sid}/antennas", json={"name": "钻石SG7700"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/stations/{sid}/power-profiles",
            json={"mode_name": "FM", "power_watts": 50},
        ).status_code
        == 200
    )
    return sid


def test_full_flow():
    sid = _create_station()

    # 电台详情包含配置
    detail = client.get(f"/api/stations/{sid}").json()
    assert detail["equipments"][0]["model"] == "FTM-150R"

    # 新建 QSO 的继承信息
    defaults = client.get(f"/api/stations/{sid}/qso-defaults").json()
    assert defaults["my_callsign"] == "BG5TEST"
    assert defaults["my_equipment"] == "八重洲 FTM-150R"
    assert defaults["my_antenna"] == "钻石SG7700"
    assert defaults["my_power"] == "50W"

    # 创建 QSO：自动继承 + 波段/距离自动计算（合肥 OM81 → 上海 PM01）
    resp = client.post(
        "/api/qsos",
        json={
            "station_id": sid,
            "call": "BD5XXX",
            "freq_mhz": 438.5,
            "mode": "FM",
            "rst_sent": "59",
            "rst_rcvd": "57",
            "qth": "上海",
            "grid": "PM01",
        },
    )
    assert resp.status_code == 200, resp.text
    qso = resp.json()
    assert qso["my_callsign"] == "BG5TEST"
    assert qso["my_equipment"] == "八重洲 FTM-150R"
    assert qso["band"] == "70cm"
    assert qso["distance_km"] and 300 < qso["distance_km"] < 600
    assert qso["rst_sent"] == "59" and qso["rst_rcvd"] == "57"

    # 第二条：不同频率
    client.post(
        "/api/qsos",
        json={"station_id": sid, "call": "BH4AAA", "freq_mhz": 14.2, "mode": "SSB"},
    )

    # 搜索
    page = client.get("/api/qsos", params={"station_id": sid, "call": "BD5"}).json()
    assert page["total"] == 1 and page["items"][0]["call"] == "BD5XXX"

    # 排序（频率升序）
    page = client.get(
        "/api/qsos", params={"station_id": sid, "sort_by": "freq", "order": "asc"}
    ).json()
    assert [i["call"] for i in page["items"]] == ["BH4AAA", "BD5XXX"]

    # 更新频率 → 波段自动重算
    qid = qso["id"]
    updated = client.put(f"/api/qsos/{qid}", json={"freq_mhz": 145.0}).json()
    assert updated["band"] == "2m"

    # 统计
    stats = client.get("/api/stats", params={"station_id": sid}).json()
    assert stats["total_qso"] == 2
    assert stats["month_qso"] == 2
    assert stats["max_distance_km"] > 300

    # 电台配置修改后，历史 QSO 快照不变
    client.put(f"/api/stations/{sid}", json={"callsign": "BG5NEW"})
    assert client.get(f"/api/qsos/{qid}").json()["my_callsign"] == "BG5TEST"


def test_adif_roundtrip():
    sid = _create_station()
    client.post(
        "/api/qsos",
        json={
            "station_id": sid,
            "call": "JA1ABC",
            "freq_mhz": 7.05,
            "mode": "SSB",
            "rst_sent": "59",
            "rst_rcvd": "55",
            "qth": "东京",
            "grid": "PM95",
        },
    )

    # 导出
    resp = client.get("/api/adif/export", params={"station_id": sid})
    assert resp.status_code == 200
    content = resp.content.decode("utf-8")
    assert "<CALL:6>JA1ABC" in content
    assert "<EOR>" in content
    assert "东京" in content

    # 导入到另一个电台
    resp2 = client.post(
        "/api/stations", json={"name": "导入测试台", "callsign": "BG5IMP"}
    )
    sid2 = resp2.json()["id"]
    resp3 = client.post(
        "/api/adif/import",
        params={"station_id": sid2},
        files={"file": ("test.adi", content.encode("utf-8"), "text/plain")},
    )
    assert resp3.status_code == 200, resp3.text
    result = resp3.json()
    assert result["imported"] == 1 and not result["errors"]

    page = client.get("/api/qsos", params={"station_id": sid2}).json()
    item = page["items"][0]
    assert item["call"] == "JA1ABC"
    assert item["qth"] == "东京"
    assert item["band"] == "40m"
    assert item["rst_rcvd"] == "55"
    # 导出携带了 STATION_CALLSIGN → 导入时保留原快照呼号
    assert item["my_callsign"] == "BG5TEST"


def test_backup():
    resp = client.post("/api/backup")
    assert resp.status_code == 200
    assert "已备份" in resp.json()["message"]
