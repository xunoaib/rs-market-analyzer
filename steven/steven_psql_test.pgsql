SELECT * 
FROM latest
INNER JOIN mapping
    ON latest.id = mapping.id
INNER JOIN fivemin
    ON fivemin.id = mapping.id
LIMIT 10;