from dataclasses import dataclass, field
from datetime import date


@dataclass(kw_only=True)
class Staff:
    """Runtime representation of the staff table in the database.

    next_of_kin dict shape = {
        "name": str,
        "phone": str,
        "relationship": str,
    }

    """

    name: str
    active: bool = field(default=True)
    cost_split: dict[str, float] | None = field(default=None, repr=False)
    personal_email: str | None = field(default=None, repr=False)
    work_email: str | None = field(default=None, repr=False)
    personal_phone: str | None = field(default=None, repr=False)
    work_phone: str | None = field(default=None, repr=False)
    employment_start_date: date | None = field(default=None, repr=False)
    next_of_kin: dict[str, dict[str, str]] | None = field(default=None, repr=False)
    notes: str | None = field(default=None, repr=False)
    payroll_page: str | None = field(default=None, repr=False)
    role: str | None = field(default=None, repr=False)
    weekly_gross_pay: float | None = field(default=None, repr=False)
    trello_card: str | None = field(default=None, repr=False)
