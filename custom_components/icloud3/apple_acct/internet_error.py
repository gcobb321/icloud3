
from ..global_variables import GlobalVariables as Gb
from ..const            import (CRLF, CRLF_DOT, EVLOG_ALERT, EVLOG_BROWN_BAR, NOT_SET,
                                ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                NOTIFY)

from ..startup          import start_ic3
from ..utils.utils      import (instr, is_empty, isnot_empty, list_add, list_del,)
from ..utils.time_util  import (time_now, time_now_secs, mins_since, format_time_age, secs_to_time, )
from ..utils.messaging  import (_evlog, _log, more_info, add_log_file_filter,
                                post_event, post_evlog_greenbar_msg, post_error_msg, post_alert,
                                log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                log_data, log_exception, log_data_unfiltered, filter_data_dict, )

from ..utils            import file_io

#----------------------------------------------------------------------------
# import asyncio
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
    internet_error_test_counter = 4

    internet_error_msg  = ''  # response msg/status_code (pyicloud_session)
    internet_error_code = ''

    internet_error_secs = 0
    status_msg_dot_cnt  = 0
    status_msg_bar      = ''
    status_check_cnt    = 0
    status_check_secs   = 0
    apple_acct_restart  = False
    is_internet_available = False
    is_apple_available  = True
    internet_error_notify_msg_sent = False
    notify_Device       = None
    log_level_save      = Gb.log_level
    start_ic3.set_log_level('rawdata')

    status_check_interval_secs = 5
    status_check_interval = dt.timedelta(seconds=status_check_interval_secs)
    cancel_status_check_timer_fct = None

#----------------------------------------------------------------------------
    def start_internet_error_handler(self):
        '''
        Setup the internet connection error monitor. This will create a ping to the users ip address
        every 15-secs that will determine when the internet is back up.
        '''
        if Gb.internet_error is False:
            return

        Gb.last_PyiCloud_request_secs = 0

        self.internet_error_secs = time_now_secs()
        self.status_check_secs   = 20
        self.log_level_save = Gb.log_level
        start_ic3.set_log_level('rawdata')

        for Device in Gb.Devices:
            Device.pause_tracking()

        post_event( f"{EVLOG_BROWN_BAR}Internet Connection Error > Tracking Paused, "
                    f"{self.internet_error_msg} "
                    f"Error Code-{self.internet_error_code}")
        log_error_msg( f"{EVLOG_ALERT}Internet Connection Error > Tracking Paused, "
                    f"{self.internet_error_msg} "
                    f"({self.internet_error_code})")

        self.update_internet_connection_status_msg()
        self.schedule_next_status_check()

#----------------------------------------------------------------------------
    def schedule_next_status_check(self):

        self.cancel_status_check_timer_fct = async_track_time_interval(Gb.hass,
                                    self.check_internet_connection,
                                    self.status_check_interval,
                                    cancel_on_shutdown=True)

#----------------------------------------------------------------------------
    async def check_internet_connection(self, check_time=None):

        # Initial internet check before first status msg
        if self.status_check_cnt == 0:
            await self.check_internet_status_httpx_request()

        self.status_check_secs -= 5
        self.update_internet_connection_status_msg()

        if self.status_check_secs > 0:
            return

        self.status_check_cnt += 1
        self.status_check_secs = 20
        self.is_internet_available = await self.check_internet_status_httpx_request()

        if self.is_internet_available:
            self.is_apple_available = \
                    await Gb.hass.async_add_executor_job(self.refresh_apple_account_data)

            if self.is_apple_available:
                self.internet_connection_is_available_again()

        if (self.internet_error_test
                and self.status_check_cnt > self.internet_error_test_counter):
            self.internet_error_test = False

        # Send Internet Down msg after 5-mins
        if (self.is_internet_available is False
                and mins_since(self.internet_error_secs) >= 2
                and self.internet_error_notify_msg_sent is False):
            self.internet_error_notify_msg_sent = True
            post_alert(ALERT_CRITICAL, (
                            "Internet Connection Lost at "
                            f"{secs_to_time(self.internet_error_secs)}"))
            post_event(f"Alert Sensor Updated > Connection Lost at "
                            f"{secs_to_time(self.internet_error_secs)}")


#----------------------------------------------------------------------------
    def refresh_apple_account_data(self):
        '''
        Cycle through each apple account and see if a refresh_client yields in a 200 response code.
        If all account have a 200, then their icloud.com endpoint is back on line and connection error
        processing will end.

        If there is not a 200, the apple_acct_restart is set to True and the account with the error will
        be restarted. This should handle ConnectionReset type of errors where just resuming tracking will
        not work because the apple acct is not reachable.

        return:
        - True: All Apple accounts were refreshed
        - False: An Apple account failed to refresh
        '''
        self.apple_acct_restart = False

        if (self.internet_error_test
                and self.status_check_cnt < self.internet_error_test_counter):
            return False

        if is_empty(Gb.PyiCloud_by_username):
            return True

        try:
            self.internet_error_test = False
            for username, PyiCloud in Gb.PyiCloud_by_username.items():
                if (PyiCloud is None
                        or PyiCloud.is_AADevices_setup_complete is False):
                    self.apple_acct_restart = True
                    continue

                if PyiCloud.refresh_icloud_data():
                    continue

                # icloud.com not available for this apple_acct, will force iCloud3 restart
                self.apple_acct_restart = True
                Gb.PyiCloud_by_username.pop(username, None)
                Gb.PyiCloudSession_by_username.pop(username, None)
                Gb.username_valid_by_username.pop(username, None)
                return False

        except Exception as err:
            log_exception(err)

        return True

#----------------------------------------------------------------------------
    def internet_connection_is_available_again(self):
        '''
        Internet is back up, reset the connection error variables and post the necessary events
        '''
        self.reset_internet_error_fields()
        Gb.internet_error = False
        self.internet_error_test = False

        data_source_not_set_Devices = [Device
                                    for Device in Gb.Devices
                                    if (Device.dev_data_source == NOT_SET)]

        # If internet is available on the first ping, then it probably means icloud.com is down,
        # the session is now invalid or the connection has been reset
        if self.status_check_cnt == 1:
            event_msg = "Internet Connection Restored > Apple may be down"

        # If no connection during startup, restart. Otherwise, resume all tracking
        elif (isnot_empty(data_source_not_set_Devices)
                or Gb.initial_icloud3_loading_flag
                or self.apple_acct_restart):
            event_msg = "Internet Connection Restored > iCloud3 Restarting"

            Gb.restart_icloud3_request_flag = True

        else:
            event_msg = "Internet Connection Restored > Tracking Resumed"

            for Device in Gb.Devices:
                Device.resume_tracking()

        post_event(f"{EVLOG_BROWN_BAR}{event_msg}")
        log_error_msg(f"{EVLOG_ALERT}{event_msg}")

        post_alert(ALERT_CRITICAL, f"Internet Connection Restored at {time_now()}")
        post_alert(ALERT_CRITICAL, "")

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

        if self.is_apple_available:
            evlog_msg = 'Internet Connection Error > '
        else:
            evlog_msg = 'Verifying `icloud.com` URL > '

        # evlog_msg+=(f"Started {format_time_age(self.internet_error_secs, xago=True)}"
        evlog_msg+=(f"Since {format_time_age(self.internet_error_secs)}"
                    f"{CRLF}Status Check in {self.status_check_secs:0>2} secs "
                    f"(#{self.status_check_cnt+1}) > "
                    f"{self.status_msg_bar}")
        post_evlog_greenbar_msg(evlog_msg)

#----------------------------------------------------------------------------
    async def check_internet_status_httpx_request(self):
        '''
        See if the internet is available by sending a data request to the Apple url used to
        validate username/passwords via the https requests handler.

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


        _hdr = ( f"HTTPX-RESPONSE, VALIDATE www.icloud.co VIA HTTPX ▼")
        _data = {'data': data}
        log_data_unfiltered(_hdr, _data)

        Gb.internet_error = data.get('error', '').startswith('InternetError')

        # internet_error test processing
        if (self.internet_error_test
                and self.status_check_cnt < self.internet_error_test_counter):
            Gb.internet_error = True

        return not Gb.internet_error

#----------------------------------------------------------------------------
    def reset_internet_error_fields(self):
        if self.cancel_status_check_timer_fct:
            self.cancel_status_check_timer_fct()

        if self.internet_error_secs > 0:
            self.internet_error_test = False
            # self.internet_error_test_after_startup = False

        self.internet_error_code = 0
        self.internet_error_msg  = ''
        self.internet_error_notify_msg_sent = False

        self.internet_error_secs = 0
        self.status_check_cnt    = 0
        self.status_check_secs   = 0
        start_ic3.set_log_level(self.log_level_save)


        Gb.last_PyiCloud_request_secs = 0
