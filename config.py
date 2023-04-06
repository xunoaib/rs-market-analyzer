from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / 'data'
DB_PATH = DATA_DIR / 'prices.db'
HEADERS = {'User-Agent': 'Market Experimentation'}
