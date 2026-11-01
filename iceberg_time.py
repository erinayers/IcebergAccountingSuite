"""Timezone-neutral time handling for Iceberg Accounting Suite (ST-005).

Rules used throughout the application:

* Everything written to a database (``Created_Time`` / ``Edited_Time``) is
  stored as an ISO 8601 string in UTC, e.g. ``2025-12-21T22:47:03+00:00``.
  UTC has no daylight-saving changes and no localized names, so records made
  on different machines, in different countries, or on either side of a DST
  switch sort and compare correctly.
* Anything shown to the user is converted to the local timezone of the
  machine at display time.  The offset is shown numerically (``UTC-05:00``)
  rather than as a name, because names such as ``Eastern Daylight Time`` are
  localized on Windows and are not unique worldwide.
* Scheduling (autosave, clock refresh) uses ``time.monotonic()`` which is not
  affected by clock or timezone changes.

Older databases contain timestamps in a few legacy layouts.  ``parse_timestamp``
understands them so existing records still display correctly.
"""

import datetime
import re
import time

from dateutil import parser as _dateutil_parser

UTC = datetime.timezone.utc

STORAGE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

_LEGACY_PREFIX = re.compile(
    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*"
)
_LEGACY_SEPARATOR = re.compile(r"\s+-\s+")
_TRAILING_TZ_NAME = re.compile(r"\s+[A-Za-z][A-Za-z .]*$")


# --------------------------------------------------------------------------- now


def utc_now():
    """Return the current time as a timezone-aware datetime in UTC."""
    return datetime.datetime.now(UTC)


def local_timezone():
    """The tzinfo used for display.  ``None`` means the machine's local zone.

    Kept as a function so tests (or a future preference) can override it.
    """
    return None


def local_now():
    """Return the current time as a timezone-aware datetime in the local zone."""
    return to_local(utc_now())


def monotonic():
    """Clock for measuring intervals. Unaffected by clock or timezone changes."""
    return time.monotonic()


# ------------------------------------------------------------------- conversions


def _assume_local(moment):
    """Attach the local zone to a naive datetime (legacy records were local)."""
    zone = local_timezone()
    if zone is None:
        return moment.astimezone()
    return moment.replace(tzinfo=zone)


def to_utc(moment):
    """Return ``moment`` as an aware UTC datetime.

    Naive datetimes are assumed to be in the local timezone, which is how
    earlier versions of Iceberg produced them.
    """
    if moment.tzinfo is None:
        moment = _assume_local(moment)
    return moment.astimezone(UTC)


def to_local(moment):
    """Return ``moment`` as an aware datetime in the local timezone."""
    if moment.tzinfo is None:
        moment = _assume_local(moment)
    return moment.astimezone(local_timezone())


def utc_offset_label(moment):
    """Return a neutral offset label such as ``UTC-05:00`` or ``UTC+00:00``."""
    offset = moment.utcoffset()
    if offset is None:
        offset = datetime.timedelta(0)
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    return f"UTC{sign}{total_minutes // 60:02d}:{total_minutes % 60:02d}"


# ------------------------------------------------------------------------ storage


def storage_timestamp(moment=None):
    """Return the string that should be written to ``Created_Time``/``Edited_Time``.

    Always UTC, second precision, ISO 8601 with explicit ``+00:00`` offset.
    """
    if moment is None:
        moment = utc_now()
    moment = to_utc(moment).replace(microsecond=0)
    return moment.isoformat()


def parse_timestamp(value):
    """Parse any timestamp Iceberg has ever written and return an aware datetime.

    Returns ``None`` when ``value`` is empty or cannot be understood.

    Supported inputs:

    * ``2025-12-21T22:47:03+00:00`` (current storage format)
    * ``2025-12-21 18:09:15.208771`` (``str(datetime.now())``, treated as local)
    * ``Sunday, 12/21/2025  -  17:47 EDT`` and ``... 17:47:03 EDT`` (legacy
      display strings, treated as local; the zone name is ignored because it
      was frequently wrong)
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    try:
        parsed = datetime.datetime.fromisoformat(text)
    except ValueError:
        parsed = None

    if parsed is None:
        legacy = _LEGACY_PREFIX.sub("", text)
        legacy = _LEGACY_SEPARATOR.sub(" ", legacy)
        legacy = _TRAILING_TZ_NAME.sub("", legacy)
        try:
            parsed = _dateutil_parser.parse(legacy, ignoretz=True)
        except (ValueError, OverflowError):
            return None

    if parsed.tzinfo is None:
        parsed = _assume_local(parsed)
    return parsed


# ------------------------------------------------------------------------ display


def format_display(moment=None, seconds=False):
    """Format a moment for people, in the local timezone with a neutral offset.

    Example: ``Sunday, 12/21/2025  -  17:47 (UTC-05:00)``
    """
    if moment is None:
        moment = local_now()
    else:
        moment = to_local(moment)
    weekday = WEEKDAY_NAMES[moment.weekday()]
    clock = f"{moment.hour:02d}:{moment.minute:02d}"
    if seconds:
        clock = f"{clock}:{moment.second:02d}"
    return (
        f"{weekday}, {moment.month}/{moment.day}/{moment.year}"
        f"  -  {clock} ({utc_offset_label(moment)})"
    )


def display_timestamp(value, seconds=True):
    """Convert a stored timestamp string into the local display format.

    Unknown or empty values are returned unchanged so nothing is hidden.
    """
    parsed = parse_timestamp(value)
    if parsed is None:
        return "" if value is None else str(value)
    return format_display(parsed, seconds=seconds)


def local_date_string(moment=None):
    """Return the local calendar date as ``YYYY-MM-DD``."""
    if moment is None:
        moment = local_now()
    else:
        moment = to_local(moment)
    return moment.strftime("%Y-%m-%d")


def local_date_from_timestamp(value, default=None):
    """Return the local ``YYYY-MM-DD`` date for a stored timestamp.

    Used for dates printed on invoices.  Falls back to ``default`` (today when
    not given) if the value cannot be parsed.
    """
    parsed = parse_timestamp(value)
    if parsed is None:
        return default if default is not None else local_date_string()
    return local_date_string(parsed)


def file_timestamp(moment=None):
    """Return a filesystem-safe UTC stamp for backup names: ``20251221T224703Z``."""
    if moment is None:
        moment = utc_now()
    return to_utc(moment).strftime("%Y%m%dT%H%M%SZ")


def get_current_time_info():
    """Compatibility helper returning ``(display_without_seconds, display_with_seconds)``."""
    moment = local_now()
    return format_display(moment), format_display(moment, seconds=True)
