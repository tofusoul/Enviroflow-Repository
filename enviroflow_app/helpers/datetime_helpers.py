from datetime import datetime

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def time_to_str(time: datetime | None) -> str | None:
    if time is None:
        return None
    return time.strftime(TIME_FORMAT)


def time_from_str(time_str: str | None) -> datetime | None:
    if time_str is None:
        return None
    return datetime.strptime(time_str, TIME_FORMAT)
