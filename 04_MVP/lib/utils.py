"""
Helper Functions for
- timestamp and date_time
- parsing numbers and booleans
"""

import time
import logging
import datetime

from typing import Any, Optional


# ------- timestamp and date time stuff ---------

def timestamp_s() -> int:
    """Return current timestamp in seconds."""
    return int(time.time())


def timestamp_ms() -> int:
    """Return current timestamp in milliseconds."""
    return round(time.time() * 1000)


def date_time_str(ts: float | None = None) -> str:
    """Return formatted date-time string for given timestamp (default: now)."""
    if ts is None:
        ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H-%M-%S")


# ------ parsing numbers and bools -----------

def is_float(value: Any) -> bool:
    """Check if a value can be parsed as float."""
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def is_int(value: Any) -> bool:
    """Check if a value can be parsed as int."""
    try:
        # int("3.5") würde ValueError werfen → korrekt
        int(value)
        return True
    except (TypeError, ValueError):
        return False


def parse_number(value: Any, decimals: int = 2, cut_nbr: bool = True) -> Optional[float | int]:
    """
    Parse a value into int, float, or None.

    Args:
        value: Input value to parse.
        decimals: Number of decimal places to round floats.
        cut_nbr: If True, round floats; if False, return raw float.

    Returns:
        int, float, or None
    """
    if is_int(value):
        return int(value)

    if is_float(value):
        fval = float(value)
        if cut_nbr:
            return round(fval, decimals) if decimals > 0 else round(fval)
        return fval

    if str(value) == "1.#QNAN":
        return None

    return None


def str_to_bool(value: Any) -> bool:
    """
    Convert string or int to boolean.

    Args:
        value: Input value (string or int).

    Returns:
        bool

    Raises:
        ValueError: If the value cannot be converted.
    """
    s = str(value).strip().lower()
    if s in ("true", "1"):
        return True
    if s in ("false", "0"):
        return False
    raise ValueError(f"Cannot convert '{value}' to boolean.")


def interval(state: dict, key: str, interval_time: int, cur_ts: int | None = None) -> bool:
    """
    Check if an interval has elapsed and reset the timestamp.

    Args:
        state: Dictionary holding timestamps.
        key: Key in the dictionary for the last timestamp.
        interval_time: Interval duration in milliseconds.
        cur_ts: Optional current timestamp (default: now in ms).

    Returns:
        True if interval is over (and timestamp reset), False otherwise.
    """
    if cur_ts is None:
        cur_ts = timestamp_ms()

    last_ts = state.get(key, 0)
    if cur_ts - last_ts >= interval_time:
        state[key] = cur_ts
        return True
    return False


def parse_log_level(log_level_str: str) -> int:
    """
    Map a string to a logging level.
    Defaults to INFO if unknown.
    """
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return log_levels.get(log_level_str.upper(), logging.INFO)


def dbc_signal(dbc, signal_name: str, msg_id: int | None = None):
    """
    Find a signal in a DBC by name and optional message ID.

    Args:
        dbc: DBC object (with messages).
        signal_name: Name of the signal to search.
        msg_id: Optional message ID.

    Returns:
        Signal object if found, else None.
    """
    if msg_id is not None:
        message = dbc.get_message_by_frame_id(msg_id)
        return next((s for s in message.signals if s.name == signal_name), None)

    for message in dbc.messages:
        signal = next((s for s in message.signals if s.name == signal_name), None)
        if signal is not None:
            return signal
    return None
