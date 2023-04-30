# Runescape Market Analyzer

A Python 3.10+ framework for scraping and analyzing Grand Exchange prices from the Runescape Wiki's [real-time price API](https://oldschool.runescape.wiki/w/RuneScape:Real-time_Prices).

## Initial Configuration

Copy the `example_env` directory to `env`, then modify its contents as needed.
The `env` directory contains configurations used by the Docker containers and
`rsmarket` tool.

The PostgreSQL database will be initialized with statements from `db/init.sql`.

## Client Usage

### Running in Docker

`rsmarket` can be built and run in Docker:

    docker build -t rsmarket    # build the image
    docker run --rm -it <args>  # run rsmarket in the built image

### Installing and Running Locally

`rsmarket` can be installed locally for development purposes. Run `pip install
-e rsmarket` to install the `rsmarket` package and command in an
[editable](https://pip.pypa.io/en/stable/topics/local-project-installs/) form.

## Server Usage

A Docker Compose file is provided to host a PostgreSQL database, continuously
log API prices with the included `rsmarket` tool, and provide a web-based
database management interface (pgAdmin).

- Start all services `docker compose up`
- Stop all services with `docker compose down`
- Stop all services and purge data volumes with `docker compose down --volumes` (WARNING: destructive!)

### pgAdmin Setup

To manage the database via pgAdmin, first navigate to http://localhost:15432,
log in with the credentials defined in `env/pgadmin-vars.env`, then add a
server with the hostname `postgres` and the credentials defined in
`env/postgres-vars.env`.
