SELECT mapping.name, latest.id, latest.high AS latest_high, fivemin."avgHighPrice" AS Fivemin_high
FROM latest
INNER JOIN mapping ON latest.id = mapping.id
INNER JOIN fivemin ON fivemin.id = latest.id
WHERE latest.high < fivemin."avgHighPrice" * 0.95 -- 5% lower than 'high' in fivemin
LIMIT 10;