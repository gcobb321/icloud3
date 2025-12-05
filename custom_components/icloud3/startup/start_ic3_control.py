from ..global_variables import GlobalVariables as Gb
from ..const            import (VERSION, VERSION_BETA, ICLOUD3, ICLOUD3_VERSION, DOMAIN, ICLOUD3_VERSION_MSG,
                                NOT_SET, IC3LOG_FILENAME,
                                CRLF, CRLF_DOT, CRLF_HDOT, CRLF_LDOT, CRLF_X, CRLF_RED_ALERT,
                                NL, NL_DOT, LINK, YELLOW_ALERT, RED_ALERT, CRLF_CHK,
                                EVLOG_ALERT, EVLOG_ERROR, EVLOG_IC3_STARTING, EVLOG_IC3_STAGE_HDR, NBSP6, DOT,
                                ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                CONF_VERSION, ICLOUD, ZONE_DISTANCE,
                                CONF_USERNAME, CONF_PASSWORD, CONF_LOCATE_ALL, CONF_SERVER_LOCATION,
                                ICLOUD, MOBAPP, DISTANCE_TO_DEVICES,
                                )

from ..utils.utils      import (instr, is_empty, isnot_empty, yes_no, list_to_str, list_add, list_del,
                                username_id, is_running_in_event_loop, )
from ..utils.messaging  import (broadcast_info_msg,
                                post_event, post_alert, post_error_msg, log_error_msg, update_alert_sensor,
                                post_monitor_msg, post_internal_error, post_greenbar_msg,
                                write_ic3log_recd,
                                log_debug_msg, log_warning_msg, log_info_msg, log_exception, log_data,
                                _evlog, _log, more_info, format_filename,
                                write_config_file_to_ic3log,
                                open_ic3log_file, )
from ..utils.time_util  import (time_now, time_now_secs, secs_to_time, format_day_date_now, )

from ..apple_acct       import apple_acct_support as aas
from ..mobile_app       import mobapp_interface
from ..startup          import start_ic3
from ..startup          import config_file
from ..tracking         import determine_interval as det_interval

#--------------------------------------------------------------------
import homeassistant.util.dt as dt_util


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_1_setup_variables():

    Gb.trace_prefix = 'STAGE1'
    stage_title = f'Stage 1 > Initial Preparations'

    open_ic3log_file()

    log_info_msg(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")

    broadcast_info_msg(stage_title)

    Gb.EvLog.display_user_message(f'iCloud3 v{Gb.version} > Initializiing')

    try:
        Gb.EvLog.alert_message          = ''
        Gb.config_track_devices_change_flag = False
        Gb.reinitialize_icloud_devices_flag = False     # Set when no devices are tracked and iC3 needs to automatically restart
        Gb.reinitialize_icloud_devices_cnt  = 0

        config_file.load_icloud3_configuration_file()
        write_config_file_to_ic3log()
        start_ic3.initialize_global_variables()
        start_ic3.set_global_variables_from_conf_parameters()

        # Run these setup items on a restart. Do not then when initially starting iC3
        if Gb.initial_icloud3_loading_flag is False:
            Gb.EvLog.startup_event_recds = []
            Gb.EvLog.startup_event_save_recd_flag = True
            post_event( f"{EVLOG_IC3_STARTING}Restarting > {ICLOUD3_VERSION_MSG}, "
                        f"{format_day_date_now()}")

        if Gb.ha_config_directory != '/config':
            post_event(f"Base Config Directory > {CRLF_DOT}{Gb.ha_config_directory}")
        post_event(f"iCloud3 Directory > {CRLF_DOT}{Gb.icloud3_directory}")
        post_event(f"iCloud3 Configuration File >{CRLF_DOT}{format_filename(Gb.icloud3_config_filename)}")

        start_ic3.display_platform_operating_mode_msg()
        start_ic3.check_ic3_event_log_file_version()

        post_monitor_msg(f"LocationInfo-{Gb.ha_location_info}")

        start_ic3.set_event_recds_max_cnt()
        start_ic3.define_tracking_control_fields()

        post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.update_event_log_display("")

        # If the internet_error handler is in test mode, force an internet_error condition
        if Gb.test_internet_error:
            Gb.internet_error = True

    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_2_prepare_configuration():

    Gb.trace_prefix = 'STAGE2'
    stage_title = f'Stage 2 > Prepare Support Services'
    log_info_msg(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        start_ic3.create_Zones_object()
        start_ic3.create_Waze_object()

        Gb.WazeHist.load_track_from_zone_table()

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.update_event_log_display("")

    try:
        configuration_needed_msg = ''
        # Default configuration was installed
        if Gb.conf_profile[CONF_VERSION] == -1:
            configuration_needed_msg = 'INITIAL INSTALLATION - CONFIGURATION IS REQUIRED'

        elif Gb.conf_profile[CONF_VERSION] == 0:
            configuration_needed_msg = 'INITIAL CONFIGURATION PARAMETERS WERE INSTALLED - ' \
                                        'THEY MUST BE REVIEWED BEFORE STARTING ICLOUD3'
        elif ((is_empty(Gb.conf_apple_accounts) and Gb.conf_data_source_ICLOUD)
                or is_empty(Gb.conf_devices)):
            configuration_needed_msg = 'ICLOUD3 APPLE ACCT OR DEVICES HAVE NOT BEEN SETUP '

        if configuration_needed_msg:
            post_greenbar_msg('iCloud3 Configuration not set up')
            post_alert(f"{configuration_needed_msg}{CRLF}"
                        f"{more_info('configure_icloud3')}")

            Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_3_setup_configured_devices():

    Gb.trace_prefix = 'STAGE3'
    stage_title = f'Stage 3 > Device Configuration'
    log_info_msg(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        # Make sure a full restart is done if all of the devices were not found in the iCloud data
        Gb.startup_alerts_by_source = {}
        data_sources = f"Apple Account-{yes_no(Gb.conf_data_source_ICLOUD)}, "
        data_sources += f"Mobile App-{yes_no(Gb.conf_data_source_MOBAPP)}"
        post_event(f"Data Sources > {data_sources}")

        # Reinitialize AppleAcct to recreate all Apple Acct objects
        if Gb.restart_requested_by == 'user':
            aas.reset_AppleAcct_Gb_variables()

        # start_ic3.setup_validate_apple_accts_upw()
        Gb.ValidateAppleAcctUPW.validate_upw_all_apple_accts()

        if Gb.config_track_devices_change_flag:
            pass
        elif (Gb.conf_data_source_ICLOUD
                and Gb.icloud_device_verified_cnt < len(Gb.Devices)):
            Gb.config_track_devices_change_flag = True
        elif Gb.log_debug_flag:
            Gb.config_track_devices_change_flag = True

        start_ic3.create_Devices_object()

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.update_event_log_display("")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_4_setup_data_sources():

    Gb.trace_prefix = 'STAGE4'
    stage_title = f"Stage 4 > Connect to Apple Accounts"
    log_info_msg(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.display_user_message(stage_title)
    broadcast_info_msg(stage_title)

    for Device in Gb.Devices:
        Device.set_fname_alert('')

    data_sources = f"Apple Account-{yes_no(Gb.conf_data_source_ICLOUD)}, "
    data_sources += f"Mobile App-{yes_no(Gb.conf_data_source_MOBAPP)}"
    post_event(f"Data Sources > {data_sources}")

    # UPW was validated in Stage 3, Redisplay results
    post_event(Gb.ValidateAppleAcctUPW.valid_upw_results_msg)

    try:
        # Get list of all unique Apple Acct usernames in config
        Gb.conf_usernames = [apple_account[CONF_USERNAME]
                                    for apple_account in Gb.conf_apple_accounts
                                    if (apple_account[CONF_USERNAME] in Gb.valid_upw_by_username
                                            and apple_account[CONF_USERNAME] != '')]

        if Gb.use_data_source_ICLOUD:
            # Password should already be validated, residual results
            if Gb.ValidateAppleAcctUPW and Gb.ValidateAppleAcctUPW.valid_upw_results_msg:
                post_event( f"Apple Acct > Verified Username-Password >"
                            f"{Gb.ValidateAppleAcctUPW.valid_upw_results_msg}")

            start_ic3.log_into_apple_accounts()
            start_ic3.setup_data_source_ICLOUD()

            for AppleAcct in Gb.AppleAcct_by_username.values():
                if AppleAcct.account_locked:
                    post_error_msg( f"{EVLOG_ERROR}Apple Account {AppleAcct.account_owner} "
                                    f"is Locked. Log onto www.icloud.com and unlock "
                                    f"your account to reauthorize location services.")
                    update_alert_sensor(AppleAcct.username_id, "Apple Acct is Locked")

        stage_title = f"Stage 4 > Connect to Mobile App Integration"
        log_info_msg(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.display_user_message(stage_title)

        mobapp_interface.get_entity_registry_mobile_app_devices()
        mobapp_interface.get_mobile_app_integration_device_info()

        if Gb.conf_data_source_MOBAPP:
            start_ic3.setup_tracked_devices_for_mobapp()

        stage_title = f"Stage 4 > Set up Apple & MobApp Data Sources"
        log_info_msg(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.display_user_message(stage_title)

        start_ic3.set_devices_verified_status()
        all_verified_flag = start_ic3.are_all_devices_verified()

    except Exception as err:
        log_exception(err)
        all_verified_flag = False

    post_event(f"{EVLOG_IC3_STAGE_HDR} {stage_title}")
    Gb.EvLog.update_event_log_display("")

    return all_verified_flag


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_5_configure_tracked_devices():

    Gb.trace_prefix = 'STAGE5'
    stage_title = f'Stage 5 > Device Configuration Summary'
    log_info_msg(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")

    if is_empty(Gb.conf_devices):
        post_event(f"No Devices have been set up")
    if is_empty(Gb.conf_apple_accounts):
        post_event(f"No Apple Accounts have been set up")

    for username, AppleAcct in Gb.AppleAcct_by_username.items():
        log_debug_msg(f"AppleAcct Finialized > {AppleAcct.account_owner}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        # start_ic3.remove_unverified_untrackable_devices()
        start_ic3.identify_tracked_monitored_devices()

        start_ic3.setup_trackable_devices()
        start_ic3.display_inactive_devices()
        start_ic3.display_all_devices_config_info()
        Gb.EvLog.setup_event_log_trackable_device_info()

    except Exception as err:
        log_exception(err)

    Gb.EvLog.update_event_log_display("")
    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.display_user_message('')


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_6_initialization_complete():

    Gb.trace_prefix = 'STAGE6'
    stage_title = f'{ICLOUD3} Initialization Complete'
    log_info_msg(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")

    broadcast_info_msg(stage_title)

    start_ic3.display_platform_operating_mode_msg()
    Gb.EvLog.display_user_message('')

    Gb.startup_log_msgs = ''

    try:
        start_ic3.display_object_lists()
        start_ic3.dump_startup_lists_to_log()
        alert_msg = ''
        if Gb.alerts_sensor_attrs:
            for source, msg in Gb.alerts_sensor_attrs.items():
                alert_msg += f"{CRLF_DOT}{source} > {msg}"

            Gb.EvLog.alert_message = 'Problems occured during startup up that should be reviewed'
            post_alert( f"The following issues were detected when starting iCloud3. "
                        f"Scroll through the Startup Log for more information: "
                        f"{alert_msg}")

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_7_initial_locate():
    '''
    The AppleAcct Authentication function updates the iCloud raw data after the account
    has been authenticated. Requesting the initial data update there speeds up loading iC3
    since the Apple Acct login & authentication was started in the __init__ module.

    This routine processes the new raw iCloud data and set the initial location.
    '''

    # The restart will be requested if using iCloud as a data source and no data was returned
    # from AppleAcct
    if is_empty(Gb.AppleAcct_by_username):
        return

    if Gb.reinitialize_icloud_devices_flag and Gb.conf_icloud_device_cnt > 0:
        return_code = reinitialize_icloud_devices()

    Gb.trace_prefix = '1stLOC'

    Gb.this_update_secs = time_now_secs()
    Gb.this_update_time = time_now()
    post_event("Requesting Initial Locate")

    for Device in Gb.Devices:
        post_greenbar_msg(f"Initial Locate > {Device.fname_devicename}")
        Device.update_sensors_flag = True
        Device.icloud_initial_locate_done = True

        if Device.AADevData_icloud:
            Device.update_dev_loc_data_from_raw_data_ICLOUD(Device.AADevData_icloud)
        else:
            continue

        Gb.iCloud3.process_updated_location_data(Device, ICLOUD)

        post_event(Device,
                    f"{Device.dev_data_source} Trigger > Initial Locate@"
                    f"{Device.loc_data_time_gps}")

        if Device.no_location_data:
            post_event(Device, f"{EVLOG_ALERT}NO GPS DATA RETURNED FROM ICLOUD LOCATION SERVICE")
            error_msg = (f"iCloud3 > {Device.fname_devicename} > "
                        "No GPS data was returned from iCloud Location "
                        "Service on the initial locate")
            log_warning_msg(error_msg)

    post_greenbar_msg('')


    # Update the distance between all devices not that they have all been located
    # Then go back through and update the device_tracker entity to set the distance
    # between devices for the first time
    det_interval.set_dist_to_devices(post_event_msg=True)
    for Device in Gb.Devices:
        Device.sensors[DISTANCE_TO_DEVICES] = \
                    det_interval.format_dist_to_devices_msg(Device, time=True, age=False)
        Device.write_ha_device_tracker_state()

#------------------------------------------------------------------
def reinitialize_icloud_devices():
    '''
    Setup restarting iCloud3 if it has not already been done.

    Return  - True - Continue with Initial Locate
            - False - Restart failes
    '''
    try:
        if Gb.AppleAcct is None:
            return

        Gb.reinitialize_icloud_devices_cnt += 1
        if Gb.reinitialize_icloud_devices_cnt > 2:
            return

        Gb.start_icloud3_inprocess_flag = False
        Gb.reinitialize_icloud_devices_flag = False
        Gb.initial_icloud3_loading_flag = False

        alert_msg = f"{EVLOG_ALERT}"
        if Gb.conf_data_source_ICLOUD:
            unverified_devices = [devicename
                        for devicename, Device in Gb.Devices_by_devicename.items() \
                        if Device.verified_flag is False]

            alert_msg +=(f"UNVERIFIED DEVICES > One or more devices was not verified. "
                        f"Apple Account access may be down, slow to respond or the internet may be down."
                        f"{CRLF_DOT}Unverified Devices > {', '.join(unverified_devices)}")
        post_event(alert_msg)

    except Exception as err:
        log_exception(err)

    return