from ..global_variables     import GlobalVariables as Gb
from ..const                import (NOT_SET, IC3LOG_FILENAME,
                                    CRLF, CRLF_DOT, CRLF_HDOT, CRLF_X, NL, NL_DOT,
                                    EVLOG_ALERT, EVLOG_ERROR, EVLOG_IC3_STARTING, EVLOG_IC3_STAGE_HDR,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    CONF_VERSION, ICLOUD_FNAME, ZONE_DISTANCE,
                                    FAMSHR_FNAME, FMF_FNAME, MOBAPP_FNAME,
                                    )

from ..support              import hacs_ic3
from ..support              import start_ic3
from ..support              import config_file
#from ..support              import pyicloud_ic3_interface
from ..support              import icloud_data_handler
from ..support              import determine_interval as det_interval

from ..helpers.common       import (instr, obscure_field, list_to_str, )
from ..helpers.messaging    import (broadcast_info_msg,
                                    post_event, post_error_msg, log_error_msg, post_startup_alert,
                                    post_monitor_msg, post_internal_error,
                                    log_start_finish_update_banner,
                                    log_debug_msg, log_warning_msg, log_info_msg, log_exception, log_rawdata,
                                    _trace, _traceha, more_info, format_filename,
                                    write_config_file_to_ic3log,
                                    open_ic3log_file, )
from ..helpers.time_util    import (time_now_secs, calculate_time_zone_offset, )

import homeassistant.util.dt as dt_util
import os


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_1_setup_variables():

    # new_log_file=False
    # ic3logger_file = Gb.hass.config.path(IC3LOG_FILENAME)
    # filemode = 'w' if (new_log_file or os.path.isfile(ic3logger_file) is False) else 'a'
    Gb.trace_prefix = 'STAGE1'
    stage_title = f'Stage 1 > Initial Preparations'

    open_ic3log_file()
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    broadcast_info_msg(stage_title)

    #check to see if restart is in process
    #if Gb.start_icloud3_inprocess_flag:
    #    return

    Gb.EvLog.display_user_message(f'iCloud3 v{Gb.version} > Initializiing')

    try:
        # Gb.start_icloud3_inprocess_flag = True
        # Gb.restart_icloud3_request_flag = False
        # Gb.all_tracking_paused_flag     = False
        Gb.this_update_secs             = time_now_secs()
        Gb.startup_alerts               = []
        Gb.EvLog.alert_message          = ''
        Gb.config_track_devices_change_flag = False
        Gb.reinitialize_icloud_devices_flag = False     # Set when no devices are tracked and iC3 needs to automatically restart
        Gb.reinitialize_icloud_devices_cnt  = 0

        if Gb.initial_icloud3_loading_flag is False:
            Gb.EvLog.startup_event_recds = []
            Gb.EvLog.startup_event_save_recd_flag = True
            post_event( f"{EVLOG_IC3_STARTING}iCloud3 v{Gb.version} > Restarting, "
                        f"{dt_util.now().strftime('%A, %b %d')}")

        config_file.load_storage_icloud3_configuration_file()
        write_config_file_to_ic3log()
        start_ic3.initialize_global_variables()
        start_ic3.set_global_variables_from_conf_parameters()

        start_ic3.define_tracking_control_fields()

        if Gb.ha_config_directory != '/config':
            post_event(f"Base Config Directory > {Gb.ha_config_directory}")
        post_event(f"iCloud3 Directory > {Gb.icloud3_directory}")
        if Gb.conf_profile[CONF_VERSION] == 0:
            post_event(f"iCloud3 Configuration File > {format_filename(Gb.config_ic3_yaml_filename)}")
        else:
            post_event(f"iCloud3 Configuration File > {format_filename(Gb.icloud3_config_filename)}")

        start_ic3.display_platform_operating_mode_msg()
        Gb.hass.loop.create_task(start_ic3.update_lovelace_resource_event_log_js_entry())
        Gb.hass.loop.create_task(hacs_ic3.check_hacs_icloud3_update_available())
        start_ic3.check_ic3_event_log_file_version()

        post_monitor_msg(f"LocationInfo-{Gb.ha_location_info}")

        calculate_time_zone_offset()
        start_ic3.set_event_recds_max_cnt()

        post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_2_prepare_configuration():

    Gb.trace_prefix = 'STAGE2'
    stage_title = f'Stage 2 > Prepare Support Services'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        if Gb.initial_icloud3_loading_flag is False:
            Gb.PyiCloud = None

        # start_ic3.initialize_global_variables()
        # start_ic3.set_global_variables_from_conf_parameters()
        start_ic3.create_Zones_object()
        start_ic3.create_Waze_object()

        Gb.WazeHist.load_track_from_zone_table()

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.update_event_log_display("")

    try:
        configuration_needed_msg = ''
        # Default configuration that has not been updated or migrated from v2
        if Gb.conf_profile[CONF_VERSION] == -1:
            configuration_needed_msg = 'INITIAL INSTALLATION - CONFIGURATION IS REQUIRED'

        elif Gb.conf_profile[CONF_VERSION] == 0:
            configuration_needed_msg = 'CONFIGURATION PARAMETERS WERE MIGRATED FROM v2 to v3 - ' \
                                        'THEY MUST BE REVIEWED BEFORE STARTING ICLOUD3'
        elif Gb.conf_devices == []:
            configuration_needed_msg = 'DEVICES MUST BE SET UP TO ENABLE TRACKING'

        if configuration_needed_msg:
            post_startup_alert('iCloud3 Integration not set up')
            event_msg =(f"{EVLOG_ALERT}CONFIGURATION ALERT > {configuration_needed_msg}{CRLF}"
                        f"{more_info('add_icloud3_integration')}")
            post_event(event_msg)

            Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)

    #write_debug_log()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_3_setup_configured_devices():

    Gb.trace_prefix = 'STAGE3'
    stage_title = f'Stage 3 > Prepare Configured Devices'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        # Make sure a full restart is done if all of the devices were not found in the iCloud data
        data_sources = ''
        if Gb.conf_data_source_FAMSHR: data_sources += f"{FAMSHR_FNAME}, "
        # if Gb.conf_data_source_FMF   : data_sources += f"{FMF_FNAME}, "
        if Gb.conf_data_source_MOBAPP: data_sources += f"{MOBAPP_FNAME}, "
        data_sources = data_sources[:-2] if data_sources else 'NONE'
        post_event(f"Data Sources > {data_sources}")

        if Gb.config_track_devices_change_flag:
            pass
        # elif (Gb.conf_data_source_FMF
        #         and Gb.fmf_device_verified_cnt < len(Gb.Devices)):
        #     Gb.config_track_devices_change_flag = True
        elif (Gb.conf_data_source_FAMSHR
                and Gb.famshr_device_verified_cnt < len(Gb.Devices)):
            Gb.config_track_devices_change_flag = True
        elif Gb.log_debug_flag:
            Gb.config_track_devices_change_flag = True

        start_ic3.create_Devices_object()

    except Exception as err:
        log_exception(err)

    #write_debug_log()

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.update_event_log_display("")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_4_setup_data_sources(retry=False):

    Gb.trace_prefix = 'STAGE4'
    stage_title = f"Stage 4 > Setup iCloud & MobApp Data Source"
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    # Missing username/password, PyiCloud can not be started
    if Gb.primary_data_source_ICLOUD:
        if Gb.username == '' or Gb.password == '':
            Gb.conf_data_source_FAMSHR = False
            Gb.conf_data_source_FMF    = False
            Gb.primary_data_source_ICLOUD = False
            post_startup_alert('iCloud username/password invalid or not set up')
            post_event( f"{EVLOG_ALERT}CONFIGURATION ALERT > The iCloud username or password has not been "
                        f"set up or is incorrect. iCloud will not be used for location tracking")

    return_code = True
    Gb.EvLog.display_user_message(stage_title)
    broadcast_info_msg(stage_title)

    try:
        if Gb.primary_data_source_ICLOUD:
            account_name = Gb.PyiCloud.account_name if Gb.PyiCloud else ''
            post_event(f"iCloud Account > Logging Into-{account_name} "
                       f"({obscure_field(Gb.username)})")
            start_ic3.setup_data_source_ICLOUD()

        if Gb.PyiCloud is None:
            post_event('iCloud Location Service > Not used as a data source')
        elif Gb.PyiCloud.account_locked:
            post_error_msg( f"{EVLOG_ERROR}iCloud Account is Locked. Log onto www.icloud.com "
                            f"and unlock your account to reauthorize location services. ")
            post_startup_alert('iCloud Account is Locked')

        if Gb.conf_data_source_MOBAPP:
            start_ic3.setup_tracked_devices_for_mobapp()
        else:
            post_event('Mobile App > Not used as a data source')

        start_ic3.set_devices_verified_status()
        return_code = _are_all_devices_verified(retry=retry)

    except Exception as err:
        log_exception(err)
        return_code = False

    # write_debug_log()

    post_event(f"{EVLOG_IC3_STAGE_HDR} {stage_title}")
    Gb.EvLog.update_event_log_display("")

    return return_code

#------------------------------------------------------------------
def _are_all_devices_verified(retry=False):
    '''
    See if all tracked devices are verified.

    Arguments:
        retry   - True  - The verification was retried
                - False - This is the first time the verification was done

    Return:
        True  - All were verifice
        False - Some were not verified
    '''

    # Get a list of all tracked devices that have not been set p by icloud or the Mobile App
    unverified_devices = [devicename
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if Device.verified_flag is False]

    if unverified_devices == []:
        return True

    if retry:
        post_startup_alert('Some devices could not be verified. Restart iCloud3')
        event_msg = (f"{EVLOG_ALERT}Some devices could not be verified. iCloud3 needs to be "
                        f"restarted to see if the unverified devices are available for "
                        f"tracking. If not, check the device parameters in the iCloud3 Configure Settings:"
                        f"{more_info('configure_icloud3')}")
    else:
        event_msg = (f"{EVLOG_ALERT}ALERT > Some devices could not be verified. iCloud Location Service "
                        f"will be reinitialized")
    event_msg += (f"{CRLF_DOT}Unverified Devices > {', '.join(unverified_devices)}")
    post_event(event_msg)

    return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_5_configure_tracked_devices():

    Gb.trace_prefix = 'STAGE5'
    stage_title = f'Stage 5 > Device Configuration Summary'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    if Gb.PyiCloud:
        log_debug_msg(f"PyiCloud Instance Finialized > {Gb.PyiCloud.instance}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        # start_ic3.remove_unverified_untrackable_devices()
        start_ic3.identify_tracked_monitored_devices()
        Gb.EvLog.setup_event_log_trackable_device_info()

        start_ic3.setup_trackable_devices()
        start_ic3.display_inactive_devices()
        Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)

    # write_debug_log()

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.display_user_message('')

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_6_initialization_complete():

    Gb.trace_prefix = 'STAGE6'
    stage_title = f'iCloud3 Initialization Complete'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    broadcast_info_msg(stage_title)

    start_ic3.display_platform_operating_mode_msg()
    Gb.EvLog.display_user_message('')

    Gb.startup_log_msgs = ''

    try:
        start_ic3.display_object_lists()
        start_ic3.write_debug_log()

        if Gb.startup_alerts:
            item_no = 1
            alert_msg = ''
            for alert in Gb.startup_alerts:
                alert_msg += f"{CRLF}{item_no}. {alert}"
                item_no += 1

            # Build alert msg for the evlog.attrs['alert_startup'] attribute for display
            alerts_str = alert_msg.replace(CRLF_HDOT, NL_DOT)
            alerts_str = alerts_str.replace(CRLF_X, NL_DOT)
            alerts_str = alerts_str.replace(CRLF, NL)
            Gb.startup_alerts_str = alerts_str

            Gb.EvLog.alert_message = 'Problems occured during startup up that should be reviewed'
            post_event( f"{EVLOG_ALERT}The following issues were detected when starting iCloud3. "
                        f"Scroll through the Startup Log for more information: "
                        f"{alert_msg}")

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_7_initial_locate():
    '''
    The PyiCloud Authentication function updates the FamShr raw data after the account
    has been authenticated. Requesting the initial data update there speeds up loading iC3
    since the iCloud acct login & authentication was started in the __init__ module.

    This routine processes the new raw FamShr data and set the initial location.

    If there are devices that use FmF and not FamShr, the FamF data will be requested
    and those devices will be updated.
    '''


    # The restart will be requested if using iCloud as a data source and no data was returned
    # from PyiCloud
    if Gb.PyiCloud is None:
            return

    if Gb.reinitialize_icloud_devices_flag and Gb.conf_famshr_device_cnt > 0:
        return_code = reinitialize_icloud_devices()

    Gb.trace_prefix = '1stLOC'

    Gb.this_update_secs = time_now_secs()
    Gb.this_update_time = dt_util.now().strftime('%H:%M:%S')
    post_event("Requesting Initial Locate")
    post_event(f"{EVLOG_IC3_STARTING}iCloud3 v{Gb.version} > Start up Complete")

    for Device in Gb.Devices:
        if Device.PyiCloud_RawData_famshr:
            Device.update_dev_loc_data_from_raw_data_FAMSHR_FMF(Device.PyiCloud_RawData_famshr)

        elif Device.PyiCloud_RawData_fmf:
            icloud_data_handler.update_PyiCloud_RawData_data(Device, results_msg_flag=False)
            Device.update_dev_loc_data_from_raw_data_FAMSHR_FMF(Device.PyiCloud_RawData_fmf)

        else:
            continue

        post_event(Device,
                    f"{Device.dev_data_source} Trigger > Initial Locate@"
                    f"{Device.loc_data_time_gps}")

        if Device.no_location_data:
            post_event(Device, f"{EVLOG_ALERT}NO GPS DATA RETURNED FROM ICLOUD LOCATION SERVICE")
            error_msg = (f"iCloud3 > {Device.fname_devicename} > "
                        "No GPS data was returned from iCloud Location "
                        "Service on the initial locate")
            log_warning_msg(error_msg)

        Device.update_sensors_flag = True

        Gb.iCloud3.process_updated_location_data(Device, ICLOUD_FNAME)

        Device.icloud_initial_locate_done = True

#------------------------------------------------------------------
def reinitialize_icloud_devices():
    '''
    Setup restarting iCloud3 if it has not already been done.

    Return  - True - Continue with Initial Locate
            - False - Restart failes
    '''
    try:
        if Gb.PyiCloud is None:
            return

        Gb.reinitialize_icloud_devices_cnt += 1
        if Gb.reinitialize_icloud_devices_cnt > 2:
            return

        Gb.start_icloud3_inprocess_flag = False
        Gb.reinitialize_icloud_devices_flag = False
        Gb.initial_icloud3_loading_flag = False
        Gb.all_tracking_paused_flag = True

        alert_msg = f"{EVLOG_ALERT}"
        if Gb.conf_data_source_ICLOUD:
            unverified_devices = [devicename for devicename, Device in Gb.Devices_by_devicename.items() \
                                            if Device.verified_flag is False]
            alert_msg +=(f"UNVERIFIED DEVICES > One or more devices was not verified. iCloud Location Svcs "
                        f"may be down, slow to respond or the internet may be down."
                        f"{CRLF_DOT}Unverified Devices > {', '.join(unverified_devices)}")

        post_event(alert_msg)

        post_event(f"{EVLOG_IC3_STARTING}Restarting iCloud Location Service")

        if Gb.PyiCloud and Gb.PyiCloud.FamilySharing:
            Gb.PyiCloud.FamilySharing.refresh_client()

        stage_4_success = stage_4_setup_data_sources(retry=None)
        if stage_4_success is False:
            stage_4_success = stage_4_setup_data_sources()

        stage_5_configure_tracked_devices()
        stage_6_initialization_complete()

        Gb.all_tracking_paused_flag = False

        if stage_4_success is False:
            post_event( f"{EVLOG_ALERT}UNVERIFIED DEVICES > One or more devices was still "
                        f"not verified"
                        f"{more_info('unverified_devices_caused_by')}")

        return False

    except Exception as err:
        log_exception(err)

    return