-- This query currently catches all prices that have dropped 5%+ since last detect
-- Still needs filters for timestamp and a way to deem price changes 'significant'

SELECT 
    mapping.name AS "Item Name",
    to_char(
        latest."lowTime" * '1 second'::interval,
        'HH:MI:SS' 
    ) AS "Change Time",  --Converts UNIX timestamp to something human readable. probably will delete
    to_char(
        latest.timestamp * '1 second'::interval,
        'HH:MI:SS' 
    ) AS "Detected Time",
    --TODO Add time since price change
    latest.low AS "New Instasell Price",
    second_max.low AS "Old Instasell Price",
    mapping.limit AS "Buy Limit"
FROM (
    SELECT *,
            ROW_NUMBER() 
            OVER (PARTITION BY id ORDER BY timestamp DESC) 
            AS rn
    FROM latest
) AS latest
INNER JOIN mapping ON latest.id = mapping.id
LEFT JOIN (
    SELECT id, low
    FROM (
        SELECT id, low,
               ROW_NUMBER()
                OVER (PARTITION BY id
                ORDER BY timestamp DESC) 
                AS rn --Assign row numbers based on timestamp for later comparisons
        FROM latest
    ) AS second_subquery
    WHERE rn = 2
) AS second_max ON latest.id = second_max.id
WHERE latest.rn = 1 -- Select the latest entry per ID
    AND latest."lowTime" > second_max.low
    AND latest.low < 0.95 * second_max.low -- Rudimentary price detection, needs extensive work to be meaningful
    --TODO Add time filter
    --TODO statistics based filters go here
ORDER BY latest."lowTime" DESC
LIMIT 500;