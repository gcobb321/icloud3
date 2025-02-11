

from ..global_variables import GlobalVariables as Gb
from ..const            import (VERSION, VERSION_BETA, ICLOUD3, ICLOUD3_VERSION, DOMAIN, ICLOUD3_VERSION_MSG,
                                DOT, ICLOUD3_ERROR_MSG, EVLOG_DEBUG, EVLOG_ERROR, EVLOG_INIT_HDR, EVLOG_MONITOR,
                                EVLOG_TIME_RECD, EVLOG_UPDATE_HDR, EVLOG_UPDATE_START, EVLOG_UPDATE_END,
                                EVLOG_ALERT, EVLOG_WARNING, EVLOG_HIGHLIGHT, EVLOG_IC3_STARTING,EVLOG_IC3_STAGE_HDR,
                                IC3LOG_FILENAME, EVLOG_TIME_RECD, EVLOG_TRACE,
                                CRLF, CRLF_DOT, NBSP, NBSP2, NBSP3, NBSP4, NBSP5, NBSP6, CRLF_INDENT, LINK,
                                DASH_50, DASH_DOTTED_50, TAB_11, RED_ALERT, RED_STOP, RED_CIRCLE, YELLOW_ALERT,
                                DATETIME_FORMAT, DATETIME_ZERO,
                                NEXT_UPDATE_TIME, INTERVAL,
                                ICLOUD, MOBAPP,
                                CONF_APPLE_ACCOUNT,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_LOG_LEVEL, CONF_PASSWORD, CONF_USERNAME,
                                CONF_DEVICES, CONF_APPLE_ACCOUNTS,
                                LATITUDE,  LONGITUDE, LOCATION_SOURCE, TRACKING_METHOD,
                                ZONE, ZONE_DATETIME, INTO_ZONE_DATETIME, LAST_ZONE,
                                TIMESTAMP, TIMESTAMP_SECS, TIMESTAMP_TIME, LOCATION_TIME, DATETIME, AGE,
                                TRIGGER, BATTERY, BATTERY_LEVEL, BATTERY_STATUS,
                                INTERVAL, ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, MOVED_DISTANCE,
                                DEVICE_STATUS, LOW_POWER_MODE, ICLOUD_LOST_MODE_CAPABLE,
                                AUTHENTICATED,
                                LAST_UPDATE_TIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_TIME, LAST_LOCATED_DATETIME, LAST_LOCATED_TIME,
                                INFO, GPS_ACCURACY, GPS, POLL_COUNT, VERT_ACCURACY, ALTITUDE,
                                BADGE,
                                )
from ..const_more_info      import more_info_text
from .common                import (obscure_field, instr, is_empty, isnot_empty, list_add, list_del, )

import homeassistant.util.dt   as dt_util
from homeassistant.components  import persistent_notification

import os
import time
from inspect                import getframeinfo, stack
import traceback
import logging

DO_NOT_SHRINK     = ['url', 'accountName', ]
FILTER_DATA_DICTS = ['items', 'userInfo', 'dsid', 'dsInfo', 'webservices', 'locations','location',
                    'params', 'headers', 'kwargs', 'clientContext', 'identifiers', 'labels', ]
FILTER_DATA_LISTS = ['devices', 'content', 'followers', 'following', 'contactDetails', 'protocols', 'trustTokens', ]
FILTER_FIELDS = [
        ICLOUD3_VERSION, AUTHENTICATED,
        LATITUDE,  LONGITUDE, LOCATION_SOURCE, TRACKING_METHOD,
        ZONE, ZONE_DATETIME, INTO_ZONE_DATETIME, LAST_ZONE,
        TIMESTAMP, TIMESTAMP_SECS, TIMESTAMP_TIME, LOCATION_TIME, DATETIME, AGE,
        TRIGGER, BATTERY, BATTERY_LEVEL, BATTERY_STATUS,
        INTERVAL, ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
        TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, MOVED_DISTANCE,
        DEVICE_STATUS, LOW_POWER_MODE, BADGE,
        LAST_UPDATE_TIME, LAST_UPDATE_DATETIME,
        NEXT_UPDATE_TIME, NEXT_UPDATE_TIME,
        LAST_LOCATED_TIME, LAST_LOCATED_DATETIME,
        INFO, GPS_ACCURACY, GPS, POLL_COUNT, VERT_ACCURACY, ALTITUDE, ICLOUD_LOST_MODE_CAPABLE,
        'ResponseCode', 'reason',
        'id', 'firstName', 'lastName', 'name', 'fullName', CONF_IC3_DEVICENAME,
        'appleId', 'emails', 'phones', 'locked',
        'deviceStatus', 'batteryStatus', 'batteryLevel', 'membersInfo',
        'deviceModel', 'rawDeviceModel', 'deviceDisplayName', 'modelDisplayName', 'deviceClass',
        'isOld', 'isInaccurate', 'timeStamp', 'altitude', 'location', 'latitude', 'longitude',
        'horizontalAccuracy', 'verticalAccuracy',
        'hsaVersion', 'hsaEnabled', 'hsaTrustedBrowser', 'hsaChallengeRequired',
        'locale', 'appleIdEntries', 'statusCode',
        'familyEligible', 'findme', 'requestInfo',
        'invitationSentToEmail', 'invitationAcceptedByEmail', 'invitationFromHandles',
        'invitationFromEmail', 'invitationAcceptedHandles',
        'items', 'userInfo', 'prsId', 'dsid', 'dsInfo', 'webservices', 'locations', 'dslang',
        'devices', 'content', 'followers', 'following', 'contactDetails', 'countryCode',
        'dsWebAuthToken', 'accountCountryCode', 'extended_login', 'trustToken', 'trustTokens',
        'data', 'json', 'headers', 'params', 'url', 'retry_cnt', 'retried', 'retry', '#',
        'code', 'ok', 'method', 'securityCode', 'fmly', 'shouldLocate', 'selectedDevice',
        'accountName', 'salt', 'a', 'b', 'c', 'm1', 'm2', 'protocols', 'iteration', 'Authorization',
        'X-Apple-OAuth-State', 'X-Apple-ID-Session-Id', 'Accept',
         'identifiers', 'labels', 'model', 'name_by_user', 'area_id', 'manufacturer', 'sw_version', ]
FILTER_OUT = [
    'features', 'BTR', 'LLC', 'CLK', 'TEU', 'SND', 'ALS', 'CLT', 'PRM', 'SVP', 'SPN', 'XRM', 'NWF', 'CWP',
    'MSG', 'LOC', 'LME', 'LMG', 'LYU', 'LKL', 'LST', 'LKM', 'WMG', 'SCA', 'PSS', 'EAL', 'LAE', 'PIN',
    'LCK', 'REM', 'MCS', 'REP', 'KEY', 'KPD', 'WIP', 'scd',
    'rm2State', 'pendingRemoveUntilTS', 'repairReadyExpireTS', 'repairReady', 'lostModeCapable', 'wipedTimestamp',
    'encodedDeviceId', 'scdPh', 'locationCapable', 'trackingInfo', 'nwd', 'remoteWipe', 'canWipeAfterLock', 'baUUID',
    'snd', 'continueButtonTitle', 'alertText', 'cancelButtonTitle', 'createTimestamp',  'alertTitle', ]


SP_str = ' '*50
SP_dict = {
    4: SP_str[1:4],
    5: SP_str[1:5],
    6: SP_str[1:6],
    8: SP_str[1:8],
    9: SP_str[1:9],
    10: SP_str[1:10],
    11: SP_str[1:11],
    12: SP_str[1:12],
    13: SP_str[1:13],
    14: SP_str[1:14],
    16: SP_str[1:16],
    22: SP_str[1:22],
    28: SP_str[1:28],
    26: SP_str[1:26],
    44: SP_str[1:44],
    48: SP_str[1:48],
    50: SP_str,
}
def SP(space_cnt):
    if space_cnt in SP_dict:     return SP_dict[space_cnt]
    if space_cnt < len(SP_str): return SP_str[1:space_cnt]
    return ' '*space_cnt

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   MISCELLANEOUS MESSAGING ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def broadcast_info_msg(info_msg):
    '''
    Display a message in the info sensor for all devices
    '''
    if INFO not in Gb.conf_sensors['device']:
        return

    Gb.broadcast_info_msg = f"{info_msg}"

    try:
        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]
            InfoSensor = Gb.Sensors_by_devicename[devicename][INFO]
            InfoSensor.write_ha_sensor_state()

    # Catch error if the Info sensor has not been set up yet during startup
    # or if the info sensor has not been selected in config_vlow > sensors
    except KeyError:
        pass


    return

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   EVENT LOG POST ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def post_event(devicename_or_Device, event_msg='+'):
    '''
    Add records to the Event Log table. This does not change
    the info displayed on the Event Log screen. Use the
    '_update_event_log_display' function to display the changes.
    '''

    devicename, event_msg = _resolve_devicename_log_msg(devicename_or_Device, event_msg)

    try:
        if event_msg.endswith(', '):
            event_msg = event_msg[:-2]
        event_msg = event_msg.replace(', , ', ', ')
    except:
        # Gb.HALogger.info(event_msg)
        pass

    Gb.EvLog.post_event(devicename, event_msg)

    if len(event_msg) <= 3:
        return

    elif event_msg[0:2] in [EVLOG_ALERT, EVLOG_ERROR, EVLOG_WARNING]:
        alert_type = event_msg[0:2]
        event_msg = (f"{devicename} > {str(event_msg)}")
        if alert_type == EVLOG_ALERT:
            log_warning_msg(event_msg)
        elif alert_type == EVLOG_ERROR:
            log_error_msg(event_msg)
        elif alert_type == EVLOG_WARNING:
            log_warning_msg(event_msg)

    elif instr(event_msg, EVLOG_IC3_STAGE_HDR):
        pass

    elif event_msg.startswith('^') is False:
        event_msg = (f"{devicename} > {str(event_msg)}")
        log_info_msg(event_msg)

    elif event_msg.startswith(EVLOG_TIME_RECD) is False:
        event_msg = (f"{devicename} > {str(event_msg)}")
        log_debug_msg(event_msg)

#--------------------------------------------------------------------
def post_error_msg(devicename_or_Device, event_msg="+"):
    '''
    Always display log_msg in Event Log; always add to HA log
    '''
    devicename, event_msg = _resolve_devicename_log_msg(devicename_or_Device, event_msg)
    if event_msg.find("iCloud3 Error") >= 0:
        for Device in Gb.Devices_by_devicename.values():
            Device.display_info_msg(ICLOUD3_ERROR_MSG)

    post_event(devicename, event_msg)

    if devicename == '*':
        devicename = 'iCloud3 Error >' if event_msg.find("iCloud3 Error") < 0 else ''
    log_msg = (f"{devicename} {event_msg}")
    log_msg = str(log_msg).replace(CRLF, ". ")

    log_error_msg(log_msg)

#--------------------------------------------------------------------
def post_monitor_msg(devicename_or_Device, event_msg='+'):
    '''
    Post the event message and display it in Event Log and HA log
    when the config parameter "log_level: eventlog" is specified or
    the Show Tracking Monitors was selected in Event Log > Actions
    '''
    devicename, event_msg = _resolve_devicename_log_msg(devicename_or_Device, event_msg)
    post_event(devicename, f"{EVLOG_MONITOR}{event_msg}")

#-------------------------------------------------------------------------------------------
def refresh_event_log(devicename='', show_one_screen=False):
    Gb.EvLog.update_event_log_display(devicename='', show_one_screen=False)

#-------------------------------------------------------------------------------------------
def post_evlog_greenbar_msg(Device, evlog_greenbar_msg='+'):
    '''
    Post an Alert Message on the first line of the event log items

    Input:
        Device:
            If specified, display msg on this Device's EvLog screen only
            If not specified, display on all screens
        evlog_greenbar_msg:
            Message to display -
    '''
    if evlog_greenbar_msg == '':
        return Gb.EvLog.clear_evlog_greenbar_msg()

    # See if the message is really in the Device parameter
    if evlog_greenbar_msg == '+':
        evlog_greenbar_msg = Device

    # Device was specified, check to see if this is the screen displayed
    else:
        fname = Device.fname if Device.is_tracked else f"{Device.fname} 🅜"
        if Gb.EvLog.evlog_attrs["fname"] != fname:
            return

    if Gb.EvLog.greenbar_alert_msg == evlog_greenbar_msg:
        return

    else:
        Gb.EvLog.greenbar_alert_msg = evlog_greenbar_msg
        Gb.EvLog.display_user_message(Gb.EvLog.user_message)

#-------------------------------------------------------------------------------------------
def clear_evlog_greenbar_msg():
    Gb.EvLog.clear_evlog_greenbar_msg()
    Gb.EvLog.display_user_message(Gb.EvLog.user_message)

#--------------------------------------------------------------------
def post_startup_alert(alert_msg):

    if alert_msg not in Gb.startup_alerts:
        Gb.startup_alerts.append(alert_msg)

#-------------------------------------------------------------------------------------------
def ha_notification(msg_line1, msg_line2=None) -> None:

    if msg_line2:
        msg_line1 += f"<br />{msg_line2}"

    persistent_notification.create(
        Gb.hass,
        f"Notification: {msg_line1}",
        title=f"iCloud3 Notification",
        notification_id="icloud3",
    )

#--------------------------------------------------------------------
def format_filename(path):
    if path.startswith('/config') or len(path) < 50:
        return path
    else:
        return (f"{Gb.ha_config_directory}……{CRLF_INDENT}"
                f"{path.replace(Gb.ha_config_directory, '')}")
#--------------------------------------------------------------------
def more_info(key):

    if key in Gb.startup_stage_status_controls:
        return f"{more_info_text['instructions_already_displayed']}"

    elif key in more_info_text:
        Gb.startup_stage_status_controls.append(key)
        return more_info_text[key]

    else:
        return f"{more_info_text['invalid_msg_key']} `{key}`"

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3-DEBUG.LOG FILE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def open_ic3log_file_init():
    '''
    Entry point for async_add_executor_job in __init__.py
    '''
    open_ic3log_file(new_log_file=Gb.log_debug_flag)

#------------------------------------------------------------------------------
def open_ic3log_file(new_log_file=False):

    # Items will be logged to home-assistane.log until the configuration file has been read
    if is_empty(Gb.conf_general):
        return

    ic3logger_file = Gb.hass.config.path(IC3LOG_FILENAME)
    filemode = 'w' if new_log_file else 'a'

    if Gb.iC3Logger is None or new_log_file:
        Gb.iC3Logger  = logging.getLogger(DOMAIN)
        Gb.iC3Logger.setLevel(logging.INFO)

        handler   = logging.FileHandler(ic3logger_file, mode=filemode, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        handler.addFilter(LoggerFilter)

        Gb.iC3Logger.addHandler(handler)

    if isnot_empty(Gb.conf_general):
        Gb.iC3Logger.propagate = (Gb.conf_general[CONF_LOG_LEVEL] == 'debug-ha')

#--------------------------------------------------------------------
def close_ic3_log_file():
    Gb.iC3Logger.removeHandler(Gb.iC3Logger.handlers[0])
    # Gb.iC3Logger.flush()

#--------------------------------------------------------------------
def write_ic3log_recd(log_msg):
    '''
    Check to make sure the icloud3-0.log file exists if the last write to it
    was moe than 2-secs ago. Recreate it if it does not. This catches deletes
    and renames while iCloud3 is running
    '''
    try:
        if is_empty(Gb.conf_general):
            Gb.prestartup_log += f"\n{dt_util.now().strftime(DATETIME_FORMAT)[5:19]} {log_msg}"
            return

        time_now_msecs = time.time()
        if time_now_msecs - Gb.iC3Logger_last_check_exist_secs > 2:
            Gb.iC3Logger_last_check_exist_secs = time_now_msecs

            check_ic3log_file_exists(Gb.hass.config.path(IC3LOG_FILENAME))

        if Gb.iC3Logger:
            Gb.iC3Logger.info(log_msg)
        else:
            open_ic3log_file(new_log_file=True)

            Gb.iC3Logger.info(log_msg)

    except Exception as err:
        return False

#--------------------------------------------------------------------
def check_ic3log_file_exists(ic3logger_file):
    '''
    See if the icloud3-0.log file exists. Recreate it if it does not. This
    catches deletes and renames while iCloud3 is running
    '''
    try:
        if Gb.iC3Logger is None:
            open_ic3log_file(new_log_file=True)

        elif Gb.iC3Logger and os.path.isfile(ic3logger_file) is False:
            Gb.iC3Logger.removeHandler(Gb.iC3Logger.handlers[0])
            open_ic3log_file(new_log_file=True)

            log_msg = f"{EVLOG_IC3_STARTING}Recreated iCloud3 Log File: {ic3logger_file}"
            log_msg = f"{format_startup_header_box(log_msg, 20)}"
            log_msg = log_msg.replace('⡇', '⛔')
            Gb.iC3Logger.info(log_msg)

        return True

    except IndexError:
        pass
    except Exception as err:
        log_exception_HA(err)

    return False

#--------------------------------------------------------------------
def archive_ic3log_file():
    '''
    At midnight, archive the log files and create a new one for the current day
    Remove icloud-2.log,
    rename icloud3-1.log to icloud3_2.log,
    rename icloud3-0.log to icloud3-1.log
    '''
    try:
        log_file_0 = Gb.hass.config.path(IC3LOG_FILENAME)
        log_file_1 = f"{Gb.hass.config.path(IC3LOG_FILENAME)}.1"    #.replace('.', '-1.')
        log_file_2 = f"{Gb.hass.config.path(IC3LOG_FILENAME)}.2"    #.replace('.', '-2.')

        post_event(f"{ICLOUD3} Log File Archived")

        if os.path.isfile(log_file_2): os.remove(log_file_2)
        if os.path.isfile(log_file_1): os.rename(log_file_1, log_file_2)

        if os.path.isfile(log_file_0):
            Gb.iC3Logger.removeHandler(Gb.iC3Logger.handlers[0])
            os.rename(log_file_0, log_file_1)

        open_ic3log_file(new_log_file=True)

    except Exception as err:
        post_event(f"{ICLOUD3} Log File Archive encountered an error > {err}")

#------------------------------------------------------------------------------
def write_config_file_to_ic3log():

    if Gb.prestartup_log:
        write_ic3log_recd(f"{Gb.prestartup_log}")
        Gb.prestartup_log = ''

    conf_tracking_recd = Gb.conf_tracking.copy()
    # conf_tracking_recd[CONF_PASSWORD] = obscure_field(conf_tracking_recd[CONF_PASSWORD])
    # conf_tracking_recd[CONF_APPLE_ACCOUNTS] = len(Gb.conf_apple_accounts)
    # conf_tracking_recd[CONF_DEVICES] = len(Gb.conf_devices)

    Gb.trace_prefix = '_INIT_'
    indent = SP(44) if Gb.log_debug_flag else SP(26)
    log_msg = ( f"{ICLOUD3_VERSION_MSG}, "
                f"{dt_util.now().strftime('%A')}, "
                f"{dt_util.now().strftime(DATETIME_FORMAT)[:19]}")
    log_msg = ( f" \n"
                f"{indent}⛔{DASH_50}\n"
                f"{indent}⛔    {log_msg}\n"
                f"{indent}⛔{DASH_50}")

    Gb.iC3Logger.info(log_msg)

    # Write the ic3 configuration (general & devices) to the Log file
    log_info_msg(f"PROFILE:\n"
                f"{indent} {Gb.conf_profile}")
    log_info_msg("")
    log_info_msg(f"GENERAL CONFIGURAION:\n"
                f"{indent} {Gb.conf_general}\n"
                f"{indent} {Gb.ha_location_info}")
    log_info_msg("")
    log_info_msg(f"TRACKING:\n"
                f"{indent} {conf_tracking_recd}")

    log_info_msg("")
    for conf_apple_accounts in Gb.conf_apple_accounts:
        log_info_msg(   f"APPLE ACCOUNTS: {conf_apple_accounts.get(CONF_USERNAME)}:\n"
                        f"{indent} {conf_apple_accounts}")

    log_info_msg("")
    for conf_device in Gb.conf_devices:
        log_info_msg(   f"DEVICE: {conf_device[CONF_FNAME]}, {conf_device[CONF_IC3_DEVICENAME]}:\n"
                        f"{indent} {conf_device}")
    log_info_msg("")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   LOG MESSAGE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def log_info_msg_HA(msg):
    Gb.HALogger.info(msg)

def log_warning_msg_HA(msg):
    Gb.HALogger.warning(msg)

def log_error_msg_HA(msg):
    Gb.HALogger.error(msg)

def log_exception_HA(err):
    Gb.HALogger.exception(err)

#--------------------------------------------------------------------
def log_info_msg(module_name, log_msg='+'):

    if module_name and log_msg == '': return
    log_msg = _resolve_module_name_log_msg(module_name, log_msg)

    log_msg = format_msg_line(log_msg)
    write_ic3log_recd(log_msg)

    log_msg = log_msg.replace(' > +', f" > ……\n{SP(22)}+")
    Gb.HALogger.debug(log_msg)

#--------------------------------------------------------------------
def log_warning_msg(module_name, log_msg='+'):

    log_msg = _resolve_module_name_log_msg(module_name, log_msg)
    log_msg = filter_special_chars(log_msg)
    Gb.HALogger.warning(log_msg)

    log_msg = format_msg_line(log_msg)
    write_ic3log_recd(log_msg)

#--------------------------------------------------------------------
def log_error_msg(module_name, log_msg='+'):

    log_msg = _resolve_module_name_log_msg(module_name, log_msg)
    log_msg = filter_special_chars(log_msg)
    Gb.HALogger.error(log_msg)

    log_msg = format_msg_line(log_msg)
    write_ic3log_recd(log_msg)

#--------------------------------------------------------------------
def log_exception(err):

    try:
        write_ic3log_recd(f"{ICLOUD3_VERSION_MSG}\n{traceback.format_exc()}")
    except:
        write_ic3log_recd(err)

    Gb.HALogger.exception(err)

#--------------------------------------------------------------------
def log_debug_msg(devicename_or_Device, log_msg='+', msg_prefix=None):

    if Gb.log_debug_flag is False: return
    if devicename_or_Device and log_msg == '': return

    devicename, log_msg = _resolve_devicename_log_msg(devicename_or_Device, log_msg)

    dn_str = '' if devicename == '*' else f"{devicename} > "
    log_msg = f"{dn_str}{str(log_msg).replace(CRLF, ', ')}"
    log_msg = format_msg_line(log_msg)

    write_ic3log_recd(log_msg)

    log_msg = log_msg.replace(' > +', f" > ……\n{SP(22)}+")
    Gb.HALogger.debug(log_msg)

#--------------------------------------------------------------------
def log_start_finish_update_banner(start_finish, devicename,
            method, update_reason):
    '''
    Display a banner in the log file at the start and finish of a
    device update cycle
    '''
    # The devicename may be the 'appleacct~devicename'
    # if instr(devicename, '~'): devicename = devicename.split('~')[1]
    # Device = Gb.Devices_by_devicename[devicename]
    text  = (f"{devicename}, {method}, {update_reason} ")
    log_msg = format_header_box(text, indent=43, start_finish=start_finish)

    log_info_msg(log_msg)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   LOG MESSAGE SUPPORT ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def format_msg_line(log_msg, area=None):
    try:
        if type(log_msg) is str is False:
            return log_msg

        msg_prefix= ' ' if log_msg.startswith('⡇') else \
                    '\n🔺 ' if instr(log_msg, 'REQUEST') else \
                    '\n🔻 ' if instr(log_msg, 'RESPONSE') else \
                    '\n❗' if instr(log_msg, 'ICLOUD DATA') else \
                    ' ⡇ ' if Gb.trace_group else \
                    '  '
        program_area =  f"{RED_STOP}    "  if instr(log_msg, EVLOG_ALERT) else \
                        f"{RED_ALERT}    " if instr(log_msg, EVLOG_ERROR) else \
                        area               if area else \
                        Gb.trace_prefix

        source  = f"{_called_from()}{program_area}"
        log_msg = format_startup_header_box(log_msg)
        log_msg = filter_special_chars(log_msg)
        log_msg = f"{source}{msg_prefix}{log_msg}"

    except:
        pass

    return log_msg

#--------------------------------------------------------------------
def filter_special_chars(log_msg, evlog_export=False):
    '''
    Filter out EVLOG_XXX control fields
    '''

    indent =SP(16) if evlog_export else \
            SP(48) if Gb.log_debug_flag else \
            SP(28)
    if log_msg.startswith('^'): log_msg = log_msg[3:]

    log_msg = log_msg.replace(EVLOG_MONITOR, '')
    log_msg = log_msg.replace(NBSP, ' ')
    log_msg = log_msg.replace(NBSP2, ' ')
    log_msg = log_msg.replace(NBSP3, ' ')
    log_msg = log_msg.replace(NBSP4, ' ')
    log_msg = log_msg.replace(NBSP5, ' ')
    log_msg = log_msg.replace(NBSP6, ' ')
    log_msg = log_msg.strip()
    log_msg = log_msg.replace(CRLF, f"\n{indent}")
    log_msg = log_msg.replace('◦', f"   ◦")
    log_msg = log_msg.replace('* >', '')
    log_msg = log_msg.replace('&lt;', '<')

    if log_msg.find('^') == -1: return log_msg.strip()

    log_msg = log_msg.replace(EVLOG_TIME_RECD , '')
    log_msg = log_msg.replace(EVLOG_UPDATE_HDR, '')
    log_msg = log_msg.replace(EVLOG_UPDATE_START, '')
    log_msg = log_msg.replace(EVLOG_UPDATE_END  , '')
    log_msg = log_msg.replace(EVLOG_ERROR, '')
    log_msg = log_msg.replace(EVLOG_ALERT, '')
    log_msg = log_msg.replace(EVLOG_WARNING, '')
    log_msg = log_msg.replace(EVLOG_INIT_HDR, '')
    log_msg = log_msg.replace(EVLOG_HIGHLIGHT, '')
    log_msg = log_msg.replace(EVLOG_IC3_STARTING, '')
    log_msg = log_msg.replace(EVLOG_IC3_STAGE_HDR, '')

    log_msg = log_msg.replace('^1^', '').replace('^2^', '').replace('^3^', '')
    log_msg = log_msg.replace('^4^', '').replace('^5^', '')


    return log_msg.strip()


#--------------------------------------------------------------------
def format_startup_header_box(log_msg):
    '''
    Put a box around this item if it is an Event Log header item
    '''
    p = log_msg.find('^')
    if p == -1:
        return log_msg

    hdr_code = log_msg[p:p+3]
    log_msg = log_msg[:p] + log_msg[p+3:]
    if hdr_code in [EVLOG_IC3_STARTING, EVLOG_IC3_STAGE_HDR]:
        log_msg = format_header_box(log_msg)

    return log_msg

#--------------------------------------------------------------------
def format_header_box(log_msg, indent=None, start_finish=None, evlog_export=False):
    '''
    Format a box around this item
    '''
    start_pos = log_msg.find('^')
    if start_pos == -1: start_pos = 0

    # Default indent for icloud3-0.log file is 43
    if indent is None: indent = 43

    top_char = bot_char = DASH_50
    if start_finish == 'start':
        bot_char = f"{'⠂'*37}"
        Gb.trace_group = True
    elif start_finish == 'finish':
        top_char = f"{'⠂'*37}"
        Gb.trace_group = False

    return (f"⡇{top_char}\n"
            f"{SP(indent)}⡇{SP(4)}{log_msg[start_pos:].upper()}\n"
            f"{SP(indent)}⡇{bot_char}")

#-------------------------------------------------------------------------------------------
def _resolve_devicename_log_msg(devicename_or_Device, event_msg):
    if event_msg == '+':
        return ("*", devicename_or_Device)
    if devicename_or_Device in Gb.Devices:
        return devicename_or_Device.devicename, event_msg
    if devicename_or_Device in Gb.Devices_by_devicename:
        return devicename_or_Device, event_msg
    return ('*', event_msg)

#--------------------------------------------------------------------
def _resolve_module_name_log_msg(module_name, log_msg):
    if log_msg == "+":
        try:
            return (module_name.replace(NBSP, ''))
        except:
            pass

    return (f"{module_name} {log_msg.replace(NBSP, '')}")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   RAWDATA LOGGING ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def log_rawdata_unfiltered(title, rawdata, data_source=None, filter_id=None):
    try:
        rawdata_copy = rawdata['raw'].copy() if 'raw' in rawdata else rawdata.copy()

    except:
        log_info_msg(f"__ {title.upper()}\n{rawdata}")
        return

    devices_data = {}

    if 'content' in rawdata_copy:
        for device_data in rawdata_copy['content']:
            devices_data[device_data['name']] = device_data

        rawdata_copy['content'] = 'DeviceData……'

    log_info_msg(f"__ {title.upper()}\n{rawdata_copy}")

    for device_data in devices_data:
        log_msg = ( f"iCloud PyiCloud Data (unfiltered -- "
                    f"{device_data}")
        log_info_msg(log_msg)

#--------------------------------------------------------------------
def log_rawdata(title, rawdata, log_rawdata_flag=False, data_source=None, filter_id=None):
    '''
    Add raw data records to the HA log file for debugging purposes.

    This is used in Pyicloud_ic3 to log all data requests and responses,
    and in other routines in iCloud3 when device_tracker or other entities
    are read from or updated in HA.

    A filter is applied to the raw data and dictionaries and lists in the
    data to eliminate displaying uninteresting fields. The fields, dictionaries,
    and list are defined in the FILTER_FIELDS, FILTER_DATA_DICTS and
    FILTER_DATA_LISTS.
    '''

    if rawdata is None:
        return False
    elif Gb.log_rawdata_flag is False and log_rawdata_flag is False:
        return False

    if (Gb.start_icloud3_inprocess_flag
            or 'all' in Gb.log_level_devices
            or Gb.log_level_devices == []):
        pass

    elif (Gb.log_level_devices
            and (instr(title, ICLOUD)
                or instr(title, MOBAPP)
                or instr(title, 'iCloud')
                or instr(title, 'Mobile'))):

        if True is True or instr(title,'iCloud Data'):
            log_level_devices = [devicename for devicename in Gb.log_level_devices if instr(title, devicename)]
            if log_level_devices == []:
                return

    rawdata_data   = {}
    log_msg        = ''

    try:
        if type(rawdata) is not dict:
            log_info_msg(f"__ {title.upper()}\n{rawdata}")
            return

        rawdata_items = {k: _shrink_value(k, v)
                                for k, v in rawdata['filter'].items()
                                if type(v) not in [dict, list]}

        rawdata_data['filter'] = {k: _shrink_value(k, v)
                                for k, v in rawdata['filter'].items()
                                if k in FILTER_FIELDS or Gb.log_rawdata_flag_unfiltered}
    except:
        rawdata_items = {k: _shrink_value(k, v)
                                for k, v in rawdata.items()
                                if type(v) not in [dict, list]}

        rawdata_data['filter'] = {k: _shrink_value(k, v)
                                        for k, v in rawdata.items()
                                        if (k in FILTER_FIELDS or Gb.log_rawdata_flag_unfiltered)}

    rawdata_data['filter']['items'] = rawdata_items
    if rawdata_data['filter']:
        for data_dict in FILTER_DATA_DICTS:
            filter_results = filter_data_dict(rawdata_data['filter'], data_dict)
            if filter_results:
                log_msg += f"\n❗   {data_dict}={filter_results}"

        for data_list in FILTER_DATA_LISTS:
            if data_list in rawdata_data['filter']:
                filter_results = _filter_data_list(rawdata_data['filter'][data_list])
                if filter_results:
                    log_msg += f"\n❗   {data_list}={filter_results}"


        if 'data' in rawdata_data['filter']:
            try:
                rawdata_data_items = {k: _shrink_value(k, v)
                                            for k, v in rawdata_data['filter']['data'].items()
                                            if k in FILTER_FIELDS and type(v) not in [dict, list]}
                if rawdata_data_items:
                    log_msg += f"\n❗   data.items={rawdata_data_items}"
            except:
                pass

            for data_dict in FILTER_DATA_DICTS:
                filter_results = filter_data_dict(rawdata_data['filter']['data'], data_dict)
                if filter_results:
                    log_msg += f"\n❗   data.{data_dict}={filter_results}"


    if log_msg:
        log_info_msg(f"{title.upper()}{log_msg}")

    return

#--------------------------------------------------------------------
def filter_data_dict(rawdata_data, data_dict):
    try:
        if data_dict == 'webservices' and 'webservices' in rawdata_data:
            webservices = { 'findme': rawdata_data['webservices']['findme'],
                            'contacts': rawdata_data['webservices']['contacts']}
            return webservices
            # return rawdata_data.get('webservices')

        filter_results = {k: _shrink_value(k, v)
                            for k, v in rawdata_data[data_dict].items()
                            if (k in FILTER_FIELDS or Gb.log_rawdata_flag_unfiltered)}

        return filter_results

    except Exception as err:
        # log_exception(err)
        return ''

#--------------------------------------------------------------------
def _filter_data_list(rawdata_data_list):

    try:
        filtered_list = ''
        for list_item in rawdata_data_list:

            filter_results = {k: _shrink_value(k, v)
                                for k, v in list_item.items()
                                if (k in FILTER_FIELDS or Gb.log_rawdata_flag_unfiltered)}

            if 'location' in filter_results and filter_results['location']:
                if Gb.log_rawdata_flag_unfiltered:
                    filter_results['location'] = {k: v for k, v in filter_results['location'].items()}
                else:
                    filter_results['location'] = {k: v for k, v in filter_results['location'].items()
                                                    if k in FILTER_FIELDS}
                filter_results['location'].pop('address', None)

            if filter_results:
                filtered_list += f"\n❗     {filter_results['name']}={filter_results}"

        return filtered_list

    except:
        return ''

#--------------------------------------------------------------------
def _shrink_value(k, v):
    if (k in DO_NOT_SHRINK
            or Gb.log_rawdata_flag_unfiltered):
        return v

    if type(v) is str:
        if v.startswith('http'):
            return v

        if len(v) > 20:
            return f"{v[:6]}……{v[-6:]}"
        else:
            return v
    else:
        return v

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ERROR MESSAGE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def internal_error_msg(err_text, msg_text=''):

    caller   = getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename).split('.')[0][:12]
    try:
        parent = getframeinfo(stack()[2][0])
        parent_lineno = parent.lineno
    except:
        parent_lineno = ''

    if msg_text:
        msg_text = (f", {msg_text}")

    log_msg =  (f"INTERNAL ERROR-RETRYING ({parent_lineno}>{caller.lineno}{msg_text} -- "
                f"{filename}»{caller.function[:20]} -- {err_text})")
    post_error_msg(log_msg)

    attrs = {}
    attrs[INTERVAL]         = 0
    attrs[NEXT_UPDATE_TIME] = DATETIME_ZERO

    return attrs

#--------------------------------------------------------------------
def internal_error_msg2(err_text, traceback_format_exec_obj):
    post_internal_error(err_text, traceback_format_exec_obj)

def post_internal_error(err_text, traceback_format_exec_obj='+'):

    '''
    Display an internal error message in the Event Log and the in the HA log file.

    Parameters:
    - traceback_format_exc  = traceback.format_exec_obj object with the error information

    Example traceback_format_exec_obj():
        [
        'Traceback (most recent call last):'
        '  File "/config/custom_components/icloud3/support/start_ic3.py", line 1268, in setup_tracked_devices_for_icloud'
        "    a = 1 + 'a'"
        '        ~~^……'
        "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        ''
        ]
    '''
    if traceback_format_exec_obj == '+':
        traceback_format_exec_obj = err_text
        err_text = ''

    tb_err_msg = traceback_format_exec_obj()
    log_error_msg(tb_err_msg)

    # rc9 Reworked message extraction due to Python code change
    err_lines = tb_err_msg.split('\n')
    err_error_msg = err_code = err_file_line_module = ""
    err_lines.reverse()


    for err_line in err_lines:
        err_line = err_line.strip()
        if (err_line == "" or err_line.find('~') >= 0 or err_line.find('^^') >= 0
                or err_line.startswith('^')):
            continue

        elif err_error_msg == "":
            err_error_msg = err_line

        elif err_code == "":
            err_code = err_line

        elif err_line.startswith('File') and err_file_line_module == '':
            err_file_line_module = err_line.replace(Gb.icloud3_directory, '')


    try:
        err_msg =  (f"{CRLF_DOT}File.. > {err_file_line_module})"
                    f"{CRLF_DOT}Code > {err_code}"
                    f"{CRLF_DOT}Error. > {err_error_msg}")

    except Exception as err:
        err_msg = f"{CRLF_DOT}Unknown Error, Review HA Logs"

    post_event(f"{EVLOG_ERROR}INTERNAL ERROR > {err_text}{err_msg}")

    attrs = {}
    attrs[INTERVAL]         = '0 sec'
    attrs[NEXT_UPDATE_TIME] = DATETIME_ZERO

    return attrs

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEBUG TRACE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def dummy_evlog():
    _evlog(None, None)
def dummy_log():
    _log(None, None)

#--------------------------------------------------------------------
def _evlog(devicename_or_Device, items='+'):
    '''
    Display a message or variable in the Event Log
    '''
    devicename, items = _resolve_devicename_log_msg(devicename_or_Device, items)

    if (type(items) is str) is False:
        items = f"{items}"
    items = items.replace('<', '&lt;')
    called_from = _called_from(trace=True)

    #rc9 Reworked post_event and write_config_file to call modules directly
    if Gb.EvLog:
        Gb.EvLog.post_event(devicename, f"{EVLOG_TRACE}{called_from} {items}")
    write_ic3log_recd(f"{called_from}⛔.⛔ . . . {devicename} > {items}")

#--------------------------------------------------------------------
def _log(items, v1='+++', v2='', v3='', v4='', v5=''):
    '''
    Display a message or variable in the HA log file
    '''
    try:
        called_from = _called_from(trace=True)
        if v1 == '+++':
            trace_msg = ''
        else:
            trace_msg = (f"|{v1}|-|{v2}|-|{v3}|-|{v4}|-|{v5}|")

        trace_msg = (f"{called_from}⛔.⛔ . . . {items} {trace_msg}")

        write_ic3log_recd(trace_msg)

    except Exception as err:
        Gb.HARootLogger.info(trace_msg)
        # log_exception(err)

#--------------------------------------------------------------------
def _called_from(trace=False):


    if Gb.log_debug_flag is False and trace == False:
        return ''

    caller = None
    level = 0
    while level < 5:
        level += 1
        caller = getframeinfo(stack()[level][0])

        if caller.filename.endswith('messaging.py') is False:
            break

    if caller is None:
        return ' '

    caller_path = caller.filename.replace('.py','')
    caller_filename = caller_path.split('/')[-1]
    if len(caller_filename) > 12 and instr(caller_filename, '_ic3_'):
        caller_filename = caller_filename.replace('_ic3_', '…')
    caller_filename = f"{caller_filename}………………"
    caller_lineno = caller.lineno

    return f"[{caller_filename[:12]}:{caller_lineno:04}] "

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   LOG FILE PASSWORD FILTER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def add_log_file_filter(item, hide_text=None):
    '''
    Set up  log file filter to replace the items value with *'s or prevent it
    from displaying in the log file. If item contains an '@' and it is being hidden,
    it is an email address and it's url will be hidden.

    parameters:
        hide_text:  True = Do not display it instead of replacing with *'s

    Note
    '''
    if item is not None:
        if hide_text is None:
            list_add(Gb.log_file_filter_items, item)
        else:
            if instr(item, '@'):
                item = item.split('@')[1]
            list_add(Gb.log_file_hide_items, item)

#--------------------------------------------------------------------
class LoggerFilter(logging.Filter):
    '''
    Filter items from being displayed in the log file (Password)
    '''
    @staticmethod
    def filter(record):
        if Gb.disable_log_filter:
            return True

        message = record.msg
        for filtered_item in Gb.log_file_filter_items:
            if instr(message, filtered_item):
                message = message.replace(filtered_item, '*'*8)

        for filtered_item in Gb.log_file_hide_items:
            if instr(message, filtered_item):
                message = message.replace(filtered_item, '')

        record.msg  = message
        record.args = []
        return True
