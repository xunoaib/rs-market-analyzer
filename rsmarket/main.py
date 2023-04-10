#!/usr/bin/env python3
import argparse
import json
from typing import Any, Literal

from sqlalchemy import Engine
from tabulate import tabulate

from . import api, db, config, logger as rslogger


def json_to_rows(data: dict):
    '''Transform a prices dict to a CSV-like list of rows. The first row contains the column names'''

    # NOTE: code duplicated in db.sql_from_dict
    keys = sorted(set(key for info in data.values() for key in info))
    rows: list[Any] = [[int(item_id)] + list(map(item_data.get, keys))
                       for item_id, item_data in data.items()]
    return ['id'] + keys, rows


def get_parser():
    parser = argparse.ArgumentParser(prog='rsmarket')
    subparsers = parser.add_subparsers(dest='cmd')
    parser_log = subparsers.add_parser(
        'log', help='Continuously log API prices to the database')
    parser_log.add_argument('-f',
                            '--force',
                            help='Skip log confirmation prompt')
    parser_log.add_argument('-dh',
                            '--disable-1h',
                            action='store_true',
                            help='Disable hourly logging')
    parser_log.add_argument('-dm',
                            '--disable-5m',
                            action='store_true',
                            help='Disable 5-minute logging')
    parser_log.add_argument('-n',
                            '--now',
                            action='store_true',
                            help='Log current prices immediately')

    parser_json = subparsers.add_parser(
        'json', help='Dump raw JSON from API endpoints')
    parser_json.add_argument('endpoint',
                             choices=['latest', '5m', '1h', 'mapping'],
                             help='API endpoint to request')
    parser_json.add_argument('-t',
                             '--tabulate',
                             action='store_true',
                             help='Pretty-print tabular results')

    parser_dbtest = subparsers.add_parser('dbtest', help='Run database tests')
    return parser


def price_logger_factory(engine: Engine):
    '''Returns a function which requests API prices and logs them to the given database engine'''

    def request_and_log(endpoint: Literal['latest', '5m', '1h']):
        prices = api.request(endpoint)
        return db.log_prices_to_db(prices, engine=engine)

    return request_and_log


def main():
    parser = get_parser()
    args = parser.parse_args()
    config.DATA_DIR.mkdir(exist_ok=True)

    # ensure mappings/recipes have been downloaded
    mappings = api.load_mappings()
    recipes = api.load_recipes()

    engine = db.connect_and_initialize(mappings)

    if args.cmd == 'json':
        prices = api.request(args.endpoint)

        if args.tabulate:
            headers, rows = json_to_rows(prices['data'])
            return print(tabulate(rows, headers=headers))

        return print(json.dumps(prices, indent=2))

    elif args.cmd == 'log':
        if not args.force and input('Are you sure you want to begin logging? [y/N] ').lower() != 'y':
            return
        request_and_log = price_logger_factory(engine)
        return rslogger.loop(request_and_log,
                             log_now=args.now,
                             enable_1h_interval=not args.disable_1h,
                             enable_5m_interval=not args.disable_5m)

    elif args.cmd == 'dbtest':
        return db.test_queries(engine)

    parser.print_help()


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        pass
