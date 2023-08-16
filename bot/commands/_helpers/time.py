from datetime import datetime, timedelta
import pytz

def how_long_ago(time_start):

    time_now = datetime.now()
    time_start_format = datetime.strptime(time_start, '%Y-%m-%dT%H:%M:%SZ')

    time_diff = time_now - time_start_format

    return pretty_time_delta(time_diff)

def pretty_time_delta(full_datetime):

    time_in_seconds = full_datetime.days * 24 * 60 * 60
    time_in_seconds += full_datetime.seconds
    time_in_seconds += full_datetime.microseconds / 1000000

    seconds = int(time_in_seconds)

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "{}d {}h {}m".format(days, hours, minutes)
    elif hours > 0:
        return "{}h {}m".format(hours, minutes)
    elif minutes > 0:
        return "{}m".format(minutes)
    else:
        return "{}s".format(seconds)

def get_formated_start_end(format_str, time_offset):

    tz_GMT = pytz.timezone('GMT')
    time_now = datetime.now(tz_GMT)

    time_start_format = time_now.strftime(format_str)

    time_end = time_now + timedelta(hours=time_offset)
    time_end_format = time_end.strftime(format_str)

    return time_start_format, time_end_format

def how_many_hours_left(end_time, time_zone):

    timezone = pytz.timezone(time_zone)
    time_now = datetime.now(timezone)

    endtime = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S%z')

    time_difference = endtime - time_now
    hours, seconds = divmod(time_difference.seconds, 3600)

    if hours > 0:
        return "{} hour(s)".format(hours)

    return "{} minute(s)".format(int(seconds/60))
