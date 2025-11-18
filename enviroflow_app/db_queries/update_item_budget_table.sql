CREATE or REPLACE TABLE items_budget as (
  SELECT
    b.code,
    b.name,
    b.sell_price,
    b.unit_of_measure,
    c.total_labour_hours as labour_hours_per_unit,
    c.total_labour_hours * 50 as labour_cost_per_unit,
    c.total_supplier_costs as supplier_costs_per_unit,
    labour_cost_per_unit + c.total_supplier_costs as total_cost_per_unit,
    b.sell_price - total_cost_per_unit as margin,
    total_cost_per_unit / b.sell_price as cost_pct,
    margin / b.sell_price as margin_pct,
    b.to_update_in_xero,
    b.buildup_needs_attention,
    b.notes,
    b.last_update,
    b.url

  FROM items_budget b
  LEFT JOIN
    (SELECT
      xero_code,
      sum(case when cost_type = 'Labour' then amount else 0 end) as total_labour_hours,
      sum(case when cost_type = 'Supplier' then total else 0 end) as total_supplier_costs,
    FROM cost_calcs
    GROUP by xero_code
    ) as c on b.code = c.xero_code
)
