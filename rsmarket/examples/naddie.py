#!/usr/bin/env python3
'''
Simple example demonstrating how to query the rsmarket database with SQLAlchemy's ORM syntax.
SQLAlchemy Unified Tutorial: https://docs.sqlalchemy.org/en/20/tutorial/
'''

import os
from pathlib import Path

import rsmarket
from dotenv import load_dotenv
from rsmarket.dbschema import ItemInfo, LatestPrice
from sqlalchemy import create_engine, false, func, select
from sqlalchemy.orm import Session
from tabulate import tabulate


def demo(session: Session):

    # find the latest timestamp so we can ignore older logs
    latest_time = select(func.max(LatestPrice.timestamp)).scalar_subquery()

    # construct query
    query = (
        select(ItemInfo.name, ItemInfo.limit, ItemInfo.value, LatestPrice.high, LatestPrice.low)  # select columns to show
        .join(LatestPrice, LatestPrice.id == ItemInfo.id)  # join with latest item prices
        .where(ItemInfo.members == false())  # only list F2P items
        .where(ItemInfo.name != 'Old school bond') # exclude bonds from query
        .where(LatestPrice.timestamp >= latest_time - 5000)  # only show the latest price
        .order_by(ItemInfo.name)  # in decreasing order of price
        .limit(100)  # limit to 10 rows
    )

    # execute query
    result = session.execute(query)
    rows = result.all()

    # print nice tabular output with headers and timestamps
    headers = list(result.keys())
    print(tabulate(rows, headers=headers))


def main():
    load_dotenv(
        Path(rsmarket.__file__).parent / '../../env/rsmarket-local.env'
    )
    engine = create_engine(os.environ['DB_ENGINE_URL'], echo=False)
    with Session(engine) as session:
        demo(session)


if __name__ == '__main__':
    main()
