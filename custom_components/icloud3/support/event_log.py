#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   EVENT LOG ROUTINES - Set up the Event Log, Post events to the
#           setup_event_log - Set up the Event Log
#           post_event - Add an event to the Event Log internal table
#           update_event_log_display - Extract the filterd records from the event log
#                       table and update the display
#           export_event_log - Export the event log records to the ic3_event_log.text file
#
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from ..global_variables     import GlobalVariables as Gb
from ..const                import (HOME, HOME_FNAME, TOWARDS,
                                    HHMMSS_ZERO, HIGH_INTEGER, NONE, MOBAPP,
                                    RED_X, RED_ALERT, YELLOW_ALERT,
                                    CIRCLE_LETTERS_DARK, CIRCLE_LETTERS_LITE,
                                    NL, NL_DOT, LDOT2,
                                    CRLF, CRLF_DOT, CRLF_CHK, RARROW, DOT, LT, GT, DASH_50,
                                    NBSP, NBSP2, NBSP3, NBSP4, NBSP5, NBSP6, CLOCK_FACE,
                                    EVENT_RECDS_MAX_CNT_BASE, EVENT_LOG_CLEAR_SECS,
                                    EVENT_LOG_CLEAR_CNT, EVENT_RECDS_MAX_CNT_ZONE, EVLOG_URL_LIST,
                                    EVLOG_TIME_RECD, EVLOG_HIGHLIGHT, EVLOG_MONITOR, EVLOG_TRACE,
                                    EVLOG_INIT_HDR, EVLOG_UPDATE_START, EVLOG_UPDATE_END,
                                    EVLOG_ALERT, EVLOG_WARNING, EVLOG_ERROR, EVLOG_NOTICE,
                                    EVLOG_HIGHLIGHT, EVLOG_IC3_STARTING, EVLOG_IC3_STAGE_HDR,
                                    EVLOG_GREEN, EVLOG_VIOLET, EVLOG_ORANGE, EVLOG_PINK, EVLOG_RED, EVLOG_BLUE,
                                    CONF_EVLOG_BTNCONFIG_URL,
                                    )

from ..utils.utils        import instr, circle_letter, str_to_list, list_to_str, isbetween
from ..utils.messaging    import (SP, log_exception, log_info_msg, log_warning_msg, _log, _evlog,
                                    filter_special_chars, format_header_box, )
from ..utils.time_util    import (time_to_12hrtime, datetime_now, time_now_secs, datetime_for_filename,
                                    adjust_time_hour_value, adjust_time_hour_values, )


import time
import homeassistant.util.dt as dt_util



CONTROL_RECD            = [HHMMSS_ZERO,'Control Record']
SENSOR_EVENT_LOG_ENTITY = 'sensor.icloud3_event_log'
ELR_DEVICENAME = 0
ELR_TIME = 1
ELR_TEXT = 2
MAX_EVLOG_RECD_LENGTH = 2000

# The text starts with a special character:
# ^1^ - LightSeaGreen
# ^2^ - BlueViolet
# ^3^ - OrangeRed
# ^4^ - DeepPink
# ^5^ - MediumVioletRed
# ^6^ - --dark-primary-color
# EVLOG_TIME_RECD   = '^t^'       # MobileApp State, ic3 Zone, interval, travel time, distance event
# EVLOG_UPDATE_HDR  = '^u^'       # update start-to-complete highlight and edge bar block
# EVLOG_UPDATE_START= '^s^'       # update start-to-complete highlight and edge bar block
# EVLOG_UPDATE_END  = '^c^'       # update start-to-complete highlight and edge bar block
# EVLOG_ERROR       = '^e^'
# EVLOG_ALERT       = '^a^'
# EVLOG_WARNING     = '^w^'
# EVLOG_INIT_HDR    = '^i^'       # iC3 initialization start/complete event
# EVLOG_HIGHLIGHT   = '^h^'       # Display item in green highlight bar
# EVLOG_IC3_STARTING  = '^i^'
# EVLOG_IC3_STAGE_HDR = '^g^'

MONITORED_DEVICE_EVENT_FILTERS = [
    'iCloud Acct Auth',
    'Apple Acct Auth',
    'Nearby Devices',
    'iOSApp Location',
    'MobApp Location',
    'Updated',
    'Trigger',
    'Old',
]

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class EventLog(object):
    def __init__(self):
        self.hass = Gb.hass
        self.initialize()

    def initialize(self):
        self.display_text_as         = {}
        self.event_recds             = []   # Device event recds
        self.startup_event_save_recd_flag = True
        self.startup_event_recds     = []   # All Event recds during startup
        self.event_recds_max_cnt     = EVENT_RECDS_MAX_CNT_BASE

        self.devicename              = ''
        self.fname_selected          = ''
        self.fnames_by_devicename    = {}
        self.clear_secs              = HIGH_INTEGER
        self.trk_monitors_flag       = False
        self.log_debug_flag          = False
        self.log_rawdata_flag           = False
        self.last_refresh_secs       = 0
        self.last_refresh_devicename = ''
        self.dist_to_devices_recd_found_flag = False    # Display only the last DistTo Devices > stmt
        self.apple_acct_auth_cnts_by_owner = {}      # Display only the last 4 Apple Acct Auth statements

        # An alert message is displayed in a green bar at the top of the EvLog screen
        #   post_greenbar_msg("msg") = Display the message
        #   clear_greenbar_msg()     = Clear the alert msg and remove the green bar
        self.greenbar_alert_msg      = ''       # Message to display in green bar at the top of the Evlog

        self.user_message            = ''       # Display a message in the name0 button
        self.user_message_alert_flag = False    # Do not clear the message if this is True

        browser_refresh_msg =      {"Browser Refresh Required": (
                                    "✪✪ A Browser Refresh is Required ✪✪ "
                                    "───────────────── "
                                    "Ctrl-Shift-Del, then Refresh "
                                    "the browser tab. You may have to "
                                    "do this several times. "
                                    "────────────────── "
                                    "If 'iCloud3 v3 - Event Log' is "
                                    "not displayed, restart HA. Also "
                                    "do this on devices running the Mobile App. "
                                    )}

        self.evlog_sensor_state_value       = ''
        self.evlog_url_list                 = EVLOG_URL_LIST.copy()
        self.evlog_url_list['urlConfig']    = Gb.evlog_btnconfig_url

        self.evlog_attrs                    = {}
        self.evlog_attrs["update_time"]     = ''
        self.evlog_attrs["alert"]           = ""
        self.evlog_attrs["alerts"]          = ""
        self.evlog_attrs["alert_startup"]   = ""
        self.evlog_attrs["alert_tracked"]   = ""
        self.evlog_attrs["alert_monitored"] = ""
        self.evlog_attrs["user_message"]    = self.user_message
        self.evlog_attrs["devicename"]      = ''
        self.evlog_attrs["fname"]           = ''
        self.evlog_attrs["fnames"]          = {'Setup': 'Waiting for HA to Finish Loading'}
        self.evlog_attrs["filtername"]      = 'Initialize'
        self.evlog_attrs["version_ic3"]     = Gb.version
        self.evlog_attrs["version_evlog"]   = Gb.version_evlog
        self.evlog_attrs["versionEvLog"]    = Gb.version_evlog
        self.evlog_attrs["log_level_debug"] = ''
        self.evlog_attrs["run_mode"]        = 'Initialize'
        self.evlog_attrs["evlog_url_list"]  = self.evlog_url_list
        self.evlog_attrs["name"]            = {"Browser Refresh is Required":
                                                "Browser Refresh is Required"}
        self.evlog_attrs["names"]           = browser_refresh_msg
        self.evlog_attrs["logs"]            = []

        self.devicename_cnts = {}

    def __repr__(self):
        return (f"<EventLog: {self.fnames_by_devicename}>")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   EVENT LOG ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def setup_event_log_trackable_device_info(self):
        '''
        Set up the name, picture and device attributes in the Event Log
        sensor.
        '''

        try:
            self.devicename = ''
            self.fname_selected = ''
            self.fnames_by_devicename = {}
            self.event_recds_max_cnt  = EVENT_RECDS_MAX_CNT_BASE

            self.fnames_by_devicename.update({devicename: self.format_evlog_device_fname(Device)
                            for devicename, Device in Gb.Devices_by_devicename_tracked.items()
                            if devicename != ''})

            self.fnames_by_devicename.update({devicename: self.format_evlog_device_fname(Device)
                            for devicename, Device in Gb.Devices_by_devicename_monitored.items()
                            if devicename != ''})

            tfz_cnt = sum([len(Device.FromZones_by_zone) for Device in Gb.Devices])
            self.event_recds_max_cnt = EVENT_RECDS_MAX_CNT_ZONE*tfz_cnt

            if self.fnames_by_devicename == {}:
                self.user_message_alert_flag = True
                self.evlog_attrs["user_message"] = 'No Devices have been configured'
                self.fnames_by_devicename["nodevices"] = 'No Devices have been configured'
                self.fname_selected = "NoDevices"

            elif self.devicename == '':
                self.devicename = next(iter(self.fnames_by_devicename))
                self.fname_selected = self.fnames_by_devicename[self.devicename]

            if Gb.evlog_version.startswith('3'):
                self.evlog_attrs["name"] = ''
                self.evlog_attrs["names"] = ''

            self.evlog_attrs["update_time"]    = "setup"
            self.evlog_attrs["user_message"]   = self.user_message
            self.evlog_attrs["devicename"]     = self.devicename
            self.evlog_attrs["fname"]          = self.fname_selected
            self.evlog_attrs["fnames"]         = self.fnames_by_devicename
            self.evlog_attrs["filtername"]     = 'Initialize'
            self.evlog_attrs["version_ic3"]    = Gb.version
            self.evlog_attrs["version_evlog"]  = Gb.version_evlog
            self.evlog_attrs["versionEvLog"]   = Gb.version_evlog
            self.evlog_attrs["run_mode"]       = "Initialize"
            self.evlog_url_list['urlConfig']   = Gb.evlog_btnconfig_url
            self.evlog_attrs["evlog_url_list"] = self.evlog_url_list

            Gb.EvLogSensor.async_update_sensor()

        except Exception as err:
            log_exception(err)

        return

#------------------------------------------------------
    def format_evlog_device_fname(self, Device):
        # verified = Gb.evlog_alert_by_devicename.get(Device.devicename, '')
        # verified = f"{RED_X} " if Device.verified_flag is False else ''
        tz_offset = '' if Device.away_time_zone_offset == 0 else f" {CLOCK_FACE}"
        tracked  = '' if Device.is_tracked else f" {circle_letter('m')}"
        return f"{Device.evlog_fname_alert_char}{Device.fname}{tracked}{tz_offset}"

#------------------------------------------------------
    def post_event(self, devicename_or_Device, event_text='+'):
        '''
        Add records to the Event Log table the device. If the device="*",
        the event_text is added to all deviceFNAMEs table.

        The event_text can consist of pseudo codes that display a 2-column table (see
        _display_usage_counts function for an example and details)

        The event_log lovelace card will display the event in a special color if
        the text starts with a special character:
        '''

        if event_text == '+':
            event_text = devicename_or_Device
            devicename = "*" if Gb.start_icloud3_inprocess_flag else '**'
        elif devicename_or_Device is None or devicename_or_Device in ['', '*']:
            devicename = "*" if Gb.start_icloud3_inprocess_flag else '**'

        if (instr(event_text, "▼") or instr(event_text, "▲")
                or len(event_text) == 0
                or instr(event_text, "event_log")):
            return

        if devicename_or_Device in Gb.Devices:
            Device = devicename_or_Device
            devicename = Device.devicename
        elif devicename_or_Device in Gb.Devices_by_devicename:
            devicename = devicename_or_Device
            Device = Gb.Devices_by_devicename[devicename]
        else:
            Device = None

        # If monitored device and the event msg is a status msg for other devices,
        # do not display it on a monitored device screen
        if Device and Device.is_monitored:
            start_pos = 2 if event_text.startswith('^') else 0
            for filter_text in MONITORED_DEVICE_EVENT_FILTERS:
                if event_text[start_pos:].startswith(filter_text):
                    return

        # Drop duplicate event_text item that has already been displayed. Also,
        # if a ^c^ start header is immediately follows an ^s^ header, the group is empty,
        # delete the ^s^ header and throw the current record (^c^ header) away.
        try:
            if (devicename.startswith('*') is False and len(self.event_recds) > 8):
                in_last_few_recds = [v for v in self.event_recds[:8] \
                                        if (v[ELR_DEVICENAME] == devicename \
                                            and v[ELR_TEXT] == event_text \
                                            and v[ELR_TEXT].startswith(EVLOG_TIME_RECD) is False
                                            and v[ELR_TEXT].startswith(EVLOG_TRACE) is False
                                            and v[ELR_TEXT].startswith('Battery') is False)]
                if in_last_few_recds != []:
                    return

                # If this is an Update Completed msg
                if event_text.startswith(EVLOG_UPDATE_END):
                    # Drop previous msg if it was an Update Started msg
                    for idx in range(0, 8):
                        if self.event_recds[idx][ELR_TEXT].startswith(EVLOG_UPDATE_START):
                            self.event_recds[idx].pop()
                            return
                        if self.is_monitor_recd(self.event_recds[idx]) is False:
                            break
        except Exception as err:
            # log_exception(err)
            pass

        try:
            this_update_time = ''
            if len(event_text) <= 5:
                pass
            #if (event_text.startswith(EVLOG_UPDATE_START)
            elif (event_text.startswith(EVLOG_UPDATE_END)
                    or event_text.startswith(EVLOG_IC3_STARTING)
                    or event_text.startswith(EVLOG_IC3_STAGE_HDR)):
                this_update_time = dt_util.now().strftime('%a')
                if Gb.log_rawdata_flag:
                    this_update_time += ',Raw'
                elif Gb.log_debug_flag:
                    this_update_time += ',Dbug'


            else:
                this_update_time = dt_util.now().strftime('%H:%M:%S')
                this_update_time = time_to_12hrtime(this_update_time)

                # If tracking from more than one zone and the tfz results are being displayed,
                # display tfz zone name in the time field. Capitalize if going towards
                if devicename.startswith('*') is False:
                    if Device := Gb.Devices_by_devicename.get(devicename):
                        Device.last_evlog_msg_secs = time_now_secs()
                        from_zone_dname = Device.FromZone_BeingUpdated.from_zone_dname
                        if event_text.startswith(EVLOG_TIME_RECD):
                            this_update_time = f"»{from_zone_dname[:6]}"# 
                            if (Device.FromZone_BeingUpdated is Device.FromZone_TrackFrom
                                    and Device.FromZone_BeingUpdated is not Device.FromZone_Home):
                                this_update_time = this_update_time.upper()

                        elif Device.FromZone_BeingUpdated is not Device.FromZone_Home:
                            this_update_time = f"»{from_zone_dname[:6]}"

        except Exception as err:
            log_exception(err)

        try:
            if (instr(type(event_text), 'dict') or instr(type(event_text), 'list')):
                event_text = str(event_text)

            if event_text.startswith(EVLOG_TIME_RECD):
                event_text = event_text.replace('N/A', '')

            if len(event_text) == 0: event_text = 'Info Message'
            event_text = self._replace_special_chars(event_text)

            if self.display_text_as is None:
                self.display_text_as = {}

            for from_text in self.display_text_as:
                event_text = event_text.replace(from_text, self.display_text_as[from_text])

            MAX_EVLOG_RECD_LENGTH = 2000
            if len(event_text) > MAX_EVLOG_RECD_LENGTH:
                event_recd = self._break_up_event_text(devicename, this_update_time, event_text, MAX_EVLOG_RECD_LENGTH)
            else:
                event_recd = [devicename, this_update_time, event_text]

                self._add_recd_to_event_recds(event_recd)

            if self._startup_error_log_filter(event_text):
                self._save_startup_log_recd(Device, event_recd)

        except Exception as err:
            log_exception(err)

#......................................................
    def _startup_error_log_filter(self, event_text):


        evlog_alert_type = event_text[:3]
        if (self.startup_event_save_recd_flag
                or evlog_alert_type in [EVLOG_NOTICE, EVLOG_ERROR, EVLOG_WARNING]
                or evlog_alert_type == EVLOG_ALERT and instr(event_text, '> Old') is False):
            save_recd_flag = True
        else:
            save_recd_flag = False

        if save_recd_flag:
            if (event_text.startswith('DistTo')
                    or event_text.startswith('Battery Info')
                    or event_text.startswith('iCloud Trigger')):
                save_recd_flag = False

        return save_recd_flag

#------------------------------------------------------
    def _break_up_event_text(self, devicename, this_update_time, event_text, MAX_EVLOG_RECD_LENGTH):
        '''
        Event_text > 2000 characters. Break up into chunks and create an evlog recd
        for each chunk
        '''
        color_symbol = ''
        if event_text.startswith('^1^'): color_symbol = '^1^'
        if event_text.startswith('^2^'): color_symbol = '^2^'
        if event_text.startswith('^3^'): color_symbol = '^3^'
        if event_text.startswith('^4^'): color_symbol = '^4^'
        if event_text.startswith('^5^'): color_symbol = '^5^'
        if event_text.startswith('^6^'): color_symbol = '^6^'
        if instr(event_text, EVLOG_ERROR): color_symbol = '!'

        chunk_cnt     = int(len(event_text)/MAX_EVLOG_RECD_LENGTH + .5)
        chunk_length  = int(len(event_text) / chunk_cnt)
        event_text   += f" ({len(event_text)}-{chunk_cnt}-{chunk_length})"

        if event_text.find(CRLF) > 0:
            split_str = CRLF
        else:
            split_str = " "
        split_str_end_len = -1 * len(split_str)
        word_chunk = event_text.split(split_str)

        chunk_no   = len(word_chunk)-1
        chunk_text = ''
        while chunk_no >= 0:
            if len(chunk_text) + len(word_chunk[chunk_no]) + len(split_str) > chunk_length:
                event_recd = [devicename, '',
                                (f"{color_symbol}{chunk_text[:split_str_end_len]} ({chunk_text[:split_str_end_len]})")]
                self._add_recd_to_event_recds(event_recd)

                chunk_text = ''

            if len(word_chunk[chunk_no]) > 0:
                chunk_text = word_chunk[chunk_no] + split_str + chunk_text

            chunk_no-=1

        event_recd = [devicename, this_update_time,
                        (f"{chunk_text[:split_str_end_len]} ({chunk_text[:split_str_end_len]})")]
        self._add_recd_to_event_recds(event_recd)
        return event_recd

#=========================================================================
    def update_event_log_display(self, devicename='', show_one_screen=False):
        '''
        Extract the records from the event log table, select the items to
        be displayed based on the log_level_debug and devicename filters and
        update the sensor.ic3_event_log attribute. This will be caught by
        the icloude-event-log-card.js custom card and display the selected
        records.

        This is called from device_tracker.py using:
            Gb.EvLog.log_attr_debug_selection

        Input variables:
            devicename:
                - Devicename of the selected device to be displayed
                - 'startup_log' > Display system events ('*' events)
                - 'clear_log_items' - Shrink the Event Log 'log' items so the
                        icloud3_event_log entity is at a minimm size

        '''
        if devicename == '' or devicename is None:
            devicename = self.devicename

        try:
            log_attr_text = ""
            if Gb.evlog_trk_monitors_flag: log_attr_text += 'monitor,'
            if Gb.log_debug_flag:          log_attr_text += 'debug,'
            if Gb.log_rawdata_flag:        log_attr_text += 'rawdata,'

            self.evlog_attrs['log_level_debug'] = log_attr_text

            max_recds = HIGH_INTEGER
            self.clear_secs = time_now_secs() + EVENT_LOG_CLEAR_SECS
            if show_one_screen:
                max_recds  = EVENT_LOG_CLEAR_CNT
                self.clear_secs = HIGH_INTEGER
                devicename = self.devicename

            elif devicename == 'startup_log':
                self.evlog_attrs['fname'] = 'Startup Events'

            elif devicename in ['', '*', '**', 'Initialize']:
                self.evlog_attrs['run_mode'] = 'Initialize'

            else:
                self.evlog_attrs['run_mode']   = 'Display'
                self.evlog_attrs['devicename'] = self.devicename = devicename
                self.evlog_attrs['fname']      = self.fname_selected = self.fnames_by_devicename[devicename]

            self.evlog_sensor_state_value = devicename

            self.evlog_attrs['logs'] = self._filtered_evlog_recds(devicename, max_recds)

            self.update_evlog_sensor()

            self.last_refresh_devicename = devicename
            self.last_refresh_secs       = time_now_secs()

        except Exception as err:
            log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Support functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    @property
    def secs_since_refresh(self):
        return time_now_secs() - self.last_refresh_secs

#------------------------------------------------------
    @staticmethod
    def log_update_time():
        return (f"{dt_util.now().strftime('%a,  %m/%d')}, "
                f"{dt_util.now().strftime(Gb.um_time_strfmt)}."
                f"{dt_util.now().strftime('%f')}")

#------------------------------------------------------
    def display_user_message(self, user_message, alert=False, clear_greenbar_msg=False):
        '''
        Display or clear the special message displayed in the name0 button on
        the Event Log. However, do not change or clear it if the persists flag
        is set (Error, Tracking is Paused, iCloud authentication is needed, etc).

        Note:
        The user_message_alert_flag must be set to False to change or clear
        a message.
        '''
        if clear_greenbar_msg:
            self.user_message_alert_flag = alert = False

        if alert:
            self.user_message_alert_flag = True

        self.user_message = user_message
        self.evlog_attrs['logs'] = self._filtered_evlog_recds(self.devicename, HIGH_INTEGER)

        self.update_evlog_sensor()

#------------------------------------------------------
    def update_evlog_sensor(self):
        # The state must change for the recds to be refreshed on the
        # Lovelace card. If the state does not change, the new information
        # is not displayed. Add the update time is added in sensor.py to make it unique.

        self.evlog_attrs["update_time"]  = self.log_update_time()
        self.evlog_attrs["user_message"] = self.user_message

        # Update EvLog sensor to display all log records
        if Gb.EvLogSensor:
            Gb.EvLogSensor.async_update_sensor()

        self.last_refresh_secs = time_now_secs()

#------------------------------------------------------
    def alert_attr_filter(self, alert_msg=None):
        if alert_msg is None:
            alert_msg = self.greenbar_alert_msg
        if alert_msg == '':
            return ''

        alert_msg = alert_msg.replace(NBSP2, ' ')
        alert_msg = alert_msg.replace(NBSP3, ' ')
        alert_msg = alert_msg.replace(NBSP4, ' ')
        alert_msg = alert_msg.replace(CRLF, NL)

        return alert_msg

#------------------------------------------------------
    def _add_recd_to_event_recds(self, event_recd):
        """Add the event recd into the event table"""

        if self.event_recds is None:
            self.event_recds = CONTROL_RECD

        try:
            if len(event_recd) != 3:
                log_warning_msg(f"INVALID EVLOG RECD (SHORT)-{event_recd}")
                return
            elif event_recd[ELR_TEXT] == '':
                log_warning_msg(f"INVALID EVLOG RECD (EMPTY TEXT)-{event_recd}")
                return

            evl_table_recd_cnt = len(self.event_recds)
            if evl_table_recd_cnt >= self.event_recds_max_cnt:
                self.devicename_cnts = {}
                for elr_recd in self.event_recds:
                    self._update_event_recds_device_cnt(elr_recd)

                self._shrink_event_recds(500)

        except Exception as err:
            log_exception(err)
            pass

        self.event_recds.insert(0, event_recd)

#------------------------------------------------------
    def _save_startup_log_recd(self, Device, event_recd):
        # Add the startup and alert events to a non-clearable table (reset on a restart)

        event_text = event_recd[ELR_TEXT]
        if Device:
            if event_text.startswith(EVLOG_UPDATE_END):
                event_text=(f"{EVLOG_IC3_STARTING}{Device.fname} > "
                            f"{event_text[3:]}")
                if instr(event_text, ','):
                    event_text = event_text.split(',')[0]
                event_recd = [event_recd[ELR_DEVICENAME], event_recd[ELR_TIME], event_text]

            # Add device name  on front of text
            elif (event_text.startswith(EVLOG_ALERT)
                    or instr(event_text, RED_X)
                    or instr(event_text, RED_ALERT)):
                if event_text.startswith('^'):
                    event_text = event_text[3:]
                event_text=(f"{ Device.fname} > {event_text}")
                event_recd = [event_recd[ELR_DEVICENAME], event_recd[ELR_TIME], event_text]


        self.startup_event_recds.insert(0, event_recd)

#------------------------------------------------------
    def _shrink_event_recds(self, shrink_cnt):
        '''
        The table has reached the maximun number of records. Remove 40% of the
        oldest device records and 60% of the monitor type records. Do not delete
        '*'/system records unles it contains a '#' since it will be a retry or
        authentication count recd:

        Parameters:
            - shrink_cnt: The total number of records to be deleted.
        '''
        try:
            if Gb.Devices == []:
                return

            keep_nonmonitor_recd_pct = .40

            delete_device_recd_cnt = shrink_cnt * keep_nonmonitor_recd_pct
            event_recds_recd_cnt   = len(self.event_recds)
            event_recds_target_cnt = self.event_recds_max_cnt - shrink_cnt
            delete_cnt = 0
            delete_reg_cnt = 0
            delete_mon_cnt = 0
            self.devicename_cnts = {}

            # Go from end of table to front
            for x in range(event_recds_recd_cnt-2, 2, -1):
                elr_recd     = self.event_recds[x]
                elr_text = elr_recd[ELR_TEXT]

                # Delete monitor recds or 20% of regular device at end of table
                if (self.is_monitor_recd(elr_text)
                        or delete_cnt < delete_device_recd_cnt):
                    delete_cnt += 1
                    if self.is_monitor_recd(elr_text):
                        delete_mon_cnt += 1
                    else:
                        delete_reg_cnt += 1

                    del self.event_recds[x]
                    self._update_event_recds_device_cnt(elr_recd)

                    if delete_cnt >= shrink_cnt:
                        break

            # If not enough recds were deleted, force deleting some
            if len(self.event_recds) > event_recds_target_cnt:
                delete_cnt += len(self.event_recds) - event_recds_target_cnt
                del self.event_recds[event_recds_target_cnt:]

            if delete_cnt > 0:
                self.post_event(f"{EVLOG_MONITOR}Event Log Table Size Reduced > "
                                f"RecdCnt-{event_recds_recd_cnt}{RARROW}"
                                f"{len(self.event_recds)}, "
                                f"Deleted-{delete_cnt} "
                                f"(DevInfo-{delete_reg_cnt}, "
                                f"Monitor-{delete_mon_cnt})")

        except Exception as err:
            # log_exception(err)
            pass

#------------------------------------------------------
    def _update_event_recds_device_cnt(self, elr_recd):
        devicename = elr_recd[ELR_DEVICENAME]
        recd_type  = 'Mon' if self.is_monitor_recd(elr_recd) else 'Reg'
        devicename_type = f"{devicename}-{recd_type}"
        if devicename_type not in self.devicename_cnts:
            self.devicename_cnts[devicename_type] = 0
        self.devicename_cnts[devicename_type] += 1

#------------------------------------------------------
    def clear_greenbar_msg(self):

        if self.greenbar_alert_msg == '':
            return

        self.greenbar_alert_msg = ''
        self.display_user_message('', clear_greenbar_msg=True)

#------------------------------------------------------
    def _filtered_evlog_recds(self, devicename='', max_recds=HIGH_INTEGER, selected_devicename=None):
        '''
        Extract the filtered records from the event_recdss and prepare them
        for display
        '''

        if devicename == '':
            devicename = self.devicename
        time_text_recds = self._extract_filtered_evlog_recds(devicename)

        if Gb.display_gps_lat_long_flag is False:
            time_text_recds = [self._apply_gps_filter(el_recd) for el_recd in time_text_recds]

        if max_recds < HIGH_INTEGER:
            recd_cnt = len(time_text_recds)
            time_text_recds = time_text_recds[0:max_recds]

            refresh_msg = ( f"{EVLOG_HIGHLIGHT}Tap `Refresh` or select a device "
                            f"to display all of the events")
            refresh_recd = ['🔄',refresh_msg]
            time_text_recds.insert(0, refresh_recd)

        if self.greenbar_alert_msg != '':
            alert_msg = ( f"{EVLOG_HIGHLIGHT}{self.greenbar_alert_msg}")
            alert_recd = ['⚠️', alert_msg]
            time_text_recds.insert(0, alert_recd)

        time_text_recds.append(CONTROL_RECD)
        time_text_recds_str = str(time_text_recds)

        if Gb.evlog_trk_monitors_flag:
            time_text_recds_str = time_text_recds_str.replace(EVLOG_MONITOR, EVLOG_BLUE)

        return time_text_recds_str

#--------------------------------------------------------------------
    def _extract_filtered_evlog_recds(self, devicename):
        '''
        Build the event items attribute for the event log sensor. Each item record
        is [device, time, state, zone, interval, travTime, dist, textMsg]
        Select the items for the device or '*' and return the string of
        the resulting list to be passed to the Event Log
        '''

        # The evlog_startup_log_flag is set in the service_handler when Show
        # Startup Log, Errors & Alerts is selected on the EvLog screen
        if Gb.evlog_startup_log_flag:
            self.greenbar_alert_msg=(   f"Start up log, alerts and èrrors"
                                        f"{RARROW}Refresh to close")
            el_recds = [el_recd[1:3] for el_recd in self.startup_event_recds
                                        if (self.is_monitor_recd(el_recd) is False
                                            or Gb.evlog_trk_monitors_flag)]
            return el_recds

        elif Gb.EvLog.greenbar_alert_msg.startswith('Start up log'):
            self.clear_greenbar_msg()

        el_devicename_check = ['*', '**', 'nodevices', devicename]

        if Device := Gb.Devices_by_devicename.get(devicename):
            filter_record = (Device.primary_data_source == MOBAPP) \
                                or Device.is_monitored
        else:
            Device = None
            filter_record = False

        # Select devicename recds, keep time & test elements, drop devicename
        try:
            self.dist_to_devices_recd_found_flag = False
            self.apple_acct_auth_cnts_by_owner   = {}

            el_recds = [self._master_reformat_text(el_recd, Device)
                                            for el_recd in self.event_recds
                                            if self._master_filter_recd(el_recd, devicename)]
            return el_recds

        except IndexError:
            for el_recd in self.event_recds:
                if el_recd[ELR_DEVICENAME] not in el_devicename_check:
                    continue
                elif el_recd[ELR_DEVICENAME] in el_devicename_check:
                    log_info_msg(f"{el_recd}")
                elif len(el_recd) <= 3:
                    log_info_msg(f"{el_recd}")

        return []

#--------------------------------------------------------------------
    def _master_filter_recd(self, el_recd, devicename):

        # Drop recd if not startup or selected device or the recd has an error

        if (el_recd[ELR_DEVICENAME] not in ['*', '**', 'nodevices', devicename]
                or len(el_recd) != 3):
            return False

        Device = Gb.Devices_by_devicename.get(devicename)
        elr_devicename, elr_time, elr_text = el_recd

        # Return all of the time/text items if 'Show Tracking Monitors' was selected in the EvLog
        if Gb.evlog_trk_monitors_flag:
            return True
        # if instr(el_recd[ELR_TEXT], 'Acct Auth'):
        #     return True

        # Only display the last DistTo Devices entry
        if elr_text.startswith('DistTo Devices'):
            if self.dist_to_devices_recd_found_flag:
                return False
            self.dist_to_devices_recd_found_flag = True

        # Only display the last DistTo Devices entry
        # Apple Acct Auth #12 > GaryCobb(xxxxxxxx), Token
        try:
            if elr_text.startswith('Apple Acct Auth'):
                apple_acct_owner = elr_text.split(' ')[5]
                cnt = self.apple_acct_auth_cnts_by_owner.get(apple_acct_owner, 0)
                cnt += 1
                self.apple_acct_auth_cnts_by_owner[apple_acct_owner] = cnt
                if cnt < 3:
                    return True
        except Exception as err:
            log_exception(err)
            pass

        # Drop Tracking Monitor recds or iCloud Authentication recds
        if self.is_monitor_recd(elr_text):
            return False

        if (instr(elr_text, 'Acct Auth')
                and Device
                and (Device.is_monitored or Device.primary_data_source == MOBAPP)):
            return False

        return True

#--------------------------------------------------------------------
    def _master_reformat_text(self, el_recd, Device):
        '''
        Reformat the text in the current recd if needed:
            - Keep/Remove gps
            - Keep/Reformat the time fields from the Home time zone to the Away time zone
        '''
        elr_time_text = el_recd[1:3]

        if Gb.display_gps_lat_long_flag is False:
            elr_time_text = self._apply_gps_filter(elr_time_text)
        if Device:
            elr_time_text = self._apply_home_to_away_time_zone_update(elr_time_text, Device.away_time_zone_offset)
        return elr_time_text

#--------------------------------------------------------------------
    @staticmethod
    def _apply_gps_filter(elr_time_text):
        '''
        Filter the gps coordinates out of the record based on the config parameter
        Convert 'GPS-(27.72683, -80.39055/±33m)' to 'GPS-/±33m'
        '''
        elr_time, elr_text = elr_time_text
        if elr_text.find('GPS-(') == -1:  return elr_time_text

        check_for_gps_flag = True
        while check_for_gps_flag:
            gps_s_pos = elr_text.find('GPS-(') + 4
            gps_acc_pos = elr_text.find('/±', gps_s_pos)
            gps_e_pos = elr_text.find(')', gps_s_pos)
            elr_text = elr_text[:gps_s_pos] + elr_text[gps_acc_pos:gps_e_pos] + elr_text[gps_e_pos+1:]
            check_for_gps_flag = elr_text.find('GPS-(') >= 0

        return [elr_time, elr_text.replace('GPS-, ', '')]

#--------------------------------------------------------------------
    @staticmethod
    def is_monitor_recd(el_recd):
        if type(el_recd) is list:
            return el_recd[ELR_TEXT].startswith(EVLOG_MONITOR)
        elif type(el_recd) is str:
            return el_recd.startswith(EVLOG_MONITOR)
        else:
            return False

#--------------------------------------------------------------------
    @staticmethod
    def _apply_home_to_away_time_zone_update(elr_time_text, device_away_time_zone_offset):
        '''
        Change the Home zone time in the elr_text to the Away Zone time if needed.
        Return [elr_time, elr_text]
        '''
        if device_away_time_zone_offset == 0:
            return elr_time_text

        elr_time, elr_text = elr_time_text
        if device_away_time_zone_offset == 0:
            return [elr_time, elr_text]

        elr_time = adjust_time_hour_value(elr_time, device_away_time_zone_offset)
        if instr(elr_text, (':')):
            elr_text = adjust_time_hour_values(elr_text, device_away_time_zone_offset)

        # Add a note that the Away Time is displayed
        if elr_text.startswith(EVLOG_UPDATE_END):
            plus_minus_sign = '+' if device_away_time_zone_offset > 0 else '-'
            elr_text += f" ({plus_minus_sign}{abs(device_away_time_zone_offset)}hrs)"

        return [elr_time, elr_text]


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   EXPORT EVENT LOG
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def export_event_log(self):
        '''
        Export Event Log to 'config/icloud_event_log-[time].log'.
        '''

        try:
            log_update_time =   (f"{dt_util.now().strftime('%a, %m/%d')}, "
                                f"{dt_util.now().strftime(Gb.um_time_strfmt)}")
            hdr_recd    = f"Time{SP(8)}Event\n{'-'*120}\n"
            export_recd = (f"iCloud3 Event Log v{Gb.version}\n\n"
                            f"Log Update Time: {log_update_time}\n"
                            f"Tracked Devices:\n")

            export_recd += f"\nGeneral Configuration:\n"
            export_recd += f"{SP(4)}{Gb.conf_general}\n"

            for devicename, Device in Gb.Devices_by_devicename.items():
                export_recd += (f"{SP(4)}{DOT}{Device.fname_devicename} >\n"
                                f"{SP(4)}{Device.conf_device}\n")

            #--------------------------------
            # # Prepare Global '*' records. Reverse the list elements using [::-1] and make a string of the results
            export_recd += f"\n\n{'_'*120}\n"
            export_recd += (f"Startup Events:\n\n")
            export_recd += hdr_recd

            el_nondevice_recds = [el_recd for el_recd in self.event_recds
                                    if el_recd[ELR_DEVICENAME].startswith("*")]

            export_recd += self._export_ic3_event_log_reformat_recds('startup', el_nondevice_recds)


            #--------------------------------
            # # Prepare recds for each device. Each record is [devicename, time, text]
            for devicename, Device in Gb.Devices_by_devicename.items():
                export_recd += f"{'_'*120}\n"
                export_recd += (f"{Device.fname_devicename}:\n\n")
                export_recd += hdr_recd

                el_recds = [el_recd for el_recd in self.event_recds
                                    if (len(el_recd) == 3
                                        and el_recd[ELR_DEVICENAME] == devicename)]

                export_recd += self._export_ic3_event_log_reformat_recds(Device.fname_devicename, el_recds)

            #--------------------------------
            # # Prepare Global '*' records. Reverse the list elements using [::-1] and make a string of the results
            export_recd += f"\n\n{'_'*120}\n"
            export_recd += (f"Other/Locate Events:\n\n")
            export_recd += hdr_recd

            export_recd += self._export_ic3_event_log_reformat_recds('other', el_nondevice_recds)

            #--------------------------------
            export_filename = (f"icloud3-event-log_{datetime_for_filename()}.log")
            export_directory = (f"{Gb.ha_config_directory}/{export_filename}")
            export_directory = export_directory.replace("//", "/")

            export_file = open(export_directory, "w", encoding="utf-8")
            export_file.write(export_recd)
            export_file.close()

            self.post_event(f"iCloud3 Event Log Exported File > {CRLF_DOT}{export_directory}")

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    def _export_ic3_event_log_reformat_recds(self, log_section, el_recds):

        try:
            if el_recds is None:
                return ''

            record_str = ''
            startup_recds_flag = False
            el_recds.reverse()
            last_tfz_zone = ''
            for record in el_recds:
                devicename = record[ELR_DEVICENAME]
                time       = record[ELR_TIME] if record[ELR_TIME] not in ['Debug', 'Rawdata'] else SP(4)
                text       = record[ELR_TEXT]

                # iCloud3 Startup Records
                if log_section == 'startup':
                    if text[0:3] in [EVLOG_IC3_STARTING, EVLOG_IC3_STAGE_HDR]:
                        text = f"{SP(9)}{format_header_box(text[3:], indent=12, evlog_export=True)}"
                    elif text.startswith('^'):
                        text = f"{SP(4)}{filter_special_chars(text[3:], evlog_export=True)}"
                    else:
                        text = f"{SP(4)}{filter_special_chars(text, evlog_export=True)}"

                # Non-device related Records
                elif log_section == 'other':
                    text = f"{filter_special_chars(text, evlog_export=True)}"

                # Device Records
                else:
                    time = (time + SP(8))[:8]
                    text = self._reformat_device_recd(log_section, time, text)

                    if time.startswith('»Home'):
                        pass

                    # Start of tfz group header
                    elif time.startswith('»') and time != last_tfz_zone:
                        text = f"{SP(4)}⡇{' ~ '*18}\n{time}{text}"
                        last_tfz_zone = time

                    # End of tfz group trailer
                    elif last_tfz_zone.startswith('»') and time != last_tfz_zone:
                        text = f"{last_tfz_zone}{SP(4)}⡇{' ~ '*18}\n{time}{text}"
                        time = last_tfz_zone = ''

                if text != '':
                    record_str += f"{time}{text}\n"

            record_str += '\n\n'
            return record_str

        except Exception as err:
            log_exception(err)
            return ''

#--------------------------------------------------------------------
    def _reformat_device_recd(self, log_section, time, text):

        # Time-record = {mobapp_state},{ic3_zone},{interval},{travel_time},{distance)


        if text.startswith(EVLOG_UPDATE_START):
            text = f"Tracking Update ({log_section})" if text[3:] == '' else text[3:]
            text = f"{SP(5)}{format_header_box(text, indent=12, start_finish='start', evlog_export=True)}"
            return text

        elif text.startswith(EVLOG_UPDATE_END):
            text = f"{SP(4)}{format_header_box(text[3:], indent=12, start_finish='finish', evlog_export=True)}"
            return text

        elif text.startswith(EVLOG_TIME_RECD):
            tfz_adj = '  ' if (time.startswith('»') and time.startswith('»Home')) is False else ''
            text = text[3:]
            item = text.split(',')
            text = (f"{' '*(11-len(time))}{tfz_adj}⡇ "
                    f"MobApp-{item[0]}, "
                    f"iCloud3-{item[1]}, "
                    f"Interval-{item[2]}, "
                    f"TravTime-{item[3]}, "
                    f"Dist-{item[4]}")
            return text

        tfz_adj = '  ' if time.startswith('»') else ''
        group_char= '' if text.startswith('⡇') else \
                    '⡇ ' if Gb.trace_group else \
                    ''

        text = filter_special_chars(text, evlog_export=True)

        return f"{SP(4)}{tfz_adj}{group_char}{text}"

#--------------------------------------------------------------------
    @staticmethod
    def _replace_special_chars(text):
        text = text.replace('<', LT)
        text = text.replace('%lt', LT)
        text = text.replace('__', '')
        text = text.replace('"', '`')
        text = text.replace("'", "`")
        text = text.replace('~','--')
        text = text.replace('Background','Bkgnd')
        text = text.replace('Geographic','Geo')
        text = text.replace('Significant','Sig')
        return text

#--------------------------------------------------------------------
    @staticmethod
    def uncompress_evlog_recd_special_characters(recd):
        '''
        The evlog records may have a compressed character that is expanded in
        icloud3-event-log-card.js. It is used to reduce space in the
        sensor.icloud3-event_log entity.
        '''
        if recd is None:
            return recd

        recd = recd.replace('⣇', "")
        recd = recd.replace('⠈', " ")
        recd = recd.replace('⠉', "  ")
        recd = recd.replace('⠋', "   ")
        recd = recd.replace('⠛', "    ")
        recd = recd.replace('⠟', "     ")
        recd = recd.replace('⠿', "      ")

        return recd
