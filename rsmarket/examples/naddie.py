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
from rsmarket.dbschema import ItemInfo, AvgHourPrice, AvgFiveMinPrice, LatestPrice
from sqlalchemy import create_engine, false, func, select, Engine, union, and_, null, or_
from sqlalchemy.orm import Session
from tabulate import tabulate
import matplotlib.ticker
from matplotlib import pyplot as plt
import seaborn as sb
import pandas as pd


def demo(session: Session, engine: Engine):

    # find the latest timestamp so we can ignore older logs
    latest_hour_time = select(func.max(AvgHourPrice.timestamp)).scalar_subquery()
    latest_latest_time = select(func.max(LatestPrice.timestamp)).scalar_subquery()

    Price = AvgHourPrice

    # shared item condition for unioned queries
    item_condition = and_(
        ItemInfo.members == false(),
        # ItemInfo.name == 'Mithril bar'
        ItemInfo.name == 'Yellow bead'
    )

    # retrieve average hourly prices for the past week
    query1 = (
        select(ItemInfo.name, Price.timestamp, Price.avgHighPrice, Price.avgLowPrice)
        .join(ItemInfo)
        .where(ItemInfo.members == false())  # only list F2P items
        .where(Price.timestamp >= latest_hour_time - 60 * 60 * 24 * 7) # show logs for the last 7 days
        .where(item_condition)
        # .limit(1000)  # limit rows
    )

    # retrieve the latest price
    query2 = (
        select(ItemInfo.name, LatestPrice.low, LatestPrice.high, LatestPrice.lowTime, LatestPrice.highTime, LatestPrice.timestamp)
        .join(ItemInfo)
        .where(item_condition)
        .where(LatestPrice.timestamp == latest_latest_time)
    )

    query = query1
    df_orig = dataframe = pd.read_sql_query(query, engine)

    # preserve only the columns to be graphed
    save_cols = {'timestamp', 'avgHighPrice', 'avgLowPrice'}
    drop_cols = set(dataframe.columns) - save_cols
    dataframe = dataframe.drop(list(drop_cols), axis=1)

    # insert latest high/low prices to the data frame
    result = session.execute(query2)
    if rows := result.all():
        _name, low, high, lowTime, highTime, ts = rows[0]
        print('latest:', rows[0])
        print('lowTime: ', datetime.fromtimestamp(lowTime))
        print('highTime:', datetime.fromtimestamp(highTime))
        print('taken at:', datetime.fromtimestamp(ts))
        dataframe.loc[-1] = [lowTime, None, low]
        dataframe.loc[-2] = [highTime, high, None]
        dataframe.index = dataframe.index + 2
        dataframe = dataframe.sort_index()

    # convert integer timestamps to datetime objects
    dataframe.timestamp = dataframe.timestamp.apply(datetime.fromtimestamp)

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
