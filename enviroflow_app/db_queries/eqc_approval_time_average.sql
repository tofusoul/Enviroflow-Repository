-- EQC Approval Time Average
SELECT
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF('day', report_sent_to_eqc, eqc_approved_date)) AS median_time_difference,
  ROUND(AVG(CAST(DATEDIFF('day', report_sent_to_eqc, eqc_approved_date) AS DOUBLE)), 2) AS mean_time_difference
FROM jobs_for_analytics
WHERE
  eqc_approved_date IS NOT NULL
  and report_sent_to_eqc IS NOT NULL
  and DATEDIFF('day', report_sent_to_eqc, eqc_approved_date) > 0
