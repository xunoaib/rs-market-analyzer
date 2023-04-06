#!/usr/bin/env python3
import argparse
import json
import sqlite3

import api
import config
import db
import logger


def get_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='cmd')
    parser_log = subparsers.add_parser(
        'log', help='Continuously log API prices to files')
    parser_log.add_argument('-n',
                            '--now',
                            action='store_true',
                            help='Log current prices immediately')

    parser_dump = subparsers.add_parser(
        'dump', help='Dump raw JSON from API endpoints')
    parser_dump.add_argument('endpoint',
                             choices=['latest', '5m', '1h', 'mapping'],
                             help='API endpoint to request')
    return parser


def main():
    args = get_parser().parse_args()
    config.DATA_DIR.mkdir(exist_ok=True)

    # con = db.connect(config.DB_PATH)
    # cur = con.cursor()
    # exit()

    if args.cmd == 'dump':
        prices = api.request(args.endpoint)
        print(json.dumps(prices, indent=2))
        return

    elif args.cmd == 'log':
        logfunc = logger.json_logger()
        # logfunc = logger.sqlite_logger()
        return logger.loop(logfunc, log_now=args.now)

    # ensure mappings/recipes have been downloaded
    mappings = api.load_mappings()
    recipes = api.load_recipes()

    prices = api.request('latest')
    print(prices)

    # logfunc = logger.json_logger()
    # logfunc = logger.sqlite_logger()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
