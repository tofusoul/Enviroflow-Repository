SELECT *
FROM quotes
WHERE (quote_ref ILIKE '%vo%'OR quote_ref ILIKE '%variation%')
  AND quote_ref NOT ILIKE '%avo%'
  AND quote_ref NOT ILIKE '%vog%'
