

from ..global_variables import GlobalVariables as Gb
from ..const            import (DOMAIN, DEVICE_TRACKER,
                                CRLF_DOT, EVLOG_NOTICE, EVLOG_ERROR, EVLOG_ALERT,
                                ICLOUD, CONF_DATA_SOURCE,
                                CONF_APPLE_ACCOUNT, CONF_USERNAME, CONF_PASSWORD, CONF_LOCATE_ALL,
                                CONF_SERVER_LOCATION,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_DEVICE_TYPE,
                                CONF_APPLE_ACCOUNT, CONF_AADEV_NAME, CONF_AADEV_DEVICE_ID,
                                CONF_RAW_MODEL, CONF_MODEL, CONF_MODEL_DISPLAY_NAME,
                                CONF_TRACKING_MODE, CONF_MOBILE_APP_DEVICE,
                                CONF_PICTURE, CONF_ICON,
                                IPHONE_DN, WATCH_DN, IPAD_DN, MAC_DN, DEVICE_TYPES, DEVICE_TYPE_TRACKING_MODE,
                                DEVICE_TYPE_PICTURE_FILENAMES, DEVICE_TYPE_ICONS,
                                TRACK, MONITOR, INACTIVE, TRACKING_MODES,
                                )

from ..utils.utils      import (instr, isnot_empty,
                                list_add, list_del, dict_del, dict_sort,
                                encode_password, decode_password, username_id,
                                is_running_in_event_loop, )
from ..utils.messaging  import (post_event, post_alert, post_monitor_msg, post_error_msg,
                                update_alert_sensor,
                                _log, log_exception, log_debug_msg, log_info_msg,
                                add_log_file_filter, )
from ..utils.time_util  import (time_now_secs, secs_to_hhmm, )


from ..apple_acct.apple_acct import (AppleAcctManager, AppleAcctFailedLoginException, HTTP_RESPONSE_CODES)
from .device_name_parser     import make_ic3_fname_from_aadevice_dname
from ..startup          import start_ic3
from ..utils            import file_io
from ..utils            import entity_io

#--------------------------------------------------------------------
from homeassistant.util import slugify
from re                 import match
from os                 import path

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#          APPLE ACCOUNT ICLOUD SUPPORT ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_log_into_apple_account(self, user_input):
    '''
    Log into the icloud account and check to see if a Authentication code is needed.
    If so, the calling step displays the Authentication form and gets the code from the user.

    Input:
        user_input  = A dictionary with the username and password, or
                        {username: icloudAccountUsername, password: icloudAccountPassword}
                    = {} to use the username/password in the tracking configuration parameters

    Exception:
        The self.AppleAcct.requres_2fa must be checked after a login to see if the account
        access needs to be verified. If so, the Authentication code entry form must be displayed.

    Returns:
        self.Pyicloud object
        self.iCloud_AppleAcctDevices object
        self.AppleAcct_FindMyFriends object
        self.opt_icloud_dname_list & self.device_form_icloud_famf_list =
                A dictionary with the devicename and identifiers
                used in the tracking configuration devices icloud_device parameter
    '''
    try:
        self.errors = {}
        self.login_successful     = False
        self.login_successful_srp = None
        self.auth_failed_503      = False

        # The username may be changed to assign a new account, if so, log into the new one
        if CONF_USERNAME not in user_input or CONF_PASSWORD not in user_input:
            return False

        username = user_input[CONF_USERNAME].lower()
        password = user_input[CONF_PASSWORD]

        add_log_file_filter(username, f"**{self.aa_idx}**")
        add_log_file_filter(username.upper(), f"**{self.aa_idx}**")
        add_log_file_filter(password)

        apple_server_location = user_input.get(CONF_SERVER_LOCATION,'usa')

        log_info_msg(   f"Apple Acct > {username}, Logging in, "
                        f"UserInput-{user_input}, Errors-{self.errors}, "
                        f"Step-{self.step_id}")

        # Already logged in and no changes
        AppleAcct = Gb.AppleAcct_by_username.get(username)
        if (AppleAcct
                and password == AppleAcct.password
                and AppleAcct.login_successful
                and AppleAcct.login_successful_srp != False
                and AppleAcct.auth_failed_503 is False
                and apple_server_location == AppleAcct.apple_server_location
                and AppleAcct.login_successful):
            self.AppleAcct = AppleAcct
            self.username = username
            self.password = password
            # self.header_msg = 'apple_acct_logged_into'

            log_info_msg(f"Apple Acct > {username}, Already Logged in, {self.AppleAcct}")
            # return True

            # Validate the account before actually logging in
            valid_upw = await Gb.ValidateAppleAcctUPW.async_validate_username_password(username, password)
            if valid_upw is False:
                if username in Gb.valid_upw_by_username:
                    del Gb.valid_upw_by_username[username]
                self.errors[CONF_USERNAME] = 'apple_acct_invalid_upw'
                log_info_msg(f"Apple Acct > {username}, Invalid Username/password")
                return False


        event_msg =(f"{EVLOG_NOTICE}Configure Settings > Logging into Apple Account {username}")
        if apple_server_location != 'usa':
            event_msg += f", iCloud.com ServerSuffix-{apple_server_location}"
        log_info_msg(event_msg)

    except Exception as err:
        log_exception(err)

    try:
        await file_io.async_make_directory(Gb.icloud_cookies_directory)

        AppleAcct = None
        AppleAcct = await Gb.hass.async_add_executor_job(
                                    create_AppleAcctManager_config_flow,
                                    username,
                                    password,
                                    apple_server_location)

        # TEST CODE -Test Internet error and AppleAcct login failure
        # _log("TEST CODE ENABLED")
        # AppleAcct = None
        # Gb.internet_error = True

        if AppleAcct is None:
            self.AppleAcct = None
            log_info_msg(f"Apple Acct > {username}, Login Failed")
            return False

        # Successful login, set AppleAcct fields
        self.AppleAcct = AppleAcct
        self.username = username
        self.password = password
        self.apple_server_location = apple_server_location
        Gb.valid_upw_by_username[username] = True
        log_info_msg(f"Apple Acct > {username}, Login successful, {self.AppleAcct}")

        start_ic3.dump_startup_lists_to_log()

        if AppleAcct.is_reauth_needed:
            log_info_msg(f"Apple Acct > {username}, 2fa Authentication Needed, {self.AppleAcct}")
            alert_msg = f"Apple Authentication needed ({secs_to_hhmm(AppleAcct.is_reauth_needed_secs)})"
            update_alert_sensor(AppleAcct.username_id, alert_msg)

            # Display the orange 'Reconfigure' button on the HA Settings screen as
            # soon as the login reports that an Auth Code is needed. Waiting until
            # the code is actually requested (step_reauth) leaves HA showing no
            # indication that the account is not usable yet.
            #
            # Do not do this while the iCloud3 Configure (OptionsFlow) dialog is open.
            # `async_start_reauth` does not just light up the orange button, it starts a
            # real HA reauth ConfigFlow, which immediately runs the ConfigFlow's
            # async_step_reauth and displays a 2nd reauth screen on top of the OptionsFlow
            # reauth screen that step_apple_acct is about to display. The orange button is
            # set by start_ic3_control when iCloud3 restarts as the Configure dialog is
            # exited if the acct still needs to be authenticated.
            if Gb.config_entry and Gb.is_config_flow_open is False:
                Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)

            return True

        self.header_msg = 'apple_acct_logged_into'

        return True

    # Login Failed, display error messages
    except (AppleAcctFailedLoginException) as err:
        err = str(err)
        Gb.HALogger.error(f"Error logging into Apple Acct: {err}")

        response_code = Gb.AppleAcctLoggingInto.response_code
        if Gb.AppleAcctLoggingInto.response_code_pw == 503:
            Gb.AppleAcctLoggingInto.setup_error(503)

        elif response_code == 302:
            Gb.AppleAcctLoggingInto.setup_error(302, 'Server Location')
            apple_server_location = Gb.AppleAcctLoggingInto.apple_server_location
            if (apple_server_location == 'usa'):
                Gb.AppleAcctLoggingInto.setup_error(302, 'Server Loc-cn')
                self.errors[CONF_SERVER_LOCATION] = 'apple_acct_login_error_302_cn'
            elif (apple_server_location == '.cn'):
                Gb.AppleAcctLoggingInto.setup_error(302, 'Server Loc-usa')
                self.errors[CONF_SERVER_LOCATION] = 'apple_acct_login_error_302_usa'
            else:
                Gb.AppleAcctLoggingInto.setup_error(302, 'Server Loc-??')
                self.errors[CONF_SERVER_LOCATION] = 'apple_acct_login_error_302'

        elif response_code == 400:
            self.errors['base'] = 'apple_acct_invalid_upw'
        elif response_code == 401 and instr(err, 'Python SRP'):
            Gb.AppleAcctLoggingInto.setup_error(401)
            self.errors['base'] = 'apple_acct_login_error_srp_401'
        elif response_code == 401:
            Gb.AppleAcctLoggingInto.setup_error(401)
            self.errors[CONF_USERNAME] = 'apple_acct_invalid_upw'
        elif response_code == 403:
            Gb.AppleAcctLoggingInto.setup_error(403)
            self.errors[CONF_USERNAME] = 'apple_acct_locked'
        else:
            Gb.AppleAcctLoggingInto.setup_error(response_code)
            self.errors['base'] = 'apple_acct_login_error_other'
        error_msg = HTTP_RESPONSE_CODES.get(response_code, 'Other Error')

        post_error_msg( f"Apple Acct > {username}, Login Failed, "
                        f"Error-{err}/{error_msg}, Code-{response_code}")

    except Exception as err:
        log_exception(err)
        Gb.HALogger.error(f"Error logging into Apple Account: {err}")
        self.errors['base'] = 'apple_acct_login_error_other'

    start_ic3.dump_startup_lists_to_log()
    return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            CREATE APPLE ACCOUNT SERVICE OBJECTS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_AppleAcctManager_config_flow(username, password, apple_server_location):
    '''
    Create the AppleAcctManager object without going through the error checking and
    authentication test routines. This is used by config_flow to open a second
    AppleAcct session
    '''
    try:
        AppleAcct = None
        AppleAcct = AppleAcctManager( username,
                                    password,
                                    apple_server_location=apple_server_location,
                                    cookie_directory=Gb.icloud_cookies_directory,
                                    session_directory=Gb.icloud_session_directory,
                                    config_flow_login=True)

    except Exception as err:
        AppleAcct = None
        pass

    # TEST CODE -Test Internet error and AppleAcct login failure
    # _log("TEST CODE ENABLED")
    # AppleAcct = None
    # Gb.internet_error = True

    if AppleAcct and AppleAcct.login_successful:
        log_debug_msg(  f"Apple Acct > {AppleAcct.account_owner}, Login Successful, "
                        f"Error-{AppleAcct.response_code_desc}, "
                        f"Update Connfiguration")
    else:
        # raise AppleAcctFailedLoginException
        return None

    # start_ic3.dump_startup_lists_to_log()
    return AppleAcct

#--------------------------------------------------------------------
@staticmethod
def create_AADevices_config_flow(AppleAcct):

    _AADevices = AppleAcct.create_AADevices_object(config_flow_login=True)

    start_ic3.dump_startup_lists_to_log()
    return _AADevices


#..............................................................................................
def clear_AppleAcct_auth_alerts():
    for username, AppleAcct in Gb.AppleAcct_by_username.items():
        if AppleAcct.is_reauth_needed:
            AppleAcct.was_ha_auth_code_alert_sent = False

#--------------------------------------------------------------------
async def async_finish_authentication_and_data_refresh(caller_self):
    '''
    Refresh the device list if the apple acct is being setup for the first time
    If AppleAcct.device_id_by_aadev_dname is empty, a Authentication code was needed
    when first logged in and the apple acct data was not authenticated and it's
    device data was never loaded/initialized by refreshed_icloud_data. This
    prevents the device's list tables to never be initialized and location data
    is not available. Do this now.
    '''
    AppleAcct = caller_self.AppleAcct
    AppleAcct.login_successful = \
        await Gb.hass.async_add_executor_job(AppleAcct.authenticate)

    if AppleAcct.login_successful is False:
        err_msg = ( f"Apple Acct > {AppleAcct.username_base}, Authentication Failed, "
                    f"Error-{AppleAcct.response_code_desc}, "
                    f"AppleServerLocation-`{AppleAcct.apple_server_location}`, "
                    "Location Data not Refreshed")
        post_error_msg(err_msg)
        return

    locate_all_devices = True

    # refresh_icloud_data is treated as a startup refresh so all of the devices are
    # initialized, not just the tracked ones. Save and restore the flag instead of
    # clearing it - iCloud3 may really be starting up, and a failure in the executor job
    # would leave the flag set and stop the 5-sec polling loop.
    was_startup_inprocess = Gb.is_icloud3_startup_inprocess
    Gb.is_icloud3_startup_inprocess = True

    try:
        await Gb.hass.async_add_executor_job(
                                AppleAcct.refresh_icloud_data,
                                locate_all_devices)

        if AppleAcct.is_authenticated:
            AppleAcct.terms_of_use_update_needed = False
            post_event( f"{AppleAcct.username_base} > "
                        f"Apple Acct > Terms of Service agreement approved")
            update_alert_sensor(AppleAcct.username_id, '')

    finally:
        Gb.is_icloud3_startup_inprocess = was_startup_inprocess

#--------------------------------------------------------------------
def any_conf_devices_for_apple_acct(ui_username):
    existing_devices = [conf_device[CONF_IC3_DEVICENAME]
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_APPLE_ACCOUNT] == ui_username]

    return isnot_empty(existing_devices)

#--------------------------------------------------------------------
def any_apple_accts_not_used():
    aa_list = list(Gb.AppleAcct_by_username.keys())
    aa_used = [conf_device[CONF_APPLE_ACCOUNT]
                            for conf_device in Gb.conf_devices]
    aa_unused = [username   for username in aa_list
                            if username not in aa_used]

    return isnot_empty(aa_unused)

#--------------------------------------------------------------------
# def delete_AppleAcct_trust_cookie(AppleAcct):
#     AppleAcct.iCloudSession.cookies.delete('X-APPLE-WEBAUTH-HSA-TRUST')
#     AppleAcct.iCloudSession.cookies.save()

#--------------------------------------------------------------------
async def async_delete_icloud_session_file(AppleAcct, username):
    '''
    Delete the cookies and session files as part of the reset_session
    and request_auth_code. This is called from config_flow/step_reauth
    and pyicloud_reset_session
    '''
    if AppleAcct:
        cookies_filename = AppleAcct.cookies_filename
        session_filename = AppleAcct.session_filename
        AppleAcct.delete_cookie_and_session_files()

        username_msg = AppleAcct.account_owner

    elif AppleAcct is None:
        cookies_base = "".join([c for c in username if match(r"\w", c)])
        cookies_filename = path.join(Gb.icloud_cookies_directory, f"{cookies_base}.cookies")
        session_filename = path.join(Gb.icloud_cookies_directory, f"{cookies_base}.session")
        await file_io.async_delete_file(cookies_filename)
        await file_io.async_delete_file(session_filename)

        username_msg = username_id(username)

    elif AppleAcct not in Gb.AppleAcct_by_username:
        return

    post_event( f"{EVLOG_NOTICE}Apple Acct > {username_msg}, "
                f"Resetting iCloud Session Files")
    log_info_msg(   f"Apple Acct > {username_msg}, "
                    f"Deleting Session Files ({Gb.icloud_cookies_directory})"
                    f"{CRLF_DOT}Cookies ({cookies_filename})"
                    f"{CRLF_DOT}Session ({session_filename})")

#--------------------------------------------------------------------
def is_asp_password(ui_password):
    '''
    True if the password is App Specific Password (ASP) format: uqvf-gguc-tzpd-knor
    '''

    return (len(ui_password) == 19
                and ui_password[4:5] == '-'
                and ui_password[9:10] == '-'
                and ui_password[14:15] == '-')

#--------------------------------------------------------------------
def login_err_msg(AppleAcct, username):
    ipv6_info = Gb.InternetError.ha_system_network_ipv6_info()
    if ipv6_info:
        err_msg = 'apple_acct_login_error_ipv6'
    elif Gb.internet_error:
        err_msg = 'internet_error'
    elif AppleAcct and AppleAcct.response_code_pw == 503:
        err_msg = 'apple_acct_login_error_503'
    elif Gb.valid_upw_by_username.get(username, None) is False:
        err_msg = 'apple_acct_invalid_upw'
    else:
        err_msg = 'apple_acct_login_error_other'

    return err_msg

#--------------------------------------------------------------------
async def async_delete_icloud_session_requests_file(username=None):
    '''
    Delete the cookies and session files as part of the reset_session and request_Authentication_code
    This is called from config_flow/setp_reauth and pyicloud_reset_session
    '''

    if username is None:
        return

    post_event(f"{EVLOG_NOTICE}Configure Apple Acct > Resetting Cookie/Session Files")
    cookie_directory  = Gb.icloud_cookies_directory
    cookie_filename   = "".join([c for c in username if match(r"\w", c)])

    delete_msg =  f"Apple Acct > Deleting Session Files > ({cookie_directory})"

    delete_msg += f"{CRLF_DOT}Session ({cookie_filename}.session)"
    await file_io.async_delete_file_with_msg(
                    'Apple Acct Session', cookie_directory, f"{cookie_filename}.session", delete_old_sv_file=True)

    post_monitor_msg(delete_msg)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            HARDWARE KEY AUTHENTICATION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_get_hwkey_names(self, AppleAcct=None):
    '''
    Retrieve HwKey names from Apple and update conf_auth_methods.
    Runs AppleAcct.get_hwkey_names() in executor (not in event loop).
    '''

    _AppleAcct_list = Gb.AppleAcct_by_username.values() if AppleAcct is None else [AppleAcct]
    for _AppleAcct in _AppleAcct_list:
        try:
            await Gb.hass.async_add_executor_job(_AppleAcct.get_hwkey_names)

        except Exception as err:
            log_exception(err)

    return


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISCOVER APPLE ACCT DEVICES-IC3 DEVICES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def build_import_devices_config_from_aadevices(self, AppleAcct):
    '''
    'iPhone de S': 'jso',
    'gary': 'gary', 'Gryphon': 'gryphon',
    iphone_van_bob': Bob,
    Annelinde (iphone_van_linde)
    iPad Air Bob (ipad_air_bob)
    Marco (device_tracker_marcos_iphone_app)
    Doris (device_tracker_doris_iphone_app)
    Marco’s iPhone (Schaeffler) (marcos_iphone_schaeffler)
    Marco's iPad Pro (marcos_ipad_pro_ic3)
    Doris' iPad Air (doris_ipad_air_ic3
    Marcos Watch (iwatch_marco)
    Doris Watch (iwatch_doris)
    'Apple Watch (Marcin)': 'apple_watch_marcin',
    'iPhone (Marcin)': 'iphone_15pro_marcin',
    'AirPods Pro (Marcin)': 'airpods_pro_marcin',
    'mmarczyk-mPK': 'macbook_pro_marcin',
    "Marcin Marczyk's iPad": 'ipad_marcin',
    'Apple Watch (Anna)': 'apple_watch_anna',
    'AirPods Pro (Anna)': 'airpods_pro_anna',
    'iPhone (Anna) (3)': 'iphone_15_anna',
    'MacBook Air': 'macbook_air_anna'}
    iPhone de Jorge E.': 'iphone_oso'}

    '''
    device_id_filter = [conf_device[CONF_AADEV_DEVICE_ID]
                            for conf_device in Gb.conf_devices
                            if conf_device[CONF_APPLE_ACCOUNT] == AppleAcct.username]

    # Build list of existing devicenames and fnames. Then add devicenames and fnames just imported
    dt_devicenames, _    = entity_io.get_entity_registry_data(domain=DEVICE_TRACKER)
    existing_devicenames = [dt_devicename.replace('device_tracker.', '') for dt_devicename in dt_devicenames]
    existing_fnames      = [conf_device[CONF_FNAME] for conf_device in Gb.conf_devices]

    for item_key, ic3_conf_device in self.imported_aa_ic3_conf_devices.items():
        list_add(existing_devicenames, ic3_conf_device[CONF_IC3_DEVICENAME])
        list_add(existing_fnames, ic3_conf_device[CONF_FNAME])

    aa_devices_to_add = {}
    for aadevice_dname, device_id in AppleAcct.device_id_by_aadev_dname.items():
        # Filter devices that already been added to the config file
        if (device_id in device_id_filter):
            continue

        raw_model, model, model_display_name = \
                    AppleAcct.device_model_info_by_aadev_dname[aadevice_dname]

        AADevData  = AppleAcct.AADevData_by_device_id.get(device_id)
        first_name = AADevData.owner_first_name if AADevData else None
        aadev_name = AADevData.name if AADevData else aadevice_dname
        ic3_fname  = make_ic3_fname_from_aadevice_dname(aadev_name, model, first_name)

        ic3_devicename = slugify(ic3_fname)
        ic3_fname      = ic3_fname.replace('-iPhone', '')

        # Check if an iCloud3 device that is inactive, change trk mode instead of add again
        conf_device_idx = Gb.conf_devices_idx_by_devicename.get(ic3_devicename, -1)
        if conf_device_idx == -1:
            pass
        elif Gb.conf_devices[conf_device_idx][CONF_TRACKING_MODE] == INACTIVE:
            pass
        else:
            ic3_devicename = _make_unique_ic3_devicename(existing_devicenames, ic3_devicename)
            ic3_fname      = _make_unique_ic3_fname(existing_fnames, ic3_fname)

        list_add(existing_devicenames, ic3_devicename)
        list_add(existing_fnames, ic3_fname)

        ic3_conf_device = {}
        ic3_conf_device[CONF_IC3_DEVICENAME]     = ic3_devicename
        ic3_conf_device[CONF_FNAME]              = ic3_fname
        ic3_conf_device[CONF_APPLE_ACCOUNT]      = AppleAcct.username
        ic3_conf_device[CONF_AADEV_NAME]  = aadevice_dname
        # ic3_conf_device.update(aadevice_conf( aadevice_dname, device_id,
        #                     model, raw_model, model_display_name))
        ic3_conf_device[CONF_AADEV_DEVICE_ID]   = device_id
        ic3_conf_device[CONF_DEVICE_TYPE]        = model.lower() if model in DEVICE_TYPES else 'iphone'
        ic3_conf_device[CONF_RAW_MODEL]          = raw_model
        ic3_conf_device[CONF_MODEL]              = model
        ic3_conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name
        ic3_conf_device[CONF_MOBILE_APP_DEVICE]  = 'None'
        device_type = model.lower()
        ic3_conf_device[CONF_TRACKING_MODE] = DEVICE_TYPE_TRACKING_MODE(device_type)
        ic3_conf_device[CONF_ICON] = DEVICE_TYPE_ICONS.get(device_type, 'mdi:account')
        if device_type in DEVICE_TYPE_PICTURE_FILENAMES:
            ic3_conf_device[CONF_PICTURE] = f'{Gb.www_evlog_js_directory}/{DEVICE_TYPE_PICTURE_FILENAMES[device_type]}'

        # Gb.device_info_by_mobapp_dname={'lillian_ipad_app': ['Lillian-iPad-app', 'iPad14,3', 'iPad14,3', 'iPadPro4'],
        # 'gary_iphone_app': ['Gary-iPhone-app', 'iPhone17,2', 'iPhone', 'iPhone16ProMax'],
        # 'gary_ipad_app': ['Gary-iPad-app', 'iPad16,3', 'iPad16,3', 'iPadPro']}

        for mobapp_dname, mobapp_info in Gb.device_info_by_mobapp_dname.items():
            mobapp_fname, mobapp_raw_model, mobapp_device_type, mobapp_model_display_name = mobapp_info

            if mobapp_raw_model == raw_model:
                if (instr(mobapp_dname, ic3_devicename)
                        or instr(ic3_devicename, mobapp_dname)
                        or instr(ic3_fname, mobapp_fname)
                        or instr(mobapp_fname, ic3_fname)):
                    ic3_conf_device[CONF_MOBILE_APP_DEVICE] = mobapp_dname
                    break

        # Create a sort_key = Tracking_mode (track/monitor/inactive),device_type,ic3_fname
        sk_tracking_mode = sk_device_type = 99
        if ic3_conf_device[CONF_TRACKING_MODE] in TRACKING_MODES:
            sk_tracking_mode = TRACKING_MODES.index(ic3_conf_device[CONF_TRACKING_MODE])
        if model in DEVICE_TYPES:
            sk_device_type = DEVICE_TYPES.index(model)
        sort_key = f"{sk_tracking_mode},{sk_device_type:02},{ic3_fname}"

        aa_devices_to_add[sort_key] = ic3_conf_device

    sorted_aa_devices_to_add = dict_sort(aa_devices_to_add)

    return sorted_aa_devices_to_add

# ---------------------------------------------------------------------------
def aadevice_conf( aadevice_dname, device_id,
                            model, raw_model, model_display_name):

    aadev_info = {}
    aadev_info[CONF_AADEV_NAME]  = aadevice_dname
    aadev_info[CONF_AADEV_DEVICE_ID]   = device_id
    aadev_info[CONF_DEVICE_TYPE]        = model.lower() if model in DEVICE_TYPES else 'iphone'
    aadev_info[CONF_RAW_MODEL]          = raw_model
    aadev_info[CONF_MODEL]              = model
    aadev_info[CONF_MODEL_DISPLAY_NAME] = model_display_name

    return aadev_info
# ---------------------------------------------------------------------------
def _make_unique_ic3_devicename(existing_devicenames, ic3_devicename):
    '''
    The devicename is built from the Apple Device dname field. Make sure it
    is not used for another HA device. If so, generate a unique name
    '''
    if ic3_devicename not in existing_devicenames:
        return ic3_devicename

    # If ic3_devicename already used, add '_ic3' and then a '_#' suffix
    ic3_devicename += '_ic3'

    cnt = 1
    while ic3_devicename in existing_devicenames:
        cnt += 1
        ic3_devicename = f"{ic3_devicename}_{cnt}"

    return ic3_devicename

# ---------------------------------------------------------------------------
def _make_unique_ic3_fname(existing_fnames, ic3_fname):
    '''
    The fname is built from the Apple Device dname field. Make sure it
    is not used for another iCloud3 device. If so, generate a unique name.
    '''
    if ic3_fname not in existing_fnames:
        return ic3_fname

    # If ic3_fename already used, add '_ic3' and then a '_#' suffix
    ic3_fname += '_ic3'

    cnt = 1
    while ic3_fname in existing_fnames:
        cnt += 1
        ic3_fname = f"{ic3_fname}_{cnt}"

    return ic3_fname
