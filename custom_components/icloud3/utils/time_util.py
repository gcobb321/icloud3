
from ..global_variables         import GlobalVariables as Gb
from ..const                    import (HIGH_INTEGER, HHMMSS_ZERO, HHMM_ZERO, DATETIME_ZERO,
                                        DATETIME_FORMAT, WAZE_USED, )

from .messaging                 import (_evlog, _log, post_event, post_alert, log_exception, internal_error_msg, )
from .utils                     import instr

import homeassistant.util.dt    as dt_util
import time
from zoneinfo                   import ZoneInfo
from datetime                   import datetime, timedelta, timezone

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Current Time conversion and formatting functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def time_now_secs():
    ''' now --> epoch/unix secs '''
    return int(time.time())

#--------------------------------------------------------------------

def time_now_utc_secs():
    ''' now ==> utc time zone (secs)'''
    return time_now_secs() - Gb.time_zone_offset_secs

#--------------------------------------------------------------------
def time_now():
    ''' now --> epoch/unix 10:23:45 '''
    return str(datetime.fromtimestamp(int(time.time())))[11:19]

#--------------------------------------------------------------------
def utcnow():
    '''
    Return the utcnow datetime item

    now=datetime.datetime(2024, 8, 29, 19, 44, 55, 444380, tzinfo=datetime.timezone.utc)
    dt_util.utcnow()=datetime.datetime(2024, 8, 29, 19, 44, 55, 446351, tzinfo=datetime.timezone.utc)
    utcnow = 2024-08-29 19:44:55.442437+00:00
    '''
    return dt_util.utcnow()

#--------------------------------------------------------------------
def datetime_plus(datetime, secs=None, mins=None, hrs=None, days=None):
        '''
        Determine the current datetime + specified interval

        datetime: datetime.datetime(2024, 8, 29, 19, 44, 55, 444380, tzinfo=datetime.timezone.utc)
        '''
        secs = secs or 0
        mins = mins or 0
        hrs  = hrs  or 0
        days = days or 0
        return datetime + timedelta(days=days, seconds=secs, minutes=mins, hours=hrs)

#--------------------------------------------------------------------
def datetime_now(datetime_struct=False):
    ''' now --> epoch/unix yyy-mm-dd 10:23:45 '''
    if datetime_struct:
        return datetime.fromtimestamp(int(time.time()))
    else:
        return str(datetime.fromtimestamp(int(time.time())))


#--------------------------------------------------------------------
def smh_time(time):
    smh_time_str = time.replace(' sec', 's').replace(' secs', 's')
    smh_time_str = smh_time_str.replace(' min', 'm').replace(' mins', 'm')
    smh_time_str = smh_time_str.replace(' hr', 'h').replace(' hrss', 'h')
    return smh_time_str

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Time conversion and formatting functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def secs_local(secs_utc):
    return secs_utc + Gb.time_zone_offset_secs

#--------------------------------------------------------------------
def time_local(secs_utc):
    ''' secs_utc --> 10:23:45 '''
    return datetime_local(secs_utc)[11:19]

#--------------------------------------------------------------------
def datetime_local(secs_utc):
    ''' secs_utc --> 2024-03-15 10:23:45 '''
    if isnot_valid(secs_utc): return DATETIME_ZERO

    return str(datetime.fromtimestamp(secs_utc))

#--------------------------------------------------------------------
def isnot_valid(secs):
    '''
    Not valid if before 1/1/2020, = 9999999999 or None
    '''
    try:
        return secs < 1 or secs == HIGH_INTEGER or secs is None
    except:
        return True
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Time conversion and formatting functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def s2t(secs_utc):
    return secs_to_time(secs_utc)

#--------------------------------------------------------------------
def secs_to_time(secs_utc):
    ''' secs --> 10:23:45/h:mm:ssa  '''

    if isnot_valid(secs_utc): return HHMMSS_ZERO

    return time_to_12hrtime(time_local(secs_utc))

#--------------------------------------------------------------------
def secs_to_datetime(secs_utc, format_ymd=False):
    ''' secs --> 2024-03-16 12:55:03 '''

    return datetime_local(secs_utc)

#--------------------------------------------------------------------
def secs_to_even_min_secs(secs_utc_or_min, min=None):
    '''
    secs --> secs for next even min interval

    Parameters:
        secs_utc_or_min - utc_secs to adjust from
        min             - adjustment minutes (+ or -)
    or:
        secs_utc_or_min - adjustment minutes (+ or -) from utc time now
        min             - Not specified
    '''

    if min is None:
        secs_utc = int(time.time())
        min_secs = secs_utc_or_min * 60
    else:
        secs_utc = secs_utc_or_min
        min_secs = min * 60

    if min_secs > 0:
        prev_secs_adj = 0
    else:
        prev_secs_adj = min_secs
        if prev_secs_adj <= -3600:
            prev_secs_adj -= 3600
        min_secs = abs(min_secs)

    return secs_utc - (secs_utc % min_secs) + min_secs + prev_secs_adj

#--------------------------------------------------------------------
def secs_to_hhmm(secs_utc):
    ''' secs --> hh:mm or hh:mma or hh:mmp '''

    try:
        if isnot_valid(secs_utc): return '00:00'

        if Gb.time_format_24_hour:
            return time_local(secs_utc+30)[:-3]

        hhmmss = time_to_12hrtime(time_local(secs_utc+30))
        hhmm = hhmmss[:-4] + hhmmss[-1:]
        hhmm += secs_to_days(secs_utc, '-d')

        return hhmm

    except:
        return '00:00'

#--------------------------------------------------------------------
def secs_since(secs):
    if isnot_valid(secs): return 0

    return round(time_now_secs() - secs)

def mins_since(secs):
    return round(secs_since(secs)/60)

#--------------------------------------------------------------------
def secs_to(secs):
    if isnot_valid(secs): return 0

    return round(secs - time_now_secs())

def mins_to(secs):
    return round(secs_since(secs)/60)


#--------------------------------------------------------------------
def secs_to_days(secs, days_text):
    ''' Return the number of days old as a text field '''

    days = secs_since(secs)/86400
    if days < 1:
        return ''

    if days_text.startswith('-'):
        return f"-{days:.0f}{days_text[:1]}"
    else:
        return f"{days:.0f}{days_text}"

#--------------------------------------------------------------------
def next_min_mark_secs(mark_mins, plus_mins=0):
    '''
    now to next mins mark in secs 
        10:23:23 --> 10:23:25 (5)
        10:23:23 --> 10:23:35 (5, 10)
        10:23:23 --> 10:23:30 (10)
        10:23:23 --> 10:23:40 (10, 10)
    '''

    now_secs  = time_now_secs()
    mark_secs = mark_mins * 60

    secs_since_last_mins_mark = now_secs % mark_secs
    secs_to_next_mins_mark    = mark_secs - secs_since_last_mins_mark
    next_mark_secs            = now_secs + secs_to_next_mins_mark + (plus_mins * 60)

    return next_mark_secs

#--------------------------------------------------------------------
def time_to_12hrtime(hhmmss, ampm=True):
    ''' 10:23:45 --> (h)h:mm:ssa or (h)h:mm:ssp '''

    try:
        if hhmmss == HHMMSS_ZERO:
            return HHMMSS_ZERO if Gb.time_format_24_hour else '00:00:00a'

        if (Gb.time_format_24_hour
                or hhmmss.endswith('a')
                or hhmmss.endswith('p')):
            return hhmmss

        hh_mm_ss    = hhmmss.split(':')
        hhmmss_hh   = int(hh_mm_ss[0])
        secs_suffix = hh_mm_ss[2].split('-')

        ap = 'a'
        if hhmmss_hh > 12:
            hhmmss_hh -= 12
            ap = 'p'
        elif hhmmss_hh == 12:
            ap = 'p'
        elif hhmmss_hh == 0:
            hhmmss_hh = 12

        if ampm is False:
            ap = ''

        hhmmss = f"{hhmmss_hh}:{hh_mm_ss[1]}:{secs_suffix[0]}{ap}"
        if len(secs_suffix) == 2:
            hhmmss += f"-{secs_suffix[1]}"
    except:
            pass

    return hhmmss

#--------------------------------------------------------------------
def time_to_24hrtime(hhmmss):
    ''' (h)h:mm:ssa or (h)h:mm:ssp --> hh:mm:ss '''

    hhmm_colon = hhmmss.find(':')
    if hhmm_colon == -1: return hhmmss

    ap = hhmmss[-1].lower()                # Get last character of time (#, a, p).lower()
    if ap not in ['a', 'p']:
        return hhmmss

    hh = int(hhmmss[:hhmm_colon])
    if hh == 12 and ap == 'a':
        hh = 0
    elif hh <= 11 and ap == 'p':
        hh += 12

    hhmmss24 = f"{hh:0>2}{hhmmss[hhmm_colon:-1]}"

    return hhmmss24
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   FORMAT TIMER & AGE FUNCTIONS
#       Timer    - An item like 30 secs, 10 mins, 1.4 hrs
#       Age      - An item like 30 secs ago, 10 mins ago, 1.4 hrs ago
#       Time_Age - An item like 10:23:45 (10 mins ago)
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def format_timer(secs):
    ''' secs --> 4.5 days/hrs/mins/secs '''

    try:
        if secs < 1:
            return '0 secs'

        if secs >= 86400:
            time_str = f"{secs/86400:.1f} days"
        elif secs < 60:
            time_str = f"{secs:.0f} secs"
        elif secs < 3600:
            time_str = f"{secs/60:.0f} mins"
        elif secs == 3600:
            time_str = "1 hr"
        else:
            time_str = f"{secs/3600:.1f} hrs"

        # change xx.0 min/hr --> xx min/hr
        time_str = time_str.replace('.0 ', ' ')
        if time_str == '1 mins': time_str = '1 min'

    except Exception as err:
        #_LOGGER.exception(err)
        time_str = ''

    return time_str

#--------------------------------------------------------------------
def format_timer_hrs(secs):
    ''' secs --> ##.# hrs '''
    if isnot_valid(secs): return '0 hrs'

    return f"{secs/3600:.1f} hrs"

#--------------------------------------------------------------------
def format_mins_timer(mins):
    ''' mins --> 4.5 days/min/hrs '''

    try:
        if mins == 0:
            return '0 min'

        if mins >= 86400:
            time_str = f"{mins/1440:.2f} days"
        elif mins < 60:
            time_str = f"{mins:.1f} min"
        elif mins == 60:
            time_str = "1 hr"
        else:
            time_str = f"{mins/60:.1f} hrs"

        # change xx.0 min/hr --> xx min/hr
        time_str = time_str.replace('.0 ', ' ')

    except Exception as err:
        time_str = ''

    return time_str

#--------------------------------------------------------------------
def format_age(secs, xago=None):
    ''' secs --> 4.5 sec/mins/hrs ago '''

    if isnot_valid(secs): return 'Never'
    if secs < 1577854800: return 'Unknown'
    ago = ' ago' if xago is None else ''

    return f"{format_timer(secs_since(secs))}{ago}"

#--------------------------------------------------------------------
def format_age_hrs(secs, xago=None):
    ''' secs --> 4.5 hrs ago '''

    if isnot_valid(secs): return 'Never'
    if secs < 1577854800: return 'Unknown'
    ago = ' ago' if xago is None else ''

    return f"{format_timer_hrs(secs_since(secs))}{ago}"

#--------------------------------------------------------------------
def format_time_age(secs, xago=None):
    ''' secs --> 10:23:45 or h:mm:ssa/p (4.5 sec/mins/hrs ago) '''

    if isnot_valid(secs): return 'Unknown'

    age_secs = secs_since(secs)
    if age_secs >= 86400:
        if secs < 1577854800:
            return 'Unknown'
        else:
            return f"{age_secs/86400:.1f} days ago"

    ago = ' ago' if xago is None else ''
    return (f"{secs_to_time(secs)} "
            f"({format_timer(age_secs)}{ago})")

#--------------------------------------------------------------------
def format_secs_since(secs):
    ''' secs --> 4.5 secs/mins/hrs '''

    if isnot_valid(secs): return 'Never'
    if secs < 1577854800: return 'Unknown'

    return f"{format_timer(secs_since(secs))}"

#--------------------------------------------------------------------
def format_now():
    ''' 12-hour time now '''
    return secs_to_time(time_now_secs())

#--------------------------------------------------------------------
def format_day_date_time_now():
    ''' Sat, 06/14, 02:11:33 '''

    return f"{dt_util.now().strftime('%a, %m/%d, %H:%M:%S')}"

#--------------------------------------------------------------------
def format_day_date():
    ''' Saturday, June 14'''

    return f"{dt_util.now().strftime('%a, %b %-d')}"

#--------------------------------------------------------------------
def format_day_date_now():
    ''' Saturday, June 14, 4:30p '''

    return f"{format_day_date()}, {secs_to_hhmm(time_now_secs())}"

#--------------------------------------------------------------------
def format_age_hrs(secs, xago=None):
    ''' secs --> 4.5 hrs ago '''

    if isnot_valid(secs): return 'Never'
    if secs < 1577854800: return 'Unknown'
    ago = ' ago' if xago is None else ''

    return f"{format_timer_hrs(secs_since(secs))}{ago}"

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Time conversion and formatting functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# def hhmmss_to_secs(hhmmss):
#     return time_to_secs(hhmmss)

def time_to_secs(hhmmss):
    ''' 10:23:45 --> secs '''
    try:
        hh_mm_ss = hhmmss.split(":")
        secs = int(hh_mm_ss[0]) * 3600 + int(hh_mm_ss[1]) * 60 + int(hh_mm_ss[2])

    except:
        secs = 0

    return secs

#--------------------------------------------------------------------
def time_remove_am_pm(hhmmssap):
    return hhmmssap.replace('a', '').replace('p', '')

#--------------------------------------------------------------------
def time_str_to_secs(time_str=None) -> int:
    ''' 20 sec/min/hrs --> secs '''

    if time_str is None or time_str == "": return 0

    try:
        s1 = str(time_str).replace('_', ' ') + " min"
        time_part = float((s1.split(" ")[0]))
        text_part = s1.split(" ")[1]

        if text_part in ('sec', 'secs'):
            secs = time_part
        elif text_part in ('min', 'mins'):
            secs = time_part * 60
        elif text_part in ('hr', 'hrs'):
            secs = time_part * 3600
        else:
            secs = 0

        if secs < 0: secs = 0

    except:
        secs = 0

    return secs

#--------------------------------------------------------------------
def datetime_to_secs(date_time, date_time_format=None):

    if date_time_format is None:
        date_time_format = "%Y-%m-%d %H:%M:%S"

    dt_struct = datetime.strptime(date_time, date_time_format)
    secs = datetime.timestamp(dt_struct)

    return secs

#--------------------------------------------------------------------
def datetime_struct_to_secs(datetime_struct):
    '''
    Determine secs from datetime structure
    Input: datetime.datetime(2025, 1, 3, 21, 17, 1, 226338, tzinfo=datetime.timezone.utc)
    Return: secs (1736156863.690547)
    '''

    return datetime_struct.timestamp()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Time conversion and formatting functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def datetime_to_time(datetime):
    '''
    Extract the time from the device timeStamp attribute
    updated by the IOS app.
    Format #1 is --'datetime': '2019-02-02 12:12:38.358-0500'
    Format #2 is --'datetime': '2019-02-02 12:12:38 (30s)'
    '''

    try:
        # '0000-00-00 00:00:00' --> '00:00:00'
        if datetime == DATETIME_ZERO:
            return HHMMSS_ZERO

        # '2019-02-02 12:12:38.358-0500' --> '12:12:38'
        elif datetime.find('.') >= 0:
            return datetime[11:19]

        # '2019-02-02 12:12:38 (30s)' --> '12:12:38 (30s)'
        elif datetime.find('-') >= 0:
            return datetime[11:]

        else:
            return datetime

    except:
        pass

    return datetime

#--------------------------------------------------------------------
def datetime_for_filename():
    '''
    Convert seconds to timestamp
    Return timestamp (05-19 09:12:30)
    '''
    try:
        time_struct = time.localtime(time_now_secs())
        timestamp   = time.strftime("%Y.%m%d-%H.%M", time_struct)

    except Exception as err:
        timestamp = DATETIME_ZERO

    return timestamp

#########################################################
#
#   TIME UTILITY ROUTINES
#
#########################################################

def calculate_time_zone_offset():
    '''
    Calculate time zone offset seconds
    '''
    try:
        # Get time_zone from HA and determine local xone offsets
        local_zone_name = Gb.ha_location_info.get('time_zone', None)

        if local_zone_name is not None:
            # Extract offset (+08:00 part of 2025-05-28 06:12:01.718366+08:00)
            local_zone_offset = str(datetime.now(ZoneInfo(local_zone_name)))[-6:]
            local_zone_offset_secs = (int(local_zone_offset[1:3])*3600 +
                                        int(local_zone_offset[4:])*60)
    except Exception as err:
        local_zone_name = None

    # HA time zone is not available or eeor getting Zone Info (internet down),
    # determine time_zone from hardware time
    if local_zone_name is None:
        local_zone_name        = dt_util.now().strftime('%Z')
        local_zone_offset      = dt_util.now().strftime('%z')
        local_zone_offset_secs = int(local_zone_offset[1:3])*3600 + \
                                        int(local_zone_offset[3:])*60

    try:
        if local_zone_offset.startswith("-"):
            local_zone_offset_secs = -1*local_zone_offset_secs

        if local_zone_offset.startswith("-"):
            local_zone_offset_secs = -1*local_zone_offset_secs

        Gb.time_zone_offset_str  = local_zone_offset
        Gb.time_zone_offset_secs = local_zone_offset_secs

        post_event( f"Local Time Zone > "
                    f"{local_zone_name}, "
                    f"(UTC {Gb.time_zone_offset_str} hrs) "
                    f"Country Code-{Gb.country_code.upper()}, "
                    f"Apple Server Time-{apple_server_time()}")

        return local_zone_offset_secs

    except Exception as err:
        log_exception(err)
        Gb.time_zone_offset_str  = 'UTC'
        Gb.time_zone_offset_secs = 0

    return 0

#--------------------------------------------------------------------------------
def apple_server_time():
    # Get Apple Server Time that displays when password authentication is done
    apple_zone_datetime = datetime.now(ZoneInfo('America/Los_Angeles'))
    apple_time_structure = '%b %d, %Y, %H:%M PST'
    if Gb.time_format_12_hour:
        apple_time_structure.replace('H', '-I')

    return apple_zone_datetime.strftime(apple_time_structure)

#--------------------------------------------------------------------------------
def adjust_time_hour_values(text_str, hh_adjustment):
    '''
    Adjust the hour value of all time fields in a text string
    '''

    time_fields = extract_time_fields(text_str)
    if time_fields == []: return text_str

    for time_field in time_fields:
        text_str = text_str.replace(time_field,
                                    adjust_time_hour_value(time_field, hh_adjustment))

    return text_str

#--------------------------------------------------------------------------------
def extract_time_fields(msg_str):
    '''
    Parse the str and extract all time fields:
        h:mm:ss, 10:23:45, h:mm:ssa, h:mm:ssp, etc
    Return:
        List of Time fields or []
    '''

    if type(msg_str) is not str:
        return []

    hhmm_colon = 0
    times_found = set()
    while msg_str.find(':', hhmm_colon) >= 0:
        hhmm_colon = msg_str.find(':',hhmm_colon)

        if msg_str[hhmm_colon-1].isnumeric() is False:
            hhmm_colon += 1
            continue

        if  msg_str[hhmm_colon+1:hhmm_colon+2].isnumeric() is False:
            hhmm_colon += 3
            continue

        # hh:mm or hh:mm:ss
        try:
            mmss_colon = 3 if msg_str[hhmm_colon+3] == ':' else 0
        except:
            mmss_colon = 0

        # if mmss_colon == len(msg_str): mmss_colon -= 1
        end_pos = hhmm_colon + mmss_colon + 3
        if hhmm_colon == 1: hhmm_colon = 2
        time = msg_str[hhmm_colon-2:end_pos]
        try:
            if instr('apAP', msg_str[end_pos]): time += msg_str[end_pos]
        except:
            pass

        if time[0].isnumeric() is False: time = time[1:]

        times_found.add(time)
        hhmm_colon += 4

    return list(times_found)

#--------------------------------------------------------------------------------
def adjust_time_hour_value(hhmmss, hh_adjustment):
    '''
    All times are based on the HA server time. When the device is in another time
    zone, convert the HA server time to the device's local time so the local time
    can be displayed on the Event Log and in time-based sensors.

    Input:
        hhmmss - HA server time (hh:mm, hh:mm:ss, hh:mm(a/p), hh:mm:ss(a/p))
        hh_adjustment - Number of hours between the HA server time and the
            local time (-12 to 12)
    Return:
        new time value in the same format as the Input hhmmss time
    '''
    try:
        if hh_adjustment == 0 or hhmmss == HHMMSS_ZERO or hhmmss == HHMM_ZERO:
            return hhmmss

        if hhmmss.find(':') == -1: return hhmmss

        if Gb.time_format_24_hour:
            hh = int(hhmmss[0:2]) + hh_adjustment
            if hh <= 0:  hh += 24
            elif hh >= 24: hh -=24
            return f"{hh:0>2}{hhmmss[2:]}"

        has_ap_flag = instr('apAP', hhmmss[-1])
        ap = hhmmss[-1].lower() if has_ap_flag else ''

        if hhmmss[1:2] == ':': hhmmss = f"0{hhmmss}"
        hhmm_flag = len(hhmmss) < 7
        _hhmmss = f"{hhmmss[:5]}:99{ap}" if hhmm_flag else hhmmss
        hhmmss24 = time_to_24hrtime(_hhmmss)

        hh = int(hhmmss24[0:2]) + hh_adjustment
        if   hh <= 0:  hh += 24
        elif hh >= 24: hh -=24
        ap = '' if has_ap_flag is False else 'a' if hh < 12 or hh == 24 else 'p'

        adj_hhmmss24 = f"{hh:0>2}{hhmmss24[2:8]}"
        adj_hhmmss   = time_to_12hrtime(adj_hhmmss24).replace(':99', '')
        if has_ap_flag is False: adj_hhmmss = adj_hhmmss.replace('a', '').replace('p', '')

        return adj_hhmmss

    except Exception as err:
        pass
        # log_exception(err)

        return hhmmss

#--------------------------------------------------------------------
def timestamp_to_time_utcsecs(utc_timestamp) -> int:
    '''
    Used by pyicloud_ic3
    Convert iCloud timeStamp into the local time zone and
    return hh:mm:ss
    '''
    ts_local = int(float(utc_timestamp)/1000) + Gb.time_zone_offset_secs
    hhmmss   = dt_util.utc_from_timestamp(ts_local).strftime(Gb.um_time_strfmt)
    if hhmmss[0] == "0":
        hhmmss = hhmmss[1:]

    return hhmmss

#--------------------------------------------------------------------
# def _has_ap(hhmmss):
#     ''' See if  the time ends in a or p (12-hour time) '''
#     return hhmmss[-1].lower() in ['a', 'p']

# def _ap(hhmmss):
#     return hhmmss[-1].lower() if _has_ap(hhmmss) else ''
