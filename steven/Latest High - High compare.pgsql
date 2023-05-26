-- This query currently catches all prices that have dropped within the past 5 minutes.
-- Still needs filters for timestamp and a way to deem price changes 'significant'
-- Also needs old highest price
SELECT 
    mapping.name AS "Item Name",
    latest."highTime", 
    latest.timestamp, 
    latest.high AS "New Price",
    mapping.limit AS "Limit"
FROM latest
INNER JOIN mapping ON latest.id = mapping.id
INNER JOIN (
    SELECT id, MAX(timestamp) AS max_timestamp
    FROM (
        SELECT id, timestamp,
               ROW_NUMBER() OVER (PARTITION BY id ORDER BY timestamp DESC) AS rn
        FROM latest
    ) AS subquery
    WHERE rn = 2 -- Select the second highest timestamp per ID
    GROUP BY id
) AS latest_second_max ON latest.id = latest_second_max.id
WHERE latest."highTime" > latest_second_max.max_timestamp
ORDER BY timestamp DESC
LIMIT 500;