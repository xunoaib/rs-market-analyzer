#!/usr/bin/env python3
import logging
from datetime import datetime

from sqlalchemy import Engine, create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from . import config
from .dbschema import Base, ItemInfo, LatestPrice, AvgFiveMinPrice, AvgHourPrice

logger = logging.getLogger(__name__)


def initialize_database(engine: Engine, mappings: dict):
    '''Initialize database tables and add item mappings'''

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        try:
            session.add_all(ItemInfo(**kwargs) for kwargs in mappings.values())
            session.commit()
        except IntegrityError:
            logger.debug('Skipped adding item mappings as they already exist')


def connect_and_initialize(mappings: dict,
                           engine_url: str = config.DB_ENGINE_URL):
    engine = create_engine(engine_url, echo=False)
    initialize_database(engine, mappings)
    return engine


def prices_to_objects(
        prices: dict) -> list[LatestPrice | AvgFiveMinPrice | AvgHourPrice]:
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


# XXX: just for testing
def test_queries(engine: Engine):
    session = Session(engine)

    # select all item prices recorded in the most recent log
    timestamp = select(func.max(LatestPrice.timestamp)).scalar_subquery()
    stmt = select(LatestPrice).where(LatestPrice.timestamp == timestamp)

    fields = ((LatestPrice.high - ItemInfo.value).label('diff'),
              LatestPrice.high, ItemInfo.value, ItemInfo.name)

    stmt = select(*fields) \
        .select_from(ItemInfo) \
        .join(LatestPrice, ItemInfo.id == LatestPrice.id) \
        .where(LatestPrice.timestamp == timestamp) \
        .where(ItemInfo.members == 0) \
        .order_by('diff')

    for res in session.execute(stmt):
        print(res)
        # print(f'{res.mapping=}')  # inspect foreign key

    session.commit()
    session.close()


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
            logger.error('Skipping duplicate %s log @ %s' %
                         (json_prices['endpoint'], json_prices['timestamp']))
            return False
