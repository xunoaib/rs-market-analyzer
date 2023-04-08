from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / 'data'
DB_ENGINE_URL = f'sqlite:///{DATA_DIR}/prices.db'
HEADERS = {'User-Agent': 'Market Experimentation'}
