
from ..global_variables import GlobalVariables as Gb
from ..const            import (HOME, NOT_SET, HHMMSS_ZERO,
                                    EVLOG_ALERT, EVLOG_ERROR,
                                    CRLF, CRLF_DOT, RARROW,
                                    ICLOUD, MOBAPP,
                                    LATITUDE, LONGITUDE,
                                    LOCATION,
                                    )

from ..startup          import start_ic3 as start_ic3
from ..apple_acct       import pyicloud_ic3_interface
from ..tracking         import determine_interval as det_interval
from ..utils.utils      import (instr, is_statzone, list_to_str, list_add, list_del, )
from ..utils.messaging  import (post_event, post_error_msg, post_monitor_msg, log_debug_msg,
                                log_exception, log_rawdata, _evlog, _log, )

from ..utils.time_util  import (time_now_secs, secs_to_time, format_timer, format_age, secs_since,)
from ..apple_acct.pyicloud_ic3  import (PyiCloudAPIResponseException, PyiCloud2FARequiredException,
                                        HTTP_RESPONSE_CODES, )


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Check the icloud Device to see if it qualified to be updated
#   on this polling cycle
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def no_icloud_update_needed_tracking(Device):
    if Device.is_tracking_paused:
        Device.icloud_no_update_reason = 'Paused'

    elif (Device.is_next_update_time_reached is False
            and Device.isin_zone
            and Device.isnotin_statzone):
        Device.icloud_no_update_reason = 'inZone & Next Update Time not Reached'

    elif Gb.use_data_source_ICLOUD is False:
        Device.icloud_no_update_reason = 'Global Mobile App Data Source'

    elif Device.is_data_source_ICLOUD is False:
        Device.icloud_no_update_reason = 'Device data from Mobile App'

    return (Device.icloud_no_update_reason != '')

#----------------------------------------------------------------------------
def no_icloud_update_needed_setup(Device):
    if Device.verified_flag is False:
        Device.icloud_no_update_reason = 'Not Verified'

    return (Device.icloud_no_update_reason != '')

#----------------------------------------------------------------------------
def is_icloud_update_needed_timers(Device):
    if (Device.is_passthru_zone_delay_active
            and Gb.this_update_secs > Device.passthru_zone_timer + \
                Gb.passthru_zone_interval_secs * 4):
        Device.icloud_update_reason = f"PassThru Zone timer expired"

    elif Device.is_statzone_timer_reached and Device.old_loc_cnt == 0:
        Device.icloud_update_reason = ( f"Stationary Zone Time Reached@"
                                        f"{secs_to_time(Device.statzone_timer)}")

    elif Device.is_passthru_timer_set and Gb.this_update_secs >= Device.passthru_zone_timer:
        Device.icloud_update_reason = ( f"Enter Zone Delay Time Reached@"
                                        f"{secs_to_time(Device.passthru_zone_timer)}")

    elif Device.is_next_update_time_reached:
        Device.icloud_update_reason = 'Next Update Time Reached'
        if Device.is_statzone_timer_reached:
            Device.icloud_update_reason = ( f"Next Update & Stat Zone Time Reached@"
                                        f"{secs_to_time(Device.statzone_timer)}")
        elif Device.isnotin_zone and Device.FromZone_NextToUpdate.from_zone != HOME:
            Device.icloud_update_reason += f" ({Device.FromZone_NextToUpdate.from_zone_dname})"

    elif Device.is_next_update_overdue:
        Device.icloud_update_reason = 'Next Update Time Overdue'

    log_debug_msg(Device, Device.icloud_update_reason)
    return (Device.icloud_update_reason != '')

#----------------------------------------------------------------------------
def is_icloud_update_needed_general(Device):
    if Gb.icloud_force_update_flag:
        Device.icloud_force_update_flag = True
        Device.icloud_update_reason = 'Immediate Update Requested'

    elif Device.is_tracking_resumed:
        Device.icloud_update_reason = 'Resume Tracking'

    elif Device.outside_no_exit_trigger_flag:
        Device.outside_no_exit_trigger_flag = False
        Device.icloud_force_update_flag = True
        Device.icloud_update_reason = "Verify Location"

    elif (Device.loc_data_secs < Device.last_update_loc_secs
            and Device.icloud_initial_locate_done):
        Device.icloud_update_reason = (f"Old Location-{Device.loc_data_time}")

    # There is no data for the device and the initial zone is not_set and
    # the old loc cnt > 0 means it has already tried to initialize the device
    # and failed. It will be controlled by the error retry cnt/timer instead of
    # the online & not_set and no location info next.
    elif (Device.no_location_data
            and Device.sensor_zone == NOT_SET
            and Device.old_loc_cnt > 0):
        Device.icloud_update_reason = ''

    elif (Device.is_online
            and Device.next_update_secs == 0
            and (Device.sensor_zone == NOT_SET
                or Device.icloud_initial_locate_done is False)):
        Device.icloud_update_reason = f"Initial iCloud Locate@{Gb.this_update_time}"

    elif Device.icloud_update_retry_flag:
        Device.icloud_update_reason  = "Retrying Location Refresh"

    log_debug_msg(Device, Device.icloud_update_reason)
    return (Device.icloud_update_reason != '')

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Get iCloud device & location info when using the
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def request_icloud_data_update(Device):
    '''
    Extract the data needed to determine location, direction, interval,
    etc. from the iCloud data set.

    Sample data set is:
        {'isOld': False, 'isInaccurate': False, 'altitude': 0.0, 'positionType': 'Wifi',
        'latitude': 27.72690098883266, 'floorLevel': 0, 'horizontalAccuracy': 65.0,
        'locationType': '', 'timeStamp': 1587306847548, 'locationFinished': True,
        'verticalAccuracy': 0.0, 'longitude': -80.3905776599289}
    '''
    if (Gb.use_data_source_ICLOUD is False
            or Device.is_data_source_ICLOUD is False
            or Device.PyiCloud is None):
            # or Gb.PyiCloud is None):
        return False

    devicename = Device.devicename

    try:
        if Device.icloud_update_reason or Device.icloud_force_update_flag:
            Device.display_info_msg("Requesting iCloud Location Update")

            Device.icloud_devdata_useable_flag = update_PyiCloud_RawData_data(Device)

            if Gb.internet_connection_error:
                for Device in Gb.Devices:
                    Device.pause_tracking
                return False

            # Retry in an error occurs
            if (Device.icloud_devdata_useable_flag is False
                    and Device.icloud_initial_locate_done is False):
                Device.icloud_devdata_useable_flag = update_PyiCloud_RawData_data(Device)

            if Device.icloud_devdata_useable_flag is False:
                Device.display_info_msg("iCloud Location Not Available")
                if Gb.icloud_acct_error_cnt > 5:
                    error_msg = (f"iCloud3 Error > No Location Returned for {devicename}. "
                                    "iCloud may be down or there is an Authentication issue. ")
                    post_error_msg(Device.devicename, error_msg)

        return True


    except (PyiCloud2FARequiredException, PyiCloudAPIResponseException) as err:
        Device.icloud_acct_error_flag      = True
        Device.icloud_devdata_useable_flag = False

        # log_exception(err)
        error_msg = ("iCloud3 Location Request Error > An error occured refreshing the iCloud "
                        "Location. iCloud may be down or there is an internet connection "
                        f"issue. iCloud3 will try again later. ({err})")
        post_error_msg(Device.devicename, error_msg)

    except Exception as err:
        Device.icloud_acct_error_flag      = True
        Device.icloud_devdata_useable_flag = False

        # log_exception(err)

    return False

#----------------------------------------------------------------------------
def update_PyiCloud_RawData_data(Device, results_msg_flag=True):
    '''
    Refresh the location data for a device and all other dvices with the
    same tracking method.

    Input:  Device:     Device that wants to be updated. After getting the
                        data for that device, all other devices wth the
                        same trackin method are also updated since the data is available.
            results_msg_flag: True - Display the useability msg in the event_log
                        False - Do not display the results in the evemt_log.

    Return: True        The device data was updated successfully
            False       An api error occurred or no device data was retured returned
    '''

    try:
        if (Gb.use_data_source_ICLOUD is False
                or Device.is_data_source_ICLOUD is False
                or Device.PyiCloud is None):
            return False

        if Device.icloud_device_id is None:
            return False

        if pyicloud_ic3_interface.is_authentication_2fa_code_needed(Device.PyiCloud):
            if pyicloud_ic3_interface.authenticate_icloud_account(Device.PyiCloud, called_from='data_handler') is False:
                return False

        if is_PyiCloud_RawData_data_useable(Device, results_msg_flag=False):
            return update_device_with_latest_raw_data(Device)

        icloud_ok, icloud_loc_time_ok, icloud_gps_ok, icloud_secs, \
            icloud_gps_accuracy, icloud_time = \
                    _get_devdata_useable_status(Device, ICLOUD)

        if icloud_ok:
            return update_all_devices_wih_latest_raw_data(Device)

        # Refresh iCloud Data
        if Device.is_data_source_ICLOUD:
            if ((secs_since(Device.PyiCloud.last_refresh_secs) >= 5
                    and  (icloud_secs != Device.loc_data_secs
                        or Device.next_update_secs > (icloud_secs + 5)))
                    or Device.icloud_initial_locate_done is False):

                device_id = None if Device.PyiCloud.locate_all_devices else Device.icloud_device_id

                locate_all_devices, device_id = _locate_all_or_acct_owner(Device)
                #if Device.PyiCloud.DeviceSvc:
                    #Device.PyiCloud.DeviceSvc.refresh_client(   requested_by_devicename=Device.devicename,
                Device.PyiCloud.refresh_icloud_data(requested_by_devicename=Device.devicename,
                                                    locate_all_devices=locate_all_devices,
                                                    device_id=device_id)
        if (Device.PyiCloud.response_code == 503
                    and Device.devicename not in Gb.username_pyicloud_503_connection_error):
                list_add(Gb.username_pyicloud_503_connection_error, Device.devicename)
                post_event( f"{EVLOG_ERROR}Apple Acct > {Device.PyiCloud.account_owner}, "
                            f"Refresh Location Data Failed, Connection Error 503, Will "
                            f"try to reconnect in 15-min")

        if update_all_devices_wih_latest_raw_data(Device) is False:
            return False

        if is_PyiCloud_RawData_data_useable(Device, results_msg_flag=False) is False:
            return False

        if (Device.moved_since_last_update_km < .0005):
            return False

        return True

    except (PyiCloud2FARequiredException, PyiCloudAPIResponseException) as err:
        try:
            _err_msg = HTTP_RESPONSE_CODES.get(Device.PyiCloud.Session.response_code,
                            'Unknown Error')

            Device.icloud_acct_error_flag      = True
            Device.icloud_devdata_useable_flag = False

            error_msg = (f"{EVLOG_ALERT}iCloud3 Location Request Error > An error occured "
                        f"refreshing the iCloud Location. iCloud may be down or there is an "
                        f"internet connection issue. iCloud3 will try again later. "
                        f"{CRLF_DOT}{_err_msg}, "
                        f"Error-{Device.PyiCloud.Session.response_code}")
                        # f"Error-{Gb.PyiCloud.Session.response_code}")

            post_event(Device, error_msg)
            post_error_msg(error_msg)

        except Exception as err:
            Device.icloud_acct_error_flag      = True
            Device.icloud_devdata_useable_flag = False
            # log_exception(err)

        return False

#----------------------------------------------------------------------------
def _locate_all_or_acct_owner(Device):
    '''
    Determine how the refresh_client should be done:
        - Locate all devices (the owners devices and icloud devices)
        - locate only the devie requesting the locate (an owners device)

    Returns:
        - [locate_all_devices, device_id]
    '''
    PyiCloud = Device.PyiCloud
    device_id = None if PyiCloud.locate_all_devices else Device.icloud_device_id

    _Device = det_interval.device_will_update_in_15secs(Device=Device, only_icloud_devices=True)

    # # If another device will update and that device is an owners device, set it to None
    # # since it will update when the owners device updates
    # if _Device and _Device.family_share_device is False:
    #     _Device = None

    # Locate_all override is enabled or
    # locate_all=False but Locating a iCloud device (not in the owners device_id list) or
    # Locate_all=False and updating an owners device but iCloud will update soon
    if (PyiCloud.locate_all_devices
            or Device.family_share_device
            or _Device):
        locate_all_devices = True
        refresh_device_id = None

    # Updating an owners device
    else:
        locate_all_devices = False
        refresh_device_id = device_id

    return (locate_all_devices, refresh_device_id)

#----------------------------------------------------------------------------
def update_all_devices_wih_latest_raw_data(Device):
    update_device_with_latest_raw_data(Device, all_devices=True)

def update_device_with_latest_raw_data(Device, all_devices=False):
    '''
    Update a Device's location data with the latest data from FamSshr or the MobApp
    if is is better or newer than the old data. Optionally, cycle thru all PyiCloud
    Devices and update the data for every device being tracked or monitored when
    new data is requested for a device since iCloud gives us data for all devices.

    Display a msg in the EvLog showing location times for all available data methods
    and the one selecetd.
    '''
    try:
        save_evlog_prefix, Gb.trace_prefix = Gb.trace_prefix, "LOCATE"
        if all_devices:
            Update_Devices = Gb.Devices
            # log_start_finish_update_banner('start', Device.devicename, 'Update All Devices from RawData', '')
        else:
            Update_Devices = [Device]

        for _Device in Update_Devices:
            if _Device.verified_flag and _Device.is_data_source_ICLOUD:
                _RawData = get_icloud_PyiCloud_RawData_to_use(_Device)
                if _RawData is None:
                    continue
            else:
                continue

            # Make sure data is really a available
            try:
                latitude = _RawData.device_data[LOCATION][LATITUDE]
            except Exception as err:
                rawdata_msg = 'No Location data'
                if _RawData:
                    log_rawdata(f"iCloud - {rawdata_msg}-{_Device.devicename}/{_Device.is_data_source_ICLOUD}",
                                {'filter': _RawData.device_data})
                continue
                # log_exception(err)

            requesting_device_flag = (_Device.devicename == Device.devicename)

            icloud_ok, icloud_loc_time_ok, icloud_gps_ok, icloud_secs, \
                icloud_gps_accuracy, icloud_time = \
                    _get_devdata_useable_status(Device, ICLOUD)

            # Add info for the Device that requested the update
            _Device.icloud_acct_error_flag = False
            if is_PyiCloud_RawData_data_useable(Device, results_msg_flag=False) is False:
                if _Device is Device:
                    if (_Device.is_offline
                            # Beta 6-Added _RawData.gps_accuracy test
                            or _RawData.gps_accuracy > Gb.gps_accuracy_threshold
                            or (_Device.is_location_good
                                and _Device.is_data_source_ICLOUD
                                and _Device.loc_data_time > _RawData.location_time
                                and _Device.loc_data_gps_accuracy < _RawData.gps_accuracy)):

                        if (Device.old_loc_cnt % 5) == 2:
                            if Device.no_location_data:
                                reason_msg = f"No Location Data, "
                            else:
                                reason_msg = (  f"NewData-{_RawData.location_time}/±{_RawData.gps_accuracy:.0f}m "
                                                f"vs {_Device.loc_data_time_gps}, ")
                            post_event(_Device,
                                        f"Rejected  #{Device.old_loc_cnt} > "
                                        f"{reason_msg}"
                                        f"Updated-{_RawData.data_source} data, "
                                        f"{Device.device_status_msg}")

            if (_RawData is None
                    or (_RawData.location_secs == 0 and _Device.mobapp_data_secs == 0)
                    or _RawData.gps_accuracy > Gb.gps_accuracy_threshold):
                pass

            # Move the newest data from PyiCloud_RawData or the MobApp data to the _Device's data fields
            # But, if there is a location error, select iCloud data so it will do another request
            elif (_RawData.location_secs >= _Device.mobapp_data_secs
                    or _Device.old_loc_cnt > 0):
                if _RawData.location_secs != _Device.loc_data_secs:
                    _Device.moved_since_last_update_km = \
                            _Device.distance_km(_RawData.device_data[LOCATION][LATITUDE],
                                                    _RawData.device_data[LOCATION][LONGITUDE])

                    # Move data from PyiCloud_RawData
                    _Device.update_dev_loc_data_from_raw_data_ICLOUD(_RawData,
                                                    requesting_device_flag=requesting_device_flag)

            elif _Device.mobapp_data_secs > 0:
                if _Device.mobapp_data_secs != _Device.loc_data_secs:
                    _Device.moved_since_last_update_km = \
                                _Device.distance_km(_Device.mobapp_data_latitude,
                                                    _Device.mobapp_data_longitude)

                    # Move data from Mobile App
                    _Device.update_dev_loc_data_from_raw_data_MOBAPP()

            # The update data msg is only displayed when the requesting Device is updated so the msg
            # for the Device being updated was never displayed even though the data was updated
            # Display it now.
            elif requesting_device_flag and all_devices is False:
                Device.display_update_location_msg()

            # If Rejected msg being displayed, no need to display the Old Loc msg too
            if Device.is_location_old_or_gps_poor:
                continue

            # This fct may be run a second time to recheck loc times for different data
            # sources. Don't redisplay it it's nothing changed.
            if _Device.loc_msg_icloud_mobapp_time == \
                        (f"{_Device.dev_data_source}-"
                        f"{_Device.loc_data_time_gps}-"
                        f"{_Device.mobapp_data_time_gps}"):
                continue
            _Device.loc_msg_icloud_mobapp_time = \
                (f"{_Device.dev_data_source}-"
                f"{_Device.loc_data_time_gps}-"
                f"{_Device.mobapp_data_time_gps}")

            other_times = ""
            if icloud_secs > 0 and Gb.used_data_source_ICLOUD and _Device.dev_data_source != 'iCloud':
                other_times += f"iCloud-{icloud_time}"

            if _Device.mobapp_monitor_flag and _Device.dev_data_source != 'MobApp':
                if other_times != "": other_times += ", "
                other_times += f"MobApp-{_Device.mobapp_data_time_gps}"

            # Display location times for the selected device and all other data sources
            # (icloud or mobapp). Display in Event log if the requesting device or a monitor
            # msg if another device. Don't redisplay this msg if the data was just updated
            # within the last 5-secs but running through this routine again.
            if secs_since(_Device.loc_data_secs) <= _Device.old_loc_threshold_secs + 5:
                event_msg =(f"Located > "
                            f"{_Device.dev_data_source}-"
                            f"{_Device.loc_data_time_gps} "
                            f"({format_age(_Device.loc_data_secs)}), "
                            f"{other_times}")

                if _Device.is_offline:
                    event_msg += f", DeviceStatus-{_Device.device_status}"

                if requesting_device_flag:
                    post_event(_Device, event_msg)
                else:
                    post_monitor_msg(_Device, event_msg)

        #pyicloud_ic3_interface.display_authentication_msg(Device.PyiCloud)
        # pyicloud_ic3_interface.display_authentication_msg(Gb.PyiCloud)
        Gb.trace_prefix = save_evlog_prefix

        return True

    except Exception as err:
        log_exception(err)

        return False

#----------------------------------------------------------------------------
def is_PyiCloud_RawData_data_useable(Device, results_msg_flag=True):
    '''
    Cycle thru the raw PyiCloud_RawData and see if the location times for all of the
    tracked devices is old.

    Rteurn:
        True - The data for the device is acceptible
        False - The data for Device is old
    '''

    icloud_ok, icloud_loc_time_ok, icloud_gps_ok, icloud_secs, \
        icloud_gps_accuracy, icloud_time = \
                    _get_devdata_useable_status(Device, ICLOUD)

    if Gb.icloud_force_update_flag or Device.icloud_force_update_flag:
        Gb.icloud_force_update_flag = False
        is_useable_flag = False
        useable_msg     = 'Update Required'
        return False

    if icloud_ok:
        is_useable_flag = True
        useable_msg     = 'Useable'
    elif icloud_loc_time_ok is False:
        is_useable_flag = False
        useable_msg     = 'Data-Old'
    elif icloud_gps_ok is False:
        is_useable_flag = False
        useable_msg     = 'Data-PoorGps'

    if results_msg_flag is False:
        return is_useable_flag

    data_type = 'iCloud'

    event_msg = f"{data_type} {useable_msg} > "
    if icloud_secs > 0 and Gb.used_data_source_ICLOUD:
        event_msg += f"iCloud-{icloud_time}, "
    if is_useable_flag is False:
        event_msg += "Requesting New Location"

    if results_msg_flag:
        post_event(Device, event_msg)
    else:
        post_monitor_msg(Device.devicename, event_msg)
    return is_useable_flag

#----------------------------------------------------------------------------
def _get_devdata_useable_status(Device, data_source):
    '''
    Determine the useable status of the RawData location data. Check the time and the gps.

    Returns:
        time_useable_flag - the age of the location_secs is under the threshold,
        gps_useable_flag - the gps accuracy is under the threshold
        time_age_string - the formatted time 'hh:mm:ss (xxx ago)'
    '''

    if Device.dev_data_useable_chk_secs == Gb.this_update_secs:
        return Device.dev_data_useable_chk_results

    loc_time_ok     = False
    gps_accuracy_ok = False
    loc_secs        = 0
    gps_accuracy    = 0
    time_str        = ''
    device_id       = None
    RawData         = None

    if data_source == ICLOUD:
        RawData = Device.PyiCloud_RawData_icloud
        device_id = Device.icloud_device_id
    else:
        return False, False, False, 0, 0, ''

    if device_id is None or RawData is None or RawData.location is None:
        return False, False, False, 0, 0, ''

    # rc7.1 Added icloud_force_update_flag check
    loc_secs     = RawData.location_secs
    loc_age_secs = secs_since(loc_secs)
    loc_time_ok  = ((loc_age_secs <= Device.old_loc_threshold_secs) and Device.icloud_force_update_flag is False)

    # If loc time is under threshold, check to see if the loc time is older than the interval
    # The interval may be < 15 secs if just trying to force a quick update with the current data. If so, do not check it
    if (loc_time_ok
            and Device.FromZone_BeingUpdated.interval_secs >= 15
            and Device.is_passthru_timer_set is False):
        loc_time_ok = (Device.FromZone_BeingUpdated.interval_secs > loc_age_secs)

        # rc9 Added loc_age_secs check so msg is only displayed after 20-secs
        if loc_time_ok is False and loc_age_secs > 20:
            event_msg = f"iCloud Loc > Refresh Needed, "
            if Device.loc_data_secs == Device.last_update_loc_secs:
                event_msg += "Location not Updated"
            else:
                event_msg+=(f"Age-{format_timer(loc_age_secs)} "
                            f"(> {format_timer(Device.FromZone_BeingUpdated.interval_secs)})")
            post_event(Device, event_msg)

    gps_accuracy_ok = RawData.is_gps_good
    gps_accuracy    = round(RawData.gps_accuracy)
    time_str        = f"{secs_to_time(loc_secs)}"
    if gps_accuracy_ok is False:
        time_str += f"/±{gps_accuracy}m"
    useable_data    = (loc_time_ok and gps_accuracy_ok)

    Device.dev_data_useable_chk_secs    = Gb.this_update_secs
    Device.dev_data_useable_chk_results = [useable_data, loc_time_ok, gps_accuracy_ok, loc_secs, gps_accuracy, time_str]


    # return useable_data, loc_time_ok, gps_accuracy_ok, loc_secs, gps_accuracy, time_str
    return Device.dev_data_useable_chk_results

#----------------------------------------------------------------------------
def get_icloud_PyiCloud_RawData_to_use(_Device):
    '''
    Analyze tracking method and location times from the raw PyiCloud device data
    to get best data to use

    Return:
        _RawData - The PyiCloud_RawData (_icloud) data object
    '''
    try:
        _RawData_icloud = _Device.PyiCloud.RawData_by_device_id.get(_Device.icloud_device_id)

        if _RawData_icloud is None:
            _RawData = None
            _Device.data_source = MOBAPP
            return

        _RawData = _RawData_icloud

        error_msg = ''
        if _RawData is None:
            error_msg = 'Web Svc not set up'
        elif _RawData.device_data is None:
            error_msg = 'No Device Data'
        elif LOCATION not in _RawData.device_data:
            error_msg = 'No Location Data'
        elif _RawData.device_data[LOCATION] == {}:
            error_msg = 'Location Data Empty'
        elif _RawData.device_data[LOCATION] is None:
            error_msg = 'Location Data Empty'
        elif _Device.is_tracking_paused:
            error_msg = 'Paused'

        if error_msg:
            if Gb.log_debug_flag:
                event_msg =(f"Location data not updated > {error_msg}, Will Retry")
                post_monitor_msg(_Device.devicename, event_msg)
            _RawData = None

        return _RawData

    except Exception as err:
        # log_exception(err)
        post_error_msg("iCloud3 Error > Error extracting device info from Apple Acct data, "
                        f"Device-{_Device.fname_devicename}, "
                        f"AppleAcct-{_Device.conf_apple_acct_username}. "
                        f"iCloudName-{_Device.conf_icloud_dname}")
        return None
