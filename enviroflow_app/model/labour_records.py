from dataclasses import dataclass
from datetime import datetime


@dataclass(kw_only=True)
class Labour_Records:
    name: str
    start_date: datetime
    end_date: datetime
    employee: str
    daily_hours: int
    num_days: int
    total_hours: int
