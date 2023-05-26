# Runescape Market Analyzer

A Python 3.10+ framework for scraping and analyzing Grand Exchange prices from the Runescape Wiki's [real-time price API](https://oldschool.runescape.wiki/w/RuneScape:Real-time_Prices).

## Configuration

Copy the `example_env` directory to `env`, then modify its contents as needed.
The `env` directory contains environment variables used by the `rsmarket` tool
and the provided Docker containers.

The PostgreSQL database is initialized with statements from
`postgres/*.sql`. If you intend to host a server, modify this file as
needed, i.e. to change the default usernames, passwords, and roles.

The database URL for `rsmarket` must be set in `env/rsmarket-local.env` and/or
`env/rsmarket-docker.env` depending on how you intend to use `rsmarket`, either
locally or with the Docker Compose file. However, the default configuration
should work fine out of the box.

## Usage

### For client-only use and/or local development

- Install `rsmarket` by running `pip install -e rsmarket`
- Modify `DB_ENGINE_URL` in `env/rsmarket-local.env` or set this environment
  variable your shell. The URL should conform to the [SQLAlchemy database URL
  format](https://docs.sqlalchemy.org/en/20/core/engines.html).
- You should now be able to use the `rsmarket` command

### For database hosting and automatic price logging

The Docker Compose file launches a PostgreSQL database and continuously logs
API prices using the `rsmarket log` command.

- Start services with `docker compose up`. Add `-d` to run them in the background
- Stop services with `docker compose down`. Add `--volumes` to completely wipe the database



### Test edit