SET default_transaction_read_only = off;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- delete database and users
CREATE DATABASE runescape;

-- remove default connect privileges on the database
REVOKE CONNECT ON DATABASE runescape FROM public;

-- enable query logging for most users
ALTER DATABASE runescape SET log_statement = 'all';
ALTER ROLE postgres SET log_statement = 'none';

-- create group roles
CREATE ROLE application_base_user NOINHERIT;
CREATE ROLE reader INHERIT;
CREATE ROLE writer INHERIT;
GRANT application_base_user TO reader, writer;

GRANT CONNECT ON DATABASE runescape TO reader, writer;
GRANT pg_read_all_data TO reader;
GRANT pg_write_all_data TO writer;

-- create user roles
CREATE ROLE rsadmin WITH INHERIT LOGIN PASSWORD 'rsadmin';
GRANT reader, writer TO rsadmin;
GRANT ALL ON schema public TO rsadmin;
ALTER ROLE rsadmin SET log_statement = 'none';

CREATE ROLE rsuser WITH INHERIT LOGIN PASSWORD 'rsuser';
GRANT reader TO rsuser;
