from pathlib import Path
import os

SCRIPT_DIR = Path(__file__).parent

DEFAULT_DATA_DIR = SCRIPT_DIR / 'data'
DATA_DIR = Path(os.getenv('DATA_DIR', DEFAULT_DATA_DIR))

DEFAULT_DB_ENGINE_URL = f'sqlite:///{DATA_DIR}/prices.db'
DB_ENGINE_URL = os.getenv('DB_ENGINE_URL', DEFAULT_DB_ENGINE_URL)

HEADERS = {'User-Agent': 'Market Experimentation'}
