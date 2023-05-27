-- This query currently catches all prices that have dropped 5%+ since last detect
-- Still needs filters for timestamp and a way to deem price changes 'significant'
SELECT
    mapping.name AS "Item Name",
--    to_char(
--        latest."highTime" * '1 second'::interval,
--        'HH:MI:SS' 
--    ) AS "Change Time",  --Converts UNIX timestamp to something human readable. probably will delete
--    to_char(
--        latest.timestamp * '1 second'::interval,
--        'HH:MI:SS' 
--    ) AS "Detected Time",
--    to_char(
--        second_max."highTime" * '1 second'::interval,
--        'HH:MI:SS' 
--    ) AS "Previous Price Time", -- Displays the last time this item traded prior to latest. (Can be used to generate a "Staleness" indicator)
    latest.high AS "New Instabuy Price",
    second_max.high AS "Previous Instabuy Price",
    mapping.limit AS "Buy Limit",
    to_char(
        (extract(epoch from now()) - latest."highTime") * '1 second'::interval,
        'HH24:MI:SS' 
    ) AS "Data Staleness",
    to_char(
        (latest."highTime" - second_max."highTime") * '1 second'::interval,
        'HH24:MI:SS' 
    ) AS "Price Staleness",
    (second_max.high - latest.high) AS "Margin_latest",
    ((second_max.high - latest.high) * mapping.limit) AS "max_profit_latest"
FROM (
    SELECT *,
            ROW_NUMBER() 
            OVER (PARTITION BY id ORDER BY timestamp DESC) 
            AS rn
    FROM latest
) AS latest
INNER JOIN mapping ON latest.id = mapping.id
LEFT JOIN (
    SELECT id, high, "highTime"
    FROM (
        SELECT id, high, "highTime",
               ROW_NUMBER()
                OVER (PARTITION BY id
                ORDER BY timestamp DESC) 
                AS rn --Assign row numbers based on timestamp for later comparisons
        FROM latest
    ) AS second_subquery
    WHERE rn = 2 --Filtering to show second newest entry in latest
) AS second_max ON latest.id = second_max.id
WHERE latest.rn = 1 -- Select the latest entry per ID
   AND latest."highTime" > second_max.high
   AND latest.high < 0.95 * second_max.high -- Rudimentary price detection, needs extensive work to be meaningful
   AND latest."highTime" - second_max."highTime" < 300 -- This is a really stupid way to filter out excessively illiquid items, but works as a proof of concept.
    --TODO statistics based filters go here (and delete previous line). Split query into low and high volume versions for simplicity?
   AND second_max.high > 30 --Filters out Vials, Feathers, Elemental runes. Number needs a tweak, probably.
ORDER BY ((second_max.high - latest.high) * mapping.limit) DESC
LIMIT 1000;