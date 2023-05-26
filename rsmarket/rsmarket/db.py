import logging
from datetime import datetime, timedelta

from sqlalchemy import create_engine, select, func, and_, false
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from tabulate import tabulate

from .dbschema import Base, ItemInfo, LatestPrice, AvgFiveMinPrice, AvgHourPrice, format_timestamp

logger = logging.getLogger(__name__)


def connect_and_initialize(mappings: dict, engine_url: str):
    '''Connect to the database, initialize tables, and add item mappings'''

    engine = create_engine(engine_url, echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        try:
            # insert rows for missing item mappings (and avoid inserting duplicates)
            known_ids = set(
                row.id for row in session.execute(select(ItemInfo.id)).all()
            )
            items = [ItemInfo(**kwargs) for kwargs in mappings.values()]
            items = [item for item in items if item.id not in known_ids]
            session.add_all(items)
            session.commit()
        except IntegrityError:
            pass

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
    volume_sum = func.round(
        func.sum(AvgHourPrice.highPriceVolume + AvgHourPrice.lowPriceVolume)
    ).label('dailyVol')
    num_log_events = func.count(AvgHourPrice.timestamp)
    col_avgHourlyVolume = (volume_sum / num_log_events).label('avgHourlyVol')
    q_avgHourlyVolume = (
        select(AvgHourPrice.id, volume_sum, col_avgHourlyVolume)  #
        .where(AvgHourPrice.timestamp > yesterday)  #
        .group_by(AvgHourPrice.id)  #
        .order_by(col_avgHourlyVolume.desc())  #
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
        .where(ItemInfo.members == false())  #
        .where(hourlyVolume * 24 > 10000)  #
        .order_by(profit.desc())  #
    )

    result = session.execute(query)
    rows = result.all()
    headers = list(result.keys())
    rows = convert_row_timestamps(rows, headers)
    rows = add_commas_to_rows(rows)
    # print(tabulate(rows, headers=headers, stralign='right'))

    if rows:
        # right-align all columns except the item name
        colalign = ['left' if h == 'name' else 'right' for h in headers]
        print(tabulate(rows, headers=headers, colalign=colalign))
    else:
        print('No data to show')


def count_24hr_samples(session: Session):
    # count the number of hourly log events in the last hour
    yesterday = (datetime.utcnow() + timedelta(days=-1)).timestamp()
    query = (
        select(func.count(AvgHourPrice.timestamp))  #
        .where(AvgHourPrice.timestamp >= yesterday)  #
        .group_by(AvgHourPrice.timestamp)  #
    )
    rows = session.execute(query).all()
    print(
        'Found {} of 24 possible hourly samples in the last 24 hours'.format(
            len(rows)
        )
    )


def log_prices_to_db(json_prices: dict, session: Session):
    if 'timestamp' not in json_prices:
        json_prices['timestamp'] = int(datetime.utcnow().timestamp())

    # remove invalid items which would cause foreign key constraints to fail
    known_ids = set(
        row.id for row in session.execute(select(ItemInfo.id)).all()
    )

    objs = prices_to_objects(json_prices)
    objs = [obj for obj in objs if obj.id in known_ids]

    if not objs:
        logging.error(
            'Attempted to log an empty list of prices for endpoint "%s" at %s'
            % (json_prices['endpoint'], json_prices['timestamp'])
        )
        return False

    # check if logs already exist for this endpoint at the given time
    obj = objs[0]
    cls = obj.__class__

    res = session.execute(
        select(cls).where(
            and_(cls.id == obj.id, cls.timestamp == obj.timestamp)
        )
    ).all()

    if res:
        logging.info(
            'Skipped adding duplicate log for %s at %s' %
            (json_prices['endpoint'], json_prices['timestamp'])
        )
        return False

    session.add_all(objs)
    session.commit()
