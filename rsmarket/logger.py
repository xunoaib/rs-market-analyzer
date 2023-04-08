import os
import json
import time
from datetime import datetime, timedelta
from typing import Literal, Any, Callable
from pathlib import Path

from . import config


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


def round_down_1h(dt: datetime):
    '''Rounds a datetime down to the current hour, on the hour'''

    return dt - timedelta(
        minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)


def round_down_5m(dt: datetime):
    '''Rounds a datetime down to the current 5th minute'''

    return dt - timedelta(
        minutes=dt.minute % 5, seconds=dt.second, microseconds=dt.microsecond)


def loop(
    request_and_log: Callable[[Literal['latest', '5m', '1h']], Any],
    log_now: bool = False,
    enable_5m: bool = True,
    enable_1h: bool = True,
    enable_latest: bool = True,
):
    '''
    Continuously requests and logs prices at 5m and 1h intervals using the
    given request_and_log function. Enabling log_now will immediately log
    prices when this function is called, instead of waiting until the next
    logging interval. Logging of individual endpoints can be enabled or
    disabled using the enable_* parameters.

    :param request_and_log: A logging function which accepts a dict of prices and logs them somewhere.
    :param log_now: Whether to log prices immediately or wait until the next predefined logging interval.
    '''

    if log_now:
        print('Requesting prices immediately...')
        if enable_latest:
            request_and_log('latest')
        if enable_5m:
            request_and_log('5m')
        if enable_1h:
            request_and_log('1h')

    now = datetime.now()
    last_1h = round_down_1h(now)
    last_5m = round_down_5m(now)

    if enable_1h:
        print(last_1h + timedelta(hours=1), '<-- Next 1h log')
    if enable_5m:
        print(last_5m + timedelta(minutes=5), '<-- Next 5m/latest log')

    while True:
        now = datetime.now()
        if now - last_5m > timedelta(minutes=5, seconds=15):
            logged = []
            if enable_5m:
                request_and_log('5m')
                logged.append('5m')
            if enable_latest:
                request_and_log('latest')
                logged.append('latest')
            if logged:
                print(last_5m, '- Logged', ' and '.join(logged))
            last_5m = round_down_5m(now)
        if now - last_1h > timedelta(hours=1, seconds=15):
            request_and_log('1h')
            print(last_1h, 'Logged 1h')
            last_1h = round_down_1h(now)
        time.sleep(1)
