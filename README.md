# Runescape Market Analyzer

A Python 3.10+ framework for scraping and analyzing Grand Exchange prices from the Runescape Wiki's [real-time price API](https://oldschool.runescape.wiki/w/RuneScape:Real-time_Prices).

## Setup

Copy the `example_env` directory to `env`, then modify its contents as needed.
The `env` directory contains environment variables used by the `rsmarket` tool
and Docker containers.

### For local development with a remote database connection

- Install `rsmarket` by running `pip install -e rsmarket`
- Define your remote database URL (`DB_ENGINE_URL`) in `env/rsmarket-local.env`
  or set this environment variable in your shell. The URL must conform
  to the [SQLAlchemy database URL format](https://docs.sqlalchemy.org/en/20/core/engines.html).
- You should now be able to use `rsmarket` or `python3 -m rsmarket`

### For database hosting and automatic price logging

The Docker Compose file (`docker-compose.yml`) hosts a PostgreSQL database
and continuously logs API prices to it using the `rsmarket log` command.

The database will be initialized by executing every `.sql` file in the
`postgres/` directory in alphabetical order. Modify these files as needed, i.e.
to change usernames, passwords, and roles.

PostgreSQL can be further configured by modifying `postgresql.conf`,
`pg_hba.conf`, and other config files in `postgres-data/` once the container
has been started and stopped at least once.

- Start all services with `docker compose up`. Add `-d` to run them in the background
- Stop all services with `docker compose down`
