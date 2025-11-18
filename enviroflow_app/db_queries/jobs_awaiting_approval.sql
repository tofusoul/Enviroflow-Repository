-- jobs awaiting approval
select
  card_title,
  url,
  sent_to_customer_date::DATE as sent_to_customer_date,
  status,
  report_by
from job_cards
where status IN ('To NHC', 'Needs Followup', 'Waiting on Deed of Assignment', 'With another department', 'Not Contacted NHC')
order by sent_to_customer_date
