-- This query currently catches a filtered list of prices that have dropped since last detect
-- Filters definitely need tuning, but it works now.
SELECT
    mapping.name AS "Item Name",
--    to_char(
--        latest."lowTime" * '1 second'::interval,
--        'HH:MI:SS' 
--    ) AS "Change Time",  --Converts UNIX timestamp to something human readable. probably will delete
--    to_char(
--        latest.timestamp * '1 second'::interval,
--        'HH:MI:SS' 
--    ) AS "Detected Time",
--    to_char(
--        second_max."lowTime" * '1 second'::interval,
--        'HH:MI:SS' 
--    ) AS "Previous Price Time", -- Displays the last time this item traded prior to latest. (Can be used to generate a "Staleness" indicator)
-- Not sure if we will need absolute times, but left them in just in case.
    latest.low AS "New Instasell Price",
    second_max.low AS "Previous Instasell Price",
    mapping.limit AS "Buy Limit",
    to_char(
        (extract(epoch from now()) - latest."lowTime") * '1 second'::interval,
        'HH24:MI:SS' 
    ) AS "Data Staleness",
    to_char(
        (latest."lowTime" - second_max."lowTime") * '1 second'::interval,
        'HH24:MI:SS' 
    ) AS "Price Staleness",
    (second_max.low - latest.low) AS "Margin_latest", -- TODO Add Sales tax
    ((second_max.low - latest.low) * mapping.limit) AS "max_profit_latest"
FROM (
    SELECT *,
            ROW_NUMBER() 
            OVER (PARTITION BY id ORDER BY timestamp DESC) 
            AS rn
    FROM latest
) AS latest
INNER JOIN mapping ON latest.id = mapping.id
LEFT JOIN (
    SELECT id, low, "lowTime"
    FROM (
        SELECT id, low, "lowTime",
               ROW_NUMBER()
                OVER (PARTITION BY id
                ORDER BY timestamp DESC) 
                AS rn --Assign row numbers based on timestamp for later comparison between latest and second latest
        FROM latest
    ) AS second_subquery
    WHERE rn = 2 --Filtering to show second newest entry in latest
) AS second_max ON latest.id = second_max.id
WHERE latest.rn = 1 -- Select the latest entry per ID
   AND latest."lowTime" > second_max.low
   AND latest.low < 0.95 * second_max.low -- Rudimentary price detection, needs extensive work to be meaningful
   AND latest."lowTime" - second_max."lowTime" < 300 -- This is a really stupid way to filter out excessively illiquid items, but works as a proof of concept.
    --TODO statistics based filters go here (and delete previous line). Split query into low and high volume versions for simplicity?
   AND second_max.low > 30 --Filters out Vials, Feathers, Elemental runes. Number needs a tweak, probably.
   AND ((second_max.low - latest.low) * mapping.limit) >= 100000 -- Dirty solution. Switch to statistic based method later
ORDER BY (extract(epoch from now()) - latest."lowTime") ASC --Ordered by data staleness instead of max profit. I suspect an API call every 5 minutes might not be enough
LIMIT 50; -- this should be more than enough assuming nothing is broken