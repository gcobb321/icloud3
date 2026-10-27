
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
from ..const            import (ICLOUD3, DOMAIN,
                                ICLOUD3_ERROR_MSG, EVLOG_DEBUG, EVLOG_ERROR, EVLOG_ATTENTION, EVLOG_MONITOR,
                                EVLOG_UPDATE_HDR, EVLOG_UPDATE_START, EVLOG_UPDATE_END,
                                EVLOG_ALERT, EVLOG_WARNING, EVLOG_HIGHLIGHT, EVLOG_IC3_STAGE_HDR,
                                ALERT_CRITICAL, ALERT_OTHER,
                                IC3LOG_FILENAME, EVLOG_TRACE,
                                DATETIME_FORMAT, DATETIME_ZERO,
                                NEXT_UPDATE_TIME,
                                ICLOUD, MOBAPP,
                                NEXT_UPDATE_TIME, )
from ..const_config     import (INTERVAL, CONF_APPLE_ACCT, CONF_IC3_DEVICENAME, CONF_FNAME,
                                CONF_LOG_LEVEL, CONF_PASSWORD, CONF_APPLE_ACCT, CONF_DEVICES,
                                CONF_APPLE_ACCOUNTS, INFO, )
from ..const_char       import (GEAR_ICON, YELLOW_WARNING, SNOW_FLAKE, CRLF, CRLF_DOT, CRLF_HDOT,
                                RARROW, NL, NL3, NL4, NLSP4, NL3U, NL3D, NL3_DATA, NL4_DATA, NBSP,
                                NBSP2, NBSP3, NBSP4, NBSP5, NBSP6, DOT, HDOT, CRLF_INDENT, LINK,
                                DASH_50, DASH_DOTTED_50, TAB_11, RED_ALERT, RED_STOP, RED_CIRCLE,
                                GREEN_ALERT, )
from ..const_more_info      import more_info_text
from .utils                 import (obscure_field, instr, is_empty, isnot_empty, apple_user, dict_sort, list_to_str, )
#from .time_util             import (format_day_date_time_now, )
from ..support              import test_controls as TEST

import homeassistant.util.dt   as dt_util
from homeassistant.components  import persistent_notification
from homeassistant.helpers     import issue_registry as ir
from homeassistant.util        import slugify

import os
import re
import threading
from functools import partial
import time
import inspect
import traceback
import logging

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
    return


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
        if event_msg.endswith(', '): event_msg = event_msg[:-2]
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

#--------------------------------------------------------------------
def post_dotted_line():
    post_event(f"{'⠒ '*28}")

#--------------------------------------------------------------------
def post_alert(devicename_or_Device, event_msg="+"):
    '''
    Display Alert message (red on yellow background) in the Event Log
    '''
    devicename, event_msg = _resolve_devicename_log_msg(devicename_or_Device, event_msg)
    evlog_alert = '' if instr(event_msg, EVLOG_ALERT) else EVLOG_ALERT

    post_event(devicename, f"{evlog_alert}{event_msg}")

#--------------------------------------------------------------------
def post_config_error(**kwargs):
    '''
    This will handle various configurationh errors detected during startup (start_ic3.py). The
    parameters below define the nature of the problem and how it should be handled.

    - The post_alert message is displayed on the Event Log
    - The icloud3_alerts sensor is updated
    - If the repair_step is specified, a HA Repairs issue is created. Submit:
        - update_device     - Opens the Update Device screen for the source    devicename
        - update_apple_acct - Opens the Update Apple Account screen for the source    apple_id
        - restart           - Sets Gb.was_icloud3_restart_requested to restart iCloud3
        - alert             - Removes the notice, nothing else is done. A condition that
                                still exists is posted again on the next startup, the
                                ones that were not are removed then.
        - notice            - Removes the notice, nothing else is done. It reports an
                                event (the configuration was changed), it is not posted
                                again and is not removed on the next startup.
    - The Device's Event Log button gets the red alert icon unless it is an alert or notice

    kwargs: source       - devicename, aa apple_id, 'general', 'repair
            name         - Device.fname, Apple Account apple_user, etc.
            error_item   - The item in error (mobapp dname, apple_user, etc.)
            error        - Configuration Error
            message      - Some Devices were not verified. Restart may be needed
            details      - {list_to_str(unverified_devices), CRLF_DOT}
            repair_step  - 'update_device', 'update_apple_acct', 'restart', 'alert', 'notice'
            fix_data     - 'update_apple_acct' only, other items used by the repair flow
            translation_key, translation_placeholders
                         - 'alert' & 'notice' only, the issue's own text in strings.json
                            & en.json. None - icloud3_notice with the title and message

    Return:
        issue_id of the Repairs issue, None if one was not created. It is also saved in
        the kwargs added to Gb.startup_msg, the issues that were not posted again are
        removed when startup is complete (clear_config_error_repair_issues).
    '''
    try:
        Gb.startup_msg.append(kwargs)

        Source       = kwargs.get('Source')                      # Device or AppleAcct
        source       = kwargs.get('source', 'Other')             # geekstergary_ipad
        source_name  = kwargs.get('source_name', '')                 # GeeksterGary
        error        = kwargs.get('error', 'Configuration Error')   # Unknown Apple Account
        error_item   = kwargs.get('error_item', '')                 # geekstergary@
        message      = kwargs.get('message', 'General Warning')     # The Apple Acct was not found Device ...
        details      = kwargs.get('details', '')                    # Gary > AppleAcct: geekstergary@
        repair_step  = kwargs.get('repair_step', '')                # update_device
        translation_key          = kwargs.get('translation_key')
        translation_placeholders = kwargs.get('translation_placeholders')

        # The source id is the Device's devicename or the AppleAcct's apple_id so the
        # alert_key is the same in the alerts sensor and the Repairs issue
        Source, source = alert_source(Source or source)
        alert_key     = alert_key_for(source, error)
        alert_title   = f"{source_name} > {error.title()} ({error_item})"
        repair_msg    = f"{message}{details}"
        alert_msg     = f"{error.upper()} > {source_name}{CRLF}{message}{details}"
        log_msg       = filter_special_chars(alert_msg)
        kwargs['alert_key'] = alert_key

        update_alert_sensor(Source=Source, name=source, error=error,
                            alert_msg=alert_title)

        post_alert(alert_msg)

        if repair_step in ['alert', 'notice', 'restart']:
            log_warning_msg(f"iCloud3: {log_msg}")
        else:
            log_error_msg(f"iCloud3: {log_msg}")

        if (repair_step not in ['alert', 'notice']
                and (Device := Gb.Devices_by_devicename.get(source))):
            Device.set_button_prefix_icon(RED_ALERT)

        if repair_step == '':
            return None

    except Exception as err:
        log_exception(err)

    # A notice is not removed by clear_config_error_repair_issues on the next startup
    if repair_step == 'notice':
        issue_id = f"{CONFIG_NOTICE_ISSUE_ID_PREFIX}_{alert_key}"
    else:
        issue_id = f"{CONFIG_ERROR_ISSUE_ID_PREFIX}_{repair_step}_{alert_key}"

    match repair_step:
        case 'update_device':
            issue_id = post_repair_issue_update_device(
                                issue_id   = issue_id,
                                alert_key  = alert_key,
                                title      = alert_title,
                                message    = repair_msg)

        case 'update_apple_acct':
            issue_id = post_repair_issue_update_apple_acct(
                                issue_id   = issue_id,
                                alert_key  = alert_key,
                                title      = alert_title,
                                message    = repair_msg,
                                fix_data   = kwargs.get('fix_data'))

        case 'restart':
            issue_id = post_repair_issue(
                                issue_id   = issue_id,
                                alert_key  = alert_key,
                                title      = alert_title,
                                alert_msg  = '',
                                fix_action = FIX_ACTION_RESTART,
                                translation_key = RESTART_TRANSLATION_KEY,
                                translation_placeholders = {
                                        'title': _evlog_msg_to_markdown(alert_title),
                                        'message': _evlog_msg_to_markdown(repair_msg)})

        case _:     # 'alert', 'notice'
            issue_id = post_repair_issue(
                                issue_id   = issue_id,
                                alert_key  = alert_key,
                                title      = alert_title,
                                alert_msg  = repair_msg,
                                translation_key = translation_key,
                                translation_placeholders = translation_placeholders)

    kwargs['issue_id'] = issue_id

    return issue_id

#--------------------------------------------------------------------
def clear_config_error_repair_issues():
    '''
    Remove the post_config_error Repairs issues that were not posted again during this
    startup, their error no longer exists. The ones posted again keep their 'Ignore'
    state. Called when startup is complete.
    '''
    keep_issue_ids = [startup_msg.get('issue_id') for startup_msg in Gb.startup_msg
                                if isinstance(startup_msg, dict)]
    clear_repair_issues(CONFIG_ERROR_ISSUE_ID_PREFIX, keep_issue_ids=keep_issue_ids)

#--------------------------------------------------------------------
def clear_config_error(Source=None, name=None, error=None):
    '''
    The configuration error posted by post_config_error was corrected later in the
    startup. Remove it from Gb.startup_msg so its Repairs issue is not kept, then
    remove the issue and its sensor.icloud3_alerts message.

    Source, error:
        The post_config_error Source (Device, AppleAcct, devicename, apple_id) and
        error ('unknown_apple_acct')
    '''
    Source, source = alert_source(Source, name)
    alert_key = alert_key_for(source, error)

    for startup_msg in Gb.startup_msg.copy():
        if (isinstance(startup_msg, dict)
                and startup_msg.get('alert_key') == alert_key):
            Gb.startup_msg.remove(startup_msg)

            if issue_id := startup_msg.get('issue_id'):
                clear_repair_issue(issue_id)

    update_alert_sensor(Source=Source, error=error, clear=True)

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
        fname_text = Gb.EvLog.format_evlog_device_fname(Device)
        if Gb.EvLog.evlog_attrs['selected_fname'] != fname_text:
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

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   ICLOUD3_ALERTS SENSOR
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def update_alert_sensor(Source=None, name=None, error=None,
                        alert_msg=None, clear=False, update_sensor=False):
    '''
    Add or remove an alert in the Device's, AppleAcct's or Gb's alerts_by_alert_key
    dictionary and rebuild the icloud3_alerts sensor attributes. The alert_key is
    'source^error' (see alert_source, alert_key_for).

    Source:
        Device, AppleAcct, devicename, apple_id or Gb. Others are kept in Gb.
    name:
        The source id when the alert is kept in Gb (ALERT_CRITICAL, etc.)
    error:
        Type of error that will become part of the alert key
    alert_msg:
        The message that will be in the alert sensor
    clear:
        True to remove the error's alert, all of the Source's alerts if error is None

    '''
    if Source is None and name is None and clear is False:
        Gb.AlertsSensor.async_update_sensor()
        return

    if error is None and clear is False:
        return

    Source, source = alert_source(Source, name)

    # Clear this message, all of the Source's alerts if no error was specified
    if clear is True:
        if error is None:
            for _alert_key in list(Source.alerts_by_alert_key):
                if _alert_key.startswith(f"{source}^"):
                    Source.alerts_by_alert_key.pop(_alert_key, None)
        else:
            Source.alerts_by_alert_key.pop(alert_key_for(source, error), None)
        update_sensor = True

    # Add the alert
    else:
        alert_key = alert_key_for(source, error)
        # Gb.alerts_by_alert_key[alert_key] = alert_msg
        Source.alerts_by_alert_key[alert_key] = alert_msg

    if Gb.is_icloud3_startup_inprocess is False:
        update_sensor = True

    Gb.AlertsSensor.alerts_sensor_extra_attrs = build_alerts_sensor_extra_attrs()

    if update_sensor:
        try:
            Gb.AlertsSensor.async_update_sensor()
        except Exception as err:
            log_exception(err)

    log_debug_msg(  f"Alerts Sensor > Sensor-{Gb.alerts_sensor}, "
                    f"Attrs-{all_alerts_by_alert_key()}")

#..........................................................................................
def alert_source(Source=None, name=None):
    '''
    Get the object that keeps the alert and the source id used in its alert_key.

    Source:
        Device, AppleAcct, devicename, apple_id or Gb
    name:
        The source id for alerts kept in Gb (ALERT_CRITICAL, etc.) when Source is
        not a Device or an AppleAcct

    Returns:
        (Device, devicename), (AppleAcct, apple_id) or (Gb, name or 'icloud3')
    '''
    if Source in Gb.Devices:
        return Source, Source.devicename
    if Source in Gb.AppleAccts:
        return Source, Source.apple_id

    if isinstance(Source, str):
        if Device := Gb.Devices_by_devicename.get(Source):
            return Device, Device.devicename
        if AppleAcct := Gb.AppleAcct_by_apple_id.get(Source):
            return AppleAcct, AppleAcct.apple_id
        return Gb, Source

    return Gb, name or 'icloud3'

#..........................................................................................
def alert_key_for(source, error):
    '''
    The alert_key used in the alerts_by_alert_key dictionaries and the Repairs issues,
    'source^error' (lower case error)
    '''
    return f"{source}^{error.lower()}"

#..........................................................................................
def alert_key_source(alert_key):
    return alert_key.split('^')[0]

#..........................................................................................
def alert_key_source_error(alert_key):
    '''
    The alert key is 'source^error' where the source is the source id (devicename, apple_id)
    of the error and the error (lower case) is the type of error.

    Returns:
        (source, error)
    '''

    if instr(alert_key, '^'):
        return alert_key.split('^')
    else:
        return alert_key, ''

#-------------------------------------------------------------------------------------------
def build_alerts_sensor_extra_attrs():
    '''
    Alerts attributes contain the various types of alerts

    Note: _source of apple acct items will be the filteredapple_user (gee**2**ry@)
    Convert it back to the real apple account text (geekstergary) for the state and attr value
    '''
    extra_attrs = {}
    extra_attrs['alert_count'] = 0
    extra_attrs['updated']     = ''

    try:
        alerts = all_alerts_by_alert_key()

        extra_attrs['alert_count'] = len(alerts)
        if is_empty(alerts):
            return extra_attrs

        extra_attrs['.'] = '-'*75

        message_text = ''
        alert_cnt = 0
        for alert_msg in alerts.values():
            alert_cnt += 1
            message_text += f"\n{DOT}{alert_msg}"

            alert_fname_msg = alert_msg.split(' > ')
            if len(alert_fname_msg) == 2:
                extra_attrs[alert_fname_msg[0]] = alert_fname_msg[1]
            else:
                extra_attrs[f"Alert #{alert_cnt}"] = alert_msg

        extra_attrs['..'] = '-'*75
        extra_attrs['message_text'] = message_text
        # extra_attrs[','] = '-'*75

    except Exception as err:
        log_exception(err)

    return extra_attrs

#-------------------------------------------------------------------------------------------
def all_alerts_by_alert_key():
    '''
    The alerts kept in Gb (critical first), the Apple Accts and the Devices.
    Used to build the icloud3_alerts sensor and the Event Log greenbar.
    '''
    alerts = {}
    alerts.update({alert_key: alert_msg
                        for alert_key, alert_msg in Gb.alerts_by_alert_key.items()
                        if alert_key.startswith(f"{ALERT_CRITICAL}^")})

    for AppleAcct in Gb.AppleAccts:
        alerts.update(dict_sort(AppleAcct.alerts_by_alert_key))

    for Device in Gb.Devices:
        alerts.update(dict_sort(Device.alerts_by_alert_key))

    alerts.update(dict_sort(Gb.alerts_by_alert_key))

    return alerts

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   HA REPAIRS ISSUE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Each iCloud3 issue has its own translation key with its text in 'issues' in
# strings.json & translations/en.json. A simple notice that does not need its own
# text can use icloud3_notice, the title and message are passed as placeholders.
#   icloud3_notice - Notice (fix_action='acknowledge'), Submit only removes it
REPAIR_NOTICE_TRANSLATION_KEY       = 'icloud3_notice'

# Fix handlers run by repairs.py when Submit is selected on a fixable issue.
#   {fix_action: handler(fix_data) -> bool}, see register_repair_fix_handler
repair_fix_handlers = {}

# The Repairs issues that are open and their sensor.icloud3_alerts entry. HA does not
# keep them when it restarts (is_persistent=False), they are posted again when
# iCloud3 starts. The alerts entry is shared by all of a device's or Apple acct's
# alerts, it is only removed with the issue if it is still the issue's title.
# The Event Log greenbar lists the alert_keys with an open issue.
#   {issue_id: (alert_key, title)}
open_repair_issues = {}

#--------------------------------------------------------------------
def post_repair_issue(  issue_id, alert_key, title, alert_msg,
                        fix_action=None, fix_data=None, severity='warning',
                        translation_key=None, translation_placeholders=None):
    '''
    Add an iCloud3 notification to HA Settings > Repairs. The title is also added to
    the sensor.icloud3_alerts attribute for the alert_key. The Event Log greenbar
    lists the alert_keys with an open issue.

    issue_id:
        Stable id of the condition, e.g. f"device_replaced_{devicename}_{device_id8}".
        Posting the same id again updates the issue instead of adding another one.
        HA keeps the issue's 'Ignore' state by id, so an ignored issue stays ignored
        when it is posted again on the next restart. A notice (fix_action='acknowledge')
        is deleted and created again so it is always displayed.
    alert_key:
        What the issue is for, used as the sensor.icloud3_alerts key:
            - devicename - The Device's fname is used
            - Apple acct apple_id - The AppleAcct's apple_user is used
            - Other text - Used as is
        The issue data has the alert_key and the devicename ('' if it is not a
        device) for the fix handler.
    title:
        sensor.icloud3_alerts message. It is also the Repairs title for icloud3_notice.
    alert_msg:
        Repairs message for icloud3_notice ('' with a translation_key). Event Log
        formatting (CRLF, CRLF_DOT) is converted to markdown for the Repairs dialog.
    fix_action:
        Name of a handler registered with register_repair_fix_handler. The issue
        is fixable and the handler runs when Submit is selected in Repairs.
        None - Informational issue, it can only be ignored
    fix_data:
        dict of str/int/float/None values passed to the fix handler
    severity:
        'warning', 'error' or 'critical'
    translation_key, translation_placeholders:
        The issue's text in 'issues' in strings.json & translations/en.json. The
        issue's fix_flow must have the 'confirm' step (and the abort reasons if it
        is fixable). None - icloud3_notice with the title and alert_msg, only for a
        notice. A fixable issue must have its own translation_key.

    Return:
        issue_id used for the Repairs issue (slugified)
    '''
    try:
        issue_id = slugify(issue_id)
        source  , error = alert_key_source_error(alert_key)
        devicename = apple_id = ''
        if Device := Gb.Devices_by_devicename.get(source):
            devicename = source
        elif AppleAcct := Gb.AppleAcct_by_apple_id.get(source):
            apple_id = source
        if fix_action is None:
            fix_action = 'acknowledge'

        data = {'devicename': devicename,
                'apple_id':   apple_id,
                'alert_key ': alert_key,
                'fix_action': fix_action}
        data.update(fix_data or {})

        # A notice reports a new event. Delete the one from an earlier post first so
        # it is displayed even if it was ignored ('Ignore' is kept by issue_id).
        if fix_action == 'acknowledge':
            _run_in_event_loop(ir.async_delete_issue, Gb.hass, DOMAIN, issue_id)

        if translation_key is None:
            if fix_action != 'acknowledge':
                raise ValueError(f"Repair issue {issue_id} is fixable and needs a translation_key")
            translation_key = REPAIR_NOTICE_TRANSLATION_KEY
            translation_placeholders = {
                                'title': _evlog_msg_to_markdown(title),
                                'message': _evlog_msg_to_markdown(alert_msg)}

        # The Repairs dialog title is 'iCloud3 Repair Issue > {fname} (...)' and the full
        # title is the message heading. fname is the name before the ' > ' in the title.
        if translation_placeholders and 'title' in translation_placeholders:
            translation_placeholders = {
                    'fname': str(translation_placeholders['title']).split(' > ')[0].strip(),
                    **translation_placeholders}

        _run_in_event_loop(ir.async_create_issue,
                                Gb.hass, DOMAIN, issue_id,
                                is_fixable     = fix_action is not None,
                                is_persistent  = False,
                                severity       = ir.IssueSeverity(severity),
                                translation_key= translation_key,
                                translation_placeholders = translation_placeholders,
                                data          = data)

        # update_alert_sensor(alert_key, title)
        # Source=None, name=None, error=None,
        #                 alert_msg=alert_key,
        open_repair_issues[issue_id] = (alert_key, title)

    except Exception as err:
        log_exception(err)

    return issue_id

#--------------------------------------------------------------------
def clear_repair_issue(issue_id):
    '''
    Remove the Repairs issue and its sensor.icloud3_alerts message. Only call this
    when the condition no longer exists. Deleting the issue also deletes its
    'Ignore' state, so it is displayed again if it is posted later.

    The alerts sensor entry is only removed if it is still this issue's title.
    Another alert for the same device or Apple acct may have replaced it.
    '''
    issue_id = slugify(issue_id)

    try:
        _run_in_event_loop(ir.async_delete_issue, Gb.hass, DOMAIN, issue_id)
    except Exception as err:
        log_exception(err)

    remove_open_repair_issue(issue_id)

#--------------------------------------------------------------------
def clear_repair_issues(issue_id_prefix, keep_issue_ids=None):
    '''
    Remove the Repairs issues with an id starting with issue_id_prefix except the
    ones in keep_issue_ids. Used to remove issues whose condition no longer exists
    while keeping the ones that were posted again (and their 'Ignore' state).

    issue_id_prefix:
        Leading words of the issue_id, 'device_replaced_gary_iphone' removes
        'device_replaced_gary_iphone_...' but not 'device_replaced_gary_iphone2_...'

    The alerts sensor entry is only removed if it is still the removed issue's title.
    '''
    issue_id_prefix = f"{slugify(issue_id_prefix)}_"
    keep_issue_ids  = [slugify(issue_id) for issue_id in (keep_issue_ids or []) if issue_id]

    for issue_id in list(open_repair_issues):
        if issue_id.startswith(issue_id_prefix) and issue_id not in keep_issue_ids:
            remove_open_repair_issue(issue_id)


    def _async_delete_issues():
        issue_registry = ir.async_get(Gb.hass)
        for domain, issue_id in list(issue_registry.issues):
            if (domain == DOMAIN
                    and issue_id.startswith(issue_id_prefix)
                    and issue_id not in keep_issue_ids):
                ir.async_delete_issue(Gb.hass, DOMAIN, issue_id)

    try:
        _run_in_event_loop(_async_delete_issues)
    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def remove_open_repair_issue(issue_id):
    '''
    The issue was removed (cleared or fixed with Submit, repairs.py). Remove it from
    the open issues and remove its sensor.icloud3_alerts entry if it is still the
    issue's title. Another alert that replaced it is left.
    '''
    alert_key, title = open_repair_issues.pop(issue_id, (None, None))
    if alert_key and all_alerts_by_alert_key().get(alert_key) == title:
        source, error = alert_key_source_error(alert_key)
        update_alert_sensor(Source=source, name=source, error=error, clear=True)

#--------------------------------------------------------------------
def open_repair_issue_alert_keys():
    '''
    The sensor.icloud3_alerts keys (devicename^error, apple_id^error) with an
    open Repairs issue. Used by the Event Log greenbar.
    '''
    return {alert_key for alert_key, _title in list(open_repair_issues.values())}

#--------------------------------------------------------------------
def register_repair_fix_handler(fix_action, handler):
    '''
    Register the function run when Submit is selected on a fixable Repairs issue.

    handler(fix_data) -> bool:
        fix_data:
            the issue's data (devicename, fix_action and the fix_data values)
        Return:
            True if fixed (the issue is removed),
            False if it failed (the issue stays in Repairs).
        Note:
            It runs in an executor thread so it can use the iCloud3
            routines and write the configuration file.
    '''
    repair_fix_handlers[fix_action] = handler

# 'acknowledge' - The issue is a notice. Submit removes it and its alerts sensor message.
register_repair_fix_handler('acknowledge', lambda fix_data: True)

# 'restart' - Submit restarts iCloud3
FIX_ACTION_RESTART = 'restart'

def _fix_repair_issue_restart(fix_data):
    post_event(f"HA Repairs > Restarting iCloud3")
    Gb.was_icloud3_restart_requested = True
    return True

register_repair_fix_handler(FIX_ACTION_RESTART, _fix_repair_issue_restart)

# 'update_device' - Submit opens the iCloud3 Configure Update Device screen for the
# fix_data 'devicename' (repairs.iCloud3DeviceRepairFlow). It does not have a handler.
FIX_ACTION_UPDATE_DEVICE = 'update_device'

# 'update_apple_acct' - Submit opens the iCloud3 Configure Update Apple Account screen
# for the fix_data 'apple_id' (repairs.iCloud3AppleAcctRepairFlow). It does not have
# a handler.
FIX_ACTION_UPDATE_APPLE_ACCT = 'update_apple_acct'

# 'analytics_approval' - Request approval to send the iCloud3 Analytics data
# (repairs.iCloud3AnalyticsRepairFlow). Submit enables it, closing the dialog with
# the X disables it. It does not have a handler. The issue_id is also the
# translation key.
FIX_ACTION_ANALYTICS_APPROVAL = 'analytics_approval'
ANALYTICS_APPROVAL_ISSUE_ID   = 'analytics_approval'

# The issues used for the configuration errors. Their fix_flow has the configuration
# screens' text, the title & message are placeholders.
UPDATE_DEVICE_TRANSLATION_KEY     = 'update_device'
UPDATE_APPLE_ACCT_TRANSLATION_KEY = 'update_apple_acct'
RESTART_TRANSLATION_KEY           = 'restart_icloud3'

# Leading words of the post_config_error issue_ids
CONFIG_ERROR_ISSUE_ID_PREFIX = 'config_error'

# Leading words of the post_config_error 'notice' issue_ids. They are only removed by Submit.
CONFIG_NOTICE_ISSUE_ID_PREFIX = 'config_notice'

#--------------------------------------------------------------------
def post_repair_issue_update_device(issue_id, alert_key, title, message,
                                            severity='warning'):
    '''
    Add a fixable iCloud3 device configuration error to HA Settings > Repairs. Submit
    opens the iCloud3 Configure Update Device screen for the device so the error can
    be corrected. The issue is removed when the configuration is updated.

    issue_id:
        Stable id of the condition, see post_repair_issue
    devicename:
        iCloud3 devicename with the error
    title:
        Short description of the error, e.g. 'Newer Apple Devices detected'. It is the
        sensor.icloud3_alerts message and is displayed as 'iCloud3: Fname, title'.
    message:
        Description of the error and how to correct it. Event Log formatting (CRLF,
        CRLF_DOT) is converted to markdown.

    Return:
        issue_id used for the Repairs issue (slugified)
    '''
    devicename, error = alert_key_source_error(alert_key)
    fname = [conf_device[CONF_FNAME] for conf_device in Gb.conf_devices
                            if conf_device[CONF_IC3_DEVICENAME] == devicename]
    fname = fname[0] if fname else devicename
    return post_repair_issue(
                issue_id   = issue_id,
                alert_key  = alert_key,
                title      = title,
                alert_msg  = '',
                fix_action = FIX_ACTION_UPDATE_DEVICE,
                fix_data   = {'devicename': devicename},
                severity   = severity,
                translation_key = UPDATE_DEVICE_TRANSLATION_KEY,
                translation_placeholders = {
                                'title':   title,
                                'message': _evlog_msg_to_markdown(message),
                                'device':  fname})

#--------------------------------------------------------------------
def post_repair_issue_update_apple_acct(issue_id, alert_key, title, message,
                                            fix_data=None, severity='warning'):
    '''
    Add a fixable iCloud3 Apple Account configuration error to HA Settings > Repairs.
    Submit opens the iCloud3 Configure Update Apple Account screen for the account so
    the error can be corrected. The issue is removed when the configuration is updated.

    issue_id:
        Stable id of the condition, see post_repair_issue
    apple_id:
        Apple Account apple_id with the error
    title:
        Short description of the error, e.g. 'INVALID USERNAME/PW'. It is the
        sensor.icloud3_alerts message and is displayed as 'iCloud3: apple_user, title'.
    message:
        Description of the error and how to correct it. Event Log formatting (CRLF,
        CRLF_DOT) is converted to markdown.
    fix_data:
        Other items used by the repair flow, e.g. 'apple_acct_status' for an unknown
        Apple Acct (start_ic3.report_unknown_apple_accounts)

    Return:
        issue_id used for the Repairs issue (slugified)
    '''
    apple_id, error = alert_key_source_error(alert_key)

    return post_repair_issue(
                issue_id   = issue_id,
                alert_key  = alert_key,
                title      = title,
                alert_msg  = '',
                fix_action = FIX_ACTION_UPDATE_APPLE_ACCT,
                fix_data   = {**(fix_data or {}), 'apple_id': apple_id},
                severity   = severity,
                translation_key = UPDATE_APPLE_ACCT_TRANSLATION_KEY,
                translation_placeholders = {
                                'title':   title,
                                'message': _evlog_msg_to_markdown(message),
                                'account': apple_user(apple_id)})

#--------------------------------------------------------------------
def _run_in_event_loop(func, *args, **kwargs):
    '''
    Run an HA @callback function in the event loop. iCloud3 startup and tracking
    run in executor threads, so the call is scheduled without waiting for it
    (waiting from the event loop thread would deadlock).
    '''
    if Gb.hass is None:
        return

    if threading.get_ident() == Gb.hass.loop_thread_id:
        func(*args, **kwargs)
    else:
        Gb.hass.loop.call_soon_threadsafe(partial(func, *args, **kwargs))

#--------------------------------------------------------------------
def _evlog_msg_to_markdown(msg):
    '''
    Convert Event Log formatting to markdown for the Repairs dialog
    '''
    msg = re.sub(r'\^\w\^', '', str(msg))
    msg = msg.replace(CRLF_DOT, '\n- ')
    msg = msg.replace(CRLF, '  \n')
    for nbsp in (NBSP6, NBSP5, NBSP4, NBSP3, NBSP2, NBSP):
        msg = msg.replace(nbsp, ' ')

    return msg.strip()

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
        filemode = 'a' if Gb.was_icloud3_reloaded else filemode


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
            write_ic3log_recd(f"Loading {Gb.icloud3_version_msg}")

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

            log_msg = f"{EVLOG_ALERT}Recreated iCloud3 Log File: {ic3logger_file}"
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
    indent = SP(37) if Gb.is_log_level_debug else SP(18)
    log_msg = ( f"iCloud3 Configuration File, {Gb.icloud3_version_msg}")
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
                f"{NLSP4}{Gb.ha_location_info}"
                f"{NLSP4}SENSORS:"
                f"{NLSP4}{Gb.conf_sensors}"
                f"{NLSP4}DEVICE SENSORS:"
                f"{NLSP4}{Gb.conf_device_sensors}")

    for conf_apple_accounts in Gb.conf_apple_accounts:
        log_msg += (f"{NLSP4}APPLE ACCOUNT: {conf_apple_accounts.get(CONF_APPLE_ACCT)}:"
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

#--------------------------------------------------------------------
def log_warning_msg(module_name, log_msg='+'):

    log_msg = _resolve_module_name_log_msg(module_name, log_msg)
    if log_msg.startswith('iCloud3: ') is False:
        log_msg = f"iCloud3: {log_msg}"
    Gb.HALogger.warning(log_msg)

    log_msg = format_msg_line(log_msg)

    write_ic3log_recd(log_msg)

#--------------------------------------------------------------------
def log_error_msg(module_name, log_msg='+'):

    log_msg = _resolve_module_name_log_msg(module_name, log_msg)
    if log_msg.startswith('iCloud3: ') is False:
        log_msg = f"iCloud3: {log_msg}"
    Gb.HALogger.error(log_msg)

    log_msg = format_msg_line(log_msg)

    write_ic3log_recd(log_msg)

#--------------------------------------------------------------------
def log_exception(err):

    try:
        write_ic3log_recd(f"{Gb.icloud3_version_msg}\n{traceback.format_exc()}")
    except:
        write_ic3log_recd(err)

    Gb.HALogger.exception(err)

#--------------------------------------------------------------------
def log_debug_msg(devicename_or_Device, log_msg='+', msg_prefix=None, log_stack_pgm=None):

    if Gb.is_log_level_debug is False or Gb.iC3Logger is None:
        return
    if devicename_or_Device and log_msg == '':
        return

    devicename, log_msg = _resolve_devicename_log_msg(devicename_or_Device, log_msg)

    if devicename: devicename = f"{devicename} > "
    log_msg = f"{devicename}{str(log_msg)}"
    log_msg = format_msg_line(log_msg, log_stack_pgm=log_stack_pgm)

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
        current_frame = f"{filename[4:]}, {frame_recd.lineno}, {frame_recd.function}"

        if return_cnt == 0:
            if cnt > 0:
                code = frame_recd.code_context[0].replace('\n', '').strip()
                log_msg += f"{NL4}{SP(9)}{[code]}"
        elif return_cnt == cnt:
            return current_frame

    log_msg = f"{NL4}🟩 LOG STACK: {hdr_msg}{log_msg}"
    log_info_msg(log_msg)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   LOG MESSAGE SUPPORT ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def format_msg_line(log_msg, log_stack_pgm=None):
    try:
        if type(log_msg) is str is False:
            return log_msg

        msg_prefix= '' if log_msg.startswith('⡇') else \
                    ''  if log_msg.startswith(NL) else \
                    NL3U if instr(log_msg, 'REQUEST') else \
                    NL3D if instr(log_msg, 'RESPONSE') else \
                    NL3D if instr(log_msg, 'HDR') else \
                    NL3_DATA if instr(log_msg, 'DATA') else \
                    '⡇ ' if Gb.trace_group else \
                    ''

        program_area = ''

        if log_stack_pgm is not None:
            source = log_stack_pgm
        elif instr(msg_prefix, '\n'):
            source = f"{_called_from_history()}"
        else:
            source = f"{_called_from()}{program_area}"

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
            SP(37) if Gb.is_log_level_debug else \
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

    log_msg = log_msg.replace(EVLOG_UPDATE_HDR, '')
    log_msg = log_msg.replace(EVLOG_UPDATE_START, '')
    log_msg = log_msg.replace(EVLOG_UPDATE_END  , '')
    log_msg = log_msg.replace(EVLOG_ERROR, '')
    log_msg = log_msg.replace(EVLOG_ALERT, '')
    log_msg = log_msg.replace(EVLOG_WARNING, '')
    log_msg = log_msg.replace(EVLOG_ATTENTION, '')
    log_msg = log_msg.replace(EVLOG_HIGHLIGHT, '')
    log_msg = log_msg.replace(EVLOG_ATTENTION, '')
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
    if hdr_code in [EVLOG_ATTENTION, EVLOG_IC3_STAGE_HDR]:
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

    indent = indent if indent is not None else 37 if Gb.is_log_level_debug else 15

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
#   ERROR MESSAGE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def internal_error_msg(err_text, msg_text=''):

    stack    = inspect.stack()
    caller   = inspect.getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename).split('.')[0][:14]
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
def _evlog(devicename_or_Device, event_msg='+'):
    '''
    Display a message or variable in the Event Log
    '''
    devicename, event_msg = _resolve_devicename_log_msg(devicename_or_Device, event_msg)

    if event_msg is None:
        return

    if (type(event_msg) is str) is False:
        event_msg = f"{event_msg}"

    event_msg   = event_msg.replace('<', '&lt;')
    called_from = _called_from(trace=True)
    function    = log_stack(return_function=True)

    if Gb.EvLog:
        Gb.EvLog.post_event(devicename, f"{EVLOG_TRACE}{called_from} {event_msg}")

    _log(event_msg)

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

    if Gb.is_log_level_debug is False and trace == False:
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
        if (caller.filename.endswith('messaging.py') is False
                and caller.filename.endswith('rawdata_logging.py') is False):
            break

    if caller is None:
        return ' '

    py_filename = _extract_py_filename(caller)

    if show_fct_name is True:
        return f"[{py_filename}: {caller.lineno}/{caller.function}]"

    py_filename = f"{py_filename}……………………"
    caller_lineno = caller.lineno

    return f"[{py_filename[:14]}:{caller_lineno:04}] "

#--------------------------------------------------------------------
def _called_from_history(trace=False):

    if Gb.is_log_level_debug is False and trace == False:
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
                    or py_filename == 'rawdata_logging'
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
def add_log_file_filter(filtered_item, filtered_text=None):
    '''
    Set up  log file filter to replace the items value with *'s or prevent it
    from displaying in the log file. If item contains an '@' and it is being hidden,
    it is an email address and it's url will be hidden.

    parameters:
        hide_text:  True = Do not display it instead of replacing with *'s

    '''

    if (filtered_item is None
            or filtered_item.strip() == ''
            or len(filtered_item) < 6):
        return
    elif TEST.DISABLE_UPW_FILTER:
        return

    if instr(filtered_item, '@') is False:
        if filtered_text is None:
            filtered_text = '*'*8
        Gb.upw_filter_items[filtered_item] = filtered_text
        return

    # email address = geekstergary@domain - reformat to xx**#**xx@
    email_id = apple_user(filtered_item)        # Will be geekstergary@
    if len(email_id) < 4: email_id = '***'

    if filtered_text is None:
        filtered_text = f"{email_id[:3]}****{email_id[-3:]}"
    else:
        filtered_text = f"{email_id[:3]}{filtered_text}{email_id[-3:]}"       # ge**2**ry@

    Gb.upw_filter_items[filtered_item] = Gb.upw_filter_items[email_id] = filtered_text
    Gb.upw_unfilter_items[filtered_text] = email_id

    filtered_item = filtered_item.upper()
    email_id      = email_id.upper()
    filtered_text = filtered_text.upper()
    Gb.upw_filter_items[filtered_item] = Gb.upw_filter_items[email_id] = filtered_text
    Gb.upw_unfilter_items[filtered_text] = email_id



#--------------------------------------------------------------------
class LoggerFilter(logging.Filter):
    '''
    Filter items from being displayed in the log file (Password)
    '''
    @staticmethod
    def filter(record):
        if TEST.DISABLE_UPW_FILTER:
            return True

        message = record.msg
        for filtered_item, filtered_text in Gb.upw_filter_items.items():
            if instr(message, filtered_item):
                message = message.replace(filtered_item, filtered_text)

        record.msg  = message
        record.args = []
        return True
