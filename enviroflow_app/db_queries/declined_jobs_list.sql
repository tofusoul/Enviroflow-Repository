--declined jobs list
select
  card_title,
  url,
  eqc_declined_date::DATE as eqc_declined_date,
  status,
  accepted_quote_value,
  submitted_quote_value,
  quote_value,
  report_by
from job_cards
where eqc_declined_date is not null
order by eqc_declined_date desc
