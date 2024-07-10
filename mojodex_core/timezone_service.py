import pytz
from datetime import datetime, timedelta, timezone
from tzlocal import get_localzone
from dateutil.parser import parse

def ensure_timezone(dt_str, default_tz=pytz.UTC):
    """
        This function takes a date string (`dt_str`) and an optional timezone object (`default_tz`), which defaults to UTC.
        It parses the date string into a datetime object using the `parse()` function from the `dateutil` module.
        If the parsed datetime object does not have timezone information, the function returns the datetime object localized to the default timezone.
        Otherwise, it returns the datetime object unchanged.
        :param dt_str: date string
        :param default_tz: timezone object
        :return: datetime object
        """
    dt = parse(dt_str)
    if dt.tzinfo is None:
        return default_tz.localize(dt)
    return dt

def device_date_to_backend_date(device_date, timezone_offset):
    """
        This function takes a device date isoformat date (`device_date`) and a timezone offset (`timezone_offset`)
        and returns it adjusted to the server's local timezone.

        :param device_date: isoformat date
        :param timezone_offset: timezone offset int - number of minutes to remove to UTC to get the user's local time
        :return: adjusted datetime object
        """
    try:
        device_date = datetime.fromisoformat(device_date)
        offset = timedelta(minutes=timezone_offset)
        adjusted_datetime = device_date + offset # set to UTC
        server_timezone = get_localzone()
        return adjusted_datetime.replace(tzinfo=pytz.UTC).astimezone(server_timezone) # set to server timezone
    except Exception as e:
        raise Exception(f"Invalid device_date or timezone_offset : {e}")

def current_time_in_timezone(timezone_offset):
    """
    This function takes a timezone offset (`timezone_offset`) and returns the current time in this timezone.
    :param timezone_offset: timezone offset as int - number of minutes to remove to UTC to get the user's local time
    :return: adjusted datetime object
    """
    try:
        offset = timedelta(minutes=timezone_offset)
        return datetime.now(timezone.utc) - offset
    except Exception as e:
        raise Exception(f"Invalid timezone_offset : {e}")

def backend_date_to_user_date(timestamp, user_timezone_offset):
    """
    This function takes a backend timestamp (`timestamp`) and a timezone offset (`user_timezone_offset`)
    :param timestamp: backend date to convert
    :param user_timezone_offset: timezone offset as int - number of minutes to remove to UTC to get the user's local time
    :return:
    """
    try:
        # backend to utc
        if timestamp.tzinfo is None:
            return pytz.UTC.localize(timestamp)
        else:
            utc_date = timestamp.astimezone(pytz.UTC)
        # utc to user timezone
        offset = timedelta(minutes=user_timezone_offset)
        return utc_date + offset
    except Exception as e:
        raise Exception(f"Invalid timestamp or user_timezone_offset : {e}")