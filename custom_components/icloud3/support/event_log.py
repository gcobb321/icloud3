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
                                    HHMMSS_ZERO, HIGH_INTEGER, NONE, IOSAPP, DOT2,
                                    EVLOG_TABLE_MAX_CNT_BASE, EVENT_LOG_CLEAR_SECS,
                                    EVENT_LOG_CLEAR_CNT, EVLOG_TABLE_MAX_CNT_ZONE, EVLOG_BTN_URLS,
                                    EVLOG_TIME_RECD, EVLOG_HIGHLIGHT, EVLOG_MONITOR,
                                    EVLOG_ERROR, EVLOG_ALERT, EVLOG_UPDATE_START, EVLOG_UPDATE_END,
                                    EVLOG_IC3_STARTING, EVLOG_IC3_STAGE_HDR,
                                    CRLF, CRLF_DOT, CRLF_CHK, RARROW, DOT, LT, GT,
                                    CONF_EVLOG_BTNCONFIG_URL,
                                    )

from ..helpers.common       import instr, circle_letter
from ..helpers.messaging    import log_exception, log_info_msg, log_warning_msg, _traceha, _trace
from ..helpers.time_util    import time_to_12hrtime, datetime_now, time_now_secs


import time
import homeassistant.util.dt as dt_util



CONTROL_RECD            = [HHMMSS_ZERO,'Control Record']
SENSOR_EVENT_LOG_ENTITY = 'sensor.icloud3_event_log'
ELR_DEVICENAME = 0
ELR_TIME = 1
ELR_TEXT = 2

# The text starts with a special character:
# ^1^ - LightSeaGreen
# ^2^ - BlueViolet
# ^3^ - OrangeRed
# ^4^ - DeepPink
# ^5^ - MediumVioletRed
# ^6^ - --dark-primary-color
# EVLOG_NOTICE      = "^2^"
# EVLOG_ERROR       = "^3^"
# EVLOG_ALERT       = "^4^"
# EVLOG_TRACE       = "^5^"
# EVLOG_MONITOR     = "^6^"

MONITORED_DEVICE_EVENT_FILTERS = [
    'iCloud Acct Auth',
    'Nearby Devices',
    'iOSApp Location',
    'Updated',
    'Trigger',
    'Old',
]

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class EventLog(object):
    def __init__(self, hass):
        self.hass = hass
        self.initialize()

    def initialize(self):
        self.display_text_as         = {}
        self.evlog_table             = []   # Device event recds
        self.evlog_table_startup     = []   # All Event recds during startup
        self.evlog_table_max_cnt     = EVLOG_TABLE_MAX_CNT_BASE

        self.devicename              = ''
        self.fname_selected          = ''
        self.devicename_by_fnames    = {}
        self.clear_secs              = HIGH_INTEGER
        self.trk_monitors_flag       = False
        self.log_debug_flag          = False
        self.log_rawdata_flag        = False
        self.last_refresh_secs       = 0
        self.last_refresh_devicename = ''
        self.user_message            = ''       # Display a message in the name0 button
        self.user_message_alert_flag = False    # Do not clear the message if this is True
        self.alert_message           = ''
        self.evlog_btn_urls          = EVLOG_BTN_URLS.copy()

        v2_v3_browser_refresh_msg ={"Browser Refresh Required":
                                   ("✪✪ This is Event Log v2, not "
                                    "v3. A Browser Refresh is "
                                    "Required ✪✪ "
                                    "───────────────── "
                                    "Ctrl-Shift-Del, then Refresh "
                                    "the browser tab. You may have to "
                                    "do this several times. "
                                    "────────────────── "
                                    "If 'iCloud3 v3 - Event Log' is "
                                    "not displayed, restart HA. Also "
                                    "do this on devices running the iOS App. "
                                    "───────────────── "
                                    "See the iCloud3 User Guide: "
                                    "https://gcobb321.github.io/icloud3_v3_docs/#/chapters/0.1-migrating-v2.4-to-v3.0?"
                                    "id=step-5-clear-the-browsers-cache "
                                    "───────────────── "
                                    )}

        self.evlog_sensor_state_value       = ''
        self.evlog_btn_urls['btnConfig']    = Gb.evlog_btnconfig_url

        self.evlog_attrs                    = {}
        self.evlog_attrs["version_ic3"]     = Gb.version
        self.evlog_attrs["version_evlog"]   = Gb.version_evlog
        self.evlog_attrs["log_level_debug"] = ''
        self.evlog_attrs["run_mode"]        = 'Initialize'
        self.evlog_attrs["evlog_btn_urls"]  = self.evlog_btn_urls
        self.evlog_attrs["user_message"]    = self.user_message
        self.evlog_attrs["update_time"]     = ''
        self.evlog_attrs["devicename"]      = ''
        self.evlog_attrs["fname"]           = ''
        self.evlog_attrs["fnames"]          = {'Setup': 'Initializing iCloud3'}
        self.evlog_attrs["filtername"]      = 'Initialize'
        self.evlog_attrs["name"]            = {"Browser Refresh is Required to load v3":
                                                "Browser Refresh is Required to load v3"}
        self.evlog_attrs["names"]           = v2_v3_browser_refresh_msg
        self.evlog_attrs["logs"]            = []

        self.devicename_cnts = {}

    def __repr__(self):
        return (f"<EventLog: {self.devicename_by_fnames}>")

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
            self.devicename_by_fnames = {}
            self.evlog_table_max_cnt  = EVLOG_TABLE_MAX_CNT_BASE

            self.devicename_by_fnames.update({devicename: Device.fname
                            for devicename, Device in Gb.Devices_by_devicename_tracked.items()
                            if devicename != ''})
            self.devicename_by_fnames.update({devicename: f"{Device.fname} {circle_letter('m')}"
                            for devicename, Device in Gb.Devices_by_devicename_monitored.items()
                            if devicename != ''})

            tfz_cnt = sum([len(Device.FromZones_by_zone) for Device in Gb.Devices])
            self.evlog_table_max_cnt = EVLOG_TABLE_MAX_CNT_ZONE*tfz_cnt

            if self.devicename_by_fnames == {}:
                self.user_message_alert_flag = True
                self.evlog_attrs["user_message"] = 'No Devices have been configured'
                self.devicename_by_fnames["nodevices"] = 'No Devices have been configured'
                self.fname_selected = "NoDevices"

            elif self.devicename == '':
                self.devicename = next(iter(self.devicename_by_fnames))
                self.fname_selected = self.devicename_by_fnames[self.devicename]

            if Gb.evlog_version.startswith('3'):
                self.evlog_attrs["name"] = ''
                self.evlog_attrs["names"] = ''

            self.evlog_btn_urls['btnConfig']   = Gb.evlog_btnconfig_url
            self.evlog_attrs["version_ic3"]    = Gb.version
            self.evlog_attrs["version_evlog"]  = Gb.version_evlog
            self.evlog_attrs["run_mode"]       = "Initialize"
            self.evlog_attrs["evlog_btn_urls"] = self.evlog_btn_urls
            self.evlog_attrs["update_time"]    = "setup"
            self.evlog_attrs["devicename"]     = self.devicename
            self.evlog_attrs["fname"]          = self.fname_selected
            self.evlog_attrs["fnames"]         = self.devicename_by_fnames
            self.evlog_attrs["filtername"]     = 'Initialize'

            Gb.EvLogSensor.async_update_sensor()

        except Exception as err:
            log_exception(err)

        return

#------------------------------------------------------
    def post_event(self, devicename, event_text='+'):
        '''
        Add records to the Event Log table the device. If the device="*",
        the event_text is added to all deviceFNAMEs table.

        The event_text can consist of pseudo codes that display a 2-column table (see
        _display_usage_counts function for an example and details)

        The event_log lovelace card will display the event in a special color if
        the text starts with a special character:
        '''

        if event_text == '+':
            event_text = devicename
            devicename = "*" if Gb.start_icloud3_inprocess_flag else '**'
        elif devicename is None or devicename in ['', '*']:
            devicename = "*" if Gb.start_icloud3_inprocess_flag else '**'

        if (instr(event_text, "▼") or instr(event_text, "▲")
                or len(event_text) == 0
                or instr(event_text, "event_log")):
            return

        # If monitored device and the event msg is a status msg for other devices,
        # do not display it on a monitoed device screen
        Device = Gb.Devices_by_devicename.get(devicename)
        if Device and Device.is_monitored:
            start_pos = 2 if event_text.startswith('^') else 0
            for filter_text in MONITORED_DEVICE_EVENT_FILTERS:
                if event_text[start_pos:].startswith(filter_text):
                    return

        # Drop duplicate event_text item that has already been displayed. Also,
        # if a ^c^ start header is immediately follows an ^s^ header, the group is empty,
        # delete the ^s^ header and throw the current record (^c^ header) away.
        try:
            if (devicename.startswith('*') is False and len(self.evlog_table) > 8):
                in_last_few_recds = [v for v in self.evlog_table[:8] \
                                        if (v[ELR_DEVICENAME] == devicename \
                                            and v[ELR_TEXT] == event_text \
                                            and v[ELR_TEXT].startswith(EVLOG_TIME_RECD) is False)]
                if in_last_few_recds != []:
                    return

                # If this is an Update Completed msg
                if event_text.startswith(EVLOG_UPDATE_END):
                    # Drop previous msg if it was an Update Started msg
                    for idx in range(0, 8):
                        if self.evlog_table[idx][ELR_TEXT].startswith(EVLOG_UPDATE_START):
                            self.evlog_table[idx].pop()
                            return
                        if self.evlog_table[idx][ELR_TEXT].startswith(EVLOG_MONITOR) is False:
                            break
        except Exception as err:
            # log_exception(err)
            pass

        try:
            if (event_text.startswith(EVLOG_UPDATE_START)
                    or event_text.startswith(EVLOG_UPDATE_END)
                    or event_text.startswith(EVLOG_IC3_STARTING)
                    or event_text.startswith(EVLOG_IC3_STAGE_HDR)):
                if len(event_text) <= 5:
                    this_update_time = ''
                elif Gb.log_rawdata_flag:
                    this_update_time = 'Rawdata'
                elif Gb.log_debug_flag:
                    this_update_time = 'Debug'
                else:
                    this_update_time = ''

            else:
                this_update_time = dt_util.now().strftime('%H:%M:%S')
                this_update_time = time_to_12hrtime(this_update_time)

                # If tracking from more than one zone and the tfz results are being displayed,
                # display tfz zone name in the time field. Capitalize if going towards
                if devicename.startswith('*') is False:
                    Device = Gb.Devices_by_devicename.get(devicename)
                    if Device:
                        Device.last_evlog_msg_secs = time_now_secs()
                        from_zone_display_as = Device.FromZone_BeingUpdated.from_zone_display_as
                        if event_text.startswith(EVLOG_TIME_RECD):
                            this_update_time = f"»{from_zone_display_as[:6]}"
                            if (Device.FromZone_BeingUpdated is Device.FromZone_TrackFrom
                                    and Device.FromZone_BeingUpdated is not Device.FromZone_Home):
                                this_update_time = this_update_time.upper()
                        elif from_zone_display_as != HOME_FNAME:
                            this_update_time = f"»{from_zone_display_as[:6]}"

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

            #Keep track of special colors so it will continue on the
            #next text chunk
            color_symbol = ''
            if event_text.startswith('^1^'): color_symbol = '^1^'
            if event_text.startswith('^2^'): color_symbol = '^2^'
            if event_text.startswith('^3^'): color_symbol = '^3^'
            if event_text.startswith('^4^'): color_symbol = '^4^'
            if event_text.startswith('^5^'): color_symbol = '^5^'
            if event_text.startswith('^6^'): color_symbol = '^6^'
            if instr(event_text, EVLOG_ERROR):     color_symbol = '!'
            char_per_line = 2000

            #Break the event_text string into chunks of 250 characters each and
            #create an event_log recd for each chunk
            if len(event_text) < char_per_line:
                event_recd = [devicename, this_update_time, event_text]

                self._insert_event_log_recd(event_recd)

            else:
                line_no       = int(len(event_text)/char_per_line + .5)
                char_per_line = int(len(event_text) / line_no)
                event_text   +=f" ({len(event_text)}-{line_no}-{char_per_line})"

                if event_text.find(CRLF) > 0:
                    split_str = CRLF
                else:
                    split_str = " "
                split_str_end_len = -1 * len(split_str)
                word_chunk = event_text.split(split_str)

                line_no = len(word_chunk)-1
                event_chunk = ''
                while line_no >= 0:
                    if len(event_chunk) + len(word_chunk[line_no]) + len(split_str) > char_per_line:
                        event_recd = [devicename, '',
                                        (f"{color_symbol}{event_chunk[:split_str_end_len]} ({event_chunk[:split_str_end_len]})")]
                        self._insert_event_log_recd(event_recd)

                        event_chunk = ''

                    if len(word_chunk[line_no]) > 0:
                        event_chunk = word_chunk[line_no] + split_str + event_chunk

                    line_no-=1

                event_recd = [devicename, this_update_time,
                                (f"{event_chunk[:split_str_end_len]} ({event_chunk[:split_str_end_len]})")]
                self._insert_event_log_recd(event_recd)

        except Exception as err:
            log_exception(err)

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
                self.evlog_attrs['fname']      = self.fname_selected = self.devicename_by_fnames[devicename]

            self.evlog_sensor_state_value = devicename
            self.evlog_attrs['logs'] = self._filtered_evlog_recds(devicename, max_recds)

            self.update_evlog_sensor()

            self.last_refresh_devicename = devicename
            self.last_refresh_secs       = time_now_secs()

        except Exception as err:
            log_exception(err)

#------------------------------------------------------
    def export_event_log(self):
        '''
        Export Event Log to 'config/icloud_event_log-[time].log'.
        '''

        try:
            log_update_time =   (f"{dt_util.now().strftime('%a, %m/%d')}, "
                                f"{dt_util.now().strftime(Gb.um_time_strfmt)}")
            hdr_recd    = (f"Time\t\t   Event\n{'-'*120}\n")
            export_recd = (f"iCloud3 Event Log v{Gb.version}\n\n"
                            f"Log Update Time: {log_update_time}\n"
                            f"Tracked Devices:\n")

            export_recd += f"\nGeneral Configuration:\n"
            export_recd += f"\t{Gb.conf_general}\n"

            for devicename, Device in Gb.Devices_by_devicename.items():
                export_recd += (f"\t{DOT}{Device.fname_devicename} >\n"
                                f"\t\t\t{Device.conf_device}\n")

            # Prepare Global '*' records. Reverse the list elements using [::-1] and make a string of the results
            export_recd += f"\n\n{'_'*120}\n"
            export_recd += (f"System Events:\n\n")
            export_recd += hdr_recd
            el_recds     = [el_recd for el_recd in self.evlog_table if el_recd[ELR_DEVICENAME].startswith("*")]
            export_recd += self._export_ic3_event_log_reformat_recds('*', el_recds)

            # Prepare recds for each device. Each record is [devicename, time, text]
            for devicename, Device in Gb.Devices_by_devicename.items():
                export_recd += f"{'_'*120}\n"
                export_recd += (f"{Device.fname_devicename}:\n\n")
                export_recd += hdr_recd

                valid_recds  = [el_recd for el_recd in self.evlog_table if len(el_recd) == 3]
                el_recds     = [el_recd for el_recd in valid_recds \
                                if (el_recd[ELR_DEVICENAME] == devicename and el_recd[ELR_TEXT] != "Device.Cnts")]
                export_recd += self._export_ic3_event_log_reformat_recds(devicename, el_recds)

            datetime = datetime_now().replace('-', '.').replace(':', '.').replace(' ', '-')
            export_filename = (f"icloud3-event-log_{datetime}.log")
            export_directory = (f"{Gb.ha_config_directory}/{export_filename}")
            export_directory = export_directory.replace("//", "/")

            export_file = open(export_directory, "w")
            export_file.write(export_recd)
            export_file.close()

            self.post_event(f"iCloud3 Event Log Exported > {export_directory}")

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
    def display_user_message(self, user_message, alert=False, clear_alert=False):
        '''
        Display or clear the special message displayed in the name0 button on
        the Event Log. However, do not change or clear it if the persists flag
        is set (Error, Tracking is Paused, iCloud authentication is needed, etc).

        Note:
        The user_message_alert_flag must be set to False to change or clear
        a message.
        '''
        if clear_alert:
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
    def _insert_event_log_recd(self, event_recd):
        """Add the event recd into the event table"""

        if self.evlog_table is None:
            self.evlog_table = CONTROL_RECD

        try:
            if len(event_recd) != 3:
                log_warning_msg(f"INVALID EVLOG RECD (SHORT)-{event_recd}")
                return
            elif event_recd[ELR_TEXT] == '':
                log_warning_msg(f"INVALID EVLOG RECD (EMPTY TEXT)-{event_recd}")
                return

            evl_table_recd_cnt = len(self.evlog_table)
            if evl_table_recd_cnt >= self.evlog_table_max_cnt:
                self.devicename_cnts = {}
                for elr_recd in self.evlog_table:
                    self._update_evlog_table_device_cnt(elr_recd)

                self._shrink_evlog_table(500)

        except Exception as err:
            log_exception(err)
            pass


        # Add the startup and alert events to a non-clearable table
        if (Gb.start_icloud3_inprocess_flag
                or Gb.initial_icloud3_loading_flag):
            self.evlog_table_startup.insert(0, event_recd)

        elif event_recd[ELR_TEXT].startswith(EVLOG_ALERT):
            self.evlog_table_startup.insert(0, event_recd)

        self.evlog_table.insert(0, event_recd)

#------------------------------------------------------
    def _shrink_evlog_table(self, shrink_cnt):
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
            evlog_table_recd_cnt   = len(self.evlog_table)
            evlog_table_target_cnt = self.evlog_table_max_cnt - shrink_cnt
            delete_cnt = 0
            delete_reg_cnt = 0
            delete_mon_cnt = 0
            self.devicename_cnts = {}

            # Go from end of table to front
            for x in range(evlog_table_recd_cnt-2, 2, -1):
                elr_recd     = self.evlog_table[x]
                el_recd_text = elr_recd[ELR_TEXT]

                # Delete monitor recds or 20% of regular device at end of tble
                if (el_recd_text.startswith(EVLOG_MONITOR)
                        or delete_cnt < delete_device_recd_cnt):
                    delete_cnt += 1
                    if el_recd_text.startswith(EVLOG_MONITOR):
                        delete_mon_cnt += 1
                    else:
                        delete_reg_cnt += 1

                    del self.evlog_table[x]
                    self._update_evlog_table_device_cnt(elr_recd)

                    if delete_cnt >= shrink_cnt:
                        break

            # If not enough recds were deleted, force deleting some
            if len(self.evlog_table) > evlog_table_target_cnt:
                delete_cnt += len(self.evlog_table) - evlog_table_target_cnt
                del self.evlog_table[evlog_table_target_cnt:]

            if delete_cnt > 0:
                event_msg = (   f"{EVLOG_MONITOR}Event Log Table Size Reduced > "
                                f"RecdCnt-{evlog_table_recd_cnt}{RARROW}"
                                f"{len(self.evlog_table)}, "
                                f"Deleted-{delete_cnt} "
                                f"(DevInfo-{delete_reg_cnt}, "
                                f"Monitor-{delete_mon_cnt})")
                self.post_event(event_msg)

        except Exception as err:
            log_exception(err)

#------------------------------------------------------
    def _update_evlog_table_device_cnt(self, elr_recd):
        devicename = elr_recd[ELR_DEVICENAME]
        recd_type  = 'Mon' if elr_recd[ELR_TEXT].startswith(EVLOG_MONITOR) else 'Reg'
        devicename_type = f"{devicename}-{recd_type}"
        if devicename_type not in self.devicename_cnts:
            self.devicename_cnts[devicename_type] = 0
        self.devicename_cnts[devicename_type] += 1

#------------------------------------------------------
    def clear_alert(self):
        self.alert_message = ''

#------------------------------------------------------
    def _filtered_evlog_recds(self, devicename='', max_recds=HIGH_INTEGER, selected_devicename=None):
        '''
        Extract the filtered records from the evlog_tables and prepare them
        for display
        '''

        if devicename == '':
            devicename = self.devicename
        time_text_recds = self._extract_filtered_evlog_recds(devicename)

        if max_recds < HIGH_INTEGER:
            recd_cnt = len(time_text_recds)
            time_text_recds = time_text_recds[0:max_recds]

            refresh_msg = ( f"{EVLOG_HIGHLIGHT}Tap `Refresh` or select a device "
                            f"to display all of the events")
            refresh_recd = ['',refresh_msg]
            time_text_recds.insert(0, refresh_recd)

        if self.alert_message != '':
            alert_msg = ( f"{EVLOG_HIGHLIGHT}{self.alert_message}")
            alert_recd = ['',alert_msg]
            time_text_recds.insert(0, alert_recd)

        time_text_recds.append(CONTROL_RECD)

        return str(time_text_recds)

#--------------------------------------------------------------------
    def _extract_filtered_evlog_recds(self, devicename):
        '''
        Build the event items attribute for the event log sensor. Each item record
        is [device, time, state, zone, interval, travTime, dist, textMsg]
        Select the items for the device or '*' and return the string of
        the resulting list to be passed to the Event Log
        '''
        if devicename == 'startup_log':
            if Gb.evlog_trk_monitors_flag:
                return [el_recd[1:3] for el_recd in self.evlog_table_startup]
            else:
                return [el_recd[1:3] for el_recd in self.evlog_table_startup
                                        if el_recd[ELR_TEXT].startswith(EVLOG_MONITOR) is False]

        el_devicename_check = ['*', '**', 'nodevices', devicename]

        if Device := Gb.Devices_by_devicename.get(devicename):
            filter_record = (Device.primary_data_source == IOSAPP) \
                                or Device.is_monitored 
        else:
            Device = None
            filter_record = False

        # Select devicename recds, keep time & test elements, drop devicename
        try:
            devicename_recds = [el_recd for el_recd in self.evlog_table
                                        if (el_recd[ELR_DEVICENAME] in el_devicename_check
                                                and len(el_recd) == 3)]

            if Gb.evlog_trk_monitors_flag:
                return [el_recd[1:3] for el_recd in devicename_recds]

            elif filter_record:
                return [el_recd[1:3] for el_recd in devicename_recds
                                                if (el_recd[ELR_TEXT].startswith(EVLOG_MONITOR) is False
                                                    and self._filter_record(Device, el_recd[ELR_TEXT]))]
            else:
                return [el_recd[1:3] for el_recd in devicename_recds
                                                if (el_recd[ELR_TEXT].startswith(EVLOG_MONITOR) is False)]

        except IndexError:
            for el_recd in self.evlog_table:
                if el_recd[ELR_DEVICENAME] not in el_devicename_check:
                    continue
                elif el_recd[ELR_DEVICENAME] in el_devicename_check:
                    log_info_msg(f"{el_recd}")
                elif len(el_recd) <= 3:
                    log_info_msg(f"{el_recd}")

        return []

#--------------------------------------------------------------------
    @staticmethod
    def _filter_record(Device, el_recd_text):
        '''
        Filter icloud account records from events for a device when its primary
        data source it's the ios app

        Return True if the record should be displayed
        '''

        if el_recd_text.startswith('iCloud Acct'):
            return False

        return True

#--------------------------------------------------------------------
    def _export_ic3_event_log_reformat_recds(self, devicename, el_records):

        try:
            if el_records is None:
                return ''

            record_str = ''
            inside_home_det_interval_flag = False
            el_records.reverse()
            for record in el_records:
                devicename = record[ELR_DEVICENAME]
                time       = record[ELR_TIME] if record[ELR_TIME] not in ['Debug', 'Rawdata'] else ''
                text       = record[ELR_TEXT]

                # Time-record = {iosapp_state},{ic3_zone},{interval},{travel_time},{distance
                if text.startswith(EVLOG_UPDATE_START):
                    block_char = '\t\t\t┌─ '
                    inside_home_det_interval_flag = True
                elif text.startswith(EVLOG_UPDATE_END):
                    block_char = '\t\t\t└─ '
                    inside_home_det_interval_flag = False
                elif text.startswith('Results:'):
                    if time.startswith('»') and time.startswith('»Home') is False:
                        block_char = '\t\t├─ '
                    else:
                        block_char = '\t├─ '
                elif inside_home_det_interval_flag and time.startswith('»'):
                    block_char = '\t\t│  '
                elif inside_home_det_interval_flag:
                    block_char = '\t│  '
                else:
                    block_char = '\t   '

                if text.startswith(EVLOG_TIME_RECD):
                    text = text[3:]
                    item = text.split(',')
                    text = (f"iOSAppState-{item[0]}, "
                            f"iCloud3Zone-{item[1]}, "
                            f"Interval-{item[2]}, "
                            f"TravelTime-{item[3]}, "
                            f"Distance-{item[4]}")

                text = text.replace("'", "").replace('&nbsp;', ' ').replace('<br>', ', ')
                text = text.replace(",  ", ",").replace('  ', ' ')
                if text.startswith('^'):
                        text = text[3:]

                chunk_len = 100
                start_pos=0
                end_pos = chunk_len + 5
                while start_pos < len(text):
                    if start_pos == 0:
                        chunk = (f"{time}{block_char}{text[start_pos:end_pos]}\n")
                    elif inside_home_det_interval_flag:
                        chunk = (f"\t\t\t│\t\t{text[start_pos:end_pos]}\n")
                    else:
                        chunk= (f"\t\t\t\t\t{text[start_pos:end_pos]}\n")
                    record_str += chunk
                    start_pos += end_pos
                    end_pos += chunk_len

            record_str += '\n\n'
            return record_str

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    @staticmethod
    def _replace_special_chars(event_text):
        event_text = event_text.replace('<', LT)
        # event_text = event_text.replace('>', GT)
        event_text = event_text.replace('__', '')
        event_text = event_text.replace('"', '`')
        event_text = event_text.replace("'", "`")
        event_text = event_text.replace('~','--')
        event_text = event_text.replace('Background','Bkgnd')
        event_text = event_text.replace('Geographic','Geo')
        event_text = event_text.replace('Significant','Sig')

        return event_text
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
