
'''
set reject_attr = [ 'integration', 'icon', 'sensor_updated', 'friendly_name' ] %}
{% for k,v in states.sensor.icloud3_alerts.attributes.items() -%}
{{ k }}: {{ v }}
{% endfor %}


{% set reject_attr = [ 'integration', 'icon', 'sensor_updated', 'friendly_name' ] %}
{% for k,v in states.sensor.icloud3_alerts.attributes.items() -%}
{% if k not in reject_attr %}
{{ k }}: {{ v }}
{% endif %}
{% endfor %}
'''


from ..global_variables import GlobalVariables as Gb
from ..const            import (VERSION, VERSION_BETA, ICLOUD3, ICLOUD3_VERSION, DOMAIN, ICLOUD3_VERSION_MSG,
                                ICLOUD3_ERROR_MSG, EVLOG_DEBUG, EVLOG_ERROR, EVLOG_INIT_HDR, EVLOG_MONITOR,
                                EVLOG_TIME_RECD, EVLOG_UPDATE_HDR, EVLOG_UPDATE_START, EVLOG_UPDATE_END,
                                EVLOG_ALERT, EVLOG_WARNING, EVLOG_HIGHLIGHT, EVLOG_IC3_STARTING,EVLOG_IC3_STAGE_HDR,
                                ALERT_CRITICAL, ALERT_OTHER,
                                IC3LOG_FILENAME, EVLOG_TIME_RECD, EVLOG_TRACE,
                                CRLF, CRLF_DOT, CRLF_HDOT,
                                NL, NL3, NL4, NLSP4, NL3U, NL3D, NL3_DATA, NL4_DATA,
                                NBSP, NBSP2, NBSP3, NBSP4, NBSP5, NBSP6,
                                DOT, HDOT, CRLF_INDENT, LINK,
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
from .utils                 import (obscure_field, instr, is_empty, isnot_empty, list_add, list_del, )

import homeassistant.util.dt   as dt_util
from homeassistant.components  import persistent_notification

import os
import time
import inspect
import traceback
import logging

DO_NOT_SHRINK     = ['url', 'accountName', ]
FILTER_DATA_DICTS = ['items', 'userInfo', 'dsid', 'dsInfo', 'webservices', 'locations','location',
                    'params', 'headers', 'kwargs', 'clientContext', 'identifiers', 'labels',
                    'securityCode', 'trustedPhoneNumber', ]
FILTER_DATA_LISTS = ['devices', 'content', 'followers', 'following', 'contactDetails', 'protocols', 'trustTokens',
                    'keyNames', 'trustedPhoneNumbers', ]
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
        'horizontalAccuracy', 'verticalAccuracy', 'positionType',
        'hsaVersion', 'hsaEnabled', 'hsaTrustedBrowser', 'hsaChallengeRequired',
        'locale', 'appleIdEntries', 'statusCode',
        'familyEligible', 'findme', 'requestInfo',
        'XXX-termsUpdateNeeded', 'iCloudTerms', 'version',
        'invitationSentToEmail', 'invitationAcceptedByEmail', 'invitationFromHandles',
        'invitationFromEmail', 'invitationAcceptedHandles',
        'items', 'userInfo', 'prsId', 'dsid', 'dsInfo', 'webservices', 'locations', 'dslang',
        'devices', 'content', 'followers', 'following', 'contactDetails', 'countryCode',
        'dsWebAuthToken', 'accountCountryCode', 'extended_login', 'trustToken', 'trustTokens',
        'data', 'json', 'headers', 'params', 'url', 'retry_cnt', 'retried', 'retry', '#',
        'code', 'ok', 'method', 'fmly', 'shouldLocate', 'selectedDevice', 'membersInfo',
        'X-Apple-OAuth-State', 'X-Apple-ID-Session-Id', 'Accept', 'Authorization',
        'identifiers', 'labels', 'model', 'name_by_user', 'area_id', 'manufacturer', 'sw_version',
        'keyNames', 'securityCode', 'trustedPhoneNumbers', 'trustedPhoneNumber',
        'authenticationType',
        'username', 'password', 'accountName', 'salt', 'protocols', 'protocol', 'iteration',
        'a', 'A', 'b', 'B', 'c', 'm1', 'M1', 'm2', 'M2', 'g', 'K', 'N', 'u', 'v',
        ]
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

log_field = ''

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

    event_msg = filter_special_chars(event_msg)
    if devicename: devicename += ' > '
    if event_msg[0:2] in [EVLOG_ALERT, EVLOG_ERROR, EVLOG_WARNING]:
        alert_type = event_msg[0:2]
        event_msg = (f"{devicename}{str(event_msg)}")
        if alert_type == EVLOG_ALERT:
            log_warning_msg(event_msg)
        elif alert_type == EVLOG_ERROR:
            log_error_msg(event_msg)
        elif alert_type == EVLOG_WARNING:
            log_warning_msg(event_msg)

    elif instr(event_msg, EVLOG_IC3_STAGE_HDR):
        pass

    elif event_msg.startswith('^') is False:
        event_msg = (f"{devicename}{str(event_msg)}")
        log_info_msg(event_msg)

    elif event_msg.startswith(EVLOG_TIME_RECD) is False:
        event_msg = (f"{devicename}{str(event_msg)}")
        log_debug_msg(event_msg)

#--------------------------------------------------------------------
def post_alert(devicename_or_Device, event_msg="+"):
    '''
    Display Alert message (red on yellow background) in the Event Log
    '''
    devicename, event_msg = _resolve_devicename_log_msg(devicename_or_Device, event_msg)
    evlog_alert = '' if instr(event_msg, EVLOG_ALERT) else EVLOG_ALERT

    return post_event(devicename, f"{evlog_alert}{event_msg}")

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
def post_greenbar_msg(Device_or_greenbar_msg, greenbar_msg='+'):
    '''
    Post an Alert Message on the first line of the event log items

    Input:
        Device:
            If specified, display msg on this Device's EvLog screen only
            If not specified, display on all screens
        greenbar_msg:
            Message to display -
    '''
    # See if the message is really in the Device parameter
    if greenbar_msg == '+':
        greenbar_msg = Device_or_greenbar_msg
        Device = None
        devicename_msg = ''
    else:
        Device = Device_or_greenbar_msg
        devicename_msg = f"{Device.fname}, "

    if greenbar_msg == '':
        return Gb.EvLog.clear_greenbar_msg()

    # Device was specified, check to see if this is the screen displayed
    if Device:
        fname = Device.fname if Device.is_tracked else f"{Device.fname} 🅜"
        if Gb.EvLog.evlog_attrs["fname"] != fname:
            return

    # if greenbar_msg.startswith('Internet Error') is False:
    #     log_debug_msg(f"GreenbarMsg > {devicename_msg}{greenbar_msg}")

    if Gb.EvLog.greenbar_alert_msg == greenbar_msg:
        return

    else:
        Gb.EvLog.greenbar_alert_msg = greenbar_msg
        Gb.EvLog.display_user_message(Gb.EvLog.user_message)

#-------------------------------------------------------------------------------------------
def clear_greenbar_msg():
    Gb.EvLog.clear_greenbar_msg()
    Gb.EvLog.display_user_message(Gb.EvLog.user_message)

#-------------------------------------------------------------------------------------------
def update_alert_sensor(type_or_key=None, alert_msg=None, update_sensor=False, replace_alert_msg=False):
    '''
    Update the Gb.alerts_sensor_attrs dictionary
    Critical alerts (ALERT_CRITICAL) will replace any previous critical alerts instead of appending it

    Type: Attribute to add or update
    '''

    if type_or_key is None and alert_msg is None:
        Gb.AlertsSensor.async_update_sensor()
        return

    if type_or_key is None:
        type_or_key = ALERT_OTHER

    update_sensor = False

    # Clear this message
    if alert_msg == '':
        Gb.alerts_sensor_attrs.pop(type, None)
        update_sensor = True

    # Not critical alert - Only keep first alert for acct or device
    elif (type_or_key != ALERT_CRITICAL
            and type_or_key in Gb.alerts_sensor_attrs
            and replace_alert_msg is False):
        return

    # Add the alert
    else:
        Gb.alerts_sensor_attrs[type_or_key] = alert_msg

        if Gb.start_icloud3_inprocess_flag is False or update_sensor:
            update_sensor = True

    # Rebuild list so importing alerts are at the top
    if len(Gb.alerts_sensor_attrs) > 1:
        new_alerts_sensor_attrs = {}
        # Critical alerts
        new_alerts_sensor_attrs.update(
            {_source: _msg  for _source, _msg in Gb.alerts_sensor_attrs.items()
                            if _source == ALERT_CRITICAL})

        # Apple Acct alerts (-source will be the filter value, change it back to the real value)
        new_alerts_sensor_attrs.update(
            {_source: _msg
                            for _source, _msg in Gb.alerts_sensor_attrs.items()
                            if instr(_source, '@')})

        # Device alerts
        new_alerts_sensor_attrs.update(
            {_source: _msg  for _source, _msg in Gb.alerts_sensor_attrs.items()
                            if _source in Gb.Devices_by_devicename})

        # Other alerts
        new_alerts_sensor_attrs.update(
            {_source: _msg  for _source, _msg in Gb.alerts_sensor_attrs.items()
                            if _source not in new_alerts_sensor_attrs})
        Gb.alerts_sensor_attrs = new_alerts_sensor_attrs

    if update_sensor:
        Gb.AlertsSensor.async_update_sensor()

    log_debug_msg(  f"Alerts Sensor > Sensor-{Gb.alerts_sensor}, "
                    f"Attrs-{Gb.alerts_sensor_attrs}")

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
async def async_open_ic3log_file_init():
    '''
    Entry point for async_add_executor_job in __init__.py

    Open log file in append mode (new_log_file=False.
    Close and reopen the log file after the Configuration file has been read in __init__/config_file
    '''
    new_log_file = True
    await Gb.hass.async_add_executor_job(open_ic3log_file, new_log_file)

#------------------------------------------------------------------------------
def open_ic3log_file(new_log_file=False):

    # Items will be logged to home-assistane.log until the configuration file has been read
    # if is_empty(Gb.conf_general):
    #     return

    try:
        ic3logger_file = Gb.hass.config.path(IC3LOG_FILENAME)
        filemode = 'w' if new_log_file else 'a'

        if Gb.iC3Logger is None or new_log_file:
            Gb.iC3Logger = logging.getLogger(DOMAIN)
            Gb.iC3Logger.setLevel(logging.INFO)

            handler   = logging.FileHandler(ic3logger_file, mode=filemode, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            handler.addFilter(LoggerFilter)

            Gb.iC3Logger.addHandler(handler)

        if isnot_empty(Gb.conf_general):
            Gb.iC3Logger.propagate = (Gb.conf_general[CONF_LOG_LEVEL] == 'debug-ha')

        if is_empty(Gb.conf_general):
            write_ic3log_recd(f"Loading {ICLOUD3_VERSION_MSG}")

        write_ic3log_recd(f"Open iCloud3 Log File ({IC3LOG_FILENAME})")

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def close_ic3log_file():

    if Gb.iC3Logger:
        write_ic3log_recd(f"Close iCloud3 Log File  ({IC3LOG_FILENAME})")
        Gb.iC3Logger.removeHandler(Gb.iC3Logger.handlers[0])
        # Gb.iC3Logger.flush()

#--------------------------------------------------------------------
def write_ic3log_recd(log_msg):
    '''
    Check to make sure the icloud3.log file exists if the last write to it
    was more than 2-secs ago. Recreate it if it does not. This catches deletes
    and renames while iCloud3 is running
    '''
    try:
        if Gb.iC3Logger is None:
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

    CAN NOT USE FILE_IO ROUTINES BECAUSE OF IMPORT ERRORS
    '''
    try:
        log_file_0 = Gb.hass.config.path(IC3LOG_FILENAME)
        log_file_1 = f"{Gb.hass.config.path(IC3LOG_FILENAME)}-1.log"
        log_file_2 = f"{Gb.hass.config.path(IC3LOG_FILENAME)}-2.log"

        post_event(f"{ICLOUD3} Log File Archived")

        if os.path.isfile(log_file_2): os.remove(log_file_2)
        if os.path.isfile(log_file_1): os.rename(log_file_1, log_file_2)

        if os.path.isfile(log_file_0):
            Gb.iC3Logger.removeHandler(Gb.iC3Logger.handlers[0])
            os.rename(log_file_0, log_file_1)

        open_ic3log_file(new_log_file=True)

        # Delete log files with old name
        try:
            os.remove(f"{Gb.hass.config.path(IC3LOG_FILENAME)}.1")
            os.remove(f"{Gb.hass.config.path(IC3LOG_FILENAME)}.2")
        except Exception as err:
            pass

    except Exception as err:
        post_event(f"{ICLOUD3} Log File Archive encountered an error > {err}")

#------------------------------------------------------------------------------
def write_config_file_to_ic3log():

    if Gb.prestartup_log:
        write_ic3log_recd(f"{Gb.prestartup_log}")
        Gb.prestartup_log = ''

    _conf_tracking = Gb.conf_tracking.copy()
    _conf_tracking.pop('devices', None)
    _conf_tracking.pop('apple_accounts', None)

    Gb.trace_prefix = '_INIT_'
    indent = SP(37) if Gb.log_debug_flag else SP(18)
    log_msg = ( f"{ICLOUD3_VERSION_MSG}, "
                f"{dt_util.now().strftime('%A')}, "
                f"{dt_util.now().strftime(DATETIME_FORMAT)[:19]}")
    log_msg = ( f"{NL4}⛔{DASH_50}{DASH_50}"
                f"{NL4}⛔    {log_msg}"
                f"{NL4}⛔{DASH_50}{DASH_50}")

    # Gb.iC3Logger.info(log_msg)

    # Write the ic3 configuration (general & devices) to the Log file
    log_msg  += (f""
                f"{NLSP4}PROFILE:"
                f"{NLSP4}{Gb.conf_profile}"
                f"{NLSP4}TRACKING:"
                f"{NLSP4}{_conf_tracking}"
                f"{NLSP4}GENERAL CONFIGURAION:"
                f"{NLSP4}{Gb.conf_general}"
                f"{NLSP4}{Gb.ha_location_info}")

    for conf_apple_accounts in Gb.conf_apple_accounts:
        log_msg += (f"{NLSP4}APPLE ACCOUNT: {conf_apple_accounts.get(CONF_USERNAME)}:"
                    f"{NLSP4}{conf_apple_accounts}")

    for conf_device in Gb.conf_devices:
        log_msg += (f"{NLSP4}DEVICE: {conf_device[CONF_IC3_DEVICENAME]}, {conf_device[CONF_FNAME]}:"
                    f"{NLSP4}{conf_device}")
    log_msg += f"{NLSP4}{DASH_50}{DASH_50}"
    log_info_msg(log_msg)

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
    # log_msg = filter_special_chars(log_msg)
    Gb.HALogger.warning(log_msg)

    log_msg = format_msg_line(log_msg)
    write_ic3log_recd(log_msg)

#--------------------------------------------------------------------
def log_error_msg(module_name, log_msg='+'):

    log_msg = _resolve_module_name_log_msg(module_name, log_msg)
    # log_msg = filter_special_chars(log_msg)
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

    if Gb.log_debug_flag is False or Gb.iC3Logger is None:
        return
    if devicename_or_Device and log_msg == '':
        return

    devicename, log_msg = _resolve_devicename_log_msg(devicename_or_Device, log_msg)

    if devicename: devicename = f"{devicename} > "
    log_msg = f"{devicename}{str(log_msg)}"
    log_msg = format_msg_line(log_msg)

    write_ic3log_recd(log_msg)

#--------------------------------------------------------------------
def log_start_finish_update_banner(start_finish, devicename,
            method, update_reason):
    '''
    Display a banner in the log file at the start and finish of a
    device update cycle
    '''
    # The devicename may be the 'appleacct~devicename'
    text  = (f"{devicename}, {method}, {update_reason} ")
    log_msg = format_header_box(text, start_finish=start_finish)

    log_info_msg(log_msg)

#--------------------------------------------------------------------
def log_banner(start_finish, msg):

    sf_char =   '🔻' if start_finish == 'start' else \
                '🔺' if start_finish == 'finish' else \
                '🔶'
    log_info_msg(f"{NL3}{sf_char}{'═'*40}{sf_char}  {msg.upper()}  {sf_char}{'═'*40}{sf_char}")

#--------------------------------------------------------------------
def log_stack(hdr_msg=None, return_function=False, return_cnt=0):
    '''
    (frame=<frame at 0x7f16894c1c60, file '/usr/src/homeassistant/homeassistant/config_entries.py',
    line 2595, code <genexpr>>, filename='/usr/src/homeassistant/homeassistant/config_entries.py',
    lineno=2595, function='<genexpr>', code_context=['                create_eager_task(\n'],
    index=0, positions=Positions(lineno=2595, end_lineno=2602, col_offset=16, end_col_offset=17))
    '''
    cnt = -1
    stack_frames = inspect.stack()
    hdr_msg = hdr_msg if hdr_msg else ''
    log_msg = ''

    for frame_recd in stack_frames[1:]:
        cnt += 1
        if cnt > 30:
            break

        filename = frame_recd.filename

        if filename.startswith('/usr/local/lib/python'):
            break

        # Return function name if this is 1 above the fct that called log_stack
        if return_function and cnt == 1:
            return frame_recd.function

        filename = filename.replace('/usr/src/homeassistant/homeassistant', 'ha')
        filename = filename.replace('/config/custom_components/icloud3', 'ic3')

        log_msg += (f"{NL4}{SP(5)}{DOT}{filename}, {frame_recd.lineno}, {frame_recd.function}, ")

        if return_cnt == 0:
            if cnt > 0:
                code = frame_recd.code_context[0].replace('\n', '').strip()
                log_msg += f"{NL4}{SP(9)}{[code]}"
        elif return_cnt == cnt:
            return log_msg

    log_msg = f"{NL4}🟩 LOG STACK: {hdr_msg}{log_msg}"
    log_info_msg(log_msg)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   LOG MESSAGE SUPPORT ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def format_msg_line(log_msg):
    try:
        if type(log_msg) is str is False:
            return log_msg

        msg_prefix= ' ' if log_msg.startswith('⡇') else \
                    ''  if log_msg.startswith(NL) else \
                    NL3U if instr(log_msg, 'REQUEST') else \
                    NL3D if instr(log_msg, 'RESPONSE') else \
                    NL3D if instr(log_msg, 'HDR') else \
                    NL3_DATA if instr(log_msg, 'DATA') else \
                    ' ⡇ ' if Gb.trace_group else \
                    ' '

        program_area = ''

        if instr(msg_prefix, '\n'):
            source = f"{_called_from_history()}"
        else:
            source  = f"{_called_from()}{program_area}"

        log_msg = format_startup_header_box(log_msg)
        log_msg = f"{source}{msg_prefix}{log_msg}"

    except:
        pass

    return log_msg

#--------------------------------------------------------------------
def filter_special_chars(log_msg, evlog_export=False):
    '''
    Filter out EVLOG_XXX control fields
    '''
    indent =SP(9) if evlog_export else \
            SP(37) if Gb.log_debug_flag else \
            SP(17)
    if log_msg.startswith('^'): log_msg = log_msg[3:]

    log_msg = log_msg.replace(EVLOG_MONITOR, '')
    log_msg = log_msg.replace(NBSP, ' ')
    log_msg = log_msg.replace(NBSP2, ' ')
    log_msg = log_msg.replace(NBSP3, ' ')
    log_msg = log_msg.replace(NBSP4, ' ')
    log_msg = log_msg.replace(NBSP5, ' ')
    log_msg = log_msg.replace(NBSP6, ' ')
    log_msg = log_msg.strip()
    log_msg = log_msg.replace(CRLF, f"\n⠂{indent}")
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
    if hdr_code in [EVLOG_IC3_STARTING, EVLOG_IC3_STAGE_HDR]:
        log_msg = log_msg[:p] + log_msg[p+3:]
        log_msg = format_header_box(log_msg)

    return log_msg

#--------------------------------------------------------------------
def format_header_box(log_msg, indent=None, start_finish=None, evlog_export=False):
    '''
    Format a box around this item
    '''
    start_pos = log_msg.find('^')
    if start_pos == -1: start_pos = 0

    indent = indent if indent is not None else 36 if Gb.log_debug_flag else 16

    top_char = bot_char = DASH_50
    if start_finish == 'start':
        bot_char = f"{'⠂'*20}"
        Gb.trace_group = True
    elif start_finish == 'finish':
        top_char = f"{'⠂'*20}"
        Gb.trace_group = False

    return (f"⡇{top_char}"
            f"\n.{SP(indent)}⡇{SP(4)}{log_msg[start_pos:].upper()}"
            f"\n.{SP(indent)}⡇{bot_char}")

#-------------------------------------------------------------------------------------------
def _resolve_devicename_log_msg(devicename_or_Device, event_msg):
    if devicename_or_Device == '*': devicename_or_Device = ''
    if event_msg == '+':
        return ('', devicename_or_Device)
    if devicename_or_Device in Gb.Devices:
        return devicename_or_Device.devicename, event_msg
    if devicename_or_Device in Gb.Devices_by_devicename:
        return devicename_or_Device, event_msg
    return ('', event_msg)

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
def log_data_unfiltered(_hdr, rawdata, data_source=None, filter_id=None):
    try:
        rawdata_copy = rawdata['raw'].copy() if 'raw' in rawdata else rawdata.copy()
        rawdata_copy = _set_validpw_invalidpw_text(rawdata_copy)

    except:
        log_info_msg(f"{_hdr.upper()}{NL3_DATA}{rawdata}")
        return

    devices_data = {}

    if 'content' in rawdata_copy:
        for device_data in rawdata_copy['content']:
            devices_data[device_data['name']] = device_data

        rawdata_copy['content'] = 'DeviceData……'

    # Cycle thru rawdata items and create log line for each dict item
    # Add dict items to rawdata_items list, save others and add at end
    if type(rawdata_copy) is dict:
        rawdata_items = ''
        rawdata_non_dict_items = {}
        for k, v in rawdata_copy.items():
            if type(k) is dict:
                d = {k: v}
                rawdata_items += f"{NL3_DATA}{d}"
            else:
                rawdata_non_dict_items[k] = v
        rawdata_items += f"{NL3_DATA}{rawdata_non_dict_items}"

    else:
        rawdata_items = f"{NL3_DATA}{rawdata_copy}"

    log_info_msg(f"{_hdr.upper()}{rawdata_items}")

    for device_data in devices_data:
        log_msg = ( f"iCloud AppleAcct Data (unfiltered -- "
                    f"{device_data}")
        log_info_msg(log_msg)

#--------------------------------------------------------------------
def log_request_data(request_response_text, method, url, kwargs, AppleAcct=None, response=None):

        log_rawdata_flag = False if response is None else response.status_code != 200

        log_rawdata_flag = log_rawdata_flag or (url.endswith('refreshClient') is False)
        if Gb.log_rawdata_flag or log_rawdata_flag or Gb.initial_icloud3_loading_flag:
            pass
        else:
            return

        try:
            username = AppleAcct.username_base if AppleAcct in Gb.AppleAcct_by_username.values() else AppleAcct
            _hdr = (f"{username}, {method}, {request_response_text}-{url.split('/')[-2:]}")

            if request_response_text.startswith('Request'):
                _data = {'url': url[8:], 'retry': kwargs.get("retry_cnt", 0)}
                _data.update(kwargs)

            elif request_response_text.startswith('Response'):
                if response is None:
                    _data = kwargs
                else:
                    try:
                        data = response.json()
                    except:
                        data = {}
                    _data = {'code': response.status_code, 'ok': response.ok, 'data': data}
                    if Gb.log_rawdata_flag_unfiltered:
                        _data['headers'] = response.headers


            log_data(_hdr, _data, log_rawdata_flag=log_rawdata_flag)

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
def log_data(_hdr, rawdata, log_rawdata_flag=False, data_source=None, filter_id=None):
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

    elif instr(_hdr,'iCloud Data'):
        log_level_devices = [devicename for devicename in Gb.log_level_devices if instr(_hdr, devicename)]
        if log_level_devices == []:
            return

    rawdata_data   = {}
    log_msg        = ''

    try:
        if type(rawdata) is not dict:
            log_info_msg(f"{_hdr.upper()}{NL3_DATA}{rawdata}")
            return

        rawdata_data = rawdata.pop('data', None)
        log_msg += _create_log_msg_from_data(rawdata)
        log_msg += _create_log_msg_from_data(rawdata_data, data=True)

        if log_msg:
            log_info_msg(f"{_hdr.upper()} {_called_from(show_fct_name=True)}{log_msg}")

        return

    except Exception as err:
        log_exception(err)
        log_info_msg(f"{_hdr.upper()} *** Data could not be filtered ***{NL3_DATA}{rawdata}")
        return

#..........................................................................................
def _create_log_msg_from_data(rawdata, data=None):
    '''
    Extract lists and dictionaries from the rawdata dictionary

    Returns a new rawdata dictionary:
        log_items_data[listitem]               - lists by the list item name
        log_items_data[listitem.sublist]       - sublists of the list
        log_items_data[dictitem]               - dictionaries by the dict item name
        log_items_data[dictietm.subdictitem]   - dicts within that dict
        log_items_data[items]                  - non-list & non_dict items
    '''
    if is_empty(rawdata):
        return ''

    log_items_data = {}
    try:
        filtered_rawdata = {k: v for k, v in rawdata.items() if k in FILTER_FIELDS}
    except Exception as err:
        log_exception(err)

    for k, v in filtered_rawdata.copy().items():
        if type(v) is list:
            if is_empty(v): continue

            # The list contains a dict item Format it as a sub dict
            if type(v[0]) is dict:
                idx = -1
                for vsd in v:
                    idx += 1
                    if k == 'content':
                        ksd = v[idx].get('name', idx)
                        log_items_data[f"{k}.{ksd}"] = _filter_rawdata_items(vsd)
                    else:
                        log_items_data[f"{k}.{idx}"] = _filter_rawdata_items(vsd, shrink_only=True)

            else:
                log_items_data[f"{k}"] = _filter_rawdata_items(v)
            filtered_rawdata.pop(k)

        elif type(v) is dict:
            if is_empty(v): continue

            # The dict contains another dict item Format it as a sub dict
            try:
                # ksd_0 = v.keys()[0]
                for ksd, vsd in v.items():
                    if ksd not in FILTER_FIELDS: continue
                    if type(vsd) is dict:
                        vsd_data = v.pop(ksd)
                        shrink_only = ksd in ['membersInfo']
                        log_items_data[f"{k}.{ksd}"] = _filter_rawdata_items(vsd_data, shrink_only)
            except:
                pass

            log_items_data[f"{k}"] = _filter_rawdata_items(v)

            filtered_rawdata.pop(k)

    filtered_rawdata = {k: shrink_item(v, k) for k, v in filtered_rawdata.items()}
    log_items_data['items'] = filtered_rawdata

    log_msg = ''
    data_text = 'data.' if data else '_.'
    for k, v in log_items_data.items():
        if isnot_empty(v):
            log_msg += f"{NL3_DATA}{data_text}{k}={v}"

    return log_msg

#..........................................................................................
def _filter_rawdata_items(item_value_dict, shrink_only=None):
    '''
    Cycle thru the items dict, filter and shrink the value items
    '''
    if (Gb.log_rawdata_flag_unfiltered
            or type(item_value_dict) is not dict):
        return item_value_dict

    _filtered_rawdata_items = {}
    for k, v in item_value_dict.items():
        if k not in FILTER_FIELDS and shrink_only is None:
            continue

        _filtered_rawdata_items[k] = shrink_item(v, k)

    return _filtered_rawdata_items

#..........................................................................................
def shrink_item(v, k=None):
    '''
    Reduce the size of str fields longer than 20-chars
    '''
    if k in DO_NOT_SHRINK:
        return v

    if (type(v) is str
            and len(v) > 20
            and v.startswith('http') is False):
        v = f"{v[:6]}……{v[-6:]}"

    return v

#--------------------------------------------------------------------
def _set_validpw_invalidpw_text(rawdata):

    rawdata_items = rawdata['data'] if 'data' in rawdata else rawdata

    try:
        if 'code' in rawdata_items:
            if rawdata_items['code'] == 409:
                rawdata_items['ok'] = 'ValidPW'
            elif rawdata_items['code'] == 401:
                rawdata_items['ok'] = 'InvalidPW'

    except:
        pass

    return rawdata

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ERROR MESSAGE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def internal_error_msg(err_text, msg_text=''):

    stack    = inspect.stack()
    caller   = inspect.getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename).split('.')[0][:12]
    try:
        parent = inspect.getframeinfo(stack()[2][0])
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
    err_lines = tb_err_msg.split('{NL4}')
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
def _evlog(items=None):
    '''
    Display a message or variable in the Event Log
    '''
    if items is None:
        return

    if (type(items) is str) is False:
        items = f"{items}"

    items       = items.replace('<', '&lt;')
    called_from = _called_from(trace=True)
    function    = log_stack(return_function=True)

    if Gb.EvLog:
        Gb.EvLog.post_event(f"{EVLOG_TRACE}{called_from} {items}")

    _log(items)

#--------------------------------------------------------------------
def _log(items, v1='+++', v2='', v3='', v4='', v5=''):
    '''
    Display a message or variable in the HA log file
    '''
    log_msg = ''
    try:
        called_from_hist = _called_from_history(trace=True)

        if v1 != '+++':
            log_msg = (f"|{v1}|-|{v2}|-|{v3}|-|{v4}|-|{v5}|")

        log_msg = (f"| _LOG | {called_from_hist}{NL}| 🟡 {items} {log_msg}  |")
        write_ic3log_recd(log_msg)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def _called_from(show_fct_name=False, trace=False):

    if Gb.log_debug_flag is False and trace == False:
        return ''

    caller = None

    level = 0
    while level < 10:
        level += 1
        caller = inspect.getframeinfo(inspect.stack()[level][0])

        if (caller.filename.endswith('_io.py')
                or instr(caller.filename, 'requests')
                or caller.filename.endswith('sessions.py')
                or instr(caller.filename, 'httpx')):
            continue
        if caller.filename.endswith('messaging.py') is False:
            break

    if caller is None:
        return ' '

    py_filename = _extract_py_filename(caller)

    if show_fct_name is True:
        return f"[{py_filename}: {caller.lineno}/{caller.function}]"

    py_filename = f"{py_filename}……………………"
    caller_lineno = caller.lineno

    return f"[{py_filename[:12]}:{caller_lineno:04}] "

#--------------------------------------------------------------------
def _called_from_history(trace=False):

    if Gb.log_debug_flag is False and trace == False:
        return ''

    level = 0
    py_filenames_list = ''
    last_py_filename  = ''
    hist_level_cnt    = 0
    actual_caller     = ''  # Caller after io, session, messaging & requests
    while level < 99:
        level += 1
        try:
            caller = inspect.getframeinfo(inspect.stack()[level][0])
            py_filename = _extract_py_filename(caller)

            if py_filename.startswith('thread'):
                break
            if (py_filename == 'messaging'
                    or py_filename == 'sessions'):
                continue

            if (actual_caller != ''
                    or caller.filename.endswith('_io.py')
                    or instr(caller.filename, 'requests')
                    or instr(caller.filename, 'httpx')):
                pass
            else:
                actual_caller = f"{py_filename}:{caller.lineno}/{caller.function[:10]}"

            if py_filename == last_py_filename:
                py_filenames_list += f",{caller.lineno}"

            else:
                last_py_filename = py_filename
                if py_filename.endswith('io'):
                    py_filename = 'io'
                elif instr(py_filename, 'request'):
                    py_filename = 'req'
                else:
                    hist_level_cnt += 1
                    if len(py_filename) > 16:
                        py_filename = f"{py_filename[:10]}…{py_filename.split('_')[-1][:6]}"

                py_filenames_list += f"; {py_filename}:{caller.lineno}"

                if hist_level_cnt == 3:
                    break
            if py_filename == '__init__':
                break
        except:
            break

    return f"[{actual_caller}] [{py_filenames_list[2:]}] "

#--------------------------------------------------------------------
def _extract_py_filename(caller):
    py_filename = caller.filename.replace('.py','').split('/')[-1]

    return py_filename



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   LOG FILE PASSWORD FILTER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def add_log_file_filter(item, replacement_text=None):
    '''
    Set up  log file filter to replace the items value with *'s or prevent it
    from displaying in the log file. If item contains an '@' and it is being hidden,
    it is an email address and it's url will be hidden.

    parameters:
        hide_text:  True = Do not display it instead of replacing with *'s

    Note
    '''
    if item is None:
        return
    elif Gb.disable_upw_filter:
        return item

    # username/email address - reformat useremailname@gmail.com --> use**#**me@ or use**1**@ (set in config_file)
    if instr(item, '@'):
        email_parts = item.split('@')
        Gb.upw_filter_items[email_parts[1]] = ''

        email_id = email_parts[0]
        if replacement_text is None:
            replacement_text = f"{email_id[:3]}****{email_id[-2:]}@"
        else:
            replacement_text = f"{email_id[:3]}{replacement_text}{email_id[-2:]}@"

        Gb.upw_filter_items[f"{email_id}@"] = Gb.upw_filter_items[email_id] = replacement_text
        Gb.upw_unfilter_items[replacement_text] = f"{email_id}@"
        item = item.upper()
        Gb.upw_filter_items[f"{email_id}@"] = Gb.upw_filter_items[email_id] = replacement_text

    elif replacement_text is not None:
        Gb.upw_filter_items[item] = replacement_text

    else:
        Gb.upw_filter_items[item] = '*'*8

#--------------------------------------------------------------------
class LoggerFilter(logging.Filter):
    '''
    Filter items from being displayed in the log file (Password)
    '''
    @staticmethod
    def filter(record):
        if Gb.disable_upw_filter:
            return True

        message = record.msg
        for filtered_item, replacement_text in Gb.upw_filter_items.items():
            if instr(message, filtered_item):
                message = message.replace(filtered_item, replacement_text)

        record.msg  = message
        record.args = []
        return True
