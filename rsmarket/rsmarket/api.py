import json
import logging
import os
from pathlib import Path
from typing import Literal

import requests

DEFAULT_HEADERS = {'User-Agent': 'Market Experimentation'}
HTTP_TIMEOUT_SEC = 10


def request(
    endpoint: Literal['latest', '5m', '1h', 'mapping'],
    annotate: bool = True,
    headers=DEFAULT_HEADERS
):
    '''
    Makes a request to the Runescape wiki prices API. Returns a JSON response
    for the given endpoint except 'mapping' which returns a list.

    :param endpoint: API endpoint, one of: latest, 5m, 1h, or mapping
    :param annotate: Whether to also add the endpoint name to the JSON response
    :param headers: HTTP headers to send with the request
    '''

    data = requests.get(
        f'https://prices.runescape.wiki/api/v1/osrs/{endpoint}',
        headers=headers,
        timeout=HTTP_TIMEOUT_SEC
    ).json()

    if annotate and endpoint != 'mapping':
        data |= {'endpoint': endpoint}
    return data


def load_mappings(fname: str | os.PathLike, download: bool = True):
    '''
    Returns a dictionary of item ids mapped to their static item info (from the 'mappings' endpoint)

    :param fname: JSON file where item mappings are or will be stored
    :param download: Whether to download the file from the API if it doesn't exist
    '''

    if not Path(fname).is_file():
        if not download:
            raise FileNotFoundError(f'{fname} not found. Did you download it?')

        logging.info('Downloading mappings to %s', fname)
        mapping = request('mapping')
        with open(fname, 'w') as f:
            json.dump(mapping, f)

    with open(fname) as f:
        return {str(m['id']): m for m in json.load(f)}


def load_recipes(fname: str | os.PathLike, download: bool = True):
    '''
    Returns a list of item recipes (from Flipping-utilities/osrs-datasets)

    :param fname: JSON file where item recipes are or will be stored
    :param download: Whether to download the file from GitHub if it doesn't exist
    '''

    if not Path(fname).is_file():
        if not download:
            raise FileNotFoundError(f'{fname} not found. Did you download it?')

        logging.info('Downloading recipes to %s', fname)
        recipes = requests.get(
            'https://raw.githubusercontent.com/Flipping-Utilities/osrs-datasets/master/recipes.json',
            timeout=HTTP_TIMEOUT_SEC
        ).json()

        with open(fname, 'w') as f:
            json.dump(recipes, f)

    with open(fname) as f:
        return json.load(f)
