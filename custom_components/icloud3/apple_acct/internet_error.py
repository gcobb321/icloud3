
from ..global_variables import GlobalVariables as Gb
from ..const            import (CRLF, NBSP2, CRLF_DOT, NL3, NL4, RED_ALERT,
                                EVLOG_ALERT, EVLOG_BROWN_BAR, NOT_SET,
                                ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                NOTIFY)

from ..startup          import start_ic3
from ..utils.utils      import (instr, is_empty, isnot_empty, list_add, list_del, is_running_in_event_loop,)
from ..utils.time_util  import (time_now, time_now_secs, mins_since, format_time_age, format_age,
                                secs_to_time, secs_since, )
from ..utils.messaging  import (_evlog, _log, more_info, add_log_file_filter,
                                post_event, post_alert, post_greenbar_msg, post_error_msg, update_alert_sensor,
                                log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                log_data, log_exception, log_data_unfiltered, )

from ..utils            import file_io
from .                  import icloud_requests_io  as icloud_io

#----------------------------------------------------------------------------
import datetime as dt

from homeassistant.helpers.event import (track_time_interval, )

STATUS_MESSAGE_DOTS = '🟨🟨🟨🟨🟥'

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   CONNECTION ERROR HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class InternetConnection_ErrorHandler:

    def __init__(self):
        self.initialize_variables()
        self.initialize_variables_test_mode()

    def initialize_variables_test_mode(self):
        # Do not request update in icloud_session_requests. let 1-min timer expire
        self.internet_error_test_timeout = False


    def initialize_variables(self):
        self.internet_error_msg  = ''  # response msg/status_code (icloud_session_requests)
        self.internet_error_code = ''

        self.internet_error_secs = 0
        self.internet_went_offline_secs = 0
        self.status_msg_dot_cnt  = 0
        self.status_msg_bar      = ''
        self.icloud_check_cnt    = 0

        self.status_check_cnt    = 0
        self.status_check_secs   = 0
        self.icloud3_restart_needed = False
        self.internet_is_available     = False
        self.all_apple_accts_refreshed = True
        self.internet_error_notify_msg_sent = False
        self.notify_Device       = None
        self.log_level_save      = Gb.log_level
        self.data                = None
        start_ic3.set_log_level('rawdata')

        self.status_check_interval_secs = 5
        self.status_check_secs          = 20
        self.status_check_interval      = dt.timedelta(seconds=self.status_check_interval_secs)
        self.cancel_status_check_timer_fct = None

#----------------------------------------------------------------------------
    def start_internet_error_handler(self):
        '''
        Setup the internet connection error monitor.
        '''
        if Gb.internet_error is False:
            return

        self.icloud3_restart_needed = False
        self.internet_error_secs = time_now_secs()
        self.internet_went_offline_secs = time_now_secs()
        self.status_check_secs   = 20
        self.log_level_save = Gb.log_level
        start_ic3.set_log_level('rawdata')

        for Device in Gb.Devices:
            Device.pause_tracking()

        self.update_internet_connection_status_msg()
        self.schedule_next_status_check()
        self.update_internet_connection_status_msg()

#----------------------------------------------------------------------------
    def schedule_next_status_check(self):
        '''
        Start ha time_interval callback. Refresh display indicator every 5-secs
        to show activity. The check_internet_connection will check the internet
        status every 20-secs.
        '''

        self.cancel_status_check_timer_fct = track_time_interval(Gb.hass,
                                    self.check_internet_connection,
                                    self.status_check_interval,
                                    cancel_on_shutdown=True)

#----------------------------------------------------------------------------
    def check_internet_connection(self, check_time=None):
        '''
        See if the intenet is back up.
        If it is still down:
            - Display the Internet Connection Error messages after 1-min
            - Update the icloud3_alert sensor after 2-mins
        if it is back up:
            - clear the alert message and EvLog status msg
            - Resume tracking
        '''

        # Initial internet check before first status msg
        if self.status_check_cnt == 0:
            self.is_internet_available()

        self.status_check_secs -= 5
        self.update_internet_connection_status_msg()

        # Check status when the check_secs reaches 0 (every 20-secs)
        if self.status_check_secs > 0:
            return

        self.status_check_cnt += 1
        self.status_check_secs = 20
        self.internet_is_available = self.is_internet_available()

        if self.internet_is_available:
            self.all_apple_accts_refreshed = self.refresh_all_apple_accts()

            if self.all_apple_accts_refreshed:
                self.internet_connection_is_available_again()
                return

        # Internet has been down for 1-min
        if self.status_check_cnt == 3:
            self.display_internet_error_msg()

        if (mins_since(self.internet_error_secs) >= 2
                and self.internet_error_notify_msg_sent is False):
            self.internet_error_notify_msg_sent = True
            update_alert_sensor(ALERT_CRITICAL, (
                            "Internet Error detected at "
                            f"{secs_to_time(self.internet_error_secs)}"))
            post_event(f"Alert Sensor Updated > Internet Error detected at "
                            f"{secs_to_time(self.internet_error_secs)}")

#----------------------------------------------------------------------------
    def is_internet_available(self):
        '''
        See if the internet is available by sending a data request to the Apple url used to
        validate username/passwords via the https requests handler.

        This it's also called from __init__.py

        Return:
            True  - Internet is available
            False - Internet is not available

        Data returned from the file_io.https routine:
            Internet available:
                data={'url': 'https://setup.icloud.com/setup/authenticate/interneterrortestr',
                'error': HTTPStatusError("Client error '401 Unauthorized' for url
                'https://setup.icloud.com/setup/authenticate/interneterrortest'
                \nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/401"), 'status_code': -9}

            Internet not available:
                data={'url': 'https://setup.icloud.com/setup/authenticate/interneterrortest',
                'error': ConnectTimeout(''), 'status_code': -9}
        '''

        url = 'https://setup.icloud.com/setup/authenticate/interneterrortest'

        self.data = icloud_io.request(url)
        #log_data(, self.data)

        Gb.internet_error = self.data['error'].startswith('InternetError')
        self.internet_error_code = self.data['code']

        if self.is_testing_internet_error(inet_chk=True):
            Gb.internet_error = True

        return not Gb.internet_error

#----------------------------------------------------------------------------
    def refresh_all_apple_accts(self):
        '''
        Cycle through each apple account and see if a refresh_client yields in a 200 response code.
        If all account have a 200, then their icloud.com endpoint is back on line and connection error
        processing will end.

        If there is not a 200, the icloud3_restart_needed is set to True and the account with the error will
        be restarted. This should handle ConnectionReset type of errors where just resuming tracking will
        not work because the apple acct is not reachable.

        return:
        - True: All Apple accounts were refreshed
        - False: An Apple account failed to refresh
        '''

        self.icloud_check_cnt += 1

        if self.is_testing_internet_error(icloud_chk=True):
            return False

        # When starting iCloud3, the Apple accounts have not been logged into yet
        # so we can not check icloud.com access by refreshing the device data
        if is_empty(Gb.AppleAcct_by_username):
            self.icloud3_restart_needed = True
            return True

        # Refresh the device data for each Apple acct
        for username, AppleAcct in Gb.AppleAcct_by_username.items():
            if (AppleAcct is None
                    or AppleAcct.is_AADevices_setup_complete is False):
                self.icloud3_restart_needed = True
                return False

            try:
                was_data_refreshed = AppleAcct.refresh_icloud_data()
                if was_data_refreshed is False:
                    self.icloud3_restart_needed = True
                    return False

            except Exception as err:
                log_exception(err)

        return True

#----------------------------------------------------------------------------
    def internet_connection_is_available_again(self):
        '''
        Internet is back up, reset the connection error variables and post the necessary events
        '''

        data_source_not_set_Devices = [Device
                                    for Device in Gb.Devices
                                    if (Device.dev_data_source == NOT_SET)]

        # If internet is available on the first ping, then it probably means icloud.com is down,
        # the session is now invalid or the connection has been
        # If no connection during startup, restart. Otherwise, resume all tracking
        if (isnot_empty(data_source_not_set_Devices)
                or Gb.initial_icloud3_loading_flag
                or self.icloud3_restart_needed):
            event_msg =(f"Internet Connection Available at {secs_to_time(time_now_secs())}, "
                        f"Down for-{format_age(self.internet_went_offline_secs, xago=False)}, "
                        f"Restarting")

            Gb.restart_icloud3_request_flag = True
            Gb.AppleAcct_by_username = {}
            Gb.iCloudSession_by_username = {}
            Gb.valid_upw_by_username = {}

        else:
            event_msg =(f"Internet Connection Available at {secs_to_time(time_now_secs())}, "
                        f"Down for-{format_age(self.internet_went_offline_secs, xago=False)}")

            for Device in Gb.Devices:
                Device.resume_tracking()

        if mins_since(self.internet_went_offline_secs) <= 1:
            event_msg =(f"Internet Connection Error at "
                        f"{secs_to_time(self.internet_went_offline_secs)} "
                        f"for less than 1-min")

        self.reset_internet_error(reset_test_control_flags=True)

        post_event(f"{EVLOG_BROWN_BAR}{event_msg}")
        log_error_msg(f"iCloud3 Alert > {event_msg}")

        # update_alert_sensor(ALERT_CRITICAL, f"Internet Connection Available at "
        #                                     f"{secs_to_time(time_now_secs())}")
        update_alert_sensor(ALERT_CRITICAL, "")

#----------------------------------------------------------------------------
    def update_internet_connection_status_msg(self):
        '''
        Display the offline message. Show a progress bar that refreshes on 5-sec
        interval while checking the status
        '''

        if self.status_check_secs < 0:
            self.status_check_secs = 20

        status_msg_dot_cnt = int(5 - self.status_check_secs/5)
        status_bar_base = '' if self.status_check_cnt % 2 == 0 else STATUS_MESSAGE_DOTS
        self.status_msg_bar = f"{status_bar_base}{STATUS_MESSAGE_DOTS[:status_msg_dot_cnt]}"

        if self.all_apple_accts_refreshed:
            mode_msg = '⚡ Internet Check'
        else:
            mode_msg = (f"⚡ Internet Check Completed, Connection Available"
                        f"{CRLF}🍎 icloud.com Check")

        post_greenbar_msg(
                f"Internet Error detected at "
                f"{format_time_age(self.internet_error_secs, xago=True)}, Trk Paused"
                f"{CRLF}{mode_msg} "
                f"#{self.status_check_cnt+1} "
                f"in {self.status_check_secs:0>2}s"
                f"{NBSP2}{self.status_msg_bar}")

#----------------------------------------------------------------------------
    def is_testing_internet_error(self, inet_chk=None, icloud_chk=None):

        if Gb.test_internet_error is False:
            return False

        if inet_chk is True and self.status_check_cnt <= Gb.test_internet_error_counter:
            return True

        if icloud_chk is True and self.icloud_check_cnt <= Gb.test_internet_error_counter:
            return True

        return False

#----------------------------------------------------------------------------
    def reset_internet_error(self, reset_test_control_flags=None):
        if self.cancel_status_check_timer_fct:
            self.cancel_status_check_timer_fct()

        if self.internet_error_secs > 0:
            post_greenbar_msg('')
            self.initialize_variables_test_mode()
            if reset_test_control_flags is True:
                Gb.test_internet_error = False
                Gb.test_internet_error_after_startup = False

        self.initialize_variables()
        start_ic3.set_log_level(self.log_level_save)
        Gb.icloud_io_request_secs = 0
        Gb.internet_error = False

#----------------------------------------------------------------------------
    def ha_system_network_ipv6_info(self):
        '''
        Extract the hassio_network_info from hass.data and determine if IPv6
        is disabled.

        Return:
            - Disabled = None
            - Enabled  = [interface-name (end0), method(auto), primary (True), enabled (True)]

        {'interface': 'wlan0', 'type': 'wireless', 'enabled': False, 'connected': False, 'primary': False,
                'mac': '2C:CF:67:4E:40:AA',
            'ipv4': {'method': 'disabled', 'address': [], 'nameservers': [], 'gateway': None, 'ready': False},
            'ipv6': {'method': 'disabled', 'addr_gen_mode': 'default', 'ip6_privacy': 'default',
                'address': [], 'nameservers': [], 'gateway': None,
                'ready': False}, 'wifi': None, 'vlan': None}
        {'interface': 'end0', 'type': 'ethernet', 'enabled': True, 'connected': True, 'primary': True,
                'mac': '2C:CF:67:4E:40:A8',
            'ipv4': {'method': 'auto',
                'address': ['10.0.2.200/24'], 'nameservers': ['10.0.2.1'], 'gateway': '10.0.2.1',
                'ready': True},
            'ipv6': {'method': 'auto', 'addr_gen_mode': 'default', 'ip6_privacy': 'default',
                'address': ['fe80::802:b59f:10ee:face/64'], 'nameservers': [], 'gateway': None,
                'ready': False}, 'wifi': None, 'vlan': None}
        '''
        try:
            hassio_network_info = Gb.hass.data.get('hassio_network_info', {})
            self._log_hassio_network_info(hassio_network_info)

            if hassio_network_info:
                interfaces = hassio_network_info.get('interfaces', {})
                for interface in interfaces:
                    if interface['ipv6']['method'] != 'disabled':
                        return [interface['interface'], interface['ipv6']['method']]
        except:
            pass

        return None

#----------------------------------------------------------------------------
    def display_internet_error_msg(self):

        if Gb.icloud_io_request_secs > 0:
            ipv6_info = self.ha_system_network_ipv6_info()
            if ipv6_info:
                alert_msg =(f"{RED_ALERT}IPv6 DETECTED > Apple location server does not respond to "
                            f"IPv6 requests. HA Network setting for IPv6 `{ipv6_info[0]}` is `{ipv6_info[1]}`.")
            else:
                alert_msg =(f"{RED_ALERT}ERROR REQUESTING LOCATION > Either an error occurred sending "
                            f"the the location request or the Apple location server did not respond."
                            f"This can be caused by IPv6 being enabled in HA.")
            alert_msg+=(f"{CRLF}1. Go to HA Devices & settings > System > Network"
                        f"{CRLF}2. Change IPv6 to `disabled`. Then Restart HA")
            post_alert(alert_msg)

        post_alert( f"INTERNET ERROR DETECTED > "
                    f"Checking status every 20-secs, Tracking Paused, "
                    f"{self.internet_error_msg}, "
                    f"Error Code-{self.internet_error_code}, Possible causes:"
                    f"{CRLF_DOT}An Internet Connection Error (Internet, WiFi, Router is down)"
                    f"{CRLF_DOT}Apple is not available (`www.icloud.com` is down)"
                    f"{CRLF}")


        post_event( f"{EVLOG_BROWN_BAR}Internet Error detected at "
                    f"{secs_to_time(self.internet_error_secs)}, "
                    f"Tracking Paused, "
                    f"{self.internet_error_msg}, "
                    f"Error-{self.internet_error_code}")

#----------------------------------------------------------------------------
    def _log_hassio_network_info(self, hassio_network_info):
        interfaces = hassio_network_info.get('interfaces', {})
        msg = ''
        for interface in interfaces:
            _interface = interface.copy()
            ipv4 = _interface.pop('ipv4', {})
            ipv6 = _interface.pop('ipv6', {})
            if msg: msg += f"{NL4}❗ "
            msg += (f" {interface['interface']}-{_interface}, "
                    f"{NL4}❗   ipv4-{ipv4}"
                    f"{NL4}❗   ipv6-{ipv6}")

        title = f"{NL3}🔻 HASSIO NETWORK CONFIGURATION (HA Settings > System > Network)"
        if msg == '': msg = 'No network interface parameters found'
        log_data_unfiltered(f"{title}", msg)
