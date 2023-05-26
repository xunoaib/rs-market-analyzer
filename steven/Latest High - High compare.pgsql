-- This query currently catches all prices that have dropped since last detect
-- Still needs filters for timestamp and a way to deem price changes 'significant'
-- Needs subquery to select old price
SELECT 
    mapping.name AS "Item Name",
    to_char(
        latest."highTime" * '1 second'::interval,
        'HH:MI:SS' 
    ) "Change Time", --Converts UNIX timestamp to something human readable
    to_char(
        latest.timestamp * '1 second'::interval,
        'HH:MI:SS' 
    ) "Detected Time", 
    latest.high AS "New Price",
    mapping.limit AS "Limit"
FROM latest
INNER JOIN mapping ON latest.id = mapping.id
INNER JOIN (
    SELECT id, MAX(timestamp) AS max_timestamp
    FROM (
        SELECT id, timestamp,
               ROW_NUMBER() OVER 
                    (PARTITION BY id 
                    ORDER BY timestamp DESC) 
                    AS rn --Assigns row numbers based on timestamp 
        FROM latest
    ) AS subquery
    WHERE rn = 2 -- Select the second highest timestamp per ID for comparison
    GROUP BY id
) AS latest_second_max ON latest.id = latest_second_max.id
WHERE latest."highTime" > latest_second_max.max_timestamp
ORDER BY timestamp DESC
LIMIT 500;