from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Station(Base):
    """电台档案：固定信息只配置一次。"""

    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    callsign: Mapped[str] = mapped_column(String(20))
    qth: Mapped[str] = mapped_column(String(200), default="")
    grid: Mapped[str] = mapped_column(String(10), default="")
    cq_zone: Mapped[str] = mapped_column(String(10), default="")
    itu_zone: Mapped[str] = mapped_column(String(10), default="")
    remark: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    equipments: Mapped[list["Equipment"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )
    antennas: Mapped[list["Antenna"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )
    power_profiles: Mapped[list["PowerProfile"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )
    qsos: Mapped[list["QSO"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )


class Equipment(Base):
    __tablename__ = "equipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    brand: Mapped[str] = mapped_column(String(50), default="")
    model: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(50), default="")
    remark: Mapped[str] = mapped_column(Text, default="")

    station: Mapped[Station] = relationship(back_populates="equipments")


class Antenna(Base):
    __tablename__ = "antennas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    name: Mapped[str] = mapped_column(String(100))
    remark: Mapped[str] = mapped_column(Text, default="")

    station: Mapped[Station] = relationship(back_populates="antennas")


class PowerProfile(Base):
    """功率配置：模式名 → 功率（W），如 FM:50 / 数字模式:20 / 便携:5。"""

    __tablename__ = "power_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    mode_name: Mapped[str] = mapped_column(String(50))
    power_watts: Mapped[float] = mapped_column(Float)

    station: Mapped[Station] = relationship(back_populates="power_profiles")


class QSO(Base):
    """通联记录。my_* 字段是创建时对本台信息的快照，
    电台配置日后修改不影响历史记录。"""

    __tablename__ = "qsos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), index=True)

    datetime_utc: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    call: Mapped[str] = mapped_column(String(20), index=True)
    freq_mhz: Mapped[float | None] = mapped_column(Float, nullable=True)
    band: Mapped[str] = mapped_column(String(10), default="")
    mode: Mapped[str] = mapped_column(String(20), default="")
    rst_sent: Mapped[str] = mapped_column(String(10), default="")
    rst_rcvd: Mapped[str] = mapped_column(String(10), default="")
    qth: Mapped[str] = mapped_column(String(200), default="")
    grid: Mapped[str] = mapped_column(String(10), default="")
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    remark: Mapped[str] = mapped_column(Text, default="")
    audio_path: Mapped[str] = mapped_column(String(300), default="")
    qsl_path: Mapped[str] = mapped_column(String(300), default="")

    # 对方台站信息（手动填写）
    their_equipment: Mapped[str] = mapped_column(String(200), default="")
    their_antenna: Mapped[str] = mapped_column(String(200), default="")
    their_power: Mapped[str] = mapped_column(String(50), default="")

    my_callsign: Mapped[str] = mapped_column(String(20), default="")
    my_qth: Mapped[str] = mapped_column(String(200), default="")
    my_grid: Mapped[str] = mapped_column(String(10), default="")
    my_equipment: Mapped[str] = mapped_column(String(200), default="")
    my_antenna: Mapped[str] = mapped_column(String(200), default="")
    my_power: Mapped[str] = mapped_column(String(50), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    station: Mapped[Station] = relationship(back_populates="qsos")
