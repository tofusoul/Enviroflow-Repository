CREATE or REPLACE TABLE items_budget as (
  SELECT
    s.code,
    s.name,
    s.sale_price,
    s.Unit,
    c.total_labour_hours as labour_hours_per_unit,
    c.total_labour_hours * 50 as labour_cost_per_unit,
    c.total_supplier_costs as supplier_costs_per_unit,
    labour_cost_per_unit + c.total_supplier_costs as cost_per_unit,
    s.sale_price - cost_per_unit as margin,
    cost_per_unit / s.sale_price as cost_pct,
    margin / s.sale_price as margin_pct,
    s.to_update_in_xero,
    s.buildup_needs_attention,
    s.notes,
    s.last_update,
    s.url

  FROM sales_items s
  LEFT JOIN
    (SELECT
      xero_code,
      sum(case when cost_type = 'Labour' then amount else 0 end) as total_labour_hours,
      sum(case when cost_type = 'Supplier' then total else 0 end) as total_supplier_costs,
    FROM cost_calcs
    GROUP by xero_code
    ) as c on s.code = c.xero_code
)
