
from ..global_variables         import GlobalVariables as Gb
from ..const                    import ( HIGH_INTEGER, HHMMSS_ZERO, DATETIME_ZERO, DATETIME_FORMAT, WAZE_USED, )

from .messaging                 import (_trace, _traceha, post_event, internal_error_msg, )
from .common                    import instr

import homeassistant.util.dt    as dt_util
import time
from datetime                   import datetime, timedelta

#import re
#[m.start() for m in re.finditer('test', 'test test test test')]
#[0, 5, 10, 15]
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Time conversion and formatting functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def time_now():
    ''' Return now in MM/DD/YYYY hh:mm:ss format'''
    return (dt_util.now().strftime(DATETIME_FORMAT)[11:19])

#--------------------------------------------------------------------
def time_now_secs():
    ''' Return the current timestamp seconds '''
    return int(time.time())

#--------------------------------------------------------------------
def time_secs():
    ''' Return the current timestamp seconds '''
    return int(time.time())

#--------------------------------------------------------------------
def time_msecs():
    ''' Return the current timestamp milli-seconds '''
    return time.time()

#--------------------------------------------------------------------
def datetime_now():
    ''' Return now in MM/DD/YYYY hh:mm:ss format'''
    return (dt_util.now().strftime(DATETIME_FORMAT)[0:19])

#--------------------------------------------------------------------
def msecs_to_time(secs):
    """ Convert milliseconds (e.g., iCloud timestamp) to hh:mm:ss """
    return secs_to_time(int(secs/1000))

#--------------------------------------------------------------------
def secs_to_time_str(secs):
    """ Create the time string from seconds """

    try:
        if secs < 1:
            return '0 min'

        if secs >= 86400:
            time_str = f"{secs/86400:.1f} days"   #secs_to_dhms_str(secs)
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
def secs_to_hrs_str(secs):
    if secs < 1:
        return '0 hrs'
    else:
        return f"{secs/3600:.1f} hrs"

#--------------------------------------------------------------------
def mins_to_time_str(mins):
    """ Create the time string from seconds """

    try:
        if mins == 0:
            return '0 min'

        if mins >= 86400:
            time_str = secs_to_dhms_str(mins*60)
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
def secs_to_hrs_mins_secs_str(secs):
    """ Create # hrs, # mins, # secs string """
    if secs < 1:
        return '0 min'

    return f"{secs/86400:.2f} days"

#---------------------------------------------------------
def secs_to_hhmmss(secs):
    """ secs --> hh:mm:ss """

    try:
        if instr(secs, ':'):
            return secs

        if secs < 1:
            return HHMMSS_ZERO

        w_secs = float(secs)

        hh = f"{int(w_secs // 3600):02}" if (w_secs >= 3600) else '00'
        w_secs = w_secs % 3600
        mm = f"{int(w_secs // 60):02}" if (w_secs >= 60) else '00'
        w_secs = w_secs % 60
        ss = f"{int(w_secs):02}"

    except:
        return '00:00:00'

    return f"{hh}:{mm}:{ss}"

#---------------------------------------------------------
def secs_to_hhmm(secs):
    """ secs --> hh:mm """

    try:
        if instr(secs, ':'):
            return secs

        w_secs = float(secs) + 30

        hh = f"{int(w_secs // 3600):02}" if (w_secs >= 3600) else '00'
        w_secs = w_secs % 3600
        mm = f"{int(w_secs // 60):02}" if (w_secs >= 60) else '00'

        return f"{hh}:{mm}"

    except:
        return '00:00'

#--------------------------------------------------------------------
def secs_to_time_hhmm(secs):
    """ secs --> hh:mm or hh:mma or hh:mmp"""
    try:
        if Gb.time_format_24_hour:
            return secs_to_24hr_time(secs + 30)[:-3]

        hhmmss = secs_to_time(secs + 30)
        return hhmmss[:-4] + hhmmss[-1:]

    except:
        return '00:00'

#--------------------------------------------------------------------
def secs_to_dhms_str(secs):
    """ Create the time 0w0d0h0m0s time string from seconds """

    return f"{secs/86400:.2f} days"

#--------------------------------------------------------------------
def waze_mins_to_time_str(waze_time_from_zone):
    '''
    Return:
        Waze used:
            The waze time string (hrs/mins) if Waze is used
        Waze not used:
            'N/A'
    '''

    #Display time to the nearest minute if more than 3 min away
    if Gb.waze_status != WAZE_USED:
        return  'N/A'

    mins = waze_time_from_zone * 60

    mins, secs = divmod(mins, 60)
    mins = mins + 1 if secs > 30 else mins
    secs = mins * 60

    return secs_to_time_str(secs)

#--------------------------------------------------------------------
def secs_since(secs):
    if secs < 1:
        return 0

    return round(time.time() - secs)

def mins_since(secs):
    return round(secs_since(secs)/60)
#--------------------------------------------------------------------
def secs_to(secs):
    if secs < 1:
        return 0

    return round(secs - time.time())

def mins_to(secs):
    return round(secs_since(secs)/60)
#--------------------------------------------------------------------
def hhmmss_to_secs(hhmmss):
    return time_to_secs(hhmmss)

def time_to_secs(hhmmss):
    """ Convert hh:mm:ss into seconds """
    try:
        hh_mm_ss = hhmmss.split(":")
        secs = int(hh_mm_ss[0]) * 3600 + int(hh_mm_ss[1]) * 60 + int(hh_mm_ss[2])

    except:
        secs = 0

    return secs

#--------------------------------------------------------------------
def secs_to_time(secs):
    """ Convert seconds to hh:mm:ss """
    if secs is None or secs < 1 or secs == HIGH_INTEGER:
        return HHMMSS_ZERO if Gb.time_format_24_hour else '12:00:00a'

    return time_to_12hrtime(secs_to_24hr_time(secs))

#--------------------------------------------------------------------
def secs_to_24hr_time(secs):
    """ Convert seconds to hh:mm:ss """
    if secs is None or secs < 1 or secs == HIGH_INTEGER:
        return HHMMSS_ZERO if Gb.time_format_24_hour else '12:00:00a'

    secs        = secs + Gb.timestamp_local_offset_secs
    time_format = '%H:%M:%S'
    t_struct    = time.localtime(secs)
    hhmmss      = f"{time.strftime(time_format, t_struct)}"

    return hhmmss

#--------------------------------------------------------------------
def time_to_12hrtime(hhmmss, ampm=True):
    '''
    Change hh:mm:ss time to a 12 hour time
    Input : hh:mm:ss where hh=(0-23)
            : hh:mm:ss (30s)
    Return: hh:mm:ss where hh=(0-11) with 'a' or 'p'
    '''

    try:
        if hhmmss == HHMMSS_ZERO:
            return HHMMSS_ZERO if Gb.time_format_24_hour else '12:00:00a'

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
def time_remove_am_pm(hhmmssap):
    return hhmmssap.replace('a', '').replace('p', '')

#--------------------------------------------------------------------
def time_str_to_secs(time_str='30 min') -> int:
    """
    Calculate the seconds in the time string.
    The time attribute is in the form of '15 sec' ',
    '2 min', '60 min', etc
    """

    if time_str == "":
        return 0

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
def timestamp_to_time_utcsecs(utc_timestamp) -> int:
    """
    Convert iCloud timeStamp into the local time zone and
    return hh:mm:ss
    """
    ts_local = int(float(utc_timestamp)/1000) + Gb.time_zone_offset_seconds
    hhmmss   = dt_util.utc_from_timestamp(ts_local).strftime(Gb.um_time_strfmt)
    if hhmmss[0] == "0":
        hhmmss = hhmmss[1:]

    return hhmmss

#--------------------------------------------------------------------
def datetime_to_time(datetime):
    """
    Extract the time from the device timeStamp attribute
    updated by the IOS app.
    Format #1 is --'datetime': '2019-02-02 12:12:38.358-0500'
    Format #2 is --'datetime': '2019-02-02 12:12:38 (30s)'
    """

    try:
        #'0000-00-00 00:00:00' --> '00:00:00'
        if datetime == DATETIME_ZERO:
            return HHMMSS_ZERO

        #'2019-02-02 12:12:38.358-0500' --> '12:12:38'
        elif datetime.find('.') >= 0:
            return datetime[11:19]

        #'2019-02-02 12:12:38 (30s)' --> '12:12:38 (30s)'
        elif datetime.find('-') >= 0:
            return datetime[11:]

        else:
            return datetime

    except:
        pass

    return datetime

#--------------------------------------------------------------------
def datetime_to_12hrtime(datetime):
    """
    Convert 2120-07-19 14:28:34 to 2:28:34
    """
    return(time_to_12hrtime(datetime_to_time(datetime)))
#--------------------------------------------------------------------
def secs_to_datetime(secs):
    """
    Convert seconds to timestamp
    Return timestamp (2020-05-19 09:12:30)
    """

    try:
        time_struct = time.localtime(secs)
        timestamp   = time.strftime("%Y-%m-%d %H:%M:%S", time_struct)

    except Exception as err:
        timestamp = DATETIME_ZERO

    return timestamp

#--------------------------------------------------------------------
def datetime_to_secs(datetime, utc_local=False) -> int:
    """
    Convert the timestamp from the device timestamp attribute
    updated by the IOS app.
    Format is --'timestamp': '2019-02-02T12:12:38.358-0500'
    Return epoch seconds
    """
    try:
        if datetime is None or datetime == '' or datetime[0:19] == DATETIME_ZERO:
            return 0

        datetime = datetime.replace("T", " ")[0:19]
        secs_utc = secs = time.mktime(time.strptime(datetime, "%Y-%m-%d %H:%M:%S"))
        if secs > 0 and utc_local is True:
            secs += Gb.time_zone_offset_seconds
        # elif secs == 0:
        #     _trace(f"{datetime} {secs} {utc_local} {secs_to_time(secs_utc)}->{secs_to_time(secs)}")

    except:
        secs = 0

    return secs

#--------------------------------------------------------------------
def timestamp4(secs):
    ts_str = str(secs).replace('.0', '')
    return str(ts_str)[-4:]

#--------------------------------------------------------------------
def secs_to_time_age_str(time_secs):
    """ Secs to '17:36:05 (2 sec ago)' """
    if time_secs < 1 or time_secs == HIGH_INTEGER:
        return '0 mins'
        # rc9  Changed 00:00:00 to 0 mins
        #return '00:00:00'

    age_secs = secs_since(time_secs)
    if age_secs >= 86400:
        return f"{age_secs/86400:.1f} days ago"

    return (f"{secs_to_time(time_secs)} "
            f"({secs_to_time_str(age_secs)} ago)")

#--------------------------------------------------------------------
def secs_to_age_str(time_secs):
    """ Secs to `2 sec ago`, `3 mins ago`/, 1.5 hrs ago` """
    if time_secs < 1 or time_secs == HIGH_INTEGER:
        return 'Unknown'

    return f"{secs_to_time_str(secs_since(time_secs))} ago"

#--------------------------------------------------------------------
def secs_since_to_time_str(time_secs):
    return secs_to_age_str(time_secs).replace(' ago', '')

#--------------------------------------------------------------------
def format_date_time_now(strftime_parameters):
    return dt_util.now().strftime(strftime_parameters)

#--------------------------------------------------------------------
def format_time_age(time_secs):
    if time_secs < 1 or time_secs == HIGH_INTEGER:
        return 'Never'

    time_age_str = (f"{secs_to_time(time_secs)} "
                    f"({secs_to_time_str(secs_since(time_secs))} ago)")

    return time_age_str

#--------------------------------------------------------------------
def format_age(secs):
    """ Secs to `52.3y ago` """
    if secs < 1:
        return 'Never'

    return f"{secs_to_time_str(secs)} ago"

#--------------------------------------------------------------------
def format_age_hrs(secs):
    return f"{secs_to_hrs_str(secs_since(secs))} ago"

#--------------------------------------------------------------------
def format_age_ts(time_secs):
    if time_secs < 1:
        return 'Never'

    return (f"{secs_to_time_str(secs_since(time_secs))} ago")

#########################################################
#
#   TIME UTILITY ROUTINES
#
#########################################################
def calculate_time_zone_offset():
    """
    Calculate time zone offset seconds
    """
    try:
        local_zone_offset = dt_util.now().strftime('%z')
        local_zone_name   = dt_util.now().strftime('%Z')
        local_zone_offset_secs = int(local_zone_offset[1:3])*3600 + int(local_zone_offset[3:])*60
        if local_zone_offset[:1] == "-":
            local_zone_offset_secs = -1*local_zone_offset_secs

        t_now    = int(time.time())
        t_hhmmss = dt_util.now().strftime('%H%M%S')
        l_now    = time.localtime(t_now)
        l_hhmmss = time.strftime('%H%M%S', l_now)
        g_now    = time.gmtime(t_now)
        g_hhmmss = time.strftime('%H%M%S', g_now)

        if (l_hhmmss == g_hhmmss):
            Gb.timestamp_local_offset_secs = local_zone_offset_secs

        post_event( f"Local Time Zone Offset > "
                    f"UTC{local_zone_offset[:3]}:{local_zone_offset[-2:]} hrs, "
                    f"{local_zone_name}, "
                    f"Country Code-{Gb.country_code.upper()}")

    except Exception as err:
        internal_error_msg(err, 'CalcTimeOffset')
        local_zone_offset_secs = 0

    Gb.time_zone_offset_seconds = local_zone_offset_secs

    return local_zone_offset_secs

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
        h:mm:ss, hh:mm:ss, h:mm:ssa, h:mm:ssp, etc
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

    if hh_adjustment == 0 or hhmmss == HHMMSS_ZERO:
        return hhmmss

    hhmm_colon = hhmmss.find(':')
    if hhmm_colon == -1: return hhmmss

    ap = hhmmss_ap = hhmmss[-1]                # Get last character of time (#, a, p)
    ap = f"{ap.lower()}m" if ap in ['a', 'p', 'A', 'P'] else '' # Reformat (pm or '')
    hh = hhmmss[:hhmm_colon] + ap              # Create Hometime zonehours field (3pm, 15)

    if hh.endswith('m'):
        dt12 = datetime.strptime(hh, '%I%p')   # Get 12-hour datetime (1900-01-01 03:00:00pm)
        h24  = dt12.strftime('%H')             # Convert to 24 hour time (03pm -> 15)
        dt24 = datetime.strptime(h24, '%H')    # Get datetime value of 24-hour time (1900-01-01 15:00:00)
        dt24 += timedelta(hours=hh_adjustment) # Add time zone offset (15-2=13)
        ap = dt24.strftime("%p")[0].lower()    # Get a/p for new time (PM -> p)
        hh_away_zone = dt24.strftime("%-I")    # Get Away time zone 12-hour value (1)

    else:
        dt24 = datetime.strptime(hh, '%H')     # Get datetime value of 24-hour time (15)
        dt24 += timedelta(hours=hh_adjustment) # Add time zone offset (15-2=13)
        hh_away_zone = dt24.strftime("%H")    # Get Away time zone 12-hour value (15)

    hhmmss = f"{hh_away_zone}{hhmmss[hhmm_colon:]}"
    if ap: hhmmss = hhmmss.replace(hhmmss_ap, ap)

    return hhmmss
