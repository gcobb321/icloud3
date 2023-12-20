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


import os
import time
import traceback
from re import match
import voluptuous as vol
from   homeassistant.util                   import slugify
import homeassistant.util.yaml.loader       as yaml_loader
import homeassistant.util.dt                as dt_util
from   homeassistant.util.location          import distance
import homeassistant.helpers.config_validation as cv
from   homeassistant.helpers.event          import track_utc_time_change
from   homeassistant.components.device_tracker import PLATFORM_SCHEMA
from   homeassistant.helpers.dispatcher     import dispatcher_send
from homeassistant import config_entries

# =================================================================

from .global_variables  import GlobalVariables as Gb
from .const             import (VERSION,
                                HOME, NOT_HOME, NOT_SET, NOT_SET_FNAME, HIGH_INTEGER, RARROW,
                                STATIONARY, TOWARDS, AWAY_FROM, EVLOG_IC3_STAGE_HDR,
                                ICLOUD, ICLOUD_FNAME, TRACKING_NORMAL,
                                CMD_RESET_PYICLOUD_SESSION, NEAR_DEVICE_DISTANCE,
                                DISTANCE_TO_OTHER_DEVICES, DISTANCE_TO_OTHER_DEVICES_DATETIME,
                                OLD_LOCATION_CNT, AUTH_ERROR_CNT,
                                IOSAPP_UPDATE, ICLOUD_UPDATE, ARRIVAL_TIME, HOME_DISTANCE,
                                EVLOG_UPDATE_START, EVLOG_UPDATE_END, EVLOG_ALERT, EVLOG_NOTICE,
                                FMF, FAMSHR, IOSAPP, IOSAPP_FNAME,
                                ENTER_ZONE, EXIT_ZONE, GPS, INTERVAL, NEXT_UPDATE, NEXT_UPDATE_TIME,
                                ZONE, CONF_LOG_LEVEL, STATZONE_RADIUS_1M,
                                )
from .const_sensor      import (SENSOR_LIST_DISTANCE, )
from .support           import start_ic3
from .support           import start_ic3_control
from .support           import stationary_zone as statzone
from .support           import iosapp_data_handler
from .support           import iosapp_interface
from .support           import pyicloud_ic3_interface
from .support           import icloud_data_handler
from .support           import service_handler
from .support           import determine_interval as det_interval

from .helpers.common    import (instr, is_zone, is_statzone, isnot_statzone, isnot_zone,
                                list_to_str,)
from .helpers.messaging import (broadcast_info_msg,
                                post_event, post_error_msg, post_monitor_msg, post_internal_error,
                                open_ic3_log_file, post_alert, clear_alert,
                                log_info_msg, log_exception, log_start_finish_update_banner,
                                log_debug_msg, close_reopen_ic3_log_file, archive_log_file,
                                _trace, _traceha, )
from .helpers.time_util import (time_now_secs, secs_to_time,  secs_to, secs_since, time_now,
                                secs_to_time, secs_to_time_str, secs_to_age_str,
                                datetime_now,  calculate_time_zone_offset, secs_to_24hr_time,
                                secs_to_time_age_str, secs_to_datetime, )
from .helpers.dist_util import (m_to_ft_str, calc_distance_km, format_dist_km, format_dist_m, )

# zone_data constants - Used in the select_zone function
ZD_DIST_M     = 0
ZD_ZONE       = 1
ZD_NAME       = 2
ZD_RADIUS     = 3
ZD_DISPLAY_AS = 4
ZD_CNT        = 5

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3:
    """iCloud3 Device Tracker Platform"""

    def __init__(self):

        Gb.started_secs                    = time_now_secs()
        Gb.hass_configurator_request_id    = {}
        Gb.version                         = VERSION

        Gb.polling_5_sec_loop_running      = False
        self.pyicloud_refresh_time         = {}     # Last time Pyicloud was refreshed for the trk method
        self.pyicloud_refresh_time[FMF]    = 0
        self.pyicloud_refresh_time[FAMSHR] = 0
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
                    f"Since-{secs_to_time_age_str(self.loop_ctrl_device_update_in_process_secs)}")
        log_debug_msg(log_msg)

#--------------------------------------------------------------------
    def start_icloud3(self):

        try:
            if Gb.start_icloud3_inprocess_flag:
                return False

            service_handler.issue_ha_notification()

            self.start_timer = time_now_secs()
            self.initial_locate_complete_flag  = False
            self.startup_log_msgs           = ''
            self.startup_log_msgs_prefix    = ''

            start_ic3_control.stage_1_setup_variables()
            start_ic3_control.stage_2_prepare_configuration()
            if Gb.polling_5_sec_loop_running is False:
                broadcast_info_msg("Set Up 5-sec Polling Cycle")
                Gb.polling_5_sec_loop_running = True
                track_utc_time_change(Gb.hass, self._polling_loop_5_sec_device,
                        second=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])

            start_ic3_control.stage_3_setup_configured_devices()
            stage_4_success = start_ic3_control.stage_4_setup_data_sources()
            if stage_4_success is False or Gb.reinitialize_icloud_devices_flag:
                start_ic3_control.stage_4_setup_data_sources(retry=True)

            start_ic3_control.stage_5_configure_tracked_devices()
            start_ic3_control.stage_6_initialization_complete()
            start_ic3_control.stage_7_initial_locate()

            close_reopen_ic3_log_file(closed_by='iCloud3 Initialization')

            Gb.trace_prefix = ''
            Gb.EvLog.display_user_message('', clear_alert=True)
            Gb.initial_icloud3_loading_flag = False
            Gb.start_icloud3_inprocess_flag = False
            Gb.startup_stage_status_controls = []
            Gb.broadcast_info_msg = None

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
        Gb.this_update_secs   = time_now_secs()
        Gb.this_update_time   = dt_util.now().strftime('%H:%M:%S')

        if Gb.config_flow_updated_parms != {''}:
            start_ic3.process_config_flow_parameter_updates()

        # Restart iCloud via service call from EvLog or config_flow
        if Gb.restart_icloud3_request_flag:
            self.start_icloud3()
            Gb.restart_icloud3_request_flag = False

        # Exit 5-sec loop if no devices, updating a device now, or restarting iCloud3
        if (self.loop_ctrl_master_update_in_process_flag
                or Gb.conf_devices == []
                or Gb.start_icloud3_inprocess_flag):

            # Authentication may take a long time, Display a status message before exiting loop
            if (Gb.pyicloud_auth_started_secs > 0):
                info_msg = ("Waiting for iCloud Account Authentication, Requested at "
                            f"{secs_to_time_age_str(Gb.pyicloud_auth_started_secs)} ")
                for Device in Gb.Devices_by_devicename.values():
                    Device.display_info_msg(info_msg)
                if Gb.this_update_time[-2:] in ['00', '15', '30', '45']:
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

        elif Gb.evlog_action_request == CMD_RESET_PYICLOUD_SESSION:
            pyicloud_ic3_interface.pyicloud_reset_session()
            Gb.evlog_action_request = ''

        try:
            #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
            #   CHECK TIMERS
            #<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>
            self._main_5sec_loop_special_time_control()

            # Start of uncommented out code to test of moving device into a statzone while home
            # if Gb.this_update_time.endswith('5:00'):
            #     if Gb.Devices[0].StatZone is None:
            #         _trace(f"{Gb.Devices[0].fname} creating")
            #         statzone.move_device_into_statzone(Gb.Devices[0])
            #         _trace(f"{Gb.Devices[0].StatZone.zone} created")
            # if Gb.this_update_time.endswith('0:00'):
            #     if Gb.Devices[0].StatZone:
            #         _trace(f"{Gb.Devices[0].StatZone.zone} removing")
            #         statzone.remove_statzone(Gb.Devices[0].StatZone, Gb.Devices[0])
            #         _trace(f"{Gb.Devices[0].StatZone.zone} removed")
            # End of uncommented out code to test of moving device into a statzone while home

            if Gb.all_tracking_paused_flag:
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
                self._main_5sec_loop_update_tracked_devices_iosapp(Device)
                self._main_5sec_loop_update_tracked_devices_icloud(Device)

                self._display_secs_to_next_update_info_msg(Device)
                # Uncomment for testing self._log_zone_enter_exit_activity(Device)
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
                Device.update_battery_data_from_iosapp()
                Device.display_battery_info_msg()

        except Exception as err:
            log_exception(err)

        Gb.any_device_was_updated_reason = ''
        self.initialize_5_sec_loop_control_flags()
        self._display_clear_authentication_needed_msg()
        self.initial_locate_complete_flag  = True

        Gb.trace_prefix = 'WRAPUP > '

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
                Device.sensors[DISTANCE_TO_OTHER_DEVICES_DATETIME] = Device.dist_to_other_devices_datetime
                Device.write_ha_sensors_state(SENSOR_LIST_DISTANCE)

            Gb.dist_to_other_devices_update_sensor_list = set()

        Gb.trace_prefix = ''


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   MAIN 5-SEC LOOP PROCESSING CONTROLLERS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _main_5sec_loop_update_tracked_devices_iosapp(self, Device):
        '''
        Update the device based on iOS App data
        '''
        if (Device.iosapp_monitor_flag is False
                or Gb.conf_data_source_IOSAPP is False):
            return

        Gb.trace_prefix = 'IOSAPP > '
        devicename = Device.devicename

        if Gb.this_update_secs >= Device.passthru_zone_timer:
            Device.reset_passthru_zone_delay()

        iosapp_data_handler.check_iosapp_state_trigger_change(Device)

        # Turn off monitoring the iOSApp if excessive errors
        if Device.iosapp_data_invalid_error_cnt > 50:
            Device.iosapp_data_invalid_error_cnt = 0
            Device.iosapp_monitor_flag = False
            event_msg =("iCloud3 Error > iOSApp entity error cnt exceeded, "
                        "iOSApp monitoring stopped. iCloud monitoring will be used.")
            post_event(devicename, event_msg)
            return

        # If the iOS App is the primary and data source next_update time is reached, get the
        # old location threshold. Send a location request to the iosapp device if the
        # data is older than the threshold, the next_update is newer than the iosapp data
        # and the next_update and data time is after the last request was sent.
        if (Device.primary_data_source == IOSAPP
                and Device.iosapp_data_updated_flag is False
                and Device.next_update_secs <= Gb.this_update_secs):
            if Device.interval_secs <= 30:
                iosapp_interface.request_location(Device, is_alive_check=False)
            else:
                Device.calculate_old_location_threshold()

                if  (secs_since(Device.loc_data_secs) > Device.old_loc_threshold_secs
                        and Device.next_update_secs > Device.loc_data_secs
                        and Device.next_update_secs > Device.iosapp_request_loc_sent_secs):
                    iosapp_interface.request_location(Device, is_alive_check=False, force_request=True)

                elif ((Gb.this_update_secs - Device.next_update_secs) % Device.interval_secs == 0
                        and Device.interval_secs >= 900):
                    iosapp_interface.request_location(Device, is_alive_check=False, force_request=True)

        # The Device is in a StatZone but the iosapp is not home. Send a location request to try to
        # sync them. Do this every 10-mins if the time since the last request is older than 10-min ago
        elif (Device.is_in_statzone
                and Device.iosapp_data_state == NOT_HOME
                and (secs_since(Device.iosapp_request_loc_sent_secs) > 36000
                    or Device.iosapp_request_loc_sent_secs == 0)
                and Gb.this_update_time.endswith('0:00')):
            iosapp_interface.request_location(Device, is_alive_check=False, force_request=True)

        # The iosapp may be entering or exiting another Device's Stat Zone. If so,
        # reset the iosapp information to this Device's Stat Zone and continue
        if Device.iosapp_data_updated_flag:
            Device.iosapp_data_invalid_error_cnt = 0

            if instr(Device.iosapp_data_change_reason, ' ') is False:
                Device.iosapp_data_change_reason = Device.iosapp_data_change_reason.title()
            event_msg = f"Trigger > {Device.iosapp_data_change_reason}"
            post_event(devicename, event_msg)

            # If using the passthru zone delay:
            #    If entering a zone, set it if it is not set
            #    If exiting, reset it
            if Gb.is_passthru_zone_used:
                if instr(Device.iosapp_data_change_reason, ENTER_ZONE):
                    if Device.set_passthru_zone_delay(IOSAPP,
                                Device.iosapp_zone_enter_zone, Device.iosapp_data_secs):
                        return

                elif instr(Device.iosapp_data_change_reason, EXIT_ZONE):
                    Device.reset_passthru_zone_delay()

            # Make sure exit distance is outside of statzone. If inside StatZone,
            # the zone needs to be removed and another on assigned out the iosapp
            # will keep exiting  when the device is still in it. it also seems to
            # stop monitoring the zone for this device but other devices seem to
            # be ok
            if (instr(Device.iosapp_data_change_reason, EXIT_ZONE)
                    and is_statzone(Device.iosapp_zone_exit_zone)
                    and Device.StatZone
                    and Device.iosapp_zone_exit_dist_m < Device.StatZone.radius_m):

                event_msg =(f"{EVLOG_ALERT}Trigger Changed > {Device.iosapp_data_change_reason}, "
                            f"Distance less than zone size "
                            f"{Device.StatZone.display_as} {Device.iosapp_zone_exit_dist_m} < {Device.StatZone.radius_m}")
                post_event(devicename, event_msg)

                statzone.kill_and_recreate_unuseable_statzone(Device)

            else:
                iosapp_data_handler.reset_statzone_on_enter_exit_trigger(Device)

            self._validate_new_iosapp_data(Device)
            self.process_updated_location_data(Device,IOSAPP_FNAME)

        # Send a location request to device if needed
        iosapp_data_handler.check_if_iosapp_is_alive(Device)

#----------------------------------------------------------------------------
    def _main_5sec_loop_update_tracked_devices_icloud(self, Device):
        '''
        Update the device based on iCloud data
        '''

        if Gb.PyiCloud is None:
            return

        Gb.trace_prefix = 'ICLOUD > '
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

        # Update device info. Get data from FmF or FamShr
        icloud_data_handler.request_icloud_data_update(Device)

        # Do not redisplay update reason if in error retries. It has already been displayed.
        if icloud_data_handler.update_device_with_latest_raw_data(Device) is False:
            Device.icloud_acct_error_flag = True

        if Device.icloud_devdata_useable_flag:
            Device.display_info_msg(Device.icloud_update_reason)
            event_msg = f"Trigger > {Device.icloud_update_reason}"
            post_event(devicename, event_msg)

        # See if the Stat Zone timer has expired or if the Device has moved a lot. Do this
        # even if the sensors are not updated to make sure the Stat Zone is set up and be
        # seleted for the Device
        self._move_into_statzone_if_timer_reached(Device)

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
        self.process_updated_location_data(Device, ICLOUD_FNAME)

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

        Gb.trace_prefix = 'MONITOR > '
        if Device.is_tracking_paused:
            return

        Device.FromZone_NextToUpdate = Device.FromZone_Home
        Device.FromZone_TrackFrom    = Device.FromZone_Home
        Device.last_track_from_zone  = HOME

        if Device.iosapp_monitor_flag and Gb.conf_data_source_IOSAPP:
            iosapp_data_handler.check_iosapp_state_trigger_change(Device)

        if Device.is_tracking_resumed:
            Device.tracking_status = TRACKING_NORMAL
        elif Device.is_next_update_time_reached is False:
            Device.calculate_distance_moved()
            if Device.loc_data_dist_moved_km < .05:
                return
        elif Device.loc_data_latitude == 0:
            return

        Device.update_sensors_flag  = True
        Device.icloud_initial_locate_done = True
        Device.icloud_update_reason = 'Monitored Device Update'

        event_msg =(f"Trigger > Moved {format_dist_km(Device.loc_data_dist_moved_km)}") #{Gb.any_device_was_updated_reason}")
        post_event(Device.devicename, event_msg)

        self.process_updated_location_data(Device, '')
        Device.update_sensor_values_from_data_fields()

#----------------------------------------------------------------------------
    def _main_5sec_loop_icloud_prefetch_control(self):
        '''
        Update the iCloud location data if it the next_update_time will be reached
        in the next 10-seconds
        '''
        if Gb.PyiCloud is None:
            return

        if Device := self._get_icloud_data_prefetch_device():
            Gb.trace_prefix = 'PREFETCH > '
            log_start_finish_update_banner('start', Device.devicename, 'icloud prefetch', '')
            post_monitor_msg(Device.devicename, "iCloud Location Requested (prefetch)")

            Device.icloud_devdata_useable_flag = \
                icloud_data_handler.update_PyiCloud_RawData_data(Device,
                        results_msg_flag=Device.is_location_old_or_gps_poor)

            log_start_finish_update_banner('finish', Device.devicename, 'icloud prefetch', '')
            Gb.trace_prefix = ''

#----------------------------------------------------------------------------
    def _main_5sec_loop_special_time_control(self):
        '''
        Various functions that are run based on the time-of-day
        '''

        time_now_mmss = Gb.this_update_time[-5:]
        time_now_ss   = Gb.this_update_time[-2:]
        time_now_mm   = Gb.this_update_time[3:5] if time_now_ss == '00' else ''

        # Every hour
        if time_now_mmss == '00:00':
            self._timer_tasks_every_hour()

        # At midnight
        if Gb.this_update_time == '00:00:00':
            self._timer_tasks_midnight()

        # At 1am
        elif Gb.this_update_time == '01:00:00':
            calculate_time_zone_offset()

        if (Gb.this_update_secs >= Gb.EvLog.clear_secs):
            Gb.EvLog.update_event_log_display(show_one_screen=True)

        # Every minute
        if time_now_ss == '00':
            close_reopen_ic3_log_file()

            for Device in Gb.Devices_by_devicename.values():
                Device.display_info_msg(Device.format_info_msg, new_base_msg=True)
                if (Device.iosapp_monitor_flag
                        and Device.iosapp_request_loc_first_secs == 0
                        and Device.iosapp_data_state != Device.loc_data_zone
                        and Device.iosapp_data_state_secs < (Gb.this_update_secs - 120)):
                    iosapp_interface.request_location(Device)


        # Every 30-secs
        if time_now_ss == '30':
            close_reopen_ic3_log_file()

        # Every 15-minutes
        if time_now_mm in ['00', '15', '30', '45']:
            if Gb.log_debug_flag:
                for devicename, Device in Gb.Devices_by_devicename_tracked.items():
                    Device.log_data_fields()

            for devicename, Device in Gb.Devices_by_devicename.items():
                if Device.dist_apart_msg:
                    event_msg =(f"Nearby Devices > (<{NEAR_DEVICE_DISTANCE}m), "
                                f"{Device.dist_apart_msg}, "
                                f"Checked-{secs_to_time(Device.near_device_checked_secs)}")
                    if event_msg != Device.last_near_devices_msg:
                        Device.last_near_devices_msg = event_msg
                        post_event(devicename, event_msg)

        # Every 1/2-hour
        if time_now_mm in ['00', '30']:
            pass

        if Gb.PyiCloud is not None and Gb.this_update_secs >= Gb.authentication_error_retry_secs:
            post_event(f"Retry Authentication > "
                        f"Timer={secs_to_time(Gb.authentication_error_retry_secs)}")
            pyicloud_ic3_interface.authenticate_icloud_account(Gb.PyiCloud)

        service_handler.issue_ha_notification()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE THE DEVICE IF A STATE OR TRIGGER CHANGE WAS RECIEVED FROM THE IOSAPP
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _validate_new_iosapp_data(self, Device):
        """
        Update the devices location using data from the iOS App
        """
        if (Gb.start_icloud3_inprocess_flag
                or Device.iosapp_monitor_flag is False):
            return ''

        update_reason = Device.iosapp_data_change_reason
        devicename    = Device.devicename

        Device.update_sensors_flag           = False
        Device.iosapp_request_loc_first_secs = 0
        Device.iosapp_request_loc_last_secs  = 0

        Device.FromZone_BeingUpdated = Device.FromZone_Home

        if (Device.is_tracking_paused
                or Device.iosapp_data_latitude == 0
                or Device.iosapp_data_longitude == 0):
            return

        if Gb.any_device_was_updated_reason == '':
            Gb.any_device_was_updated_reason = f'{Device.iosapp_data_change_reason}, {Device.fname_devtype}'
        return_code = IOSAPP_UPDATE

        # Check to see if the location is outside the zone without an exit trigger
        for from_zone, FromZone in Device.FromZones_by_zone.items():
            if is_zone(from_zone):
                info_msg = self._is_outside_zone_no_exit( Device, from_zone, '',
                                        Device.iosapp_data_latitude,
                                        Device.iosapp_data_longitude)

                if Device.outside_no_exit_trigger_flag:
                    post_event(devicename, info_msg)

                    # Set located time to trigger time so it won't fire as trigger change again
                    Device.loc_data_secs = Device.iosapp_data_secs + 10
                    return

        try:
            log_start_finish_update_banner('start', devicename, IOSAPP_FNAME, update_reason)
            Device.update_sensors_flag = True

            # Request the iosapp location if iosapp location is old and the next update
            # time is reached and less than 1km from the zone
            if (Device.is_iosapp_data_old
                    and Device.is_next_update_time_reached
                    and Device.FromZone_NextToUpdate.zone_dist < 1
                    and Device.FromZone_NextToUpdate.dir_of_travel == TOWARDS
                    and Device.isnot_inzone):

                iosapp_interface.request_location(Device)

                Device.update_sensors_flag = False

            if Device.update_sensors_flag:
                Device.update_dev_loc_data_from_raw_data_IOSAPP()

        except Exception as err:
            post_internal_error('iOSApp Update', traceback.format_exc)
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

        update_reason = Device.icloud_update_reason
        devicename    = Device.devicename
        zone          = Device.loc_data_zone

        if Gb.any_device_was_updated_reason == '':
            Gb.any_device_was_updated_reason = f'{Device.icloud_update_reason}, {Device.fname_devtype}'

        Device.icloud_update_retry_flag     = False
        Device.iosapp_request_loc_last_secs = 0

        Device.FromZone_BeingUpdated = Device.FromZone_Home

        log_start_finish_update_banner('start', devicename, ICLOUD_FNAME, update_reason)

        try:
            Device.update_sensors_flag = True
            Device.calculate_old_location_threshold()

            #icloud data overrules device data which may be stale
            latitude  = Device.loc_data_latitude
            longitude = Device.loc_data_longitude

            # See if the GPS accuracy is poor, the locate is old, there is no location data
            # available or the device is offline
            self._check_old_loc_poor_gps(Device)

            # Check to see if currently in a zone. If so, check the zone distance.
            # If new location is outside of the zone and inside radius*4, discard
            # by treating it as poor GPS
            if isnot_statzone(zone) or Device.sensor_zone == NOT_SET:
                Device.outside_no_exit_trigger_flag = False
                Device.update_sensors_error_msg= ''

            else:
                Device.update_sensors_error_msg = \
                            self._is_outside_zone_no_exit(Device, zone, '', latitude, longitude)

            # if Device.is_offline or Device.is_pending:
            if Device.is_offline:
                offline_msg = ( f"Device Status Exception > {Device.fname_devtype}, "
                                f"{Device.device_status_msg}")
                if instr(Device.update_sensors_error_msg, 'Offline') is False:
                    log_info_msg(Device.devicename, offline_msg)
                    post_event(Device.devicename, offline_msg)

            # 'Verify Location' update reason overrides all other checks and forces an iCloud update
            # if Device.icloud_update_reason == 'Verify Location':
            #     pass

            # Bypass all update needed checks and force an iCloud update
            if Device.icloud_force_update_flag:
                # Device.icloud_force_update_flag = False
                pass

            elif Device.icloud_devdata_useable_flag is False or Device.icloud_acct_error_flag:
                Device.update_sensors_flag = False

            # Ignore old location when in a zone and discard=False
            # let normal next time update check process
            elif (Device.is_gps_poor
                    and Gb.discard_poor_gps_inzone_flag
                    and Device.is_inzone
                    and Device.outside_no_exit_trigger_flag is False):

                Device.old_loc_cnt -= 1
                Device.old_loc_msg = ''

                if Device.is_next_update_time_reached is False:
                    Device.update_sensors_flag = False

            # Outside zone, no exit trigger check. This is valid for location less than 2-minutes old
            # added 2-min check so it wouldn't hang with old iosapp data. Force a location update
            elif (Device.outside_no_exit_trigger_flag
                    and secs_since(Device.iosapp_data_secs) < 120):
                pass

            # Discard if the next update time has been reached and location is old but
            # do the update anyway if it is newer than the last update. This prevents
            # the situation where a non-iOS App device (Watch) that is always getting
            # data that is a little old from never updating and eventually ending up
            # with a long (2-hour) interval time and never getting updated.
            if (Device.is_location_old_or_gps_poor
                    and Device.is_tracked
                    and Device.is_next_update_time_reached):

                # Reset the  error cnt if the still old data is newer than last time (rc9)
                if (Device.old_loc_cnt > 4
                        and Device.FromZone_Home.interval_secs >= 300
                        and Device.loc_data_secs > Device.last_update_loc_secs):
                    event_msg = (f"Location Old > Using Anyway, "
                                f"{Device.last_update_loc_time}{RARROW}"
                                f"{Device.loc_data_time}")
                    post_event(Device.devicename, event_msg)
                    Device.old_loc_cnt = 0
                    Device.old_loc_msg = ''
                    Device.last_update_loc_secs = Device.loc_data_secs
                else:
                    Device.update_sensors_error_msg = Device.old_loc_msg
                    Device.update_sensors_flag = False

            # See if the Stat Zone timer has expired or if the Device has moved a lot. Do this
            # again (after the initial update needed check) since the data has been updated
            # and the gps might be good now where it was bad earlier.
            if self._move_into_statzone_if_timer_reached(Device):
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
    def process_updated_location_data(self, Device, update_requested_by):
        try:
            devicename = Gb.devicename = Device.devicename
            # Device.tracking_status = TRACKING_NORMAL

            # Makw sure the Device iosapp_state is set to the statzone if the device is in a statzone
            # and the Device iosapp state value is not_nome. The Device state value can be out of sync
            # if the iosapp was updated but no trigger or state change was detected when a FamShr
            # update is processed since the Device's location gps did not actually change
            iosapp_data_handler.sync_iosapp_data_state_statzone(Device)

            # Location is good or just setup the StatZone. Determine next update time and update interval,
            # next_update_time values and sensors with the good data
            if Device.update_sensors_flag:
                self._get_tracking_results_and_update_sensors(Device, update_requested_by)

            else:
                # Old location, poor gps etc. Determine the next update time to request new location info
                # with good data (hopefully). Update interval, next_update_time values and sensors with the time
                det_interval.determine_interval_after_error(Device, counter=OLD_LOCATION_CNT)
                if (Device.old_loc_cnt > 0
                        and (Device.old_loc_cnt % 4) == 0):
                    iosapp_interface.request_location(Device)

            Device.icloud_force_update_flag = False
            Device.write_ha_sensors_state()
            Device.write_ha_device_from_zone_sensors_state()
            Device.write_ha_device_tracker_state()
            self._log_zone_enter_exit_activity(Device)

            # Refresh the EvLog if this is an initial locate or the devicename is displayed
            if (devicename == Gb.EvLog.evlog_attrs["devicename"]
                    or (self.initial_locate_complete_flag == False
                        and devicename == Gb.Devices[0].devicename)):
                Gb.EvLog.update_event_log_display(devicename)

            log_start_finish_update_banner('finish',  devicename,
                                    f"{Device.data_source_fname}/{Device.dev_data_source}",
                                    "gen update")

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
        Device.selected_zone_results = self._select_zone(Device)
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
        update_reason = Device.iosapp_data_change_reason \
                                    if update_requested_by == IOSAPP_FNAME \
                                    else Device.icloud_update_reason

        if Gb.PyiCloud:
            icloud_data_handler.update_device_with_latest_raw_data(Device)
        else:
            Device.update_dev_loc_data_from_raw_data_IOSAPP()

        if Device.is_tracked and Device.is_location_data_rejected():
            if Device.is_dev_data_source_FAMSHR_FMF:
                det_interval.determine_interval_after_error(Device, counter=OLD_LOCATION_CNT)

        elif Device.is_monitored and Device.is_offline:
            det_interval.determine_interval_monitored_device_offline(Device)

        else:
            post_event(devicename, EVLOG_UPDATE_START)

            self._post_before_update_monitor_msg(Device)

            if self._determine_interval_and_next_update(Device):
                Device.update_sensor_values_from_data_fields()

            event_msg = EVLOG_UPDATE_END
            update_requested_by = 'Tracking' if Device.is_tracked else 'Monitor'
            from_zone = Device.FromZone_TrackFrom.from_zone

            event_msg += f"{Device.dev_data_source} Results > "
            if Device.FromZone_TrackFrom.dir_of_travel == TOWARDS:
                event_msg+=(f"Arrive: {Device.FromZone_TrackFrom.from_zone_display_as[:8]} at "
                            f"{Device.sensors[ARRIVAL_TIME]}")
            else:
                event_msg+=(f"Next Update: {Device.FromZone_TrackFrom.next_update_time}")

            post_event(devicename, event_msg)

        self._post_after_update_monitor_msg(Device)

#----------------------------------------------------------------------------
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
            if Device.is_dev_data_source_IOSAPP:
                Device.trigger = (f"{Device.iosapp_data_trigger}@{Device.iosapp_data_time}")
            else:
                Device.trigger = (f"{Device.dev_data_source}@{Device.loc_data_datetime[11:19]}")

            self._update_current_zone(Device)

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
                log_start_finish_update_banner('start', devicename, Device.dev_data_source, from_zone)

                det_interval.determine_interval(Device, FromZone)

            # Determine zone to be tracked from now that all of the zone distances have been determined
            det_interval.determine_TrackFrom_zone(Device)

            # pr1.4
            # If the location is old and an update is being done (probably from an iosapp trigger),
            # see if the error interval is greater than this update interval. Is it is, Reset the counter
            if Device.old_loc_cnt > 8:
                error_interval_secs, error_cnt, max_error_cnt = det_interval.get_error_retry_interval(Device)
                if error_interval_secs > Device.interval_secs:
                    event_msg =(f"Location Old #{Device.old_loc_cnt} > Old Loc Counter Reset, "
                                f"NextUpdate-{secs_to_age_str(Device.interval_sec)}, "
                                f"OldLocRetryUpdate-{secs_to_age_str(error_interval_secs)}")
                    Device.old_loc_cnt = 0

            log_start_finish_update_banner('finish', devicename, Device.dev_data_source, from_zone)

        except Exception as err:
            log_exception(err)
            post_internal_error('Det IntervalLoop', traceback.format_exc)

        return True

#------------------------------------------------------------------------------
    def _request_update_devices_no_iosapp_same_zone_on_exit(self, Device):
        '''
        The Device is exiting a zone. Check all other Devices that were in the same
        zone that do not have the iosapp installed and set the next update time to
        5-seconds to see if that device also exited instead of waiting for the other
        devices inZone interval time to be reached.

        Check the next update time to make sure it has not already been updated when
        the device without the iOS app is with several devices that left the zone.
        '''
        devices_to_update = [_Device
                        for _Device in Gb.Devices_by_devicename_tracked.values()
                        if (Device is not _Device
                            and _Device.is_data_source_IOSAPP is False
                            and _Device.loc_data_zone == Device.loc_data_zone
                            and secs_to(_Device.FromZone_Home.next_update_secs) > 60)]

        if devices_to_update == []:
            return

        for _Device in devices_to_update:
            _Device.icloud_force_update_flag = True
            det_interval.update_all_device_fm_zone_sensors_interval(_Device, 15)
            event_msg = f"Trigger > Check Zone Exit, GeneratedBy-{Device.fname}"
            post_event(_Device.devicename, event_msg)

#------------------------------------------------------------------------------
    def _log_zone_enter_exit_activity(self, Device):
        '''
        An entry can be written to the 'zone-log-[year]-[device-[zone].csv' file.
        This file shows when a device entered & exited a zone, the time the device was in
        the zone, the distance to Home, etc. It can be imported into a spreadsheet and used
        at year end for expense calculations.
        '''
        # Uncomment the following for testing
        # if Gb.this_update_time.endswith('0:00') or Gb.this_update_time.endswith('5:00'):
        #     Device.iosapp_zone_exit_secs = time_now_secs()
        #     Device.iosapp_zone_exit_time = time_now()
        #     Device.last_zone = HOME
        #     pass
        # elif 'none' in Device.log_zones:

        if ('none' in Device.log_zones
                or Device.log_zone == Device.loc_data_zone
                or (Device.log_zone == '' and Device.loc_data_zone not in Device.log_zones)):
            return

        if Device.log_zone == '':
            Device.log_zone = Device.loc_data_zone
            Device.log_zone_enter_secs = Gb.this_update_secs
            event_msg = f"Log Zone Activity > Logging Started-{Gb.zone_display_as[Device.log_zone]}"
            post_event(Device.devicename, event_msg)
            return

        # Must be in the zone for at least 4-minutes
        inzone_secs = secs_since(Device.log_zone_enter_secs)
        inzone_hrs  = inzone_secs/3600
        if inzone_secs < 240: return

        filename = (f"zone-log-{dt_util.now().strftime('%Y')}-"
                    f"{Device.log_zones_filename}.csv")

        with open(filename, 'a', encoding='utf8') as f:
            if os.path.getsize(filename) == 0:
                recd = "Date,Zone Enter Time,Zone Exit Time,Time (Mins),Time (Hrs),Distance (Home),Zone,Device\n"
                f.write(recd)

            recd = (f"{datetime_now()[:10]},"
                    f"{secs_to_datetime(Device.log_zone_enter_secs)},"
                    f"{secs_to_datetime(Gb.this_update_secs)},"
                    f"{inzone_secs/60:.0f},"
                    f"{inzone_hrs:.2f},"
                    f"{Device.sensors[HOME_DISTANCE]:.2f},"
                    f"{Device.log_zone},"
                    f"{Device.devicename}"
                    "\n")
            f.write(recd)
            event_msg = f"Log Zone Activity > Logging Ended-{Gb.zone_display_as[Device.log_zone]}"
            post_event(Device.devicename, event_msg)

        if Device.loc_data_zone in Device.log_zones:
            Device.log_zone = Device.loc_data_zone
            Device.log_zone_enter_secs = Gb.this_update_secs
        else:
            Device.log_zone = ''
            Device.log_zone_enter_secs = 0

#------------------------------------------------------------------------------
#
#   DETERMINE THE ZONE THE DEVICE IS CURRENTLY IN
#
#------------------------------------------------------------------------------
    def _update_current_zone(self, Device, display_zone_msg=True):

        '''
        Get current zone of the device based on the location

        Parameters:
            selected_zone_results - The zone may have already been selected. If so, this list
                            is the results from a previous _select_zone
            display_zone_msg - True if the msg should be posted to the Event Log

        Returns:
            Zone    Zone object
            zone    zone name or not_home if not in a zone

        NOTE: This is the same code as (active_zone/async_active_zone) in zone.py
        but inserted here to use zone table loaded at startup rather than
        calling hass on all polls
        '''

        # Zone selected may have been done when determing if the device just entered a zone
        # during the passthru check. If so, use it and then reset it
        if Device.selected_zone_results == []:
            ZoneSelected, zone_selected, zone_selected_dist_m, zones_distance_list = \
                self._select_zone(Device)
        else:
            ZoneSelected, zone_selected, zone_selected_dist_m, zones_distance_list = \
                Device.selected_zone_results
            Device.selected_zone_results = []

        if zone_selected == 'unknown':
            return ZoneSelected, zone_selected

        if ZoneSelected is None:
            ZoneSelected         = Gb.Zones_by_zone[NOT_HOME]
            zone_selected        = NOT_HOME
            zone_selected_dist_m = 0

        # In a zone but if not in a track from zone and was in a Stationary Zone,
        # reset the stationary zone
        elif Device.is_in_statzone and isnot_statzone(zone_selected):
            statzone.exit_statzone(Device)


        # Get distance between zone selected and current zone to see if they overlap.
        # If so, keep the current zone
        if (zone_selected != NOT_HOME
                and self._is_overlapping_zone(Device.loc_data_zone, zone_selected)):
            zone_selected = Device.loc_data_zone
            ZoneSelected  = Gb.Zones_by_zone[Device.loc_data_zone]

        # The zone changed
        elif Device.loc_data_zone != zone_selected:
            # See if any device without the iosapp was in this zone. If so, request a
            # location update since it was running on the inzone timer instead of
            # exit triggers from the ios app
            if (Gb.iosapp_monitor_any_devices_false_flag
                    and zone_selected == NOT_HOME
                    and Device.loc_data_zone != NOT_HOME):
                self._request_update_devices_no_iosapp_same_zone_on_exit(Device)

            Device.loc_data_zone        = zone_selected
            Device.zone_change_secs     = time_now_secs()
            Device.zone_change_datetime = datetime_now()

            # The zone changed, update the enter/exit zone times if the
            # Device does not use the iOS App
            if zone_selected == NOT_HOME:
                if (Device.iosapp_monitor_flag is False
                        or Device.iosapp_zone_exit_secs == 0):
                    Device.iosapp_zone_exit_secs = time_now_secs()
                    Device.iosapp_zone_exit_time = time_now()

            else:
                if (Device.iosapp_monitor_flag is False
                        or Device.iosapp_zone_enter_secs == 0):
                    Device.iosapp_zone_enter_secs = time_now_secs()
                    Device.iosapp_zone_enter_time = time_now()

        if display_zone_msg:
            self._post_zone_selected_msg(Device, ZoneSelected, zone_selected,
                                            zone_selected_dist_m, zones_distance_list)

        return ZoneSelected, zone_selected

#--------------------------------------------------------------------
    def _select_zone(self, Device, latitude=None, longitude=None):
        '''
        Cycle thru the zones and see if the Device is in a zone (or it's stationary zone).

        Parameters:
            latitude, longitude - Override the normally used Device.loc_data_lat/long when
                            calculating the zone distance from the current location
        Return:
            ZoneSelected - Zone selected object or None
            zone_selected - zone entity name
            zone_selected_distance_m - distance to the zone (meters)
            zones_distance_list - list of zone info [distance_m|zoneName-distance]
        '''

        if latitude is None:
            latitude  = Device.loc_data_latitude
            longitude = Device.loc_data_longitude
            gps_accuracy_adj = int(Device.loc_data_gps_accuracy / 2)

        # [distance from zone, Zone, zone_name, redius, display_as]
        zone_data_selected = [HIGH_INTEGER, None, '', HIGH_INTEGER, '', 1]

        # Exit if no location data is available
        if Device.no_location_data:
            ZoneSelected         = Gb.Zones_by_zone['unknown']
            zone_selected        = 'unknown'
            zone_selected_dist_m = 0
            zones_msg            = f"Zone > Unknown, GPS-{Device.loc_data_fgps}"
            post_event(Device.devicename, zones_msg)
            return ZoneSelected, zone_selected, 0, []

        # Verify that the statzone was not left without an exit trigger. If so, move this device out of it.
        if (Device.is_in_statzone
                and Device.StatZone.distance_m(latitude, longitude) > Device.StatZone.radius_m):
            statzone.exit_statzone(Device)

        zones_data = [[Zone.distance_m(latitude, longitude), Zone, Zone.zone,
                        Zone.radius_m, Zone.display_as]
                                for Zone in Gb.Zones
                                if (Zone.passive is False)]

        # Do not select a new zone for the Device if it just left a zone. Set to Away and next_update will be soon
        # if Device.was_inzone is False or secs_since(Device.iosapp_zone_exit_secs) >= Gb.exit_zone_interval_secs/2:
        # Select all the zones the device is in
        inzone_zones = [zone_data   for zone_data in zones_data
                                    if zone_data[ZD_DIST_M] <= zone_data[ZD_RADIUS] + gps_accuracy_adj]

        for zone_data in inzone_zones:
            if zone_data[ZD_RADIUS] <= zone_data_selected[ZD_RADIUS]:
                zone_data_selected = zone_data

        ZoneSelected  = zone_data_selected[ZD_ZONE]
        zone_selected = zone_data_selected[ZD_NAME]
        zone_selected_dist_m = zone_data_selected[ZD_DIST_M]

        # Selected a statzone
        if zone_selected in Gb.StatZones_by_zone:
            Device.StatZone = Gb.StatZones_by_zone[zone_selected]

        # In a zone and the iosapp enter zone info was not set, set it now
        if (zone_selected != Device.iosapp_zone_enter_zone
                and is_zone(zone_selected) and isnot_zone(Device.iosapp_zone_enter_zone)):
            Device.iosapp_zone_enter_secs = Gb.this_update_secs
            Device.iosapp_zone_enter_time = Gb.this_update_time
            Device.iosapp_zone_enter_zone = zone_selected

        # Build an item for each zone (dist-from-zone|zone_name|display_name-##km)
        zones_distance_list = \
            [(f"{int(zone_data[ZD_DIST_M]):08}|{zone_data[ZD_NAME]}|{zone_data[ZD_DIST_M]}")
                    for zone_data in zones_data if zone_data[ZD_NAME] != zone_selected]

        return ZoneSelected, zone_selected, zone_selected_dist_m, zones_distance_list

#--------------------------------------------------------------------
    @staticmethod
    def _post_zone_selected_msg(Device, ZoneSelected, zone_selected,
                                    zone_selected_dist_m, zones_distance_list):

        device_zones      = [_Device.loc_data_zone for _Device in Gb.Devices]
        zones_cnt_by_zone = {zone:device_zones.count(zone) for zone in set(device_zones)}

        zones_cnt_summary = [f"{Gb.zone_display_as[_zone]} ({cnt}), "
                                        for _zone, cnt in zones_cnt_by_zone.items()]
        zones_cnt_summary_msg = list_to_str(zones_cnt_summary).replace('──', 'NotSet')

        zones_distance_msg = ''
        zones_displayed = [zone_selected]
        if (zone_selected == NOT_HOME
                or (is_statzone(zone_selected)
                        and isnot_statzone(Device.loc_data_zone))):
            zones_distance_list.sort()
            for zone_distance_list in zones_distance_list:
                zdl_items  = zone_distance_list.split('|')
                _zone      = zdl_items[1]
                _zone_dist = float(zdl_items[2])

                zones_displayed.append(_zone)
                zones_distance_msg += f"{Gb.zone_display_as[_zone]}-{format_dist_m(_zone_dist)} "
                if zones_cnt_by_zone.get(_zone, 0) > 0:
                    zones_distance_msg += f" ({zones_cnt_by_zone[_zone]}), "
                else:
                    zones_distance_msg += ", "

        zones_cnt_list = [f"{Gb.zone_display_as[_zone]} ({zones_cnt_by_zone[_zone]}), "
                                        for _zone, cnt in zones_cnt_by_zone.items()
                                        if _zone not in zones_displayed]
        zones_cnt_msg = list_to_str(zones_cnt_list)
        if zones_cnt_msg: zones_cnt_msg += ', '

        # if display_zone_msg:
        # Format the Zone Selected Msg (ZoneName (#))
        zone_selected_msg = Gb.zone_display_as[zone_selected]

        if ZoneSelected.radius_m > 0:
            zone_selected_msg += f"-{format_dist_m(zone_selected_dist_m)}"
        if zone_selected in zones_cnt_by_zone:
            zone_selected_msg += f" ({zones_cnt_by_zone[zone_selected]})"

        # Format the Zones with devices when in a zone (ZoneName (#))
        zones_cnt_summary = [f"{Gb.zone_display_as[_zone]} ({cnt}), "
                                    for _zone, cnt in zones_cnt_by_zone.items()]

        # if zones_distance_msg: zones_distance_msg = f" > {zones_distance_msg}"
        if zones_cnt_msg: zones_cnt_msg = f"{zones_cnt_msg.replace('──', 'NotSet')}"

        gps_accuracy_msg = ''
        if zone_selected_dist_m > ZoneSelected.radius_m:
            gps_accuracy_msg = (f"AccuracyAdjustment-"
                                f"{int(Device.loc_data_gps_accuracy / 2)}m, ")

        zones_msg =(f"Zone > "
                    f"{zone_selected_msg} > "
                    f"{zones_distance_msg}"
                    f"{zones_cnt_msg}"
                    f"{gps_accuracy_msg}"
                    f"GPS-{Device.loc_data_fgps}")
        if zone_selected == Device.log_zone:
            zones_msg += ' (Activity Logged)'
        post_event(Device.devicename, zones_msg)

        if Device.loc_data_zone != Device.sensors[ZONE]:
            if NOT_SET not in zones_cnt_by_zone:
            # if 'xxx' not in zones_cnt_by_zone:
                for _Device in Gb.Devices:
                    if Device is not _Device:
                        event_msg = f"Zone-Device Counts > {zones_cnt_summary_msg}"
                        post_event(_Device.devicename, event_msg)

#--------------------------------------------------------------------
    def _move_into_statzone_if_timer_reached(self, Device):
        '''
        Check the Device's Stationary Zone expired timer and distance moved:
            Update the Device's Stat Zone distance moved
            Reset the timer if the Device has moved further than the distance limit
            Move Device into the Stat Zone if it has not moved further than the limit
        '''
        if Gb.is_statzone_used is False:
            return False

        calc_dist_last_poll_moved_km = calc_distance_km(Device.sensors[GPS], Device.loc_data_gps)
        Device.update_distance_moved(calc_dist_last_poll_moved_km)

        # See if moved less than the stationary zone movement limit
        # If updating via the ios app and the current state is stationary,
        # make sure it is kept in the stationary zone
        if Device.is_statzone_timer_reached is False or Device.is_location_old_or_gps_poor:
            return False

        if Device.is_statzone_move_limit_exceeded:
            Device.statzone_reset_timer

        # Monitored devices can move into a tracked zone but can not create on for itself
        elif Device.is_monitored: #beta 4/13b16
            pass

        elif (Device.isnot_in_statzone
                or (is_statzone(Device.iosapp_data_state) and Device.loc_data_zone == NOT_SET)):
            statzone.move_device_into_statzone(Device)

        return True

#--------------------------------------------------------------------
    def _is_overlapping_zone(self, current_zone, new_zone):
        '''
        Check to see if two zones overlap each other. The current_zone and
        new_zone overlap if their distance between centers is less than 2m.

        Return:
            True    They overlap
            False   They do not oerlap, ic3 is starting
        '''
        try:
            if current_zone == NOT_SET:
                return False
            elif current_zone == new_zone:
                return True

            if current_zone == "": current_zone = HOME
            CurrentZone = Gb.Zones_by_zone[current_zone]
            NewZone     = Gb.Zones_by_zone[new_zone]

            zone_dist = CurrentZone.distance_m(NewZone.latitude, NewZone.longitude)

            return (zone_dist <= 2)

        except:
            return False

#--------------------------------------------------------------------
    def _get_icloud_data_prefetch_device(self):
        '''
        Get the time (secs) until the next update for any device. This is used to determine
        when icloud data should be prefetched before it is needed.

        Return:
            Device that will be updated in 5-secs
        '''
        # At least 10-secs between prefetch refreshes
        if (secs_since(Gb.pyicloud_refresh_time[FAMSHR]) < 10
                and secs_since(Gb.pyicloud_refresh_time[FMF]) < 10):
            return None

        prefetch_before_update_secs = 5
        for Device in Gb.Devices_by_devicename_tracked.values():
            if (Device.is_data_source_ICLOUD is False
                    or Device.is_tracking_paused):
                continue
            if Device.icloud_initial_locate_done is False:
                return Device

            secs_to_next_update = secs_to(Device.next_update_secs)

            if Device.inzone_interval_secs < -15 or Device.inzone_interval_secs > 15:
                continue

            # If going towards a TrackFmZone and the next update is in 15-secs or less and distance < 1km
            # and current location is older than 15-secs, prefetch data now
            # Changed to is_approaching_tracked_zone and added error_cnt check (rc9)
            if (Device.is_approaching_tracked_zone
                    and Device.old_loc_cnt <= 4):
                Device.old_loc_threshold_secs = 15
                return Device

            if Device.is_location_gps_good:
                continue

            # Updating the device in the next 10-secs
            Device.display_info_msg(f"Requesting iCloud Location, Next Update in {secs_to_time_str(secs_to_next_update)} secs")
            return Device

        return None

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
            start_ic3.set_primary_data_source(IOSAPP)
            Device.data_source = IOSAPP
            log_msg = ("iCloud3 Error > More than 20 iCloud Authentication "
                        "or Location errors. iCloud may be down. "
                        "The iOSApp data source will be used. "
                        "Restart iCloud3 at a later time to see if iCloud "
                        "Loction Services is available.")
            post_error_msg(log_msg)

#----------------------------------------------------------------------------
    def _display_clear_authentication_needed_msg(self):

        if Gb.PyiCloud is None:
            pass

        elif (Gb.PyiCloud.requires_2fa
                and Gb.EvLog.alert_message != 'iCloud Account authentication is needed'):
            post_alert('iCloud Account authentication is needed')

        elif (Gb.PyiCloud.requires_2fa is False
                and Gb.EvLog.alert_message == 'iCloud Account authentication is needed'):
            clear_alert()

#--------------------------------------------------------------------
    def _format_fname_devtype(self, Device):
        try:
            return f"{Device.fname_devtype}"
        except:
            return ''

#--------------------------------------------------------------------
    def _is_overlapping_zone(self, zone1, zone2):
        '''
        zone1 and zone2 overlap if their distance between centers is less than 2m
        '''
        try:
            if zone1 == zone2:
                return True

            if zone1 == "": zone1 = HOME
            Zone1 = Gb.Zones_by_zone[zone1]
            Zone2 = Gb.Zones_by_zone[zone2]

            zone_dist = Zone1.distance(Zone2.latitude, Zone2.longitude)

            return (zone_dist <= 2)

        except:
            return False

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
        device_monitor_msg = (f"Device Monitor > {Device.data_source}, "
                            f"{Device.icloud_update_reason}, "
                            f"AttrsZone-{Device.sensor_zone}, "
                            f"LocDataZone-{Device.loc_data_zone}, "
                            f"Located-%tage, "
                            f"iOSAppGPS-{Device.iosapp_data_fgps}, "
                            f"iOSAppState-{Device.iosapp_data_state}), "
                            f"GPS-{Device.loc_data_fgps}")

        if Device.last_device_monitor_msg != device_monitor_msg:
            Device.last_device_monitor_msg = device_monitor_msg
            device_monitor_msg = device_monitor_msg.\
                        replace('%tage', Device.loc_data_time_age)
            post_monitor_msg(Device.devicename, device_monitor_msg)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Perform tasks on a regular time schedule
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _timer_tasks_every_hour(self):
        # Clean out lingering StatZone
        Gb.StatZones_to_delete = [StatZone  for StatZone in Gb.StatZones
                                            if StatZone.radius_m == STATZONE_RADIUS_1M]

#--------------------------------------------------------------------
    def _timer_tasks_midnight(self):

        post_event(f"{EVLOG_IC3_STAGE_HDR}")
        if instr(Gb.conf_general[CONF_LOG_LEVEL], 'auto-reset'):
                start_ic3.set_log_level('info')
                start_ic3.update_conf_file_log_level('info')

        for devicename, Device in Gb.Devices_by_devicename.items():
            Gb.pyicloud_authentication_cnt  = 0
            Gb.pyicloud_location_update_cnt = 0
            Gb.pyicloud_calls_time          = 0.0

        if Gb.WazeHist:
            Gb.WazeHist.wazehist_delete_invalid_records()
            Gb.WazeHist.compress_wazehist_database()
            Gb.WazeHist.wazehist_update_track_sensor()
            if Gb.wazehist_recalculate_time_dist_flag:
                Gb.wazehist_recalculate_time_dist_flag = False
                Gb.WazeHist.wazehist_recalculate_time_dist_all_zones()

        # Close log file, rename to '-1', open a new log file
        archive_log_file()
        post_event(f"{EVLOG_IC3_STAGE_HDR}End of Day File Maintenance Started")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEVICE STATUS SUPPORT FUNCTIONS FOR GPS ACCURACY, OLD LOC DATA, ETC
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _check_old_loc_poor_gps(self, Device):
        """
        If this is checked in the icloud location cycle,
        check if the location isold flag. Then check to see if
        the current timestamp is the same as the timestamp on the previous
        poll.

        If this is checked in the iosapp cycle,  the trigger transaction has
        already updated the lat/long so
        you don't want to discard the record just because it is old.
        If in a zone, use the trigger but check the distance from the
        zone when updating the device.

        Update the old_loc_cnt if just_check=False
        """

        try:
            if Device.is_location_gps_good or Device.icloud_devdata_useable_flag:
                Device.old_loc_cnt = 0
                Device.old_loc_msg = ''
            else:
                Device.old_loc_cnt += 1

                if Device.old_loc_cnt == 1:
                    return

                cnt_msg = f"#{Device.old_loc_cnt}"
                if Device.no_location_data:
                    Device.old_loc_msg = f"No Location Data {cnt_msg}"
                elif Device.is_offline:
                    Device.old_loc_msg = f"Device Offline/201 {cnt_msg}"
                elif Device.is_location_old:
                    Device.old_loc_msg = f"Location Old {cnt_msg} > {secs_to_age_str(Device.loc_data_secs)}"
                elif Device.is_gps_poor:
                    Device.old_loc_msg = f"Poor GPS > {cnt_msg}, Accuracy-±{Device.loc_data_gps_accuracy:.0f}m"
                else:
                    Device.old_loc_msg = f"Locaton > Unknown {cnt_msg}, {secs_to_age_str(Device.loc_data_secs)}"

        except Exception as err:
            log_exception(err)
            Device.old_loc_cnt = 0
            Device.old_loc_msg = ''

#--------------------------------------------------------------------
    def _is_outside_zone_no_exit(self, Device, zone, trigger, latitude, longitude):
        '''
        If the device is outside of the zone and less than the zone radius + gps_acuracy_threshold
        and no Geographic Zone Exit trigger was received, it has probably wandered due to
        GPS errors. If so, discard the poll and try again later

        Updates:    Set the Device.outside_no_exit_trigger_flag
                    Increase the old_location_poor_gps count when this innitially occurs
        Return:     Reason message
        '''
        if Device.iosapp_monitor_flag is False:
            return ''

        trigger = Device.trigger if trigger == '' else trigger
        if (instr(trigger, ENTER_ZONE)
                or Device.sensor_zone == NOT_SET
                or zone not in Gb.Zones_by_zone
                or Device.icloud_initial_locate_done is False):
            Device.outside_no_exit_trigger_flag = False
            return ''

        Zone           = Gb.Zones_by_zone[zone]
        dist_fm_zone_m = Zone.distance_m(latitude, longitude)
        zone_radius_m  = Zone.radius_m
        zone_radius_accuracy_m = zone_radius_m + Gb.gps_accuracy_threshold

        info_msg = ''
        if (dist_fm_zone_m > zone_radius_m
                and Device.got_exit_trigger_flag is False
                and Zone.is_statzone is False):
            if (dist_fm_zone_m < zone_radius_accuracy_m
                    and Device.outside_no_exit_trigger_flag == False):
                Device.outside_no_exit_trigger_flag = True
                Device.old_loc_cnt += 1

                info_msg = ("Outside of Zone without iOSApp `Exit Zone` Trigger, "
                            f"Keeping in Zone-{Zone.display_as} > ")
            else:
                Device.got_exit_trigger_flag = True
                info_msg = ("Outside of Zone without iOSApp `Exit Zone` Trigger "
                            f"but outside threshold, Exiting Zone-{Zone.display_as} > ")

            info_msg += (f"Distance-{format_dist_m(dist_fm_zone_m)}, "
                        f"KeepInZoneThreshold-{format_dist_m(zone_radius_m)} "
                        f"to {format_dist_m(zone_radius_accuracy_m)}, "
                        f"Located-{Device.loc_data_time_age}")

        if Device.got_exit_trigger_flag:
            Device.outside_no_exit_trigger_flag = False

        return info_msg

#--------------------------------------------------------------------
    def _display_secs_to_next_update_info_msg(self, Device):
        '''
        Display the secs until the next update in the next update time field.
        if between 90s to -90s. if between -90s and -120s, resisplay time
        without the age to make sure it goes away. The age may be for a non-Home
        zone but displat it in the Home zone sensor.
        '''
        if (Gb.primary_data_source_ICLOUD is False
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
            Device.sensors[NEXT_UPDATE] = next_update_hhmmss

        except Exception as err:
            log_exception(err)
            pass

        return

############ LAST LINE ###########