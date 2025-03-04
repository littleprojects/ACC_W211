'''
Helper Functions
'''

import math
import time
import logging
import datetime


# return ts in sec
def ts():
    return math.floor(time.time())


# return timestamp in ms
def ts_ms():
    return round(time.time() * 1000)


# return date and Time string
def date_time_str(ts=time.time()):
    return str(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')) + ": "


# parse Float numbers
def is_float(value):
    try:
        float(value)
        return True
    except:
        return False


# parse integer
def is_int(value):
    try:
        int(value)
        return True
    except:
        return False


# parse number to int, Float, None or return the string
def parse_number(value, decimals=2, cut_nbr=True):
    if is_int(value):
        return int(value)

    if is_float(value):
        if cut_nbr:
            if decimals > 0:
                return round(float(value), decimals)  # return float
            else:
                return round(float(value))  # return int
        else:
            return float(value)

    if value == '1.#QNAN':
        return None

    return None


# parse string or int to bool
def str_to_bool(s: str):
    """
    convert string and int to bool
    :param s:
    :return:
    """
    s = str(s)  # convert int to str
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    elif s == '0':
        return False
    elif s == '1':
        return True
    else:
        raise ValueError("The parameter '" + str(s) + "' can't be converted to a boolean!")
    

# check if a interval is over or not, check and reset global variabel
def interval(global_var_name, interval_time, cur_ts=None):
    """
    Return True if the interval is over
    param: global_var_name  - name of the global timestamp var to check the current time
    param: interval_time    - interval duration in seconds
    param: cur_ts           - optional current timestamp input

    :return:    True or False (True Interval is over) if TRUE -> global_var will set to current timestamp
    """

    if cur_ts is None:
        cur_ts = ts_ms()

    last_interval_ts = globals()[global_var_name]

    # calc time diff
    ts_diff = cur_ts - last_interval_ts

    # check number
    # interval_time = utils.parseNumber(interval_time)

    # is time diff over or equal interval time
    if ts_diff >= interval_time:
        # rest mdf_interval timestamp
        globals()[global_var_name] = cur_ts

        # yes
        return True

    # no
    return False


def parse_log_level(log_level_str):
    """
    Set Module loglevel
    :param log_level_str: config sentence to map to loglevel
    :return: loglevel
    """
    log_level_str = log_level_str.upper()

    log_level = {"DEBUG": logging.DEBUG,
                 "INFO": logging.INFO,
                 "WARNING": logging.WARNING,
                 "ERROR": logging.ERROR,
                 "CRITICAL": logging.CRITICAL
                 }

    if log_level.get(log_level_str):
        return log_level.get(log_level_str)
    else:
        return logging.INFO