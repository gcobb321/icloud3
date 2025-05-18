"""
Platform that supports scanning iCloud.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.icloud/


Special Note: I want to thank Walt Howd, (iCloud2 fame) who inspired me to
    tackle this project. I also want to give a shout out to Kovács Bálint,
    Budapest, Hungary who wrote the Python WazeRouteCalculator and some
    awesome HA guys (Petro31, scop, tsvi, troykellt, balloob, Myrddyn1,
    mountainsandcode,  diraimondo, fabaff, squirtbrnr, and mhhbob) who
    gave me the idea of using Waze in iCloud3.
                ...Gary Cobb aka GeeksterGary, Vero Beach, Florida, USA

Thanks to all
"""


#--------------------------------------------------------------------

from .global_variables  import GlobalVariables as Gb
from .const             import (VERSION, VERSION_BETA,
                                HOME, NOT_HOME, NOT_SET, HIGH_INTEGER, RARROW, LT, NBSP3, CLOCK_FACE, LINK,
                                CRLF, DOT, LDOT2, CRLF_DOT, CRLF_LDOT, CRLF_HDOT, CRLF_X, NL, NL_DOT,
                                EVLOG_IC3_STAGE_HDR, RED_ALERT,
                                ICLOUD, TRACKING_NORMAL, FNAME,
                                CONF_USERNAME, CONF_PASSWORD, CONF_TOTP_KEY,
                                IPHONE, IPAD, WATCH, AIRPODS, IPOD, ALERT,
                                CMD_RESET_PYICLOUD_SESSION, NEAR_DEVICE_DISTANCE,
                                DISTANCE_TO_OTHER_DEVICES, DISTANCE_TO_OTHER_DEVICES_DATETIME,
                                OLD_LOCATION_CNT, AUTH_ERROR_CNT,
                                MOBAPP_UPDATE, ICLOUD_UPDATE, ARRIVAL_TIME, TOWARDS, AWAY_FROM,
                                EVLOG_UPDATE_START, EVLOG_UPDATE_END, EVLOG_ERROR, EVLOG_ALERT, EVLOG_NOTICE,
                                ICLOUD, MOBAPP,
                                ENTER_ZONE, EXIT_ZONE, INTERVAL, NEXT_UPDATE, NOTIFY,
                                CONF_LOG_LEVEL, STATZONE_RADIUS_1M,
                                )
from .const_sensor      import (SENSOR_LIST_DISTANCE, )
from .startup           import hacs_ic3
from .startup           import start_ic3
from .startup           import start_ic3_control
from .tracking          import stationary_zone as statzone
from .mobile_app        import mobapp_data_handler
from .mobile_app        import mobapp_interface
from .apple_acct        import pyicloud_ic3_interface
from .apple_acct        import icloud_data_handler
from .tracking          import service_handler
from .tracking          import zone_handler
from .tracking          import determine_interval as det_interval
from .utils.file_io     import (is_event_loop_running,  is_event_loop_running2,)
from .utils.utils       import (instr, is_empty, isnot_empty, is_zone, is_statzone, isnot_statzone,
                                list_to_str, isbetween, get_username_base, )
from .utils.file_io     import (file_exists, directory_exists, make_directory, extract_filename, )
from .utils.messaging   import (broadcast_info_msg,
                                post_event, post_error_msg, post_monitor_msg, post_internal_error,
                                post_evlog_greenbar_msg, clear_evlog_greenbar_msg,
                                log_info_msg, log_exception, log_start_finish_update_banner,
                                log_debug_msg, archive_ic3log_file,
                                _evlog, _log, )
from .utils.time_util   import (time_now, time_now_secs, secs_to, secs_since, mins_since,
                                secs_to_time, secs_to_hhmm, secs_to_datetime,
                                calculate_time_zone_offset, secs_to_even_min_secs,
                                format_timer, format_age, format_time_age, format_secs_since, )
from .utils.dist_util   import (km_to_um, m_to_um_ft, )

#--------------------------------------------------------------------
import time
import traceback
from re import match
import homeassistant.util.dt        as dt_util
from   homeassistant.helpers.event  import track_utc_time_change

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3:
    """iCloud3 Device Tracker Platform"""

    def __init__(self):

        Gb.started_secs                    = time_now_secs()
        Gb.hass_configurator_request_id    = {}
        Gb.version                         = f"{VERSION}{VERSION_BETA}"
        Gb.version_beta                    = VERSION_BETA

        Gb.polling_5_sec_loop_running      = False
        self.pyicloud_refresh_time         = {}     # Last time Pyicloud was refreshed for the trk method
        self.pyicloud_refresh_time[ICLOUD] = 0
        self.attributes_initialized_flag   = False
        self.e_seconds_local_offset_secs   = 0

        Gb.authenticated_time              = 0
        Gb.icloud_acct_error_cnt           = 0
        Gb.authentication_error_retry_secs = HIGH_INTEGER
        Gb.evlog_trk_monitors_flag         = False
        Gb.any_device_was_updated_reason   = ''
        Gb.start_icloud3_inprocess_flag    = False
        Gb.restart_icloud3_request_flag    = False

        self.initialize_5_sec_loop_control_flags()

        #initialize variables configuration.yaml parameters
        start_ic3.set_global_variables_from_conf_parameters()


    def __repr__(self):
        return (f"<iCloud3: {Gb.version}>")

    @property
    def loop_ctrl_device_update_in_process(self):
        return (self.loop_ctrl_device_update_in_process_secs > 0)

#--------------------------------------------------------------------
    def initialize_5_sec_loop_control_flags(self):
        self.loop_ctrl_master_update_in_process_flag = False
        self.loop_ctrl_device_update_in_process_secs = 0
        self.loop_ctrl_devicename = ''

    def _set_loop_control_device(self, Device):
        self.loop_ctrl_device_update_in_process_secs = time_now_secs()
        self.loop_ctrl_devicename = Device.devicename

    def _clear_loop_control_device(self):
        self.loop_ctrl_device_update_in_process_secs = 0
        self.loop_ctrl_devicename = ''

    def _display_loop_control_msg(self, process):
        log_msg = ( f"Loop Control > {process} Device update in process > "
                    f"Updating-{self.loop_ctrl_devicename} "
                    f"Since-{format_time_age(self.loop_ctrl_device_update_in_process_secs)}")
        log_debug_msg(log_msg)

#--------------------------------------------------------------------
    def start_icloud3(self):

        try:
            if Gb.start_icloud3_inprocess_flag:
                return False

            service_handler.issue_ha_notification()

            self.startup_secs = time_now_secs()
            self.initial_locate_complete_flag  = False
            self.startup_log_msgs           = ''
            self.startup_log_msgs_prefix    = ''
            Gb.start_icloud3_inprocess_flag = True
            Gb.restart_icloud3_request_flag = False
            Gb.all_tracking_paused_flag     = False
            Gb.all_tracking_paused_secs     = 0

            start_ic3_control.stage_1_setup_variables()
            start_ic3_control.stage_2_prepare_configuration()

            start_ic3_control.stage_3_setup_configured_devices()
            stage_4_success = start_ic3_control.stage_4_setup_data_sources()
            if stage_4_success is False or Gb.reinitialize_icloud_devices_flag:
                stage_4_success = start_ic3_control.stage_4_setup_data_sources_retry()
                if stage_4_success is False or Gb.reinitialize_icloud_devices_flag:
                    stage_4_success = start_ic3_control.stage_4_setup_data_sources_retry(final_retry=True)

            start_ic3_control.stage_5_configure_tracked_devices()
            start_ic3_control.stage_6_initialization_complete()
            start_ic3_control.stage_7_initial_locate()

            Gb.trace_prefix = '------'
            Gb.EvLog.display_user_message('', clear_evlog_greenbar_msg=True)

            Gb.EvLog.startup_event_save_recd_flag = False
            Gb.initial_icloud3_loading_flag = False
            Gb.start_icloud3_inprocess_flag = False
            Gb.startup_stage_status_controls = []
            Gb.broadcast_info_msg = None

            if Gb.polling_5_sec_loop_running is False:
                broadcast_info_msg("Set Up 5-sec Polling Cycle")
                Gb.polling_5_sec_loop_running = True
                track_utc_time_change(Gb.hass, self._polling_loop_5_sec_device,
                        second=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])


            return True

        except Exception as err:
            log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This function is called every 5 seconds by HA. Cycle through all
#   of the iCloud devices to see if any of the ones being tracked need
#   to be updated. If so, we might as well update the information for
#   all of the devices being tracked since PyiCloud gets data for
#   every device in the account
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _polling_loop_5_sec_device(self, ha_timer_secs):
        Gb.this_update_secs = time_now_secs()
        Gb.this_update_time = time_now()

        if Gb.start_icloud3_inprocess_flag:
            return

        if Gb.config_parms_update_control != {''}:
            start_ic3.handle_config_parms_update()

        # An internet request was made more than 1-minute ago, assume it is down
        #if Gb.last_PyiCloud_request_secs > 0 and secs_since(Gb.last_PyiCloud_request_secs) > 60:
        #    Gb.internet_connection_error = True

        if (Gb.internet_connection_error
                or Gb.internet_connection_error_secs > 0):
            self._handle_internet_connection_error()

        # Restart iCloud via service call from EvLog or config_flow
        if Gb.restart_icloud3_request_flag:
            self.start_icloud3()

        # Exit 5-sec loop if no devices, updating a device now, or restarting iCloud3
        info_msg = ''
        if self.loop_ctrl_master_update_in_process_flag or Gb.start_icloud3_inprocess_flag:
            info_msg = "iCloud3 is Starting"
        elif Gb.conf_devices == []:
            info_msg = "No devices have been set up"
        if info_msg:
            for Device in Gb.Devices_by_devicename.values():
                Device.display_info_msg(info_msg)

            if Gb.this_update_time[-3:] in ['0:00', '5:00']:
                log_info_msg(info_msg)
            return

        # Make sure this master flag does not stay set which causes all tracking to stop
        if secs_since(self.loop_ctrl_device_update_in_process_secs) > 180:
            log_msg = (f"{EVLOG_NOTICE}iCloud3 Notice > Resetting Master Update-in-Process Control Flag, "
                        f"Was updating-{self.loop_ctrl_devicename}")
            post_event(log_msg)
            self.initialize_5_sec_loop_control_flags()

        # Handle any EvLog > Actions requested by the 'service_handler' module.
        if Gb.evlog_action_request == '':
            pass

        try:
            #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
            #   CHECK TIMERS
            #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
            self._main_5sec_loop_special_time_control()

            # Start - Uncommented code to test of moving device into a statzone while home
            # if Gb.this_update_time.endswith('5:00'):
            #     if Gb.Devices[0].StatZone is None:
            #         _evlog(f"{Gb.Devices[0].fname} creating")
            #         statzone.move_device_into_statzone(Gb.Devices[0])
            #         _evlog(f"{Gb.Devices[0].StatZone.zone} created")
            # if Gb.this_update_time.endswith('0:00'):
            #     if Gb.Devices[0].StatZone:
            #         _evlog(f"{Gb.Devices[0].StatZone.zone} removing")
            #         statzone.remove_statzone(Gb.Devices[0].StatZone, Gb.Devices[0])
            #         _evlog(f"{Gb.Devices[0].StatZone.zone} removed")
            # End - Unccommented code to test of moving device into a statzone while home

            if Gb.all_tracking_paused_flag:
                post_evlog_greenbar_msg(f"All Devices > Tracking Paused at "
                                        f"{format_time_age(Gb.all_tracking_paused_secs)}")
                return

            #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
            #   UPDATE TRACKED DEVICES
            #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
            self.loop_ctrl_master_update_in_process_flag = True
            self._main_5sec_loop_icloud_prefetch_control()

            for Device in Gb.Devices_by_devicename_tracked.values():
                if self.loop_ctrl_device_update_in_process:
                    self._display_loop_control_msg('Tracked')
                    break
                if Device.is_tracking_paused:
                    continue

                self._set_loop_control_device(Device)
                self._main_5sec_loop_update_tracked_devices_mobapp(Device)
                self._main_5sec_loop_update_tracked_devices_icloud(Device)
                self._display_secs_to_next_update_info_msg(Device)
                # Start - Uncomment for testing
                # zone_handler.log_zone_enter_exit_activity(Device)
                # End - Uncomment for testing
                self._clear_loop_control_device()

            # Remove all StatZones from HA flagged for removal in StatZone module
            # Removing them after the devices have been updated lets HA process the
            # statzone 'leave' automation trigger associated with a device before
            # the zone is deleted.
            if Gb.StatZones_to_delete:
                for StatZone in Gb.StatZones_to_delete:
                    try:
                        StatZone.remove_ha_zone()
                    except:
                        pass
                Gb.StatZones_to_delete = []

            #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
            #   UPDATE MONITORED DEVICES
            #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
            for Device in Gb.Devices_by_devicename_monitored.values():
                if self.loop_ctrl_device_update_in_process:
                    self._display_loop_control_msg('Monitored')
                    break
                if Device.is_tracking_paused:
                    continue

                self._set_loop_control_device(Device)
                self._main_5sec_loop_update_monitored_devices(Device)
                self._clear_loop_control_device()

            #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
            #   UPDATE BATTERY INFO
            #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
            for Device in Gb.Devices_by_devicename.values():
                Device.update_battery_data_from_mobapp()
                Device.display_battery_info_msg()

        except Exception as err:
            log_exception(err)

        self._display_device_alert_evlog_greenbar_msg()
        Gb.any_device_was_updated_reason = ''
        self.initialize_5_sec_loop_control_flags()
        #self._display_clear_authentication_needed_msg()
        self.initial_locate_complete_flag  = True

        Gb.trace_prefix = 'WRAPUP'

        #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
        #   POST UPDATE LOOP TASKS
        #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>

        # Update the EvLog display if the displayed device was updated after
        # the last EvLog refresh
        if Gb.log_debug_flag is False:
            if Device := Gb.Devices_by_devicename.get(Gb.EvLog.devicename):
                if Device.last_evlog_msg_secs > Gb.EvLog.last_refresh_secs:
                    Gb.EvLog.update_event_log_display(devicename=Device.devicename)

        # Update distance sensors (_zone/home.waze/calc_distace) to update the
        # distance to each device
        if Gb.dist_to_other_devices_update_sensor_list:
            for devicename in Gb.dist_to_other_devices_update_sensor_list:
                Device = Gb.Devices_by_devicename[devicename]
                Device.sensors[DISTANCE_TO_OTHER_DEVICES] = Device.dist_to_other_devices.copy()
                Device.sensors[DISTANCE_TO_OTHER_DEVICES_DATETIME] = \
                            secs_to_datetime(Device.dist_to_other_devices_secs)
                Device.write_ha_sensors_state(SENSOR_LIST_DISTANCE)

            Gb.dist_to_other_devices_update_sensor_list = set()

        Gb.trace_prefix = '------'


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   MAIN 5-SEC LOOP PROCESSING CONTROLLERS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _main_5sec_loop_update_tracked_devices_mobapp(self, Device):
        '''
        Update the device based on Mobile App data
        '''
        if (Device.mobapp_monitor_flag is False
                or Gb.conf_data_source_MOBAPP is False):
            return

        Gb.trace_prefix = 'MOBAPP'
        devicename = Device.devicename

        if Gb.this_update_secs >= Device.passthru_zone_timer:
            Device.reset_passthru_zone_delay()

        mobapp_data_handler.check_mobapp_state_trigger_change(Device)

        # Turn off monitoring the MobApp if excessive errors
        if Device.mobapp_data_invalid_error_cnt > 50:
            Device.mobapp_data_invalid_error_cnt = 0
            Device.mobapp_monitor_flag = False
            event_msg =("iCloud3 Error > MobApp entity error cnt exceeded, "
                        "MobApp monitoring stopped. iCloud monitoring will be used.")
            post_event(devicename, event_msg)
            return

        # If the Mobile App is the primary and data source next_update time is reached, get the
        # old location threshold. Send a location request to the mobapp device if the
        # data is older than the threshold, the next_update is newer than the mobapp data
        # and the next_update and data time is after the last request was sent.
        if (Device.primary_data_source == MOBAPP
                and Device.mobapp_data_updated_flag is False
                and Device.next_update_secs <= Gb.this_update_secs):
            if Device.interval_secs <= 30:
                mobapp_interface.request_location(Device, is_alive_check=False)
            else:
                Device.calculate_old_location_threshold()

                if  (secs_since(Device.loc_data_secs) > Device.old_loc_threshold_secs
                        and Device.next_update_secs > Device.loc_data_secs
                        and Device.next_update_secs > Device.mobapp_request_loc_sent_secs):
                    mobapp_interface.request_location(Device, is_alive_check=False, force_request=True)

                elif ((Gb.this_update_secs - Device.next_update_secs) % Device.interval_secs == 0
                        and Device.interval_secs >= 900):
                    mobapp_interface.request_location(Device, is_alive_check=False, force_request=True)

        # The Device is in a StatZone but the mobapp is not home. Send a location request to try to
        # sync them. Do this every 10-mins if the time since the last request is older than 10-min ago
        elif (Device.isin_statzone
                and Device.mobapp_data_state == NOT_HOME
                and (secs_since(Device.mobapp_request_loc_sent_secs) > 36000
                    or Device.mobapp_request_loc_sent_secs == 0)
                and Gb.this_update_time.endswith('0:00')):
            mobapp_interface.request_location(Device, is_alive_check=False, force_request=True)

        # The mobapp may be entering or exiting another Device's Stat Zone. If so,
        # reset the mobapp information to this Device's Stat Zone and continue
        if Device.mobapp_data_updated_flag:
            Device.mobapp_data_invalid_error_cnt = 0

            if instr(Device.mobapp_data_change_reason, ' ') is False:
                Device.mobapp_data_change_reason = Device.mobapp_data_change_reason.title()
            event_msg = f"MobApp Trigger > {Device.mobapp_data_change_reason}"
            post_event(devicename, event_msg)

            if Gb.is_passthru_zone_used:
                if instr(Device.mobapp_data_change_reason, ENTER_ZONE):
                    if Device.set_passthru_zone_delay(MOBAPP,
                                Device.mobapp_zone_enter_zone, Device.mobapp_data_secs):
                        return

                elif instr(Device.mobapp_data_change_reason, EXIT_ZONE):
                    Device.reset_passthru_zone_delay()

            # Make sure exit distance is outside of statzone. If inside StatZone,
            # the zone needs to be removed and another on assigned out the mobapp
            # will keep exiting  when the device is still in it. it also seems to
            # stop monitoring the zone for this device but other devices seem to
            # be ok
            if (instr(Device.mobapp_data_change_reason, EXIT_ZONE)
                    and is_statzone(Device.mobapp_zone_exit_zone)
                    and Device.StatZone
                    and Device.mobapp_zone_exit_dist_m < Device.StatZone.radius_m):

                event_msg =(f"{EVLOG_ALERT}MobApp Trigger Changed > {Device.mobapp_data_change_reason}, "
                            f"Distance less than zone size "
                            f"{Device.StatZone.dname} {Device.mobapp_zone_exit_dist_m} < {Device.StatZone.radius_m}")
                post_event(devicename, event_msg)

                statzone.kill_and_recreate_unuseable_statzone(Device)

            else:
                mobapp_data_handler.reset_statzone_on_enter_exit_trigger(Device)

            self._validate_new_mobapp_data(Device)
            self.process_updated_location_data(Device, MOBAPP)

        # Send a location request to device if needed
        mobapp_data_handler.check_if_mobapp_is_alive(Device)

#----------------------------------------------------------------------------
    def _main_5sec_loop_update_tracked_devices_icloud(self, Device):
        '''
        Update the device based on iCloud data
        '''

        if (Device.PyiCloud is None):
            return

        Gb.trace_prefix = 'ICLOUD'
        devicename = Device.devicename
        Device.icloud_update_reason = Device.icloud_no_update_reason = ''
        Device.calculate_old_location_threshold()

        if Gb.this_update_secs > Device.passthru_zone_timer:
            Device.reset_passthru_zone_delay()

        if (Device.is_tracking_paused
                or icloud_data_handler.no_icloud_update_needed_tracking(Device)
                or icloud_data_handler.no_icloud_update_needed_setup(Device)):
            return

        if (Device.is_tracking_resumed
                or icloud_data_handler.is_icloud_update_needed_timers(Device)
                or icloud_data_handler.is_icloud_update_needed_general(Device)):
            Device.tracking_status = TRACKING_NORMAL
        else:
            return

        # Update device info. Get data from iCloud
        icloud_data_handler.request_icloud_data_update(Device)

        # Test forcing Away --> Home with home_zone HA config override
        # if time_now_secs() > Gb.started_secs + 120:
        #     Device.loc_data_latitude  = Gb.HomeZone.latitude
        #     Device.loc_data_longitude = Gb.HomeZone.longitude
        #     _evlog(Device, "Home location Override")

        # Do not redisplay update reason if in error retries. It has already been displayed.
        if icloud_data_handler.update_device_with_latest_raw_data(Device) is False:
            Device.icloud_acct_error_flag = True

        if Device.icloud_devdata_useable_flag:
            Device.display_info_msg(Device.icloud_update_reason)
            event_msg = f"Trigger > {Device.icloud_update_reason}"
            post_event(devicename, event_msg)

            # See if the Stat Zone timer has expired or if the Device has moved a lot. Do this
            # even if the sensors are not updated to make sure the Stat Zone is set up and can be
            # seleted for the Device
            statzone.move_into_statzone_if_timer_reached(Device)

            # Get in-zone name or away, will be used in process_updated_location_data routine
            # when results are calculted. We need to get it now to see if the passthru is
            # needed or still active
            Device.selected_zone_results = zone_handler.select_zone(Device)

            # If entering a zone, set the passthru expire time (if needed)
            if self._started_passthru_zone_delay(Device):
                return

        if Device.icloud_acct_error_flag and Device.is_next_update_overdue is False:
            self._display_icloud_acct_error_msg(Device)
            Device.icloud_acct_error_flag = False
            return

        Gb.icloud_acct_error_cnt = 0

        self._validate_new_icloud_data(Device)
        self._post_before_update_monitor_msg(Device)
        self.process_updated_location_data(Device, ICLOUD)

        # Refresh the EvLog if this is an initial locate
        if self.initial_locate_complete_flag == False:
            if devicename == Gb.Devices[0].devicename:
                Gb.EvLog.update_event_log_display(devicename)

        Device.icloud_initial_locate_done = True
        Device.selected_zone_results = []

#---------------------------------------------------------------------
    def _main_5sec_loop_update_monitored_devices(self, Device):
        '''
        Update the monitored device with new location and battery info
        '''

        Gb.trace_prefix = 'MONITR'
        if Device.is_tracking_paused:
            return

        Device.FromZone_NextToUpdate = Device.FromZone_Home
        Device.FromZone_TrackFrom    = Device.FromZone_Home
        Device.last_track_from_zone  = HOME

        if Device.mobapp_monitor_flag and Gb.conf_data_source_MOBAPP:
            mobapp_data_handler.check_mobapp_state_trigger_change(Device)

        if Device.is_tracking_resumed:
            Device.tracking_status = TRACKING_NORMAL
        elif Device.is_next_update_time_reached is False:
            Device.calculate_distance_moved()
            if Device.loc_data_dist_moved_km < .05:
                return
        elif Device.loc_data_latitude == 0.0:
            return

        Device.update_sensors_flag  = True
        Device.icloud_initial_locate_done = True
        Device.icloud_update_reason = 'Monitored Device Update'

        event_msg =(f"Trigger > Moved {km_to_um(Device.loc_data_dist_moved_km)}")

        self.process_updated_location_data(Device, '')
        Device.update_sensor_values_from_data_fields()

#----------------------------------------------------------------------------
    def _main_5sec_loop_icloud_prefetch_control(self):
        '''
        Update the iCloud location data if it the next_update_time will be reached
        in the next 10-seconds
        '''
        if (Gb.use_data_source_ICLOUD is False
                or Gb.all_tracking_paused_flag):
            return
        # if Gb.PyiCloud is None:
        #     return

        if Device := det_interval.device_will_update_in_15secs():
            if Device.PyiCloud is None: return

            Gb.trace_prefix = 'GETLOC'
            log_start_finish_update_banner('start', Device.devicename, 'icloud prefetch', '')
            post_monitor_msg(Device.devicename, "iCloud Location Requested (prefetch)")

            Device.icloud_devdata_useable_flag = \
                icloud_data_handler.update_PyiCloud_RawData_data(Device,
                        results_msg_flag=Device.is_location_old_or_gps_poor)

            log_start_finish_update_banner('finish', Device.devicename, 'icloud prefetch', '')
            Gb.trace_prefix = '------'

#----------------------------------------------------------------------------
    def _main_5sec_loop_special_time_control(self):
        '''
        Various functions that are run based on the time-of-day
        '''

        time_now_mmss = Gb.this_update_time[-5:]
        time_now_ss   = Gb.this_update_time[-2:]
        time_now_mm   = Gb.this_update_time[3:5] if time_now_ss == '00' else ''

        # Every hour:
        #   - Check for iCloud3 update in HACS data
        #   - Clean up lingering Stat Zones
        if time_now_mmss == '00:00':
            self._timer_tasks_every_hour()

        # At midnight:
        #   - Reset auto-reset log levels
        #   - Reset daily counts
        #   - Compress the WazeHist database
        #   - Cycle the iCloud3 log files
        if Gb.this_update_time == '00:15:00':
            self._timer_tasks_midnight()

        # At 1am:
        #   - Check for daylight savings time change
        elif Gb.this_update_time == '01:00:00':
            calculate_time_zone_offset()

        if (Gb.this_update_secs >= Gb.EvLog.clear_secs):
            Gb.EvLog.update_event_log_display(show_one_screen=True)

        # Every 30-seconds:
        #   - See if a device needs a 2fa request via a otp token
        if time_now_ss in ['00', '30']:
            self._check_apple_acct_2fa_totp_key_request()
            pass

        # Every minute:
        #   - Update the device's info msg
        #   - Check to see if a MobApp location refresh has been requested
        if time_now_ss == '00':
            self._check_mobappp_location_request()

        # Every 15-minutes:
        #   - Refresh a device's distance to the other devices
        if time_now_mm in ['00', '15', '30', '45']:
            det_interval.set_dist_to_devices(post_event_msg=True)

            if Gb.log_debug_flag:
                for devicename, Device in Gb.Devices_by_devicename_tracked.items():
                    Device.log_data_fields()

            if isnot_empty(Gb.username_pyicloud_503_connection_error):
                pyicloud_ic3_interface.retry_apple_acct_login()

        # Every 5-minutes
        if time_now_mmss[1:] in ['0:00', '5:00']:
            # There are some Devices that monitor the mobapp that are not in the HA MobApp Integrations
            # devices list. Rebuild the list and try again. The MobApp Integrations may not have been
            # set up on the first try when iCloud3 started.
            if Gb.device_mobapp_verify_retry_needed:
                mobapp_data_handler.unverified_devices_mobapp_handler()


        # Every 10-minutes
        # if time_now_mm in ['00', '10', '20', '30', '40', '50']:
        #     pass

        # Every 1/2-hour
        # if time_now_mm in ['00', '30']:
        #     pass

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE THE DEVICE IF A STATE OR TRIGGER CHANGE WAS RECIEVED FROM THE MOBAPP
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _validate_new_mobapp_data(self, Device):
        """
        Update the devices location using data from the Mobile App
        """
        if (Gb.start_icloud3_inprocess_flag
                or Device.mobapp_monitor_flag is False):
            return ''

        update_reason = Device.mobapp_data_change_reason
        devicename    = Device.devicename

        Device.update_sensors_flag           = False
        Device.mobapp_request_loc_first_secs = 0
        Device.mobapp_request_loc_last_secs  = 0

        Device.FromZone_BeingUpdated = Device.FromZone_Home

        if (Device.is_tracking_paused
                or Device.mobapp_data_latitude == 0.0
                or Device.mobapp_data_longitude == 0.0):
            return

        if Gb.any_device_was_updated_reason == '':
            Gb.any_device_was_updated_reason = f'{Device.mobapp_data_change_reason}, {Device.fname_devtype}'
        return_code = MOBAPP_UPDATE

        # Check to see if the location is outside the zone without an exit trigger
        for from_zone, FromZone in Device.FromZones_by_zone.items():
            if is_zone(from_zone):
                info_msg = zone_handler.is_outside_zone_no_exit( Device, from_zone, '',
                                        Device.mobapp_data_latitude,
                                        Device.mobapp_data_longitude)

                if Device.outside_no_exit_trigger_flag:
                    post_event(devicename, info_msg)

                    # Set located time to trigger time so it won't fire as trigger change again
                    Device.loc_data_secs = Device.mobapp_data_secs + 10
                    return

        try:
            #log_start_finish_update_banner('start', devicename, MOBAPP, update_reason)
            Device.update_sensors_flag = True

            # Request the mobapp location if mobapp location is old and the next update
            # time is reached and less than 1km from the zone
            if (Device.is_mobapp_data_old
                    and Device.is_next_update_time_reached
                    and Device.FromZone_NextToUpdate.zone_dist_km < 1
                    and Device.FromZone_NextToUpdate.dir_of_travel == TOWARDS
                    and Device.isnotin_zone):

                mobapp_interface.request_location(Device)

                Device.update_sensors_flag = False

            if Device.update_sensors_flag:
                Device.update_dev_loc_data_from_raw_data_MOBAPP()

        except Exception as err:
            post_internal_error('MobApp Update', traceback.format_exc)
            return_code = ICLOUD_UPDATE

        return

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Cycle through all iCloud devices and update the information for the devices
#   being tracked
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _validate_new_icloud_data(self, Device):

        """
        Request device information from iCloud (if needed) and update
        device_tracker information.

        _Device -
                None     =  Update all devices
                Not None =  Update specified device
        arg_other-devicename -
                None     =  Update all devices
                Not None =  One device in the list reached the next update time.
                            Do not update another device that now has poor location
                            gps after all the results have been determined if
                            their update time has not been reached.
        """

        zone = Device.loc_data_zone

        if Gb.any_device_was_updated_reason == '':
            Gb.any_device_was_updated_reason = f'{Device.icloud_update_reason}, {Device.fname_devtype}'

        Device.icloud_update_retry_flag     = False
        Device.mobapp_request_loc_last_secs = 0

        Device.FromZone_BeingUpdated = Device.FromZone_Home

        try:
            Device.update_sensors_flag = True
            Device.calculate_old_location_threshold()

            #icloud data overrules device data which may be stale
            latitude  = Device.loc_data_latitude
            longitude = Device.loc_data_longitude


            # See if the GPS accuracy is poor, the locate is old, there is no location data
            # available or the device is offline
            self._set_old_location_status(Device)

            # Check to see if currently in a zone. If so, check the zone distance.
            # If new location is outside of the zone and inside radius*4, discard
            # by treating it as poor GPS
            if Device.update_sensors_flag is False:
                pass

            elif isnot_statzone(zone) or Device.sensor_zone == NOT_SET:
                Device.outside_no_exit_trigger_flag = False
                Device.update_sensors_error_msg= ''

            else:
                Device.update_sensors_error_msg = \
                            zone_handler.is_outside_zone_no_exit(Device, zone, '', latitude, longitude)


            # 'Verify Location' update reason overrides all other checks and forces an iCloud update
            if Device.icloud_update_reason == 'Verify Location':
                pass

            # Bypass all update needed checks and force an iCloud update
            elif Device.icloud_force_update_flag:
                pass

            # elif Device.is_offline or Device.no_location_data:
            #     pass

            elif Device.icloud_devdata_useable_flag is False or Device.icloud_acct_error_flag:
                Device.update_sensors_flag = False

            # Ignore old location when in a zone and discard=False
            # let normal next time update check process
            elif (Device.is_gps_poor
                    and Gb.discard_poor_gps_inzone_flag
                    and Device.isin_zone
                    and Device.no_location_data is False
                    and Device.outside_no_exit_trigger_flag is False):

                Device.old_loc_cnt -= 1
                Device.old_loc_msg = ''

                if Device.is_next_update_time_reached is False:
                    Device.update_sensors_flag = False

            # Outside zone, no exit trigger check. This is valid for location less than 2-minutes old
            # added 2-min check so it wouldn't hang with old mobapp data. Force a location update
            elif (Device.outside_no_exit_trigger_flag
                    and secs_since(Device.mobapp_data_secs) < 120):
                pass

            # Discard if the next update time has been reached and location is old but
            # do the update anyway if it is newer than the last update. This prevents
            # the situation where a non-Mobile App device (Watch) that is always getting
            # data that is a little old from never updating and eventually ending up
            # with a long (2-hour) interval time and never getting updated.
            if (Device.is_location_old_or_gps_poor
                    and Device.is_tracked
                    and Device.is_next_update_time_reached):

                # Reset the  error cnt if the still old data is newer than last time (rc9)
                if (Device.old_loc_cnt > 4
                        and Device.FromZone_Home.interval_secs >= 300
                        and Device.loc_data_secs > Device.last_update_loc_secs):
                    event_msg = (f"iCloud Loc > Old, Using Anyway, "
                                f"{Device.last_update_loc_time}{RARROW}"
                                f"{Device.loc_data_time}")
                    post_event(Device, event_msg)

                    Device.old_loc_cnt = 0
                    Device.old_loc_msg = ''
                    Device.last_update_loc_secs = Device.loc_data_secs
                else:
                    Device.update_sensors_error_msg = Device.old_loc_msg
                    Device.update_sensors_flag = False

            # A non-MobApp device (Watch) location will be requested when a nearby MobApp device
            # leaves a zone. If the location is valid but before the request
            # time, it will be left in the zone until the Next Update Time. Treat the
            # location as old to force an update to check the zone status again. Clear
            # the check zone exit time when the update is done. Stop checking when
            # the old loc cnt > 8 or the location is > 2-hr ago. It probably was never located.

            if (Device.loc_data_secs < Device.check_zone_exit_secs
                    and mins_since(Device.loc_data_secs) < 120
                    and Device.old_loc_cnt <= 8):
                Device.old_loc_cnt += 1
                Device.old_loc_msg = 'Located before Zone Exit Check'
                Device.update_sensors_error_msg = Device.old_loc_msg
                Device.update_sensors_flag = False
                Device.check_zone_exit_secs = 0

            elif (Device.check_zone_exit_secs > 0
                    and Device.loc_data_secs >= Device.check_zone_exit_secs):
                Device.check_zone_exit_secs = 0

            # See if the Stat Zone timer has expired or if the Device has moved a lot. Do this
            # again (after the initial update needed check) since the data has been updated
            # and the gps might be good now where it was bad earlier.
            # if self._move_into_statzone_if_timer_reached(Device):
            if statzone.move_into_statzone_if_timer_reached(Device):
                Device.icloud_update_reason = "Stationary Zone Time Reached"
                Device.update_sensors_flag = True
                Device.selected_zone_result = []

        except Exception as err:
            post_internal_error('iCloud Update', traceback.format_exc)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Determine the update interval, Update the sensors and device_tracker entity
#
#   1. Cycle through each trackFromZone zone for the Device and determint the interval,
#   next_update_time, distance from the zones, etc. Then update all of the TrackFromZone
#   sensors for the Device (this is normally just the Home zone).
#   2. Update the sensors for the device.
#   3. Update the device_tracker entity for the device.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def process_updated_location_data(self, Device, data_source):
        try:
            devicename = Gb.devicename = Device.devicename
            acct_name = ''

            if data_source == ICLOUD:
                update_reason = f"{Device.icloud_update_reason}"
                if Device.PyiCloud:
                    acct_name = Device.PyiCloud.account_owner_link

            elif data_source == MOBAPP:
                update_reason = Device.mobapp_data_change_reason
            else:
                update_reason = Device.trigger

            # Makw sure the Device mobapp_state is set to the statzone if the device is in a statzone
            # and the Device mobapp state value is not_nome. The Device state value can be out of sync
            # if the mobapp was updated but no trigger or state change was detected when a iCloud
            # update is processed since the Device's location gps did not actually change
            mobapp_data_handler.sync_mobapp_data_state_statzone(Device)

            # Location is good or just setup the StatZone. Determine next update time and update interval,
            # next_update_time values and sensors with the good data
            if Device.update_sensors_flag:
                log_start_finish_update_banner('start', f"{devicename}{acct_name}",
                                                data_source, update_reason)
                self._get_tracking_results_and_update_sensors(Device, data_source)

            else:
                # Old location, poor gps etc. Determine the next update time to request new location info
                # with good data (hopefully). Update interval, next_update_time values and sensors with the time
                det_interval.determine_interval_after_error(Device, counter=OLD_LOCATION_CNT)
                if (Device.old_loc_cnt > 0
                        and (Device.old_loc_cnt % 4) == 0):
                    mobapp_interface.request_location(Device)

            Device.icloud_force_update_flag = False
            Device.write_ha_sensors_state()
            Device.write_ha_device_from_zone_sensors_state()
            Device.write_ha_device_tracker_state()
            zone_handler.log_zone_enter_exit_activity(Device)

            # Refresh the EvLog if this is an initial locate or the devicename is displayed
            if (devicename == Gb.EvLog.evlog_attrs["devicename"]
                    or (self.initial_locate_complete_flag == False
                        and devicename == Gb.Devices[0].devicename)):
                Gb.EvLog.update_event_log_display(devicename)

            # log_start_finish_update_banner('finish',  devicename,
            #                         f"{Device.data_source_fname}/{Device.dev_data_source}",
            #                         "gen update")

        except Exception as err:
            log_exception(err)
            post_internal_error('iCloud Update', traceback.format_exc)

        Device.display_battery_info_msg()

        Device.update_in_process_flag = False

#----------------------------------------------------------------------------
    def _started_passthru_zone_delay(self, Device):

        if Gb.is_passthru_zone_used is False:
            return False

        # Get in-zone name or away, will be used in process_updated_location_data routine
        # when results are calculted. We need to get it now to see if the passthru is
        # needed or still active
        # Device.selected_zone_results = zone_handler.select_zone(Device)
        ZoneSelected, zone_selected, zone_selected_dist_m, zones_distance_list = \
            Device.selected_zone_results

        # Entering a zone (going from not_home to a zone)
        # If entering a zone, set the passthru expire time (if needed) and the next
        # update interval to 1-minute
        if (Device.loc_data_zone == NOT_HOME
                and zone_selected not in ['', NOT_HOME]
                and Device.is_statzone_trigger_reached is False
                and is_statzone(zone_selected) is False
                and Device.is_next_update_overdue is False):

            if Device.set_passthru_zone_delay(ICLOUD, zone_selected, time_now_secs()):
                Device.selected_zone_results = []
                return True

        elif (Device.is_passthru_timer_set
                and Gb.this_update_secs >= Device.passthru_zone_timer):
            Device.reset_passthru_zone_delay()

        return False

#----------------------------------------------------------------------------
    def _get_tracking_results_and_update_sensors(self, Device, update_requested_by):
        '''
        All sensor update checked passed and an update is needed. Get the latest icloud
        data, verify it's usability, and update the location data, determine the next
        interval and next_update_time and display the tracking results
        '''
        devicename = Device.devicename
        update_reason = Device.mobapp_data_change_reason \
                                    if update_requested_by == MOBAPP \
                                    else Device.icloud_update_reason

        if Device.PyiCloud:
        # if Gb.PyiCloud:
            icloud_data_handler.update_device_with_latest_raw_data(Device)
        else:
            Device.update_dev_loc_data_from_raw_data_MOBAPP()

        if Device.is_tracked and Device.is_location_data_rejected():
            if Device.is_dev_data_source_iCloud:
                det_interval.determine_interval_after_error(Device, counter=OLD_LOCATION_CNT)

        elif Device.is_monitored and Device.is_offline:
            det_interval.determine_interval_monitored_device_offline(Device)

        elif Device.is_tracked and Device.no_location_data:
            det_interval.determine_interval_after_error(Device, counter=OLD_LOCATION_CNT)

        else:
            post_event(devicename, EVLOG_UPDATE_START)

            self._post_before_update_monitor_msg(Device)

            if self._determine_interval_and_next_update(Device):
                Device.update_sensor_values_from_data_fields()

            update_requested_by = 'Tracking' if Device.is_tracked else 'Monitor'
            from_zone = Device.FromZone_TrackFrom.from_zone

            post_event(devicename, (
                        f"{EVLOG_UPDATE_END}{Device.dev_data_source} Results > "
                        f"{self._results_special_msg(Device)}"))

        if Device.dev_data_source == ICLOUD and Device.PyiCloud:
            acct_name = Device.PyiCloud.account_owner_link
        else:
            acct_name = ''
        log_start_finish_update_banner('finish', f"{devicename}{acct_name}",
                                        Device.dev_data_source,
                                        f"CurrZone-{Device.sensor_zone}")

        self._post_after_update_monitor_msg(Device)
#...............................................................................
    def _results_special_msg(self, Device):
        if Device.is_offline:
            return 'Offline'

        if is_empty(Device.sensors[ARRIVAL_TIME]):
            # return (f"Update in {format_timer(Device.FromZone_TrackFrom.interval_secs)} "
            return (f"Update in {Device.interval_str} "
                    f"at {Device.FromZone_TrackFrom.next_update_time}")

        if (Device.isin_zone
                and Device.loc_data_zone == Device.FromZone_TrackFrom.from_zone):
            special_msg = (f"{Device.FromZone_TrackFrom.from_zone_dname[:8]} "
                    f"Since {Device.sensors[ARRIVAL_TIME].replace('@', '')}")
            #if Device.away_time_zone_offset == 0:
            special_msg += f", Update {secs_to_hhmm(Device.FromZone_TrackFrom.next_update_secs)}"
            return special_msg

        if Device.FromZone_TrackFrom.dir_of_travel != AWAY_FROM:
            if Device.FromZone_TrackFrom.waze_time > 0:
                arrival_secs = Device.FromZone_TrackFrom.waze_time * 60 + time_now_secs()
                arrival_time = (f"in {format_timer(secs_to(arrival_secs))} "
                                f"at {secs_to_hhmm(arrival_secs)}")
            else:
                arrival_time = (f"~{Device.sensors[ARRIVAL_TIME]}, "
                                f"Update {format_timer(secs_to(Device.FromZone_TrackFrom.next_update_secs))}")
            return (f"Arrive {Device.FromZone_TrackFrom.from_zone_dname[:8]} "
                    f"{arrival_time}")


        return (f"Arrive {Device.FromZone_TrackFrom.from_zone_dname[:8]} "
                f"around {Device.sensors[ARRIVAL_TIME]}")

#-------------------------------------------------------------------------------
    def _determine_interval_and_next_update(self, Device):
        '''
        Determine the update interval, Update the sensors and device_tracker entity:
            1. Cycle through each trackFromZone zone for the Device and determint the interval,
            next_update_time, distance from the zones, etc. Then update all of the TrackFromZone
            sensors for the Device (this is normally just the Home zone).
            2. Update the sensors for the device.
            3. Update the device_tracker entity for the device.
        '''
        devicename = Device.devicename

        if Device.update_in_process_flag:
            info_msg  = "Retrying > Last update not completed"
            event_msg = info_msg
            post_event(devicename, event_msg)

        try:
            if Device.is_dev_data_source_MOBAPP:
                Device.trigger = (f"{Device.mobapp_data_trigger}@{Device.mobapp_data_time}")
            else:
                Device.trigger = (f"{Device.dev_data_source}@{Device.loc_data_time}")

            zone_handler.update_current_zone(Device)

        except Exception as err:
            post_internal_error('Update Stat Zone', traceback.format_exc)

        try:
            Device.update_in_process_flag = True

            # Update the devices that are near each other
            # See if a device updated updated earlier in this 5-sec loop was just updated and is
            # near the device being updated now
            det_interval.update_near_device_info(Device)

            # Cycle thru each Track From Zone get the interval and all other data
            devicename = Device.devicename

            for from_zone, FromZone in Device.FromZones_by_zone.items():
                det_interval.determine_interval(Device, FromZone)

            # Determine zone to be tracked from now that all of the zone distances have been determined
            det_interval.determine_TrackFrom_zone(Device)

            # Save the source/time summary of the update for the next update msg
            Device.last_loc_data_time_gps = f"{Device.dev_data_source}-{Device.loc_data_time_gps} "

            # If the location is old and an update is being done (probably from an mobapp trigger),
            # see if the error interval is greater than this update interval. Is it is, Reset the counter
            if Device.old_loc_cnt > 8:
                error_interval_secs, error_cnt, max_error_cnt = det_interval.get_error_retry_interval(Device)
                if error_interval_secs > Device.interval_secs:
                    event_msg =(f"iCloud Loc > Old #{Device.old_loc_cnt}, Old Loc Counter Reset, "
                                f"NextUpdate-{format_age(Device.interval_secs)}, "
                                f"OldLocRetryUpdate-{format_age(error_interval_secs)}")
                    Device.old_loc_cnt = 0

            # log_start_finish_update_banner('finish', devicename, Device.dev_data_source, '')

        except Exception as err:
            log_exception(err)
            post_internal_error('Det IntervalLoop', traceback.format_exc)

        return True

#--------------------------------------------------------------------
    def _display_icloud_acct_error_msg(self, Device):
        '''
        An error ocurred accessing the iCloud account. This can be a
        Authentication error or an error retrieving the loction data. Update the error
        count and turn iCloud tracking off when the error count is exceeded.
        '''
        Gb.icloud_acct_error_cnt += 1

        if Device.icloud_initial_locate_done is False:
            Device.update_sensors_error_msg = "Retrying Initial Locate"
        else:
            Device.update_sensors_error_msg = "iCloud Authentication or Location Error (may be Offline)"

        det_interval.determine_interval_after_error(Device, counter=AUTH_ERROR_CNT)

        if Gb.icloud_acct_error_cnt > 20:
            start_ic3.set_primary_data_source(MOBAPP)
            Device.primary_data_source = MOBAPP
            log_msg = ("iCloud3 Error > More than 20 iCloud Authentication "
                        "or Location errors. iCloud may be down. "
                        "The MobApp data source will be used. "
                        "Restart iCloud3 at a later time to see if iCloud "
                        "Loction Services is available.")
            post_error_msg(log_msg)

#----------------------------------------------------------------------------
    def _display_device_alert_evlog_greenbar_msg(self):
        '''
        Check to see if any startup alerts of device issues exist. If so, display
        them in the green alert bar at the to p of the EvLog.

        Tracked device screen displayed - Show  all alert messages
        Monitored device screen displayed - Show only that devices alerts
        '''
        if (Gb.EvLog.evlog_attrs['fname'] == 'Startup Events'
                or Gb.EvLog.greenbar_alert_msg.startswith('Start up log')
                or Gb.WazeHist.wazehist_recalculate_time_dist_running_flag):
            return

        general_alert_msg = startup_alert_attr = ''
        tracked_alert_attr = monitored_alert_attr = ''

        if (Gb.internet_connection_error
                or Gb.internet_connection_error_secs > 0):
            return

        if Gb.version_hacs:
            general_alert_msg += (  f"{CRLF_LDOT}iCloud3 {Gb.version_hacs} is available on HACS, "
                                    f"you are running v{Gb.version}")

        if Gb.disable_log_filter:
            general_alert_msg += f"{RED_ALERT}PASSWORD LOG FILTER DISABLED (Gb.disable_log_filter)"

        if (Gb.startup_alerts
                # and is_empty(Gb.username_pyicloud_503_connection_error)
                and is_empty(Gb.usernames_setup_error_retry_list)):
            Gb.startup_alerts = []

        if isnot_empty(Gb.startup_alerts):
            startup_alert_attr = Gb.startup_alerts_str
            general_alert_msg += f"{CRLF_LDOT}Alerts starting iCloud3{RARROW}Review Event Log for more info"

            for devicename, error_msg in Gb.conf_startup_errors_by_devicename.items():
                general_alert_msg += f"{CRLF_LDOT}{devicename} > {error_msg}"

        for username, PyiCloud in Gb.PyiCloud_by_username.items():
            if PyiCloud:
                if PyiCloud.login_successful is False:
                    general_alert_msg += (  f"{CRLF_LDOT}Apple Acct > {PyiCloud.account_owner_short}, "
                                            f"Login Failed")
                if PyiCloud.requires_2fa:
                    general_alert_msg += (  f"{CRLF_LDOT}Apple Acct > {PyiCloud.account_owner_short}, "
                                            f"Authentication Needed")

        if (Gb.icloud_acct_error_cnt > 5
                and instr(general_alert_msg, 'errors accessing') is False):
            general_alert_msg += f"{CRLF_LDOT}Internet or Apple may be down, errors accessing Apple Acct"

        apple_acct_errors = [username.split('@')[0] for username in Gb.username_valid_by_username
                                                    if Gb.username_valid_by_username[username] is False]
        if isnot_empty(apple_acct_errors):
            general_alert_msg += f"{CRLF_LDOT}Apple Acct Login Errors-{list_to_str(apple_acct_errors)}"

        verified_msg = poor_location_msg = offline_msg =''
        paused_msg = mobapp_unavailable_msg = ''

        for Device in Gb.Devices:
            device_alert_msg = ''
            if (Device.verified_flag is False
                    or (Device.is_data_source_ICLOUD is False and Device.is_data_source_MOBAPP is False)):
                verified_msg += f"{Device.fname}, "
            elif Device.is_tracking_paused:
                paused_msg += f"{Device.fname}, "
            elif Device.is_tracked:
                if Device.mobapp_device_unavailable_flag:
                    mobapp_unavailable_msg += (  f"{Device.fname} "
                                                f"({Device.conf_mobapp_fname}), ")

                if Device.is_offline:
                    offline_msg += f"{Device.fname}, "
                elif Device.no_location_data:
                    poor_location_msg += f"{Device.fname}, "
                elif mins_since(Device.loc_data_secs) > 300:
                    age_hrs = int(mins_since(Device.loc_data_secs)/60)
                    poor_location_msg += f"{Device.fname} (> {age_hrs} hrs ago), "
            if isbetween(Device.dev_data_battery_level, 1, 19):
                device_alert_msg = f"{Device.fname} > Low Battery ({Device.dev_data_battery_level}%)"

            if device_alert_msg:
                general_alert_msg += f"{CRLF_LDOT}{device_alert_msg}"

            if device_alert_msg != Device.alert:
                Device.alert = Device.sensors[ALERT] = device_alert_msg
                Device.write_ha_device_tracker_state()

        if paused_msg:
            general_alert_msg += f"{CRLF_LDOT}Paused-{paused_msg[:-2]}"
        if verified_msg:
            general_alert_msg += f"{CRLF_LDOT}Setup Errors-{verified_msg[:-2]}"
        if poor_location_msg:
            general_alert_msg += f"{CRLF_LDOT}Poor Location-{poor_location_msg[:-2]}"
        if offline_msg:
            general_alert_msg += f"{CRLF_LDOT}Offline-{offline_msg[:-2]}"
        if mobapp_unavailable_msg:
            general_alert_msg += f"{CRLF_LDOT}MobApp Device Unavailable-{mobapp_unavailable_msg[:-2]}"

        if Gb.EvLog.alert_attr_filter(startup_alert_attr) != startup_alert_attr:
            Gb.EvLog.evlog_attrs['alert_startup'] = Gb.EvLog.alert_attr_filter(startup_alert_attr)
        if Gb.EvLog.alert_attr_filter(tracked_alert_attr) != tracked_alert_attr:
            Gb.EvLog.evlog_attrs['alert_tracked'] = Gb.EvLog.alert_attr_filter(tracked_alert_attr)
        if Gb.EvLog.alert_attr_filter(monitored_alert_attr) != monitored_alert_attr:
            Gb.EvLog.evlog_attrs['alert_monitored'] = Gb.EvLog.alert_attr_filter(monitored_alert_attr)

        if general_alert_msg.startswith(CRLF):
            general_alert_msg = general_alert_msg[1:]
        if general_alert_msg != Gb.EvLog.greenbar_alert_msg:
            post_evlog_greenbar_msg(general_alert_msg)
        elif general_alert_msg == '' and Gb.EvLog.greenbar_alert_msg:
            clear_evlog_greenbar_msg()

#----------------------------------------------------------------------------
    def _check_apple_acct_authentication_needed(self):

        msg = ""
        for username, PyiCloud in Gb.PyiCloud_by_username.items():
            if PyiCloud.requires_2fa:
                msg += (f"Apple Acct > {PyiCloud.account_owner}, "
                        f"Auth Code Needed")

#--------------------------------------------------------------------
    def _format_fname_devtype(self, Device):
        try:
            return f"{Device.fname_devtype}"
        except:
            return ''

#--------------------------------------------------------------------
    def _wait_if_update_in_process(self, Device=None):
        # An update is in process, must wait until done

        wait_cnt = 0
        while self.loop_ctrl_master_update_in_process_flag:
            wait_cnt += 1
            if Device:
                Device.write_ha_sensor_state(INTERVAL, (f"WAIT-{wait_cnt}"))

            time.sleep(2)

#--------------------------------------------------------------------
    def _post_before_update_monitor_msg(self, Device):
        """ Post a monitor msg for all other devices with this device's update reason """
        return

#--------------------------------------------------------------------
    def _post_after_update_monitor_msg(self, Device):
        """ Post a monitor event after the update with the result """
        #device_monitor_msg = (f"Device Monitor > {Device.data_source}, "
        device_monitor_msg = (f"Device Monitor > {Device.dev_data_source}, "
                            f"{Device.icloud_update_reason}, "
                            f"AttrsZone-{Device.sensor_zone}, "
                            f"LocDataZone-{Device.loc_data_zone}, "
                            f"Located-%tage, "
                            f"MobAppGPS-{Device.mobapp_data_fgps}, "
                            f"MobAppState-{Device.mobapp_data_state}), "
                            f"GPS-{Device.loc_data_fgps}")

        if Device.last_device_monitor_msg != device_monitor_msg:
            Device.last_device_monitor_msg = device_monitor_msg
            device_monitor_msg = device_monitor_msg.\
                        replace('%tage', Device.loc_data_time_age)
            post_monitor_msg(Device.devicename, device_monitor_msg)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Internet Connection Error Handler
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _handle_internet_connection_error(self):
        '''
        Handle all internet connection issues

            error   time(secs)  meaning
            True    = 0         Internet just went down - pause tracking
            False   > 0         Internet is back up, resume tracking
        '''
        # Internet just went down. Pause tracking and set timer
        Gb.last_PyiCloud_request_secs = 0

        if (Gb.internet_connection_error
                and Gb.internet_connection_error_secs == 0):
            Gb.internet_connection_error_secs = time_now_secs()
            Gb.internet_connection_status_waiting_for_response = False
            Gb.internet_connection_status_request_cnt = 0
            self._internet_connection_status_msg()

            for Device in Gb.Devices:
                Device.pause_tracking()

            post_event( f"{EVLOG_ALERT}Internet Connection Error > Tracking Paused, "
                        f"{Gb.internet_connection_error_msg} "
                        f"({Gb.internet_connection_error_code})")

            # If the Mobile App is set up, send a message to the 1st Device that can use
            # the notify service
            # if isnot_empty(Gb.mobapp_id_by_mobapp_dname):
            #     Devices = [Device   for Device in Gb.Devices
            #                         if Device.is_tracked and Device.mobapp[NOTIFY] != '']
            #     if isnot_empty(Devices):
            #         message =  {"message":  "Internet Connection Error > iCloud3 Tracking Paused, "
            #                                 f"{secs_to_time(time_now_secs())}, "
            #                                 f"{Gb.internet_connection_error_msg} "
            #                                 f"({Gb.internet_connection_error_code})"}
            #         mobapp_interface.send_message_to_device(Devices[0], message)

            return

        self._internet_connection_status_msg()

        if Gb.internet_connection_error is False:
            self.reset_internet_connection_error()
            return

        if Gb.internet_connection_status_request_cnt == 0:
            pass
        elif Gb.this_update_time[-2:] not in ['00' ,'15', '30', '45']:
            return

        # See if internet is back up

        is_internet_available = Gb.PyiCloudValidateAppleAcct.is_internet_available()
        if is_internet_available:
            self.reset_internet_connection_error()

#...............................................................................
    @staticmethod
    def reset_internet_connection_error():
        start_ic3.initialize_internet_connection_fields()

        data_source_not_set_Devices = [Device
                                    for Device in Gb.Devices
                                    if (Device.dev_data_source == NOT_SET)]

        # If no connection during startup, restart. Otherwiae, resume all tracking
        #if isnot_empty(devices_not_setup):
        notify_Device = None
        if isnot_empty(data_source_not_set_Devices):
            post_event(f"{EVLOG_ALERT}Internet Connection Available > iCloud3 Restarting")
            Gb.restart_icloud3_request_flag = True
        else:
            post_event(f"{EVLOG_ALERT} Internet Connection Available > Tracking Resumed")

            for Device in Gb.Devices:
                Device.resume_tracking()
                # if (notify_Device is None
                #         and Device.mobapp[NOTIFY] != ''):
                #     notify_Device = Device

        # If the Mobile App is set up, send a message to the 1st Device that can use
        # the notify service
        # if notify_Device:
        #     message =  {"message":  "Internet Connection Available > iCloud3 Tracking Resumed, "
        #                             f"{secs_to_time(time_now_secs())}"}
        #     mobapp_interface.send_message_to_device(notify_Device, message)

#...............................................................................
    def _internet_connection_status_msg(self):
        '''
        Display the offline message. Show a progress bar that refreshes on 5-sec
        interval while checking the status
        '''
        if Gb.internet_connection_progress_cnt > 10:
            Gb.internet_connection_progress_cnt = 1
        else:
            Gb.internet_connection_progress_cnt += 1
        progress_bar = '🟡'*Gb.internet_connection_progress_cnt
        evlog_msg =(f"INTERNET CONNECTION ERROR > Since "
                    f"{format_time_age(Gb.internet_connection_error_secs, xago=True)}"
                    f"{CRLF}Checking-{secs_to_time(Gb.internet_connection_status_request_secs)} "
                    f"(#{Gb.internet_connection_status_request_cnt}) "
                    f"{progress_bar}")
        post_evlog_greenbar_msg(evlog_msg)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Perform tasks on a regular time schedule
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _timer_tasks_every_hour(self):
        # See if there is a new iCloud3 version on HACS
        # Gb.hass.loop.create_task(hacs_ic3.check_hacs_icloud3_update_available(Gb.this_update_timr))

        # Clean out lingering StatZone
        Gb.StatZones_to_delete = [StatZone  for StatZone in Gb.StatZones
                                            if StatZone.radius_m == STATZONE_RADIUS_1M]

#--------------------------------------------------------------------
    def _check_apple_acct_2fa_totp_key_request(self):

        # Get all Apple accts needing a 2fa-auth code that have otp tokens
        conf_apple_accts = [conf_apple_acct
                        for conf_apple_acct in Gb.conf_apple_accounts
                        if (conf_apple_acct[CONF_USERNAME] in Gb.PyiCloud_by_username
                            and Gb.PyiCloud_by_username[conf_apple_acct[CONF_USERNAME]].requires_2fa
                            and conf_apple_acct[CONF_TOTP_KEY])]

        if is_empty(conf_apple_accts):
            return

        pyicloud_ic3_interface.send_totp_key(conf_apple_accts)

#--------------------------------------------------------------------
    def _check_mobappp_location_request(self):
        '''
        Update the devices info msg
        Check to see if the MobApp's location needs to be refreshed
        '''
        for Device in Gb.Devices_by_devicename.values():
            Device.display_info_msg(Device.format_info_msg, new_base_msg=True)

            if (Device.mobapp_monitor_flag
                    and Device.mobapp_request_loc_first_secs == 0
                    and Device.mobapp_data_state != Device.loc_data_zone
                    and Device.mobapp_data_state_secs < (Gb.this_update_secs - 120)):
                mobapp_interface.request_location(Device)

#--------------------------------------------------------------------
    def _timer_tasks_midnight(self):

        post_event(f"{EVLOG_IC3_STAGE_HDR}")

        # Close log file, rename to 'icloud.log.1', open a new log file
        archive_ic3log_file()

        log_start_finish_update_banner('start', 'End-of-Day Maintenance', 'Started', '')

        if instr(Gb.conf_general[CONF_LOG_LEVEL], 'auto-reset'):
            start_ic3.set_log_level('info')
            start_ic3.update_conf_file_log_level('info')

        for username, PyiCloud in Gb.PyiCloud_by_username.items():
            PyiCloud.auth_cnt = 0

        if (Gb.WazeHist
                and Gb.WazeHist.is_historydb_USED
                and Gb.internet_connection_error is False):
            Gb.WazeHist.end_of_day_maintenance()

        log_start_finish_update_banner('finish', 'End-of-Day Maintenance', 'Complete', '')
        post_event( f"{EVLOG_IC3_STAGE_HDR}End of Day File Maintenance > "
                    f"iCloud3 v{Gb.version}, "
                    f"{dt_util.now().strftime('%A, %b %d')}")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEVICE STATUS SUPPORT FUNCTIONS FOR GPS ACCURACY, OLD LOC DATA, ETC
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _set_old_location_status(self, Device):
        """
        If this is checked in the icloud location cycle,
        check if the location isold flag. Then check to see if
        the current timestamp is the same as the timestamp on the previous
        poll.

        If this is checked in the mobapp cycle,  the trigger transaction has
        already updated the lat/long so
        you don't want to discard the record just because it is old.
        If in a zone, use the trigger but check the distance from the
        zone when updating the device.

        Update the old_loc_cnt if just_check=False
        """

        if Device.is_location_gps_good or Device.icloud_devdata_useable_flag:
            Device.old_loc_cnt = 0
            Device.old_loc_msg = ''
            return

        try:
            Device.old_loc_cnt += 1

            if Device.old_loc_cnt == 1:
                return

            cnt_msg = f"#{Device.old_loc_cnt}.{Device.max_error_cycle_cnt}"
            cnt_msg = cnt_msg.replace('.0', '')
            # No GPS data takes presidence over offline
            if Device.no_location_data:
                Device.old_loc_msg = f"iCloud Loc > No GPS Data {cnt_msg}"
                Device.update_sensors_flag = False
            elif Device.is_offline:
                Device.old_loc_msg = f"Device > Offline {cnt_msg}"
                Device.update_sensors_flag = False
                statzone.clear_statzone_timer_distance(Device)
            elif Device.is_location_old:
                Device.old_loc_msg = f"iCloud Loc > Old {cnt_msg}, {format_age(Device.loc_data_secs)}"
            elif Device.is_gps_poor:
                Device.old_loc_msg = f"Poor GPS > {cnt_msg}, Accuracy-±{Device.loc_data_gps_accuracy:.0f}m"
            else:
                Device.old_loc_msg = f"iCloud Loc > Unknown {cnt_msg}, {format_age(Device.loc_data_secs)}"

        except Exception as err:
            log_exception(err)
            Device.old_loc_cnt = 0
            Device.old_loc_msg = ''

#--------------------------------------------------------------------
    def _display_secs_to_next_update_info_msg(self, Device):
        '''
        Display the secs until the next update in the next update time field.
        if between 90s to -90s. if between -90s and -120s, resisplay time
        without the age to make sure it goes away. The age may be for a non-Home
        zone but displat it in the Home zone sensor.
        '''
        if (Gb.use_data_source_ICLOUD is False
                or Device.is_data_source_ICLOUD is False
                or Device.is_tracking_paused):
            return

        try:
            age_secs = secs_to(Device.next_update_secs)
            if (age_secs <= -90 or age_secs >= 90):
                return age_secs

            next_update_hhmmss = Device.sensors[NEXT_UPDATE]
            Device.sensors[NEXT_UPDATE] = f"{age_secs} secs"
            Device.write_ha_sensors_state([NEXT_UPDATE])

        except Exception as err:
            log_exception(err)
            pass

        return

############ LAST LINE ###########