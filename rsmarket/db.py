#!/usr/bin/env python3
import logging
from datetime import datetime, timedelta
from typing import cast

from sqlalchemy import Engine, Integer, create_engine, select, func
from sqlalchemy.orm import Session, aliased
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


def add_commas_to_rows(rows):
    results = []
    for row in rows:
        tup = tuple(
            f'{int(v):,}' if isinstance(v, int) or isinstance(v, float) else v
            for v in row
        )
        results.append(tup)
    return results


def latest_margins(session: Session):
    '''Shows the highest and latest profit margins for all F2P items'''

    # use only use most recent prices
    ts_latest = select(func.max(LatestPrice.timestamp)).scalar_subquery()
    ts_hour = select(func.max(AvgHourPrice.timestamp)).scalar_subquery()

    # average hourly volumes calculated from the total daily volumes
    yesterday = (datetime.utcnow() + timedelta(days=-1)).timestamp()
    sum_of_volumes = func.sum(
        AvgHourPrice.highPriceVolume + AvgHourPrice.lowPriceVolume
    )
    col_dailyVolume = func.round(sum_of_volumes).label('dailyVol')
    col_avgHourlyVolume = (col_dailyVolume / 24).label('avgHourlyVol')
    q_avgHourlyVolume = (
        select(AvgHourPrice.id, col_dailyVolume, col_avgHourlyVolume)  #
        .where(AvgHourPrice.timestamp > yesterday)  #
        .order_by(AvgHourPrice.timestamp)  #
        .group_by(AvgHourPrice.id)  #
        .order_by(col_avgHourlyVolume.desc())
    ).subquery()
    dailyVolume = q_avgHourlyVolume.c.dailyVol

    margin = (LatestPrice.high - LatestPrice.low).label('margin')
    profit = (margin * ItemInfo.limit).label('profit')
    # volume = (AvgHourPrice.lowPriceVolume
    #           + AvgHourPrice.highPriceVolume).label('totVol')
    hourlyVolume = q_avgHourlyVolume.c.avgHourlyVol
    columns = (
        profit,
        # hourlyVolume,
        dailyVolume,
        AvgHourPrice.lowPriceVolume.label('lowVol'),
        AvgHourPrice.highPriceVolume.label('highVol'),
        # avg_hourly_volume,
        margin,
        LatestPrice.low.label('lowPrice'),
        LatestPrice.high.label('highPrice'),
        ItemInfo.limit,
        ItemInfo.name,
        # LatestPrice.lowTime, LatestPrice.highTime
    )

    # # margins, volumes, and profits based on the last hour's stats (inaccurate)
    # query = (
    #     select(*columns)  #
    #     .join(ItemInfo, LatestPrice.id == ItemInfo.id)  #
    #     .join(AvgHourPrice, LatestPrice.id == AvgHourPrice.id)  #
    #     .where(LatestPrice.timestamp == ts_latest)  #
    #     .where(AvgHourPrice.timestamp == ts_hour)  #
    #     .where(ItemInfo.members == 0)  #
    #     .where(volume > 10000)  #
    #     .order_by(profit.desc())  #
    # )

    query = (
        select(*columns)  #
        .join(ItemInfo, LatestPrice.id == ItemInfo.id)  #
        .join(AvgHourPrice, LatestPrice.id == AvgHourPrice.id)  #
        .join(q_avgHourlyVolume, ItemInfo.id == q_avgHourlyVolume.c.id)  #
        .where(LatestPrice.timestamp == ts_latest)  #
        .where(AvgHourPrice.timestamp == ts_hour)  #
        .where(ItemInfo.members == 0)  #
        .where(hourlyVolume * 24 > 10000)  #
        .order_by(profit.desc())  #
    )

    result = session.execute(query)
    rows = result.all()
    headers = list(result.keys())
    rows = convert_row_timestamps(rows, headers)
    rows = add_commas_to_rows(rows)
    # print(tabulate(rows, headers=headers, stralign='right'))

    # right-align all columns except the item name
    colalign = ['left' if h == 'name' else 'right' for h in headers]
    if not rows:
        print('No data to show')
        return
    print(tabulate(rows, headers=headers, colalign=colalign))


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
