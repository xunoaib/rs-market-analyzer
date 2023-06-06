#!/usr/bin/env python3
import os
import pickle
from pathlib import Path

import pandas as pd
import rsmarket
from dotenv import load_dotenv
from rsmarket.dbschema import ItemInfo, LatestPrice, AvgHourPrice, AvgFiveMinPrice
from sqlalchemy import create_engine, false, func, select


def df_query_with_cache(query, engine):
    '''
    Returns a cached query result or executes it if it doesn't exist or has changed.
    Note: Parameterized args/values aren't cached, so manual deletion
    of the cache may be necessary to ensure accurate results.
    '''
    try:
        with open('cache.query.sql') as f:
            if str(query).strip() != f.read().strip():
                raise FileNotFoundError
        with open('cache.pickle', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print('Executing fresh query')
        df = pd.read_sql_query(query, engine)
        with open('cache.pickle', 'wb') as f:
            pickle.dump(df, f)
        with open('cache.query.sql', 'w') as f:
            f.write(str(query))
        return df


def demo(engine):
    latest_time = select(func.max(AvgFiveMinPrice.timestamp)).scalar_subquery()
    query = (
        select(ItemInfo.name, AvgFiveMinPrice, ItemInfo.limit)
        .join(AvgFiveMinPrice, AvgFiveMinPrice.id == ItemInfo.id)
        # .where(ItemInfo.members == false())
        .where(ItemInfo.name == 'Uncut sapphire')
        .where(AvgFiveMinPrice.timestamp > latest_time - 60 * 60 * 24 * 1)
        .order_by(ItemInfo.value.desc())
    )

    df = df_query_with_cache(query, engine)  # cached
    # df = pd.read_sql_query(query, engine)  # non-cached

    COL_PAIRS = [
        ('avgHighPrice', 'highPriceVolume'),
        ('avgLowPrice', 'lowPriceVolume')
    ]

    dfs = []
    for priceCol, volumeCol in COL_PAIRS:
        dft = df.drop(list(set(df.columns) - {priceCol, volumeCol}), axis=1) \
                .rename(columns={priceCol: 'price', volumeCol: 'volume'}) \
                .groupby(['price']).sum().reset_index() \
                .sort_values(['price'], ascending='low' in volumeCol)
        dft['percentile'] = dft['volume'].cumsum() / dft['volume'].sum()
        dfs.append(dft)

    if not all(len(d) for d in dfs):
        print('Error: Empty result')
        return

    percs = [0, 5, 10, 25]  # top, 5th, 10th, and 25th percentiles

    for dft in dfs:
        for perc in percs:
            row = dft.loc[(dft.percentile >= (100 - perc) / 100).idxmax()]
            print(f'{perc:>3}th percentile =', int(row['price']), 'gp')
        print('-' * 28)

def main():
    load_dotenv()
    load_dotenv(
        Path(rsmarket.__file__).parent / '../../env/rsmarket-local.env'
    )
    engine = create_engine(os.environ['DB_ENGINE_URL'], echo=False)
    demo(engine)


if __name__ == '__main__':
    main()
