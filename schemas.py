from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------- 电台配置 ----------
class EquipmentBase(BaseModel):
    brand: str = ""
    model: str
    type: str = ""
    remark: str = ""


class EquipmentOut(EquipmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    station_id: int


class AntennaBase(BaseModel):
    name: str
    remark: str = ""


class AntennaOut(AntennaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    station_id: int


class PowerProfileBase(BaseModel):
    mode_name: str
    power_watts: float


class PowerProfileOut(PowerProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    station_id: int


# ---------- 电台 ----------
class StationBase(BaseModel):
    name: str
    callsign: str
    qth: str = ""
    grid: str = ""
    cq_zone: str = ""
    itu_zone: str = ""
    remark: str = ""


class StationCreate(StationBase):
    pass


class StationUpdate(BaseModel):
    name: str | None = None
    callsign: str | None = None
    qth: str | None = None
    grid: str | None = None
    cq_zone: str | None = None
    itu_zone: str | None = None
    remark: str | None = None


class StationOut(StationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class StationDetail(StationOut):
    equipments: list[EquipmentOut] = []
    antennas: list[AntennaOut] = []
    power_profiles: list[PowerProfileOut] = []


# ---------- QSO ----------
class QSOBase(BaseModel):
    datetime_utc: datetime | None = None
    call: str
    freq_mhz: float | None = None
    band: str = ""
    mode: str = ""
    rst_sent: str = ""
    rst_rcvd: str = ""
    qth: str = ""
    grid: str = ""
    distance_km: float | None = None
    their_equipment: str = ""
    their_antenna: str = ""
    their_power: str = ""
    remark: str = ""
    audio_path: str = ""
    qsl_path: str = ""


class QSOCreate(QSOBase):
    station_id: int
    # 快照字段可显式传入（如 ADIF 导入）；缺省时由服务端从电台配置继承
    my_callsign: str | None = None
    my_qth: str | None = None
    my_grid: str | None = None
    my_equipment: str | None = None
    my_antenna: str | None = None
    my_power: str | None = None


class QSOUpdate(BaseModel):
    station_id: int | None = None
    datetime_utc: datetime | None = None
    call: str | None = None
    freq_mhz: float | None = None
    band: str | None = None
    mode: str | None = None
    rst_sent: str | None = None
    rst_rcvd: str | None = None
    qth: str | None = None
    grid: str | None = None
    distance_km: float | None = None
    their_equipment: str | None = None
    their_antenna: str | None = None
    their_power: str | None = None
    remark: str | None = None
    audio_path: str | None = None
    qsl_path: str | None = None
    my_callsign: str | None = None
    my_qth: str | None = None
    my_grid: str | None = None
    my_equipment: str | None = None
    my_antenna: str | None = None
    my_power: str | None = None


class QSOOut(QSOBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    station_id: int
    datetime_utc: datetime
    my_callsign: str
    my_qth: str
    my_grid: str
    my_equipment: str
    my_antenna: str
    my_power: str
    created_at: datetime


class QSOPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[QSOOut]


class QSODefaults(BaseModel):
    """新建 QSO 时自动继承的本台信息。"""

    my_callsign: str = ""
    my_qth: str = ""
    my_grid: str = ""
    my_equipment: str = ""
    my_antenna: str = ""
    my_power: str = ""
    power_profiles: list[PowerProfileOut] = []


# ---------- 统计 ----------
class Stats(BaseModel):
    total_qso: int = 0
    month_qso: int = 0
    max_distance_km: float | None = None
    top_band: str = ""
    top_mode: str = ""


# ---------- 运行时配置（后台管理） ----------
class BandRange(BaseModel):
    low_mhz: float = Field(gt=0)
    high_mhz: float = Field(gt=0)
    name: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_range(self):
        if self.high_mhz <= self.low_mhz:
            raise ValueError(f"波段 {self.name}: 上限必须大于下限")
        return self


class SettingsOut(BaseModel):
    mode_options: list[str]
    default_mode: str
    default_rst: str
    qso_columns: list[str]
    bands: list[BandRange]
    backup_interval_hours: int
    backup_keep: int


class SettingsUpdate(BaseModel):
    mode_options: list[str] | None = Field(None, min_length=1)
    default_mode: str | None = Field(None, min_length=1)
    default_rst: str | None = None
    qso_columns: list[str] | None = Field(None, min_length=1)
    bands: list[BandRange] | None = None
    backup_interval_hours: int | None = Field(None, ge=1, le=8760)
    backup_keep: int | None = Field(None, ge=1, le=365)

    @field_validator("mode_options")
    @classmethod
    def clean_modes(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        cleaned: list[str] = []
        for m in v:
            m = m.strip()
            if m and m not in cleaned:
                cleaned.append(m)
        if not cleaned:
            raise ValueError("至少保留一个有效模式")
        return cleaned


# ---------- 通用 ----------
class Message(BaseModel):
    message: str = "ok"


class UploadResult(BaseModel):
    path: str = Field(description="相对 /data 的文件路径，可拼 /files/ 访问")
    url: str
