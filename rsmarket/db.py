#!/usr/bin/env python3
import logging
from datetime import datetime

from sqlalchemy import Engine, create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from tabulate import tabulate

from . import config
from .dbschema import Base, ItemInfo, LatestPrice, AvgFiveMinPrice, AvgHourPrice, format_timestamp

logger = logging.getLogger(__name__)


def connect_and_initialize(
    mappings: dict, engine_url: str = config.DB_ENGINE_URL
):
    '''Connect to the database, initialize tables, and add item mappings'''

    engine = create_engine(engine_url, echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        try:
            session.add_all(ItemInfo(**kwargs) for kwargs in mappings.values())
            session.commit()
        except IntegrityError:
            logger.debug('Skipped adding item mappings as they already exist')

    return engine


def prices_to_objects(
    prices: dict
) -> list[LatestPrice | AvgFiveMinPrice | AvgHourPrice]:
    '''Converts a prices dict (from an API endpoint) into a new list of database objects'''

    classes = {
        'latest': LatestPrice,
        '5m': AvgFiveMinPrice,
        '1h': AvgHourPrice,
    }

    data = prices['data']
    timestamp = prices['timestamp']
    endpoint = prices['endpoint']
    cls = classes[endpoint]

    return [
        cls(**kwargs, id=int(itemid), timestamp=timestamp)
        for itemid, kwargs in data.items()
    ]


def convert_row_timestamps(rows, headers: list[str]):
    '''
    Converts all UTC timestamps into datetime strings given a list of rows and
    their headers. Any headers containing the case-insensitive string 'time'
    will be converted.
    '''

    results = []
    for row in rows:
        tup = tuple(
            format_timestamp(v) if 'time' in k.lower() else v
            for k, v in zip(headers, row)
        )
        results.append(tup)
    return results


def latest_margins(session: Session):
    '''Shows the highest and latest profit margins for all F2P items'''

    ts_last_latest = select(func.max(LatestPrice.timestamp)).scalar_subquery()
    ts_last_hour = select(func.max(AvgHourPrice.timestamp)).scalar_subquery()

    margin = (LatestPrice.high - LatestPrice.low).label('margin')
    profit = (margin * ItemInfo.limit).label('profit')
    volume = (AvgHourPrice.lowPriceVolume
              + AvgHourPrice.highPriceVolume).label('volume')
    columns = (
        margin, volume, ItemInfo.limit, profit, LatestPrice.low,
        LatestPrice.high, LatestPrice.id, ItemInfo.name, LatestPrice.lowTime,
        LatestPrice.highTime
    )

    query = (
        select(*columns)  #
        .join(ItemInfo, LatestPrice.id == ItemInfo.id)  #
        .join(AvgHourPrice, LatestPrice.id == AvgHourPrice.id)  #
        .where(LatestPrice.timestamp == ts_last_latest)  #
        .where(AvgHourPrice.timestamp == ts_last_hour)  #
        .where(ItemInfo.members == 0)  #
        .where(volume > 10000)  #
        .order_by(profit.desc())  #
    )

    result = session.execute(query)
    rows = result.all()
    headers = list(result.keys())
    rows = convert_row_timestamps(rows, headers)

    print(tabulate(rows, headers=headers))


def test_queries(engine: Engine):
    '''Sandbox for database queries'''

    with Session(engine) as session:
        latest_margins(session)
        session.commit()


def log_prices_to_db(json_prices: dict, engine: Engine):
    if 'timestamp' not in json_prices:
        json_prices['timestamp'] = int(datetime.utcnow().timestamp())

    objs = prices_to_objects(json_prices)

    with Session(engine) as session:
        try:
            session.add_all(objs)
            session.commit()
            return True
        except IntegrityError:
            logger.error(
                'Skipping duplicate %s log @ %s' %
                (json_prices['endpoint'], json_prices['timestamp'])
            )
            return False
