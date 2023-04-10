from datetime import datetime
from dateutil import tz

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def format_timestamp(timestamp: int, date_format='%b %d %Y %H:%M'):
    '''Convert UTC timestamp to local datetime'''

    utc = datetime.utcfromtimestamp(timestamp)
    utc = utc.replace(tzinfo=tz.tzutc())
    localtime = utc.astimezone(tz.tzlocal())
    return localtime.strftime(date_format)


class Base(DeclarativeBase):
    pass


class ItemInfo(Base):
    __tablename__ = 'mapping'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str]
    examine: Mapped[str]
    members: Mapped[int]
    value: Mapped[int]
    limit: Mapped[int] = mapped_column(nullable=True)
    lowalch: Mapped[int] = mapped_column(nullable=True)
    highalch: Mapped[int] = mapped_column(nullable=True)
    icon: Mapped[str]

    def __repr__(self) -> str:
        return f'ItemMapping(id={self.id!r}, name={self.name!r})'


class LatestPrice(Base):
    __tablename__ = 'latest'

    id: Mapped[int] = mapped_column(ForeignKey('mapping.id'), primary_key=True)
    timestamp: Mapped[int] = mapped_column(primary_key=True)
    high: Mapped[int] = mapped_column(nullable=True)
    highTime: Mapped[int] = mapped_column(nullable=True)
    low: Mapped[int] = mapped_column(nullable=True)
    lowTime: Mapped[int] = mapped_column(nullable=True)
    mapping: Mapped[ItemInfo] = relationship()

    def __repr__(self) -> str:
        timestamp = format_timestamp(self.timestamp)
        highTime = format_timestamp(self.highTime)
        lowTime = format_timestamp(self.lowTime)
        return f'LatestPrice(id={self.id!r}, low={self.low}, high={self.high}, lowTime="{lowTime}", highTime="{highTime}", timestamp="{timestamp}")'


class AvgHourPrice(Base):
    __tablename__ = 'onehour'

    id: Mapped[int] = mapped_column(ForeignKey('mapping.id'), primary_key=True)
    timestamp: Mapped[int] = mapped_column(primary_key=True)
    avgHighPrice: Mapped[int] = mapped_column(nullable=True)
    highPriceVolume: Mapped[int] = mapped_column(nullable=True)
    avgLowPrice: Mapped[int] = mapped_column(nullable=True)
    lowPriceVolume: Mapped[int] = mapped_column(nullable=True)
    mapping: Mapped[ItemInfo] = relationship()

    def __repr__(self) -> str:
        timestamp = format_timestamp(self.timestamp)
        return f'AvgHourPrice(id={self.id!r}, avgLowPrice={self.avgLowPrice}, avgHighPrice={self.avgHighPrice}, highPriceVolume={self.highPriceVolume}, lowPriceVolume={self.lowPriceVolume}, timestamp="{timestamp}")'


class AvgFiveMinPrice(Base):
    __tablename__ = 'fivemin'

    id: Mapped[int] = mapped_column(ForeignKey('mapping.id'), primary_key=True)
    timestamp: Mapped[int] = mapped_column(primary_key=True)
    avgHighPrice: Mapped[int] = mapped_column(nullable=True)
    highPriceVolume: Mapped[int] = mapped_column(nullable=True)
    avgLowPrice: Mapped[int] = mapped_column(nullable=True)
    lowPriceVolume: Mapped[int] = mapped_column(nullable=True)
    mapping: Mapped[ItemInfo] = relationship()

    def __repr__(self) -> str:
        timestamp = format_timestamp(self.timestamp)
        return f'AvgFiveMinPrice(id={self.id!r}, avgLowPrice={self.avgLowPrice}, avgHighPrice={self.avgHighPrice}, highPriceVolume={self.highPriceVolume}, lowPriceVolume={self.lowPriceVolume}, timestamp="{timestamp}")'
