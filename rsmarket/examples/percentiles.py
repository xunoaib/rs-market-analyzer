#!/usr/bin/env python3
import argparse
import pickle

import pandas as pd
from rsmarket.dbschema import AvgFiveMinPrice, ItemInfo
from rsmarket.main import get_engine
from sqlalchemy import func, select

CACHE_FILE = 'cache.pickle'


def write_cache(query, df, fname=CACHE_FILE):
    with open(fname, 'wb') as f:
        pickle.dump((df, str(query)), f)


def read_cache(fname):
    with open(fname, 'rb') as f:
        return pickle.load(f)


def read_cache_or_request(query, engine, fname=CACHE_FILE):
    '''
    Tries to load a cached dataframe, but will execute the query and re-cache
    if the query structure has changed or the cache file doesn't exist.
    '''
    try:
        df, cached_query = read_cache(fname)
        if str(query) != cached_query:
            raise FileNotFoundError
    except FileNotFoundError:
        df = pd.read_sql_query(query, engine)
        write_cache(query, df, fname)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--cache',
        action='store_true',
        help='Load query result from cache'
    )
    parser.add_argument('item', help='Item name to search for')
    args = parser.parse_args()

    engine = get_engine()
    latest_time = select(func.max(AvgFiveMinPrice.timestamp)).scalar_subquery()
    query = (
        select(ItemInfo.name, AvgFiveMinPrice, ItemInfo.limit)  #
        .join(AvgFiveMinPrice, AvgFiveMinPrice.id == ItemInfo.id)  #
        .where(func.lower(ItemInfo.name) == func.lower(args.item))  #
        .where(AvgFiveMinPrice.timestamp > latest_time - 60 * 60 * 24 * 1)  #
        .order_by(ItemInfo.value.desc())  #
    )

    if args.cache:
        df = read_cache_or_request(query, engine)
    else:
        df = pd.read_sql_query(query, engine)
        write_cache(query, df)

    PRICE_COLS = ('avgHighPrice', 'avgLowPrice')
    VOLUME_COLS = ('highPriceVolume', 'lowPriceVolume')
    dfs = []

    for priceCol, volumeCol in zip(PRICE_COLS, VOLUME_COLS):
        dft = df.drop(list(set(df.columns) - {priceCol, volumeCol}), axis=1) \
                .rename(columns={priceCol: 'price', volumeCol: 'volume'}) \
                .groupby(['price']).sum().reset_index() \
                .sort_values(['price'], ascending='low' in volumeCol)
        dft['percentile'] = dft['volume'].cumsum() / dft['volume'].sum()
        dfs.append(dft)

    if not all(len(d) for d in dfs):
        print('Error: no results found')
        return

    percentiles = [0, 5, 10, 25]  # top, 5th, 10th, and 25th percentiles

    print(' Price percentiles for "{}"\n'.format(df['name'][0]))
    for dft, label in zip(dfs, ['Instabought', 'Instasold']):
        print(f' {label} percentiles')
        print(' ' + '-' * 25)
        for percentile in percentiles:
            row = dft.loc[(dft.percentile >= percentile / 100).idxmax()]
            print(f'{percentile:>3}th percentile =', int(row['price']), 'gp')
        print()


if __name__ == '__main__':
    main()
