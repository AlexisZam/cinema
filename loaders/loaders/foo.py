"""Parse datetimes from a string."""

import logging
import re
from datetime import UTC, datetime, timedelta

DAYS_LIST = ["Πέμ.", "Παρ.", "Σάβ.", "Κυρ.", "Δευτ.", "Τρ.", "Τετ."]  # noqa: RUF001

DAY = r"Δευτ.|Τρ.|Τετ.|Πέμ.|Παρ.|Σάβ.|Κυρ."  # noqa: RUF001
DAY_SEP = r"-|, | & "
DAYS = f"(?:(?:{DAY})(?:{DAY_SEP})?)+"

TIME = r"[0-2]\d.[0-6]\d"
TIME_SEP = r"/ "
TIMES = f"(?:(?:{TIME})(?:{TIME_SEP})?)+"

DAYTIME = f"{DAYS} {TIMES}"
DAYTIME_SEP = ", "
DAYTIMES = f"(?:{DAYTIME}(?:{DAYTIME_SEP})?)+"

SUB = r"με υπότιτλους|μεταγλ."
ANNOTATED_DAYTIMES = f"(?:({DAYTIMES})(?: ({SUB}))?)+"

today = datetime.now(tz=UTC).date()
days = (today.weekday() - 3) % 7
last_thursday = today - timedelta(days=days)


def parse_datetimes(datetimes: str) -> list[tuple[datetime, bool]]:
    """Parse datetimes from a string."""
    datetimes = " ".join(datetimes.replace(": ", "").split())
    _datetimes = []
    for dts, sub in re.findall(ANNOTATED_DAYTIMES, datetimes):
        for days, times in re.findall(f"({DAYS}) ({TIMES})", dts):
            _days = []
            _day = None
            for day_sep, day in re.findall(f"({DAY_SEP})?({DAY})", days):
                if day_sep == "-":
                    if _day is None:
                        logging.error("Malformed day range")
                        continue
                    for i in range(DAYS_LIST.index(_day) + 1, DAYS_LIST.index(day)):
                        _days.append(DAYS_LIST[i])
                    _days.append(day)
                else:
                    _days.append(day)
                _day = day
            for day in _days:
                for t in re.findall(f"{TIME}", times):
                    offset = DAYS_LIST.index(day)
                    d = last_thursday + timedelta(days=offset)
                    t_ = datetime.strptime(t, "%H.%M").astimezone()
                    dt = datetime.combine(d, t_.time())
                    dubbed = sub == "μεταγλ."
                    _datetimes.append((dt, dubbed))
    return _datetimes


if __name__ == "__main__":
    datetimes = (
        "Σάβ.-Κυρ. 15.15/ 17.30/ 19.50, "  # noqa: RUF001
        "Δευτ. 13.00/ 15.15/ 17.30/ 19.50 μεταγλ., "
        "Πέμ.-Τετ. 22.10 με υπότιτλους"
    )
    for dt, dub in parse_datetimes(datetimes):
        logging.debug(dt, dub)
