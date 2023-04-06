from datetime import datetime, timedelta
from functools import partial
from typing import Literal, Any, Callable
from pathlib import Path
import os
import json
import sqlite3
import time

import api
import config
import db


def sqlite_logger(db_fname: str | os.PathLike = config.DB_PATH):
    '''Prepares and returns a partial function which logs prices to a database'''

    return partial(log_sqlite, con=db.connect(db_fname))


def json_logger(directory: str | os.PathLike = config.DATA_DIR / 'json'):
    '''Prepares and returns a partial function which logs prices to a JSON file'''

    return partial(log_json, directory=directory)


def log_sqlite(prices: dict, con: sqlite3.Connection):
    '''Requests and logs item prices to a SQLite database'''

    # first add extra fields to be stored in the database
    price_data = prices['data']
    timestamp = int(datetime.utcnow().timestamp())
    for item_id, item_data in price_data.items():
        item_data['id'] = int(item_id)
        item_data['timestamp'] = prices.get('timestamp', timestamp)

    # convert and insert price dicts into the database
    table = db.endpoint_to_table(prices['endpoint'])
    db.insert_from_dict(price_data, table, con.cursor())
    con.commit()


def log_json(prices: dict,
             directory: str | os.PathLike = config.DATA_DIR / 'json'):
    '''Requests and logs item prices to a timestamped JSON file'''

    directory = Path(directory)
    directory.mkdir(exist_ok=True)
    timestamp = prices.get('timestamp', int(datetime.utcnow().timestamp()))
    fname = directory / '{}_{}.json'.format(timestamp, prices['endpoint'])
    with open(fname, 'w') as f:
        f.write(json.dumps(prices, sort_keys=True, indent=4))
    return fname


def loop(log_func: Callable[[dict], Any], log_now: bool = False):
    '''
    Continuously requests and logs prices at 5m and 1h intervals using the
    given log_func. Enabling log_now will also log prices immediately when this
    function is called, instead of waiting until the next predefined interval.

    :param logfunc: A logging function with the signature logfunc(prices), preferably one returned by json_logger or sqlite_logger.
    '''

    def request_and_log(endpoint: Literal['latest', '5m', '1h']):
        prices = api.request(endpoint)
        try:
            log_func(prices)
        except sqlite3.IntegrityError as exc:
            print(f'Skipping duplicate rows ({exc})')

    def round_down_1h(dt: datetime):
        return dt - timedelta(minutes=now.minute,
                              seconds=now.second,
                              microseconds=now.microsecond)

    def round_down_5m(dt: datetime):
        return dt - timedelta(minutes=now.minute % 5,
                              seconds=now.second,
                              microseconds=now.microsecond)

    # TODO: ignore duplicate constraint errors!
    if log_now:
        print('Requesting 1h, 5m, and latest prices...')
        request_and_log('1h')
        request_and_log('5m')
        request_and_log('latest')

    # round time down to the last 5th minute
    now = datetime.now()
    last_1h = round_down_1h(now)
    last_5m = round_down_5m(now)

    print('Next 1h log at', last_1h + timedelta(hours=1))
    print('Next 5m log at', last_5m + timedelta(minutes=5))

    while True:
        now = datetime.now()
        if now - last_5m > timedelta(minutes=5, seconds=15):
            request_and_log('5m')
            request_and_log('latest')
            last_5m = round_down_5m(now)
            print('Logged', last_5m)
        if now - last_1h > timedelta(hours=1, seconds=15):
            request_and_log('1h')
            last_1h = round_down_1h(now)
            print('Logged', last_1h)
        time.sleep(1)
