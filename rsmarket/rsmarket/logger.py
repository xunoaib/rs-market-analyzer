import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Any, Callable


def log_json(prices: dict, directory: str | os.PathLike):
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
        minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond
    )


def round_down_5m(dt: datetime):
    '''Rounds a datetime down to the current 5th minute'''

    return dt - timedelta(
        minutes=dt.minute % 5, seconds=dt.second, microseconds=dt.microsecond
    )


def loop(
    request_and_log: Callable[[Literal['latest', '5m', '1h']], Any],
    log_now: bool = False,
    enable_5m_interval: bool = True,
    enable_1h_interval: bool = True
):
    '''
    Continuously requests and logs 5m, 1h, and latest prices at 5m and 1h
    intervals using the given request_and_log function. Enabling log_now will
    immediately log prices when this function is called instead of waiting
    for the next log interval.

    The enable_* functions control the frequency of logs, ie: to prevent the
    5m/latest prices from being logged every 5m and filling up the database.
    Disabling the 5m interval will cause all endpoints to instead be logged
    every 1h.

    :param request_and_log: A logging function which accepts a dict of prices and logs them somewhere.
    :param log_now: Whether to log prices immediately or wait until the next predefined logging interval.
    '''

    if not enable_5m_interval and not enable_1h_interval:
        raise AssertionError('At least one logging interval must be enabled')

    if log_now:
        logging.info('Requesting 1h, 5m, and latest prices immediately...')
        request_and_log('latest')
        request_and_log('5m')
        request_and_log('1h')

    now = datetime.now()
    last_1h = round_down_1h(now)
    last_5m = round_down_5m(now)

    if enable_1h_interval:
        logging.info(
            'Next hourly log event at: {}'.
            format(last_1h + timedelta(hours=1))
        )
    if enable_5m_interval:
        logging.info(
            'Next five minute log event at: {}'.
            format(last_5m + timedelta(minutes=5))
        )

    while True:
        now = datetime.now()

        if enable_5m_interval and now - last_5m > timedelta(
            minutes=5, seconds=15
        ):
            request_and_log('5m')
            request_and_log('latest')
            logging.info('%s Logged 5m and latest prices' % last_5m)
            last_5m = round_down_5m(now)

        if enable_1h_interval and now - last_1h > timedelta(
            hours=1, seconds=15
        ):
            request_and_log('1h')

            # only log these endpoints if they weren't logged above
            if not enable_5m_interval:
                request_and_log('5m')
                request_and_log('latest')
                logging.info('%s Logged 1h, 5m, and latest prices' % last_1h)
            else:
                logging.info('%s Logged 1h prices' % last_1h)
            last_1h = round_down_1h(now)

        time.sleep(1)
