#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD SERVICE HANDLER MODULE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from ..global_variables import GlobalVariables as Gb
from ..const            import (DOMAIN,
                                RED_ALERT, EVLOG_ALERT, EVLOG_ERROR, CRLF_DOT, EVLOG_IC3_STARTING,
                                ICLOUD3_VERSION_MSG,
                                CMD_RESET_PYICLOUD_SESSION,
                                LOCATION, NEXT_UPDATE_TIME, NEXT_UPDATE, INTERVAL,
                                CONF_DEVICENAME, CONF_ZONE, CONF_COMMAND, CONF_LOG_LEVEL,
                                ICLOUD_LOST_MODE_CAPABLE,
                                )

from ..utils.utils      import (instr, )
from ..utils.messaging  import (post_event, post_alert, post_error_msg, post_monitor_msg,
                                post_greenbar_msg, clear_greenbar_msg,
                                more_info,
                                log_info_msg, log_debug_msg, log_exception,
                                _evlog, _log, )
from ..utils.time_util  import (secs_to_time, time_str_to_secs, datetime_now, secs_since,
                                time_now_secs, time_now, )

from ..mobile_app        import mobapp_interface
from ..startup           import config_file
from ..startup           import start_ic3
from ..tracking          import determine_interval as det_interval

#--------------------------------------------------------------------
import asyncio
import homeassistant.helpers.config_validation as cv
from homeassistant          import data_entry_flow
import voluptuous as vol

#--------------------------------------------------------------------
# EvLog Action Commands
CMD_ERROR                  = 'error'
CMD_PAUSE                  = 'pause'
CMD_RESUME                 = 'resume'
CMD_WAZE                   = 'waze'
CMD_REQUEST_LOCATION       = 'location'
CMD_EXPORT_EVENT_LOG       = 'export_event_log'
CMD_WAZEHIST_MAINTENANCE   = 'wazehist_maint'
CMD_WAZEHIST_TRACK         = 'wazehist_track'
CMD_DISPLAY_STARTUP_EVENTS = 'startuplog'
CMD_RESET_PYICLOUD_SESSION = 'reset_session'
CMD_LOG_LEVEL              = 'log_level'
CMD_REFRESH_EVENT_LOG      = 'refresh_event_log'
CMD_RESTART                = 'restart'
CMD_FIND_DEVICE_ALERT      = 'find_alert'
CMD_DISPLAY_MESSAGE_ALERT  = 'message_alert'
CMD_LOCATE                 = 'locate'

REFRESH_EVLOG_FNAME             = 'Refresh Event Log'
HIDE_TRACKING_MONITORS_FNAME    = 'Hide Tracking Monitors'
SHOW_TRACKING_MONITORS_FNAME    = 'Show Tracking Monitors'


GLOBAL_ACTIONS =  [CMD_EXPORT_EVENT_LOG,
                    CMD_DISPLAY_STARTUP_EVENTS,
                    CMD_RESET_PYICLOUD_SESSION,
                    CMD_WAZE,
                    CMD_REFRESH_EVENT_LOG,
                    CMD_RESTART,
                    CMD_LOG_LEVEL,
                    CMD_WAZEHIST_MAINTENANCE,
                    CMD_WAZEHIST_TRACK,
                    'event_log_version',
                    ]
DEVICE_ACTIONS =  [CMD_REQUEST_LOCATION,
                    CMD_PAUSE,
                    CMD_RESUME,
                    CMD_FIND_DEVICE_ALERT,
                    CMD_DISPLAY_MESSAGE_ALERT,
                    CMD_LOCATE, ]

NO_EVLOG_ACTION_POST_EVENT = [
                    'Show Startup Log, Errors & Alerts',
                    REFRESH_EVLOG_FNAME,
                    HIDE_TRACKING_MONITORS_FNAME,
                    SHOW_TRACKING_MONITORS_FNAME,
                    CMD_DISPLAY_STARTUP_EVENTS,
                    'event_log_version',
                    'Event Log Version']

ACTION_FNAME_TO_ACTION = {
                    'Restart iCloud3': 'restart',
                    'Pause Tracking': 'pause',
                    'Resume Tracking': 'resume',
                    'Locate Device(s) using iCloud iCloud': 'locate',
                    'Send Locate Request to iOS App': 'locate iosapp',
                    'Send Locate Request to Mobile App': 'locate mobapp',
                    'Send Locate Request to Mobile App': 'locate mobileapp'
}

SERVICE_SCHEMA = vol.Schema({
    vol.Optional('command'): cv.string,
    vol.Optional('action'): cv.string,
    vol.Optional(CONF_DEVICENAME): cv.slugify,
    vol.Optional('action_fname'): cv.string,
    vol.Optional('number'): cv.string,
    vol.Optional('message'): cv.string,
    vol.Optional('sounds'): cv.string,
})

from   homeassistant.util.location import distance

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEFINE THE PROCESS INVOKED BY THE HASS.SERVICES.REGISTER FOR EACH SERVICE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def process_update_service_request(call):
    """ icloud3.update service call request """

    action = call.data.get('command') or call.data.get('action')
    if action is None: return

    action       = action.lower()
    action_fname = call.data.get('action_fname')
    devicename   = call.data.get(CONF_DEVICENAME)

    action, devicename = resolve_action_devicename_values(action, devicename)

    update_service_handler(action, action_fname, devicename)

#--------------------------------------------------------------------
def process_restart_icloud3_service_request(call):
    """ icloud3.restart service call request  """

    Gb.InternetError.reset_internet_error(reset_test_control_flags=True)

#--------------------------------------------------------------------
def process_find_iphone_alert_service_request(call):
    """Call the find_iphone_alert to play a sound on the phone"""

    devicename = call.data.get(CONF_DEVICENAME)
    action, devicename = resolve_action_devicename_values("", devicename)

    find_iphone_alert_service_handler(devicename)

#--------------------------------------------------------------------
def process_lost_device_alert_service_request(call):
    """Call the find_iphone_alert to play a sound on the phone"""

    devicename = call.data.get(CONF_DEVICENAME)
    number     = call.data.get('number')
    message    = call.data.get('message')
    action, devicename = resolve_action_devicename_values("", devicename)

    try:
        Device = Gb.Devices_by_devicename.get(devicename)
        devicename = devicename or '?'
        number = number or '?'
        message = message or ('This Phone has been lost. \
                                Please call this number to report it found.')

        if Device is None:
            result_msg = f"Failed, Unknown device_name-{devicename}"

        elif devicename == '?' or number == '?' or message == '?' :
            result_msg = (  f"Required field missing, device_name-{devicename}, "
                            f"number-{number}, message-{message}")

        elif (Device.AADevData_icloud
                and Device.AADevData_icloud.device_data
                and Device.AADevData_icloud.device_data.get(ICLOUD_LOST_MODE_CAPABLE, False)):

            lost_device_alert_service_handler(devicename, number, message)

            result_msg = (  f"Alert Notification sent, Device-{Device.fname_devicename}, "
                            f"Number-{number}, Message-{message}")
        else:
            result_msg = f"Device {Device.fname_devicename} can not receive Lost Device Alerts"

    except Exception as err:
        log_exception(err)
        result_msg = "Internal Error"

    post_event(f"{EVLOG_ERROR}Lost Mode Alert > {result_msg}")

#--------------------------------------------------------------------
def process_display_message_alert_service_request(call):
    '''
    Call the display_message_alert to display a message and (optionally) play a sound on the phone
    '''

    devicename = call.data.get(CONF_DEVICENAME)
    message    = call.data.get('message')
    sounds     = call.data.get('sounds')
    action, devicename = resolve_action_devicename_values("", devicename)

    display_message_alert_service_handler(devicename, message, sounds)

#--------------------------------------------------------------------
def resolve_action_devicename_values(action, devicename):
    '''
    Convert the action and devicenames to their actual intervalues when they are being executed
    from the Developer Tools/Services screen.
        - action text dexcription --> action parameter
        - ha_device_id --> devicename parameter

    Return the action and devicename values
    '''
    # Convert action and devicename to the real values if the service call
    # is coming in from the Developer Tools/Services screen
    if action in ACTION_FNAME_TO_ACTION:
        action = ACTION_FNAME_TO_ACTION[action]
    if devicename == 'startup_log':
        return action, devicename

    if devicename in Gb.Devices_by_ha_device_id:
        devicename = Gb.Devices_by_ha_device_id[devicename].devicename
    if devicename not in Gb.Devices_by_devicename:
        devicename = None

    return action, devicename

#--------------------------------------------------------------------
def _post_device_event_msg(devicename, msg):
    if devicename:
        post_event(devicename, msg)
    else:
        post_event(msg)

def _post_device_monitor_msg(devicename, msg):
    if devicename:
        post_monitor_msg(devicename, msg)
    else:
        post_monitor_msg(msg)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEFINE THE PROCESS INVOKED BY THE HASS.SERVICES.REGISTER FOR EACH SERVICE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def register_icloud3_services():
    ''' Register iCloud3 Service Call Handlers '''

    try:
        Gb.hass.services.register(DOMAIN, 'action',
                    process_update_service_request, schema=SERVICE_SCHEMA)
        Gb.hass.services.register(DOMAIN, 'update',
                    process_update_service_request, schema=SERVICE_SCHEMA)
        Gb.hass.services.register(DOMAIN, 'restart',
                    process_restart_icloud3_service_request, schema=SERVICE_SCHEMA)
        Gb.hass.services.register(DOMAIN, 'find_iphone_alert',
                    process_find_iphone_alert_service_request, schema=SERVICE_SCHEMA)
        Gb.hass.services.register(DOMAIN, 'lost_device_alert',
                    process_lost_device_alert_service_request, schema=SERVICE_SCHEMA)
        Gb.hass.services.register(DOMAIN, 'display_message_alert',
                    process_display_message_alert_service_request, schema=SERVICE_SCHEMA)

        return True

    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ROUTINES THAT HANDLE THE INDIVIDUAL SERVICE REQUESTS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def update_service_handler(action_entry=None, action_fname=None, devicename=None):
    """
    Authenticate against iCloud and scan for devices.


    Actions:
    - pause             - stop polling for the devicename or all devices
    - resume            - resume polling devicename or all devices, reset
                            the interval override to normal interval
                            calculations
    - pause-resume      - same as above but toggles between pause and resume
    - reset             - reset everything and rescans all of the devices
    - location          - request location update from mobile app
    - locate x mins     - locate in x minutes from iCloud
    - locate iosapp     - request location update from ios app
    - locate mobapp     - request location update from mobile app
    - locate mobile     - request location update from mobile app
    - config_flow       - Display the Configure screens handled by the config_flow module
    """
    # Ignore Action requests during startup. They are caused by the devicename changes
    # to the EvLog attributes indicating the startup stage.
    if (Gb.start_icloud3_inprocess_flag
            or action_entry is None):
        return

    action = action_entry

    if action == f"{CMD_REFRESH_EVENT_LOG}+clear_greenbar_msgs":
        action = CMD_REFRESH_EVENT_LOG

    if (action == CMD_REFRESH_EVENT_LOG
            and Gb.EvLog.secs_since_refresh <= 2
            and Gb.EvLog.last_refresh_devicename == devicename):
        _post_device_monitor_msg(devicename, f"Service Action Ignored > {action_fname}, Action-{action_entry}")
        return

    if action_fname not in NO_EVLOG_ACTION_POST_EVENT:
        _post_device_monitor_msg(devicename, f"Service Action Received > Action-{action_entry}")

    action_entry  = action_entry.replace('eventlog', 'monitor')
    action_entry  = action_entry.replace(':', '')
    action        = action_entry.split(' ')[0]
    action_option = action_entry.replace(action, '').strip()

    # EvLog version sent from the EvLog program already set, ignore the svc call
    if action == 'event_log_version':
        return

    devicename_msg = devicename if devicename in Gb.Devices_by_devicename else None
    action_msg     = action_fname if action_fname else f"{action.title()}"

    event_msg = f"Service Action > Action-{action_msg}"
    if action_option: event_msg += f", Options-{action_option}"
    if devicename:    event_msg += f", Device-{devicename}"

    if action_fname not in NO_EVLOG_ACTION_POST_EVENT:
        _post_device_event_msg(devicename_msg, event_msg)

    if action_msg == 'Restart iCloud3':
        post_event(f"{EVLOG_IC3_STARTING}Restart Requested > {ICLOUD3_VERSION_MSG}")

    if action in GLOBAL_ACTIONS:
        _handle_global_action(action, action_option)

    elif devicename == 'startup_log':
        pass

    elif action in DEVICE_ACTIONS:
        if devicename:
            Devices = [Gb.Devices_by_devicename[devicename]]
        else:
            Devices = [Device for Device in Gb.Devices_by_devicename.values()]

        if action == CMD_PAUSE:
            if devicename is None:
                Gb.all_tracking_paused_flag = True
                Gb.all_tracking_paused_secs = time_now_secs()
            for Device in Devices:
                Device.pause_tracking()

        elif action == CMD_RESUME:
            Gb.InternetError.reset_internet_error(reset_test_control_flags=True)

            Gb.all_tracking_paused_flag = False
            Gb.all_tracking_paused_secs = 0
            Gb.EvLog.display_user_message('', clear_greenbar_msg=True)
            for Device in Devices:
                Device.resume_tracking()

        elif action == CMD_LOCATE:
            # Trigger an Internet Error test
            if Gb.test_internet_error_after_startup:
                Gb.InternetError.reset_internet_error(reset_test_control_flags=True)
                Gb.test_internet_error = True
                Gb.icloud_io_request_secs = time_now_secs() + 70
                Device = Gb.Devices_by_devicename.get(Gb.EvLog.evlog_attrs["devicename"])
                if Device:
                    _handle_action_device_locate(Device, '')
                return

            for Device in Devices:
                _handle_action_device_locate(Device, action_option)

        elif action == CMD_REQUEST_LOCATION:
            for Device in Devices:
                _handle_action_device_location_mobapp(Device)

        else:
            return


    # Display the startup log selected
    if devicename == 'startup_log':
        Gb.evlog_startup_log_flag = True
        pass

    # Another option selected, startup log already displayed
    # Keep Startup log display but also display other selection
    elif (Gb.EvLog.evlog_attrs['fname'] == 'Startup Events'
            and action == 'log_level'
            and action_option == 'monitor'):
        devicename = 'startup_log'
        Gb.evlog_startup_log_flag = True

    # Regular event log displayed
    else:
        Gb.evlog_startup_log_flag = False

    Gb.EvLog.update_event_log_display(devicename)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   HANDLER THE VARIOUS ACTION ACTION REQUESTS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def _handle_global_action(global_action, action_option):

    if global_action == CMD_RESTART:
        Gb.log_debug_flag_restart         = Gb.log_debug_flag
        Gb.log_rawdata_flag_restart       = Gb.log_rawdata_flag
        Gb.restart_icloud3_request_flag   = True
        Gb.restart_requested_by           = 'user'
        Gb.InternetError.reset_internet_error(reset_test_control_flags=True)
        post_greenbar_msg(f"Restarting {ICLOUD3_VERSION_MSG}")
        Gb.EvLog.display_user_message('iCloud3 is Restarting')

        log_info_msg(f"\n{'-'*10} Opened by Event Log > Actions > Restart {'-'*10}")
        return

    elif global_action == CMD_EXPORT_EVENT_LOG:
        Gb.EvLog.export_event_log()
        return

    elif global_action == CMD_REFRESH_EVENT_LOG:
        return

    elif global_action == CMD_DISPLAY_STARTUP_EVENTS:
        return

    elif global_action == CMD_RESET_PYICLOUD_SESSION:
        # This will be handled in the 5-second ic3 loop
        # Gb.evlog_action_request = CMD_RESET_PYICLOUD_SESSION
        post_event(f"{EVLOG_ERROR}The `Action > Request Apple Verification Code` "
                        "is no longer available. This must be done using the "
                        "`Configuration > Enter/Request An Apple Account Verification "
                        "Code` screen")
        return

    elif global_action == CMD_LOG_LEVEL:
        handle_action_log_level(action_option)
        return

    elif global_action == CMD_WAZEHIST_MAINTENANCE:
        event_msg = f"{EVLOG_ALERT}Waze History > Recalculate Route Time/Dist, "
        if Gb.WazeHist.wazehist_recalculate_time_dist_running_flag:
            Gb.WazeHist.wazehist_recalculate_time_dist_abort_flag = True
            event_msg+="Stopped"
            post_event(event_msg)

        elif Gb.wazehist_recalculate_time_dist_flag:
            event_msg+=("Starting Immediately"
                        f"{CRLF_DOT}SELECT AGAIN TO STOP")
            post_event(event_msg)
            Gb.wazehist_recalculate_time_dist_flag = False
            Gb.WazeHist.wazehist_recalculate_time_dist_all_zones()

        else:
            Gb.wazehist_recalculate_time_dist_flag = True
            event_msg+=(f"Scheduled to run tonight at Midnight "
                        f"{CRLF_DOT}SELECT AGAIN TO RUN IMMEDIATELY")
            post_event(event_msg)

    elif global_action == CMD_WAZEHIST_TRACK:
        Gb.WazeHist.wazehist_update_track_sensor()
        return

    elif global_action == 'event_log_version':
        return

#--------------------------------------------------------------------
def handle_action_log_level(action_option, change_conf_log_level=True):

    # Show/Hide Tracking Monitors
    if instr(action_option, 'monitor'):
        Gb.evlog_trk_monitors_flag = not Gb.evlog_trk_monitors_flag
        return

    new_log_debug_flag   = Gb.log_debug_flag
    new_log_rawdata_flag = Gb.log_rawdata_flag

    # Log Level Debug
    if instr(action_option, 'debug'):
        new_log_debug_flag   = (not Gb.log_debug_flag)
        new_log_rawdata_flag = False

    # Log Level Rawdata
    if instr(action_option, 'rawdata'):
        new_log_rawdata_flag = (not Gb.log_rawdata_flag)
        new_log_debug_flag   = new_log_rawdata_flag

    if new_log_rawdata_flag is False:
        Gb.log_rawdata_flag_unfiltered = False

    # Log Level Rawdata Auto Reset at midnight
    new_log_level = 'rawdata-auto-reset' if new_log_rawdata_flag \
        else 'debug-auto-reset' if new_log_debug_flag \
        else 'info'

    start_ic3.set_log_level(new_log_level)
    start_ic3.update_conf_file_log_level(new_log_level)

    log_level_fname = new_log_level.replace('-', ' ').title()
    post_event(f"Log Level Change > New Level: {log_level_fname}")

def _on_off_text(condition):
    return 'On' if condition else 'Off'

#--------------------------------------------------------------------
def _handle_action_device_location_mobapp(Device):
    '''
    Request Mobile App location from the EvLog > Actions
    '''
    if Device.is_data_source_MOBAPP is False:
        return _handle_action_device_locate(Device, 'mobapp')

    Device.display_info_msg('Updating Location')

    if Device.mobapp_monitor_flag:
        Device.mobapp_data_change_reason = f"Location Requested@{time_now()}"
        mobapp_interface.request_location(Device, force_request=True)

#--------------------------------------------------------------------
def _handle_action_device_locate(Device, action_option):
    '''
    Set the next update time & interval from the Action > locate service call
    '''

    if action_option in ['mobapp', 'iosapp', 'mobileapp']:
        if Device.is_data_source_MOBAPP:
            _handle_action_device_location_mobapp(Device)
            return
        else:
            post_event(Device, "Mobile App Location Tracking is not available")

    if (Gb.use_data_source_ICLOUD is False
            or (Device.icloud_device_id is None)
            or Device.is_data_source_ICLOUD is False):
        post_event(Device, "iCloud Location Tracking is not available")
        return

    # elif Device.is_offline:
    #     post_event(Device, "The device is offline, iCloud Location Tracking is not available")
    #     return

    try:
        interval_secs = time_str_to_secs(action_option)
        if interval_secs == 0:
            interval_secs = 5
    except:
        interval_secs = 5

    if Device.is_tracking_paused:
        Gb.all_tracking_paused_flag = False
        Gb.EvLog.display_user_message('', clear_greenbar_msg=True)
        Device.resume_tracking()

    Gb.InternetError.reset_internet_error(reset_test_control_flags=True)
    Device.reset_tracking_fields(interval_secs)
    det_interval.update_all_device_fm_zone_sensors_interval(Device, interval_secs)
    Device.icloud_update_reason = f"Location Requested@{time_now()}"
    post_event(Device, f"Location will be updated at {Device.next_update_time}")
    Device.write_ha_sensors_state([NEXT_UPDATE, INTERVAL])

#--------------------------------------------------------------------
def set_ha_notification(title, message, issue=True):
    '''
    Format an HA Notification
    '''
    Gb.ha_notification = {
        'title': title,
        'message': f'{message}<br><br>*iCloud3 Notification {datetime_now()}*',
        'notification_id': DOMAIN}

    if issue:
        issue_ha_notification()

#--------------------------------------------------------------------
def issue_ha_notification():

    if Gb.ha_notification == {}:
        return

    Gb.hass.services.call("persistent_notification", "create", Gb.ha_notification)
    Gb.ha_notification = {}


#--------------------------------------------------------------------
def find_iphone_alert_service_handler(devicename):
    """
    Call the lost iPhone function if using th e iCloud tracking method.
    Otherwise, send a notification to the Mobile App
    """
    Device = Gb.Devices_by_devicename[devicename]
    if Device.is_data_source_ICLOUD:
        device_id = Device.icloud_device_id
        if device_id and Device.AppleAcct and Device.AppleAcct.AADevices:
            Device.AppleAcct.AADevices.play_sound(device_id, subject="Find My iPhone Alert")

            post_event(devicename, "iCloud Find My iPhone Alert sent")
            return

    if Device.conf_icloud_device_id and Device.verified is False:
        alert_msg =(f"{EVLOG_ALERT}ALERT CAN NOT BE SENT - The iCloud device has been specified "
                    f"but it was not verified during startup and is not available."
                    f"{more_info('icloud_dind_my_phone_alert_error')}")
    else:
        alert_msg =("The iCloud iCloud Device was not specified or is not available. "
                    "The alert will be sent using the Mobile App")
    post_event(devicename, alert_msg)

    message =   {"message": "Find My iPhone Alert",
                    "data": {
                        "push": {
                            "sound": {
                            "name": "alarm.caf",
                            "critical": 1,
                            "volume": 1
                            }
                        }
                    }
                }
    mobapp_interface.send_message_to_device(Device, message)

#--------------------------------------------------------------------
def lost_device_alert_service_handler(devicename, number, message=None):
    """
    Call the lost iPhone function if using the iCloud tracking method.
    Otherwise, send a notification to the Mobile App
    """
    if message is None:
        message = 'This Phone has been lost. Please call this number to report it found.'

    Device = Gb.Devices_by_devicename[devicename]
    if Device.is_data_source_ICLOUD:
        device_id = Device.icloud_device_id
        if device_id and Device.AppleAcct and Device.AppleAcct.AADevices:
            Device.AppleAcct.AADevices.lost_device(device_id, number=number, message=message)

            post_event(devicename, "iCloud Lost Device Alert sent")
            return

#--------------------------------------------------------------------
def display_message_alert_service_handler(devicename, message, sounds=False):
    '''
    Call the display message function of pyicloud.
    '''
    if message is None:
        message = 'Please review latest Home Assitant notifications for critical alerts'

    Device = Gb.Devices_by_devicename[devicename]
    if Device.is_data_source_ICLOUD:
        device_id = Device.icloud_device_id
        if device_id and Device.AppleAcct and Device.AppleAcct.AADevices:
            Device.AppleAcct.AADevices.display_message(device_id, message=message, sounds=sounds)

            post_event(devicename, "iCloud Display Message Alert sent")
            return
