#!/usr/bin/env python3
'''
Simple example demonstrating how to query the rsmarket database with raw SQL.
SQLAlchemy Unified Tutorial:        https://docs.sqlalchemy.org/en/20/tutorial/
SQlAlchemy Using SELECT Statements: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html
SQLAlchemy Documentation Topics:    https://docs.sqlalchemy.org/en/20/index.html
'''

import sqlalchemy
from rsmarket.db import convert_row_timestamps
from rsmarket.main import get_engine
from sqlalchemy.orm import Session
from tabulate import tabulate


def demo(session: Session):

    sql = '''
        select l.id, m.name, l.timestamp, l.high, l.low, (l.high - l.low) as margin
        from latest l
        join mapping m on m.id = l.id
        where l.timestamp = (
            select max(timestamp) from latest
        )
        order by margin desc, l.id
    '''

    statement = sqlalchemy.text(sql)
    result = session.execute(statement)
    headers = list(result.keys())
    rows = result.all()
    rows = convert_row_timestamps(rows, headers)
    print(tabulate(rows, headers=headers))


def main():
    if (engine := get_engine()):
        with Session(engine) as session:
            demo(session)


if __name__ == '__main__':
    main()
