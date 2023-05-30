#!/usr/bin/env python3
'''
Simple example demonstrating how to query the rsmarket database with SQLAlchemy's ORM syntax.
SQLAlchemy Unified Tutorial: https://docs.sqlalchemy.org/en/20/tutorial/
'''

import os
from datetime import datetime
from pathlib import Path

import rsmarket
from dotenv import load_dotenv
from rsmarket.dbschema import ItemInfo, AvgHourPrice, LatestPrice
from sqlalchemy import create_engine, false, func, select, Engine
from sqlalchemy.orm import Session
from tabulate import tabulate
import matplotlib.ticker
from matplotlib import pyplot as plt
import seaborn as sb
import pandas as pd


def demo(session: Session, engine: Engine):

    # find the latest timestamp so we can ignore older logs
    latest_time = select(func.max(AvgHourPrice.timestamp)).scalar_subquery()

    Price = AvgHourPrice

    # construct query
    profit = ((Price.avgHighPrice - Price.avgLowPrice) * ItemInfo.limit).label('profit')

    query = (
        select(ItemInfo.name, Price.timestamp, Price.avgHighPrice, Price.avgLowPrice)
        .join(ItemInfo).where(ItemInfo.name == 'Yellow bead')
        .where(ItemInfo.members == false())  # only list F2P items
        .where(Price.timestamp >= latest_time - 60 * 60 * 24 * 7) # show logs for the last 7 days
        # .limit(1000)  # limit rows
    )

    print(query)  # show sql to be executed

    df_orig = dataframe = pd.read_sql_query(query, engine)

    # preserve only the columns to be graphed
    drop_cols = set(dataframe.columns) - {'timestamp', 'avgHighPrice', 'avgLowPrice'}
    dataframe = dataframe.drop(list(drop_cols), axis=1)

    # convert integer timestamps to datetime objects
    dataframe.timestamp = dataframe.timestamp.apply(datetime.utcfromtimestamp)

    # convert to long (tidy) form to plot multiple columns: https://stackoverflow.com/a/44941463/1127098
    dfm = dataframe.melt('timestamp', var_name='cols', value_name='vals')

    # plot data
    title = '{} of {}'.format(Price.__name__, df_orig['name'][0])
    g = sb.catplot(x='timestamp', y='vals', hue='cols', data=dfm, scale=.75, kind='point').set(title=title)

    # add grid lines to x/y axes
    sb.set_style('whitegrid')
    for ax in g.axes.flat:
        ax.set_axisbelow(True)
        ax.grid(True, color='lightgray', axis='both')

    # configure number of xticks and their label angle
    g.ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(60))
    plt.xticks(rotation=90)

    # reposition legend
    sb.move_legend(g, 'upper right')

    plt.tight_layout()
    plt.show()


def main():
    load_dotenv()
    load_dotenv(
        Path(rsmarket.__file__).parent / '../../env/rsmarket-local.env'
    )
    engine = create_engine(os.environ['DB_ENGINE_URL'], echo=False)
    with Session(engine) as session:
        demo(session, engine)


if __name__ == '__main__':
    main()
