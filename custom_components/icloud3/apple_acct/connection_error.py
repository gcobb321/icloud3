
from ..global_variables import GlobalVariables as Gb
from ..const            import (CRLF, CRLF_DOT, EVLOG_ALERT, NOT_SET,
                                CONF_EXTERNAL_IP_ADDRESS, INTERNET_STATUS_PING_IPS,
                                )

from ..utils.utils      import (instr, is_empty, isnot_empty, list_add, list_del,)
from ..utils.time_util  import (time_now, time_now_secs, secs_to_time, format_time_age, )
from ..utils.file_io    import (httpx_request_url_data)
from ..utils.messaging  import (_evlog, _log, more_info, add_log_file_filter,
                                post_event, post_evlog_greenbar_msg,
                                log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                log_rawdata, log_exception, log_rawdata_unfiltered, filter_data_dict, )

from ..startup          import config_file
from ..startup          import start_ic3

#----------------------------------------------------------------------------
import asyncio

from homeassistant.components.ping.helpers import PingDataSubProcess

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   INTERNET PING FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def scan_for_pingable_ip():
    '''
    Scan the Ping_IP_addresses table and the external IP address of the users network provider
    and find a pingable IP. This IP address will be used when an internet connection error
    is being retested,
    '''

    scan_ip_addresses = {}
    if Gb.external_ip_address:
        scan_ip_addresses[Gb.external_ip_name] = Gb.external_ip_address
    scan_ip_addresses.update(INTERNET_STATUS_PING_IPS)

    _log(f"Check Pingable IP Address > {scan_ip_addresses=})")
    for ip_name, ip_address in scan_ip_addresses.items():
        if ip_address is None:
            continue
        _log(f"Check Pingable IP Address > {ip_address} ({ip_name})")

        try:
            is_pingable = await async_is_ip_address_pingable(ip_address, ip_name)

        except Exception as err:
            log_exception(err)

        if is_pingable:
            _log(f"Pingable IP Address > {Gb.pingable_ip_address} ({Gb.pingable_ip_name})")
            return

#----------------------------------------------------------------------------
def is_ip_address_pingable(ip_address=None, ip_name=None):
    return asyncio.run_coroutine_threadsafe(
                async_is_ip_address_pingable(ip_address, ip_name), Gb.hass.loop
            ).result()

#----------------------------------------------------------------------------
async def async_is_ip_address_pingable(ip_address=None, ip_name=None):
    '''
    Determine if an ip_address is pingable and set the Gb.external_ip_xxx if it is pingable

    -   Use ip_address if specified
    -   Use Gb.external_ip_address if not specified
    '''

    Ping = None
    results = {}
    if ip_address is not None:
        Ping = PingDataSubProcess(Gb.hass, host=ip_address, count=3, privileged=False)
    else:
        if Gb.pingable_ip_Ping is not None:
            Ping       = Gb.pingable_ip_Ping
            ip_address = Gb.pingable_ip_address
            ip_name    = Gb.pingable_ip_name
        else:
            return False

    if Ping is not None:
        results = await Ping.async_ping()

    is_pingable = isnot_empty(results)
    if is_pingable:
        Gb.pingable_ip_Ping    = Ping
        Gb.pingable_ip_address = ip_address
        Gb.pingable_ip_name    = ip_name

    # _log(f"{ip_address=} {ip_name=} {is_pingable=}")
    return is_pingable


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   IDENTIFY AND PREPARE USERS ISP EXTERNAL IP ADDRESS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def get_external_ip_address():
    '''
    Get the HA Server External IP. This IP is Pinged when a connection error was encountered to determine
    when the internet is back online.
    '''
    if Gb.external_ip_address:
        return

    await request_external_ip_address('ipify.org', 'https://api.ipify.org/?format=json')
    if Gb.external_ip_address:
        return

    await request_external_ip_address('ipinfo.io', 'https://ipinfo.io/json')


#----------------------------------------------------------------------------
async def request_external_ip_address(ip_name, ip_url):
    '''
    Get the external ip address from the ip_url service and update the Gb.external_ip_address/name
    if successful

    Two sources are used:
        - https://api.ipify.org/?format=json > URL in the example of setting up a Rest Sensor in the HA documentation
            Resopnse = {'ip': '73.1.225.32'}

        - https://api.ipify.org/?format=json > A URL that provides external IP and host information
            Response = {'ip': '73.1.225.32', 'hostname': 'c-73-1-225-32.hsd1.fl.comcast.net',
                        'city': 'Lake Worth Beach', 'region': 'Florida', 'country': 'US',
                        'loc': '26.6171,-80.0723', 'org': 'AS7922 Comcast Cable Communications, LLC',
                        'postal': '33466', 'timezone': 'America/New_York',
                        'readme': 'https://ipinfo.io/missingauth'}
    '''
    data = await httpx_request_url_data(ip_url)
    log_debug_msg(f"Get External IP Address, {data}")

    ip_address  = data.get('ip', None)
    if ip_address:
        Gb.external_ip_name    = ip_name
        Gb.external_ip_address = ip_address
        # _log(f"External IP Address > {Gb.external_ip_address} ({Gb.external_ip_name})")

        # Update the configuration file if the current ip name/address has changed
        ip_name_address = f"{Gb.external_ip_name},{ip_address}"
        if Gb.conf_profile[CONF_EXTERNAL_IP_ADDRESS] != ip_name_address:
            Gb.conf_profile[CONF_EXTERNAL_IP_ADDRESS] = ip_name_address
            config_file.write_icloud3_configuration_file()

    return ip_address


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   CONNECTION ERROR HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def handle_internet_connection_error(self):
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
        internet_connection_status_msg()

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

    internet_connection_status_msg()

    if Gb.internet_connection_error is False:
        self.reset_internet_connection_error()
        return

    if Gb.internet_connection_status_request_cnt == 0:
        pass
    elif Gb.this_update_time[-2:] not in ['00' ,'15', '30', '45']:
        return

    # See if internet is back up


    is_pingable = is_ip_address_pingable()
    if is_pingable:
        self.reset_internet_connection_error()

    # is_internet_available = Gb.PyiCloudValidateAppleAcct.is_internet_available()
    # if is_internet_available:
    #     self.reset_internet_connection_error()

#...............................................................................
def reset_internet_connection_error():
    '''
    Internet is back up, reset the connection error variables and post the necessary events
    '''
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
def internet_connection_status_msg():
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
