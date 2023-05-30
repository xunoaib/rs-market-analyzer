#!/usr/bin/env python3
'''
Simple example demonstrating how to query the rsmarket database with SQLAlchemy's ORM syntax.
SQLAlchemy Unified Tutorial: https://docs.sqlalchemy.org/en/20/tutorial/
'''

import os
from pathlib import Path

import rsmarket
from dotenv import load_dotenv
from rsmarket.dbschema import ItemInfo, AvgHourPrice
from sqlalchemy import create_engine, false, func, select
from sqlalchemy.orm import Session
from tabulate import tabulate
from matplotlib import pyplot as plt
import seaborn as sb
import pandas as pd


def demo(session: Session):

    # find the latest timestamp so we can ignore older logs
    latest_time = select(func.max(AvgHourPrice.timestamp)).scalar_subquery()

    # construct query
    profit = ((AvgHourPrice.avgHighPrice-AvgHourPrice.avgLowPrice)*ItemInfo.limit).label('profit')
    weekly = AvgHourPrice.timestamp >= latest_time - 600000

    query = (
        select(ItemInfo.name, ItemInfo.limit, AvgHourPrice.avgHighPrice, AvgHourPrice.avgLowPrice, AvgHourPrice.timestamp, profit)  # select columns to show
        .join(AvgHourPrice, AvgHourPrice.id == ItemInfo.id)  # join with latest item prices
        .where(ItemInfo.name == 'Yellow bead')
        .where(ItemInfo.members == false())  # only list F2P items
        .where(ItemInfo.name != 'Old school bond') # exclude bonds from query
        .where(AvgHourPrice.timestamp >= latest_time - 600000)  # only show the latest price
        #.limit(1000)  # limit to 10 rows
    )

    # execute query
    result = session.execute(query)
    rows = result.all()


    dataframe = pd.read_sql_query(query, create_engine(os.environ['DB_ENGINE_URL'], echo=False))
    print(dataframe.columns)
    ax = sb.lineplot(x='timestamp', y='avgHighPrice', data=dataframe, hue='name', palette='colorblind', legend=True)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=40, ha="right")
    for i in ax.containers:
        ax.bar_label(i,)
    sb.lineplot(x='timestamp', y='avgLowPrice', data=dataframe)
    plt.tight_layout()
    plt.show()

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
