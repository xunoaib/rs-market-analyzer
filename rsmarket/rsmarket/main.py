#!/usr/bin/env python3
import argparse
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any, Literal

import requests
from psycopg2.errors import InsufficientPrivilege
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, ProgrammingError
from tabulate import tabulate

from . import api, db
from . import logger as rslogger

logging.basicConfig(
    level=os.getenv('LOGLEVEL', 'INFO').upper(),
    format='%(asctime)s [%(levelname)s] %(message)s',
)


def get_engine():
    '''
    Configures and returns a SQL engine (using $DB_ENGINE_URL) after loadng
    environment vars from .env and rsmarket-local.env. Returns False if the
    variable was not defined.
    '''

    # look for local .env if running in another directory (ie: examples)
    load_dotenv(os.getcwd() + '/.env')

    # look for the non-docker config
    load_dotenv(Path(__file__).parent / '../../env/rsmarket-local.env')

    if engine_url := os.getenv('DB_ENGINE_URL'):
        return create_engine(engine_url, echo=False)

    logging.error('DB_ENGINE_URL not set')
    return False


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
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Enable verbose tracebacks'
    )
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

    parser_dbtest = subparsers.add_parser(
        'dbtest', help='Run various database tests'
    )
    db_subparsers = parser_dbtest.add_subparsers(dest='subcmd')
    db_subparsers.add_parser('count')
    db_subparsers.add_parser('margins')

    return parser


def price_logger_factory(session: Session):
    '''Returns a function which requests API prices and logs them to the given database engine'''

    def request_and_log(endpoint: Literal['latest', '5m', '1h']):
        try:
            prices = api.request(endpoint)
            return db.log_prices_to_db(prices, session=session)
        except requests.RequestException:
            logging.exception('Error requesting prices')
            return False

    return request_and_log


def _main():
    parser = get_parser()
    args = parser.parse_args()

    if args.verbose:
        os.environ['VERBOSE'] = '1'

    if args.cmd == 'json':
        prices = api.request(args.endpoint)
        if args.tabulate:
            headers, rows = json_to_rows(prices['data'])
            print(tabulate(rows, headers=headers))
        else:
            print(json.dumps(prices, indent=2))
        return

    if not (engine := get_engine()):
        return False

    # ensure data directory exists and mappings/recipes have been downloaded
    DATA_DIR = Path(os.getenv('DATA_DIR', Path(__file__).parent / 'data'))
    DATA_DIR.mkdir(exist_ok=True)
    mappings = api.load_mappings(DATA_DIR / 'mappings.json')
    recipes = api.load_recipes(DATA_DIR / 'recipes.json')

    session = Session(engine)

    if args.cmd == 'log':
        db.initialize(mappings, engine)
        if not args.force and input(
            'Are you sure you want to begin logging? [y/N] '
        ).lower() != 'y':
            return
        request_and_log = price_logger_factory(session)
        rslogger.loop(
            request_and_log,
            log_now=args.now,
            enable_1h_interval=not args.disable_1h,
            enable_5m_interval=not args.disable_5m
        )

    elif args.cmd == 'dbtest':
        match args.subcmd:
            case 'count':
                db.count_24hr_samples(session)
            case 'margins':
                db.latest_margins(session)
            case _:
                db.latest_margins(session)

    else:
        parser.print_help()


def main():
    # shutdown gracefully when Docker sends SIGTERM
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    try:
        return _main()
    except (ProgrammingError, InsufficientPrivilege, OperationalError) as exc:
        if os.getenv('VERBOSE', '0').lower() in ('0', 'false'):
            logging.error('For a full traceback, use -v or set VERBOSE=1')
            logging.error(str(exc.args[0]).strip())
        else:
            logging.exception(exc)
    except (KeyboardInterrupt, BrokenPipeError, SystemExit):
        pass


if __name__ == '__main__':
    main()
