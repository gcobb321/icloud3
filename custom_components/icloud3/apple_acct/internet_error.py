
from ..global_variables import GlobalVariables as Gb
from ..const            import (CRLF, NBSP2, CRLF_DOT, EVLOG_ALERT, EVLOG_BROWN_BAR, NOT_SET, RED_ALERT,
                                ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                NOTIFY)

from ..startup          import start_ic3
from ..utils.utils      import (instr, is_empty, isnot_empty, list_add, list_del,)
from ..utils.time_util  import (time_now, time_now_secs, mins_since, format_time_age, format_age,
                                secs_to_time, secs_since, )
from ..utils.messaging  import (_evlog, _log, more_info, add_log_file_filter,
                                post_event, post_evlog_greenbar_msg, post_error_msg, update_alert_sensor,
                                log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                log_data, log_exception, log_data_unfiltered, filter_data_dict, )

from ..utils            import file_io

#----------------------------------------------------------------------------
import datetime as dt

from homeassistant.helpers.event         import async_track_time_interval

STATUS_MESSAGE_DOTS = '🟨🟨🟨🟨🟥'

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   CONNECTION ERROR HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class InternetConnection_ErrorHandler:

    # Raise ConnectionError in PyiCloud_session
    internet_error_test = False
    internet_error_test_after_startup = False   # Activated via EvLog > Actions > Export EvLog, then Locate
    internet_error_test_timeout = False          # Do not request update in pyicloud_session. let 1-min timer expire
    internet_error_test_mode = internet_error_test or internet_error_test_after_startup or internet_error_test_timeout
    internet_error_test_counter = 4

    internet_error_msg  = ''  # response msg/status_code (pyicloud_session)
    internet_error_code = ''

    internet_error_secs = 0
    status_msg_dot_cnt  = 0
    status_msg_bar      = ''
    icloud_check_cnt    = 0
    status_check_cnt    = 0
    status_check_secs   = 0
    apple_acct_restart_needed = False
    internet_is_available     = False
    all_apple_accts_refreshed = True
    internet_error_notify_msg_sent = False
    notify_Device       = None
    log_level_save      = Gb.log_level
    start_ic3.set_log_level('rawdata')

    status_check_interval_secs = 5
    status_check_secs       = 20
    status_check_interval = dt.timedelta(seconds=status_check_interval_secs)
    cancel_status_check_timer_fct = None

#----------------------------------------------------------------------------
    def start_internet_error_handler(self):
        '''
        Setup the internet connection error monitor.
        '''
        if Gb.internet_error is False:
            return

        self.apple_acct_restart_needed = False
        self.internet_error_secs = time_now_secs()
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

        self.cancel_status_check_timer_fct = async_track_time_interval(Gb.hass,
                                    self.check_internet_connection,
                                    self.status_check_interval,
                                    cancel_on_shutdown=True)

#----------------------------------------------------------------------------
    async def check_internet_connection(self, check_time=None):
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
            await self.is_internet_available()

        self.status_check_secs -= 5
        self.update_internet_connection_status_msg()

        if self.status_check_secs > 0:
            return

        self.status_check_cnt += 1
        self.status_check_secs = 20
        self.internet_is_available = await self.is_internet_available()

        if self.internet_is_available:
            self.all_apple_accts_refreshed = \
                    await Gb.hass.async_add_executor_job(self.refresh_all_apple_accts)

            if self.all_apple_accts_refreshed:
                self.internet_connection_is_available_again()
                return

            elif self.icloud_check_cnt == 2:
                post_event( f"{EVLOG_ALERT}Internet Connection available > "
                            f"Checking Apple Connection")

        if self.internet_error_test_ended():
    # def self.internet_error_test_ended(self):
    #     if (self.internet_error_test_mode
    #             and self.status_check_cnt > self.internet_error_test_counter
    #             and self.icloud_check_cnt > self.internet_error_test_counter):
            self.reset_internet_error_test_fields()

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
    def refresh_all_apple_accts(self):
        '''
        Cycle through each apple account and see if a refresh_client yields in a 200 response code.
        If all account have a 200, then their icloud.com endpoint is back on line and connection error
        processing will end.

        If there is not a 200, the apple_acct_restart_needed is set to True and the account with the error will
        be restarted. This should handle ConnectionReset type of errors where just resuming tracking will
        not work because the apple acct is not reachable.

        return:
        - True: All Apple accounts were refreshed
        - False: An Apple account failed to refresh
        '''
        self.icloud_check_cnt += 1

        # if (self.internet_error_test_mode
        #         and self.icloud_check_cnt < self.internet_error_test_counter):
        if self.internet_error_test_ended() is False:
            return False

        if is_empty(Gb.PyiCloud_by_username):
            return True

        self.reset_internet_error_test_fields()

        for username, PyiCloud in Gb.PyiCloud_by_username.items():
            if (PyiCloud is None
                    or PyiCloud.is_AADevices_setup_complete is False):
                self.apple_acct_restart_needed = True
                return False

            try:
                if PyiCloud.refresh_icloud_data() is False:
                    self.apple_acct_restart_needed = True
                    return False
            except Exception as err:
                log_exception(err)

        return True

#----------------------------------------------------------------------------
    def internet_connection_is_available_again(self):
        '''
        Internet is back up, reset the connection error variables and post the necessary events
        '''

        last_internet_error_secs = self.internet_error_secs
        self.reset_internet_error_fields()


        # if (self.internet_error_test_mode
        #         and self.status_check_cnt > self.internet_error_test_counter
        #         and self.icloud_check_cnt > self.internet_error_test_counter):
        # if self.internet_error_test_ended():
        self.reset_internet_error_test_fields()

        data_source_not_set_Devices = [Device
                                    for Device in Gb.Devices
                                    if (Device.dev_data_source == NOT_SET)]

        # If internet is available on the first ping, then it probably means icloud.com is down,
        # the session is now invalid or the connection has been
        # If no connection during startup, restart. Otherwise, resume all tracking
        if (isnot_empty(data_source_not_set_Devices)
                or Gb.initial_icloud3_loading_flag
                or self.apple_acct_restart_needed):
            event_msg =(f"Internet Connection restored at {secs_to_time(time_now_secs())}, "
                        f"Down for-{format_age(last_internet_error_secs, xago=False)}, "
                        f"Restarting")

            Gb.restart_icloud3_request_flag = True
            Gb.PyiCloud_by_username = {}
            Gb.PyiCloudSession_by_username = {}
            Gb.username_valid_by_username = {}

        else:
            event_msg =(f"Internet Connection restored at {secs_to_time(time_now_secs())}, "
                        f"Down for-{format_age(last_internet_error_secs, xago=False)}")

            for Device in Gb.Devices:
                Device.resume_tracking()

        if mins_since(last_internet_error_secs) <= 1:
            event_msg =(f"Internet Connection issue at "
                        f"{secs_to_time(last_internet_error_secs)} "
                        f"for less than 1-min")

        post_event(f"{EVLOG_BROWN_BAR}{event_msg}")
        log_error_msg(f"iCloud3 Alert > {event_msg}")

        update_alert_sensor(ALERT_CRITICAL, f"Internet Connection restored at "
                                            f"{secs_to_time(time_now_secs())}")
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
            mode_msg = 'Internet Check'
        else:
            mode_msg = 'icloud.com Chk'

        post_evlog_greenbar_msg(
                f"Internet Error detected at "
                f"{format_time_age(self.internet_error_secs, xago=True)}, Tracking Paused"
                f"{CRLF}{mode_msg}, {self.status_check_secs:0>2} secs "
                f"(#{self.status_check_cnt+1}){NBSP2}"
                f"{self.status_msg_bar}")

#----------------------------------------------------------------------------
    async def is_internet_available(self):
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

        _hdr = ( f"HTTPX-REQUEST, VALIDATE www.icloud.com VIA HTTPX ▲")
        _data = {'url': url[8:]}
        log_data_unfiltered(_hdr, _data)


        data = await file_io.async_httpx_request_url_data(url)


        _hdr = ( f"HTTPX-RESPONSE, VALIDATE www.icloud.com VIA HTTPX ▼")
        _data = {'data': data}
        log_data_unfiltered(_hdr, _data)

        Gb.internet_error = data['error'].startswith('InternetError')
        self.internet_error_code = data['status_code']

        # if self.internet_error_test_mode:
        #     if self.status_check_cnt < self.internet_error_test_counter:
        if self.internet_error_test_ended() is False:
            Gb.internet_error = True
            return self.internet_error_test_ended(inet_chk=True)

        return not Gb.internet_error

#----------------------------------------------------------------------------
    def internet_error_test_ended(self, inet_chk=None, icloud_chk=None):
        if self.internet_error_test_mode is False:
            return None

        if inet_chk is True and self.status_check_cnt >= self.internet_error_test_counter:
            return True

        if icloud_chk is True and self.icloud_check_cnt >= self.internet_error_test_counter:
            return True

        return (self.status_check_cnt >= self.internet_error_test_counter
                and self.icloud_check_cnt >= self.internet_error_test_counter)


#----------------------------------------------------------------------------
    def reset_internet_error_fields(self):
        if self.cancel_status_check_timer_fct:
            self.cancel_status_check_timer_fct()

        if self.internet_error_secs > 0:
            self.reset_internet_error_test_fields()

        post_evlog_greenbar_msg('')

        self.internet_error_code = 0
        self.internet_error_msg  = ''
        self.internet_error_notify_msg_sent = False

        self.internet_error_secs = 0
        self.status_check_cnt    = 0
        self.status_check_secs   = 0
        start_ic3.set_log_level(self.log_level_save)

        Gb.last_PyiCloud_request_secs = 0
        Gb.internet_error = False

#----------------------------------------------------------------------------
    def reset_internet_error_test_fields(self):
        self.internet_error_test               = False
        self.internet_error_test_mode          = False
        self.internet_error_test_after_startup = False
        self.internet_error_test_timeout       = False
        self.internet_error_test_counter       = 4

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
        interfaces = Gb.hass.data['hassio_network_info']['interfaces']
        for interface in interfaces:
            if interface['ipv6']['method'] != 'disabled':
                return [interface['interface'], interface['ipv6']['method']]

        return None

#----------------------------------------------------------------------------
    def display_internet_error_msg(self):
        post_event( f"{EVLOG_BROWN_BAR}Internet Error detected at "
                    f"{secs_to_time(self.internet_error_secs)}, "
                    f"Tracking Paused, "
                    f"{self.internet_error_msg}, "
                    f"Error-{self.internet_error_code}")
        post_event( f"{EVLOG_ALERT}Internet Error detected > "
                    f"Checking status every 20-secs, Tracking Paused, "
                    f"{self.internet_error_msg}, "
                    f"Error Code-{self.internet_error_code}, Possible causes:"
                    f"{CRLF_DOT}An Internet Connection Error (Internet, WiFi, Router is down)"
                    f"{CRLF_DOT}Apple is not available (`www.icloud.com` is down)"
                    f"{CRLF}")

        if Gb.last_PyiCloud_request_secs > 0:
            ipv6_info = self.ha_system_network_ipv6_info()
            if ipv6_info:
                post_event(
                        f"{EVLOG_ALERT}{RED_ALERT}IPv6 DETECTED > Apple location server does not respond to "
                        f"IPv6 requests. HA Network setting for IPv6 `{ipv6_info[0]}` is `{ipv6_info[1]}`."
                        f"{CRLF}1. Go to HA Devices & settings > System > Network"
                        f"{CRLF}2. Change to `disabled`. Then Restart HA")
