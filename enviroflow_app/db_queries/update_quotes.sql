CREATE OR REPLACE TABLE quotes as
SELECT
    COALESCE(a.quote_no, b.quote_no) AS quote_no,
    COALESCE(a.quote_ref, b.site) AS quote_ref,
    COALESCE(a.customer, b.customer) AS customer,
    a.quote_status AS quote_status,
    COALESCE(a.created, b.date_created) AS created,
    COALESCE(a.line_pct,  b.line_pct) AS line_pct,
    a.item_code AS item_code,
    COALESCE(b.item, a.item_desc) AS item_desc,
    COALESCE(a.quantity, b.quantity) AS quantity,
    COALESCE(a.unit_price, b.unit_price) AS unit_price,
    COALESCE(b.total, a.line_total) AS line_total,
    CASE
      WHEN a.quote_no IS NOT NULL and b.quote_no is NULL then 'Xero'
      when b.quote_no IS NOT NULL THEN 'Simpro'
    END AS quote_source

FROM
    full_xero_quotes AS a
FULL OUTER JOIN
    full_simpro_quotes AS b
ON a.quote_no = b.quote_no;
