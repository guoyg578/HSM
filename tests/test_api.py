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
            "their_equipment": "ICOM IC-7300",
            "their_antenna": "GP天线",
            "their_power": "100W",
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
    # 对方设备/天线/功率经 RIG / APP_HSM_THEIR_ANTENNA / RX_PWR 往返保留
    assert item["their_equipment"] == "ICOM IC-7300"
    assert item["their_antenna"] == "GP天线"
    assert item["their_power"] == "100W"


def test_backup():
    resp = client.post("/api/backup")
    assert resp.status_code == 200
    assert "已备份" in resp.json()["message"]


def test_settings():
    # 默认值
    s = client.get("/api/settings").json()
    assert "FM" in s["mode_options"]
    assert s["default_mode"] == "FM"
    assert s["default_rst"] == "59"
    assert any(b["name"] == "70cm" for b in s["bands"])

    # 更新：自定义模式列表 + 默认值 + 波段表
    resp = client.put(
        "/api/settings",
        json={
            "mode_options": ["FM", "NFM", " NFM ", ""],  # 去重去空白
            "default_mode": "NFM",
            "default_rst": "55",
            "bands": [{"low_mhz": 400.0, "high_mhz": 500.0, "name": "70cm宽"}],
        },
    )
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    assert updated["mode_options"] == ["FM", "NFM"]
    assert updated["default_mode"] == "NFM"

    # 波段推导使用配置后的表
    sid = _create_station()
    qso = client.post(
        "/api/qsos", json={"station_id": sid, "call": "BC1CFG", "freq_mhz": 438.5}
    ).json()
    assert qso["band"] == "70cm宽"

    # 非法值被拒绝
    assert client.put("/api/settings", json={"mode_options": []}).status_code == 422
    assert client.put("/api/settings", json={"backup_keep": 0}).status_code == 422
    assert (
        client.put(
            "/api/settings",
            json={"bands": [{"low_mhz": 5, "high_mhz": 2, "name": "x"}]},
        ).status_code
        == 422
    )

    # 恢复默认，避免影响其他用例
    defaults = client.get("/api/settings/defaults").json()
    assert client.put("/api/settings", json=defaults).status_code == 200
    assert client.get("/api/settings").json()["default_mode"] == "FM"


def test_qth_to_grid_autofill():
    """只填 QTH 不填网格时，按地名估算网格并算出距离。"""
    sid = _create_station()  # 本台 安徽合肥 OM81

    # 只给 QTH：网格与距离都应被推导出来
    qso = client.post(
        "/api/qsos", json={"station_id": sid, "call": "BD1QTH", "qth": "北京"}
    ).json()
    assert qso["grid"] == "OM89"
    assert qso["distance_km"] and 800 < qso["distance_km"] < 1000

    # 显式给的网格不被地名覆盖（QTH 与网格冲突时以网格为准）
    qso = client.post(
        "/api/qsos",
        json={"station_id": sid, "call": "BD2QTH", "qth": "北京", "grid": "PM95"},
    ).json()
    assert qso["grid"] == "PM95"

    # 识别不了的地名不产生网格，也不该报错
    qso = client.post(
        "/api/qsos", json={"station_id": sid, "call": "BD3QTH", "qth": "某个山头"}
    ).json()
    assert qso["grid"] == ""
    assert qso["distance_km"] is None

    # 编辑时补 QTH：网格为空才推导
    qid = qso["id"]
    updated = client.put(f"/api/qsos/{qid}", json={"qth": "上海"}).json()
    assert updated["grid"] == "PM01"
    assert updated["distance_km"] and 300 < updated["distance_km"] < 600

    # 已有网格时改 QTH 不会被覆盖
    updated = client.put(f"/api/qsos/{qid}", json={"qth": "广州"}).json()
    assert updated["grid"] == "PM01"


def test_qso_columns_setting():
    """表格默认列：可配置、拒绝空列表、恢复默认。"""
    assert client.get("/api/settings").json()["qso_columns"]

    resp = client.put("/api/settings", json={"qso_columns": ["date", "call"]})
    assert resp.status_code == 200
    assert resp.json()["qso_columns"] == ["date", "call"]

    assert client.put("/api/settings", json={"qso_columns": []}).status_code == 422

    defaults = client.get("/api/settings/defaults").json()
    assert client.put("/api/settings", json=defaults).status_code == 200
    assert client.get("/api/settings").json()["qso_columns"] == defaults["qso_columns"]


def test_switch_qso_station():
    """QSO 切换所属电台：my_* 快照按新电台重新继承，距离重算。"""
    sid = _create_station()  # 合肥 OM81
    sid2 = client.post(
        "/api/stations",
        json={"name": "移动台", "callsign": "BG5MOB", "qth": "北京", "grid": "OM89"},
    ).json()["id"]

    qso = client.post(
        "/api/qsos", json={"station_id": sid, "call": "BD5SWX", "grid": "PM01"}
    ).json()
    assert qso["my_callsign"] == "BG5TEST"
    old_distance = qso["distance_km"]

    moved = client.put(f"/api/qsos/{qso['id']}", json={"station_id": sid2}).json()
    assert moved["station_id"] == sid2
    assert moved["my_callsign"] == "BG5MOB"
    assert moved["my_grid"] == "OM89"
    # 新电台没配设备/天线，快照随之清空
    assert moved["my_equipment"] == ""
    # 本台网格变了 → 距离按新网格重算
    assert moved["distance_km"] and moved["distance_km"] != old_distance

    # 目标电台的列表能查到，原电台查不到
    calls = [
        x["call"]
        for x in client.get("/api/qsos", params={"station_id": sid2}).json()["items"]
    ]
    assert "BD5SWX" in calls
    calls = [
        x["call"]
        for x in client.get("/api/qsos", params={"station_id": sid}).json()["items"]
    ]
    assert "BD5SWX" not in calls

    # 切到不存在的电台 → 404，记录不受影响
    assert (
        client.put(f"/api/qsos/{qso['id']}", json={"station_id": 99999}).status_code
        == 404
    )
    assert client.get(f"/api/qsos/{qso['id']}").json()["station_id"] == sid2


def test_geo_qth_grid_endpoint():
    """QTH 预览接口：命中/未命中/空值。"""
    hit = client.get("/api/geo/qth-grid", params={"qth": "安徽省合肥市"}).json()
    assert hit["found"] and hit["grid"] == "OM81" and hit["matched"] == "合肥"

    # 城市优先于省份，长名优先于其子串
    assert client.get("/api/geo/qth-grid", params={"qth": "马鞍山"}).json()["grid"] == "OM91"
    # 省份兜底到省会
    assert client.get("/api/geo/qth-grid", params={"qth": "安徽"}).json()["grid"] == "OM81"
    # 英文地名（ADIF 导入常见）
    assert client.get("/api/geo/qth-grid", params={"qth": "Tokyo"}).json()["grid"] == "PM95"

    miss = client.get("/api/geo/qth-grid", params={"qth": "火星基地"}).json()
    assert not miss["found"] and miss["grid"] == ""
    assert not client.get("/api/geo/qth-grid", params={"qth": ""}).json()["found"]
