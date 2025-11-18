# Tables to Add on the Queries Page
## Full Tables to Fetch

job_cards
jobs_for_analytics
projects
projects_for_analytics
quotes
labour_hours

## Specific Queries and templates to Add

```sql
-- approved jobs list
select
  card_title,
  url,
  DATE(eqc_approved_date) as eqc_approved_date,
  status,
  accepted_quote_value,
  submitted_quote_value,
  quote_value,
  report_by
from job_cards
where eqc_approved_date is not null
order by eqc_approved_date desc
```

```sql
-- jobs awaiting approval
select
  card_title,
  url,
  DATE(sent_to_customer_date) as sent_to_customer_date,
  status,
  report_by
from job_cards
where status IN ('To NHC', 'Needs Followup', 'Waiting on Deed of Assignment', 'With another department', 'Not Contacted NHC')
order by sent_to_customer_date
```

```sql
-- make into a jinja2 template, where the quote number is a variable
from quotes
where quote_no > 'QU-4278'
order by quote_no asc
```

```sql
-- full projects table with corrected date formats
from projects_for_analytics
select
    "name",
    job_names,
    shared_drains,
    statuses,
    DATE(original_booking_date) as original_booking_date,
    surveyed_by,
    report_by,
    eqc_claim_manager,
    total_quote_value,
    project_manager,
    assigned_to,
    site_staff,
    concreter,
    labour_hours,
    labour_cost_total,
    supplier_costs_total,
    total_costs,
    gross_profit,
    gp_margin_pct,
    est_proj_overhead,
    job_cards_urls,
    job_ids,
    latitude,
    longitude,
    quote_nos,
    variation_quote_nos,
    DATE(work_start) as work_start,
    DATE(work_end) as work_end,
    customer_details,
    qty_from_cards,
    timeline,
    labour_records,
    sum_qty_from_cards,
    xero_costs_linked
order by statuses
```

```sql
-- list of jobs by eqc approval date. Make it into a jinja2 template where the eqc_approved_date is a variable
SELECT
  "name",
  url,
  report_by,
  eqc_claim_manager
  status,
  report_sent_to_eqc,
  eqc_approved_date,
  survey_completed_on,
  c_quote_value
from jobs_for_analytics
where status in (
  'NHC Approved - awaiting shared drain contact/approval',
  'NHC Approved',
  'Potential job for alternative drainlayer',
  'Scheduled Work',
  'In Dispute/ON HOLD',
  'NHC Declined',
  'Manager''s Approval To Close',
  'Ready to Start',
  'Ready To Invoice',
  'Invoiced',
  'Backlog/Delayed/Reschedule',
  'Next Job - Customer Has Been Called',
  'Upcoming',
  'Current',
  'Pipelining to finish',
  'Concrete/Asphalt to finish',
  'Zade jobs',
  'Landy small Jobs',
  'Rodolfo,  Small Jobs',
  'Daves, Small Jobs',
  'Small Jobs Complete - PMs to check',
  'Andy - Completed Job: Check before invoice',
  'Shea - Completed Job: Check before invoice',
  'Brendan - Completed Job: Check before invoice',
  'Book Final Sign Off Meeting',
  'Book Final Sign Off Meeting',
  'To Invoice',
  'Send Invoice',
  'Work Completed',
  )
AND eqc_approved_date >= '2024-04-01'
ORDER by report_sent_to_eqc DESC
```

```sql
--declined jobs list
select
  card_title,
  url,
  Date(eqc_declined_date) as eqc_declined_date,
  status,
  accepted_quote_value,
  submitted_quote_value,
  quote_value,
  report_by
from job_cards
where eqc_declined_date is not null
order by eqc_declined_date desc
```

```sql
-- EQC Approval Time Average
SELECT
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF('day', report_sent_to_eqc, eqc_approved_date)) AS median_time_difference,
  ROUND(AVG(CAST(DATEDIFF('day', report_sent_to_eqc, eqc_approved_date) AS DOUBLE)), 2) AS mean_time_difference
FROM jobs_for_analytics
WHERE
  eqc_approved_date IS NOT NULL
  and report_sent_to_eqc IS NOT NULL
  and DATEDIFF('day', report_sent_to_eqc, eqc_approved_date) > 0
```

```sql
-- list of jobs by eqc approval date
SELECT
  "name",
  url,
  report_by,
  eqc_claim_manager
  status,
  report_sent_to_eqc,
  eqc_approved_date,
  survey_completed_on,
  c_quote_value
from jobs_for_analytics
where status in (
  'NHC Approved - awaiting shared drain contact/approval',
  'NHC Approved',
  'Potential job for alternative drainlayer',
  'Scheduled Work',
  'In Dispute/ON HOLD',
  'NHC Declined',
  'Manager''s Approval To Close',
  'Ready to Start',
  'Ready To Invoice',
  'Invoiced',
  'Backlog/Delayed/Reschedule',
  'Next Job - Customer Has Been Called',
  'Upcoming',
  'Current',
  'Pipelining to finish',
  'Concrete/Asphalt to finish',
  'Zade jobs',
  'Landy small Jobs',
  'Rodolfo,  Small Jobs',
  'Daves, Small Jobs',
  'Small Jobs Complete - PMs to check',
  'Andy - Completed Job: Check before invoice',
  'Shea - Completed Job: Check before invoice',
  'Brendan - Completed Job: Check before invoice',
  'Book Final Sign Off Meeting',
  'Book Final Sign Off Meeting',
  'To Invoice',
  'Send Invoice',
  'Work Completed',
  )
AND eqc_approved_date >= '2024-04-01'
ORDER by report_sent_to_eqc DESC
```
