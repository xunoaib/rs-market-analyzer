#!/usr/bin/env python3
import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from sqlalchemy import Engine
from tabulate import tabulate

from . import api, db, logger as rslogger

logging.basicConfig(
    level=os.getenv('LOGLEVEL', 'INFO').upper(),
    format='%(asctime)s [%(levelname)s] %(message)s',
)


def json_to_rows(data: dict):
    '''Transform a prices dict into a CSV-like list of rows. The first row contains the column names'''

    keys = sorted(set(key for info in data.values() for key in info))
    rows: list[Any] = [
        [int(item_id)] + list(map(item_data.get, keys))
        for item_id, item_data in data.items()
    ]
    return ['id'] + keys, rows


def get_parser():
    parser = argparse.ArgumentParser(prog='rsmarket')
    subparsers = parser.add_subparsers(dest='cmd', required=True)
    parser_log = subparsers.add_parser(
        'log', help='Continuously log API prices to the database'
    )
    parser_log.add_argument(
        '-f',
        '--force',
        action='store_true',
        help='Skip log confirmation prompt'
    )
    parser_log.add_argument(
        '-dh',
        '--disable-1h',
        action='store_true',
        help='Disable hourly logging'
    )
    parser_log.add_argument(
        '-dm',
        '--disable-5m',
        action='store_true',
        help='Disable 5-minute logging'
    )
    parser_log.add_argument(
        '-n',
        '--now',
        action='store_true',
        help='Log current prices immediately'
    )

    parser_json = subparsers.add_parser(
        'json', help='Dump raw JSON from API endpoints'
    )
    parser_json.add_argument(
        'endpoint',
        choices=['latest', '5m', '1h', 'mapping'],
        help='API endpoint to request'
    )
    parser_json.add_argument(
        '-t',
        '--tabulate',
        action='store_true',
        help='Pretty-print tabular results'
    )

    subparsers.add_parser('dbtest', help='Run database tests')
    return parser


def price_logger_factory(engine: Engine):
    '''Returns a function which requests API prices and logs them to the given database engine'''

    def request_and_log(endpoint: Literal['latest', '5m', '1h']):
        prices = api.request(endpoint)
        return db.log_prices_to_db(prices, engine=engine)

    return request_and_log


def _main():
    # attempt to load the non-docker config to ensure consistent behavior
    # between docker and non-docker environments
    SCRIPT_DIR = Path(__file__).parent
    load_dotenv(SCRIPT_DIR / '../../env/rsmarket-local.env')

    parser = get_parser()
    args = parser.parse_args()

    if args.cmd == 'json':
        prices = api.request(args.endpoint)
        if args.tabulate:
            headers, rows = json_to_rows(prices['data'])
            print(tabulate(rows, headers=headers))
        else:
            print(json.dumps(prices, indent=2))
        return

    # ensure database url has been set
    engine_url = os.getenv('DB_ENGINE_URL')
    if not engine_url:
        logging.error('DB_ENGINE_URL not set')
        return False

    # ensure data directory exists and mappings/recipes have been downloaded
    DATA_DIR = Path(os.getenv('DATA_DIR', SCRIPT_DIR / 'data'))
    DATA_DIR.mkdir(exist_ok=True)

    mappings = api.load_mappings(DATA_DIR / 'mappings.json')
    recipes = api.load_recipes(DATA_DIR / 'recipes.json')
    engine = db.connect_and_initialize(mappings, engine_url)

    if args.cmd == 'log':
        if not args.force and input(
            'Are you sure you want to begin logging? [y/N] '
        ).lower() != 'y':
            return
        request_and_log = price_logger_factory(engine)
        rslogger.loop(
            request_and_log,
            log_now=args.now,
            enable_1h_interval=not args.disable_1h,
            enable_5m_interval=not args.disable_5m
        )
    elif args.cmd == 'dbtest':
        db.test_queries(engine)
    else:
        parser.print_help()


def main():
    try:
        return _main()
    except (KeyboardInterrupt, BrokenPipeError):
        pass


if __name__ == '__main__':
    main()