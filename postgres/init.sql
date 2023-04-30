-- wipes, then initializes the postgresql database, users and roles

SET default_transaction_read_only = off;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- delete database and users
DROP DATABASE runescape;
DROP ROLE rsadmin;
DROP ROLE rsuser;

-- create database and tables
CREATE DATABASE runescape;

-- create roles
CREATE ROLE rsadmin;
ALTER ROLE rsadmin WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD 'rsadmin';

CREATE ROLE rsuser;
ALTER ROLE rsuser WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD 'rsuser';

-- remove default connect privileges on the database
REVOKE CONNECT ON DATABASE runescape FROM public;

-- grant connect privileges to users
GRANT CONNECT ON DATABASE runescape TO rsuser;
GRANT CONNECT ON DATABASE runescape TO rsadmin;

-- grant read/write privileges to users
GRANT pg_read_all_data TO rsuser;
GRANT pg_read_all_data TO rsadmin;
GRANT pg_write_all_data TO rsadmin;
