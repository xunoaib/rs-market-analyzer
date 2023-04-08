from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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
        return f'LatestPrice(id={self.id!r}, low={self.low}, high={self.high}, lowTime={self.lowTime}, highTime={self.highTime}, timestamp={self.timestamp!r})'


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
        return f'AvgHourPrice(id={self.id!r}, avgLowPrice={self.avgLowPrice}, avgHighPrice={self.avgHighPrice}, highPriceVolume={self.highPriceVolume}, lowPriceVolume={self.lowPriceVolume}, timestamp={self.timestamp!r})'


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
        return f'AvgFiveMinPrice(id={self.id!r}, avgLowPrice={self.avgLowPrice}, avgHighPrice={self.avgHighPrice}, highPriceVolume={self.highPriceVolume}, lowPriceVolume={self.lowPriceVolume}, timestamp={self.timestamp!r})'
