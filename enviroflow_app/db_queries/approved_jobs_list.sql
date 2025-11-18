-- approved jobs list
select
  card_title,
  url,
  eqc_approved_date::DATE as eqc_approved_date,
  status,
  accepted_quote_value,
  submitted_quote_value,
  quote_value,
  report_by
from job_cards
where eqc_approved_date is not null
order by eqc_approved_date desc
