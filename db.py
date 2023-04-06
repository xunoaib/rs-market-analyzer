#!/usr/bin/env python3
from typing import Literal
import os
import sqlite3

import api
import config


def connect(db_fname: str | os.PathLike = config.DB_PATH):
    '''Opens and/or initializes the SQLite prices database file'''

    con = sqlite3.connect(db_fname)
    cur = con.cursor()

    cur.execute('''
        create table if not exists mapping(
            id int,
            name text,
            examine text,
            members int,
            value int,
            "limit" int,
            lowalch int,
            highalch int,
            icon text,
            primary key (id)
        );
    ''')

    cur.execute('''
        create table if not exists latest(
            id int,
            timestamp int,
            high int,
            highTime int,
            low int,
            lowTime int,
            primary key (id, timestamp)
        );
    ''')

    for table in ['fivemin', 'hour']:
        cur.execute(f'''
            create table if not exists {table}(
                id int,
                timestamp int,
                avgHighPrice int,
                highPriceVolume int,
                avgLowPrice int,
                lowPriceVolume int,
                primary key (id, timestamp)
            );
        ''')

    con.commit()

    # ensure the mappings table is populated
    if cur.execute('select count(*) from mapping').fetchone()[0] == 0:
        mappings = api.load_mappings()
        insert_from_dict(mappings, 'mapping', cur)

    con.commit()
    cur.close()
    return con


def insert_from_dict(data: dict, table: str, cur: sqlite3.Cursor):
    '''Converts and inserts values of a dict as tuples into the given database table.'''

    sql, rows = sql_from_dict(data, table)
    for rowset in (rows[i:i + 1000] for i in range(0, len(rows), 1000)):
        cur.executemany(sql, rowset)


def sql_from_dict(
        data: dict,
        table: str,
        sql_template='insert into {table} ({fields}) values ({placeholders})'):
    '''
    Converts dict values into a list of tuples and generates SQL to insert them
    into the given database table, but does not perform the insertion. Returns
    a SQL INSERT statement and a list of tuples which can be passed to it.

    :param data: A dictionary whose values are dicts with keys corresponding to the columns of the given table.
    :param table: Database table to use for the INSERT statement
    :param sql_template: SQL statement format string
    '''

    # first, identify all possible fields because not every item will have them
    fields = sorted(set(key for info in data.values() for key in info))
    rows = [
        tuple(item_data.get(field) for field in fields)
        for item_data in data.values()
    ]

    placeholders = ','.join('?' * len(fields))
    fields = ','.join(f'"{f}"' for f in fields)
    sql = sql_template.format(table=table,
                              fields=fields,
                              placeholders=placeholders)
    return sql, rows


def endpoint_to_table(endpoint: Literal['latest', '5m', '1h']):
    '''Returns the SQL table name corresponding to an API endpoint'''

    return {
        '5m': 'fivemin',
        '1h': 'hour',
        'latest': 'latest',
    }[endpoint]
