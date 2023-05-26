#!/bin/bash

for file in /db-dumps/*.sql; do
    psql -f "$file"
done
