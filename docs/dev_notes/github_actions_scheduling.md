# GitHub Actions Scheduling for Enviroflow_App

## Scheduling Workflows in GitHub Actions
- GitHub Actions uses UTC for cron schedules.
- To run at 10am, 1pm, and 6pm NZST (UTC+12):
  - 10am NZST = 22:00 UTC (previous day)
  - 1pm NZST = 01:00 UTC
  - 6pm NZST = 06:00 UTC
- Example cron schedule in workflow YAML:

```yaml
on:
  schedule:
    - cron: '0 22 * * 0-4'  # 10am NZST, Monday-Friday
    - cron: '0 1 * * 0-4'   # 1pm NZST, Monday-Friday
    - cron: '0 6 * * 0-4'   # 6pm NZST, Monday-Friday
```

## Best Practices
- Always document the local time and UTC conversion in your workflow.
- Be aware of daylight saving changes (NZDT is UTC+13).
- Use comments in your workflow YAML to clarify the schedule.

## References
- [GitHub Actions: Events that trigger workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)
- [Crontab Guru](https://crontab.guru/) for cron syntax help

---

This document is referenced in the migration plan and workflow documentation.
