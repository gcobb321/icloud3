
from ..global_variables     import GlobalVariables as Gb
from ..const                import (
                                    ICLOUD3, APPLE_SPECIAL_ICLOUD_SERVER_COUNTRY_CODE,
                                    RARROW, RARROW2, HHMMSS_ZERO, DATETIME_ZERO, NONE_FNAME, INACTIVE_DEVICE,
                                    ICLOUD, MOBAPP, NO_MOBAPP, NO_IOSAPP, HOME,
                                    CONF_PARAMETER_TIME_STR,
                                    CONF_INZONE_INTERVALS,
                                    CONF_FIXED_INTERVAL, CONF_EXIT_ZONE_INTERVAL,
                                    CONF_MOBAPP_ALIVE_INTERVAL, CONF_IOSAPP_ALIVE_INTERVAL,
                                    CONF_IC3_VERSION, VERSION, VERSION_BETA,
                                    CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_CARD_PROGRAM, CONF_TRAVEL_TIME_FACTOR,
                                    CONF_EVLOG_VERSION, CONF_EVLOG_VERSION_RUNNING, CONF_EVLOG_BTNCONFIG_URL,
                                    CONF_UPDATE_DATE, CONF_VERSION_INSTALL_DATE,
                                    CONF_USERNAME, CONF_PASSWORD, CONF_LOCATE_ALL, CONF_TOTP_KEY,
                                    CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX,
                                    CONF_DEVICES, CONF_IC3_DEVICENAME, CONF_SETUP_ICLOUD_SESSION_EARLY,
                                    CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT, CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES,
                                    CONF_DATA_SOURCE, CONF_DISPLAY_GPS_LAT_LONG, CONF_LOG_ZONES,
                                    CONF_APPLE_ACCOUNT, CONF_FAMSHR_DEVICENAME,
                                    CONF_MOBILE_APP_DEVICE, CONF_IOSAPP_DEVICE,
                                    CONF_TRACKING_MODE,
                                    CONF_PICTURE, CONF_INZONE_INTERVAL, CONF_TRACK_FROM_ZONES,
                                    CONF_STAT_ZONE_FNAME, CONF_DEVICE_TRACKER_STATE_SOURCE,
                                    CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                    CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                    CONF_TRACK_FROM_BASE_ZONE_USED,
                                    CF_DEFAULT_IC3_CONF_FILE,
                                    DEFAULT_PROFILE_CONF, DEFAULT_TRACKING_CONF, DEFAULT_GENERAL_CONF,
                                    DEFAULT_SENSORS_CONF, DEFAULT_DATA_CONF,
                                    HOME_DISTANCE, CONF_SENSORS_TRACKING_DISTANCE,
                                    CONF_SENSORS_DEVICE, BATTERY_STATUS,
                                    CONF_WAZE_USED, CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE, CONF_DISTANCE_METHOD,
                                    WAZE_SERVERS_BY_COUNTRY_CODE, WAZE_SERVERS_FNAME,
                                    CONF_EXCLUDED_SENSORS, CONF_OLD_LOCATION_ADJUSTMENT, CONF_DISTANCE_BETWEEN_DEVICES,
                                    CONF_PICTURE_WWW_DIRS, PICTURE_WWW_STANDARD_DIRS,
                                    RANGE_DEVICE_CONF, RANGE_GENERAL_CONF, MIN, MAX, STEP, RANGE_UM,
                                    CF_PROFILE, CF_DATA, CF_TRACKING, CF_GENERAL, CF_SENSORS,
                                    CONF_DEVICES, CONF_APPLE_ACCOUNTS, DEFAULT_APPLE_ACCOUNTS_CONF,
                                    IC3LOG_FILENAME,
                                    )

from ..support              import start_ic3
from ..support              import waze
from ..helpers              import file_io
from ..helpers.common       import (instr, ordereddict_to_dict, isbetween, list_add, is_empty)
from ..helpers.messaging    import (log_exception, _evlog, _log, log_info_msg, )
from ..helpers.time_util    import (datetime_now, )

import os
import json
import base64

import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   configuration file I/O
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_load_storage_icloud3_configuration_file():
    return await Gb.hass.async_add_executor_job(load_storage_icloud3_configuration_file)

def load_storage_icloud3_configuration_file():

    # Make the .storage/icloud3 directory if it does not exist
    file_io.make_directory(Gb.ha_storage_icloud3)

    if file_io.file_exists(Gb.icloud3_config_filename) is False:
        _LOGGER.info(f"Creating Configuration File-{Gb.icloud3_config_filename}")

        initialize_icloud3_configuration_file()
        # Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()
        # build_initial_config_file_structure()
        # write_storage_icloud3_configuration_file()

    success = read_storage_icloud3_configuration_file()

    if success:
        write_storage_icloud3_configuration_file('_backup')
    else:
        _restore_config_file_from_backup()
        _add_parms_and_check_config_file()

    _count_device_tracking_methods_configured()

    if CONF_LOG_LEVEL in Gb.conf_general:
        start_ic3.set_log_level(Gb.conf_general[CONF_LOG_LEVEL])

    Gb.www_evlog_js_directory = Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]
    Gb.www_evlog_js_filename  = f"{Gb.www_evlog_js_directory}/{Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]}"

    return

#-------------------------------------------------------------------------------------------
def read_storage_icloud3_configuration_file(filename_suffix=''):
    '''
    Read the config/.storage/.icloud3.configuration file and extract the
    data into the Global Variables

    Parameters:
        filename_suffix: A suffix added to the filename that allows saving multiple copies of
                            the configuration file
    '''

    try:
        filename = f"{Gb.icloud3_config_filename}{filename_suffix}"
        Gb.conf_file_data = file_io.read_json_file(filename)

        if Gb.conf_file_data == {}:
            return False

        Gb.conf_profile   = Gb.conf_file_data[CF_PROFILE]
        Gb.conf_data      = Gb.conf_file_data[CF_DATA]

        Gb.conf_tracking  = Gb.conf_data[CF_TRACKING]
        Gb.conf_apple_accounts = Gb.conf_tracking.get(CONF_APPLE_ACCOUNTS, [])
        Gb.conf_devices   = Gb.conf_tracking.get(CONF_DEVICES, [])
        Gb.conf_general   = Gb.conf_data[CF_GENERAL]
        Gb.conf_sensors   = Gb.conf_data[CF_SENSORS]
        Gb.log_level      = Gb.conf_general[CONF_LOG_LEVEL]

        _add_parms_and_check_config_file()

        return True

    except Exception as err:
        _LOGGER.exception(err)

    return False

#--------------------------------------------------------------------
def write_storage_icloud3_configuration_file(filename_suffix=None):
    '''
    Update the config/.storage/.icloud3.configuration file

    Parameters:
        filename_suffix: A suffix added to the filename that allows saving multiple copies o
                            the configuration file
    '''
    _reconstruct_conf_file()

    try:
        if filename_suffix is None: filename_suffix = ''
        filename = f"{Gb.icloud3_config_filename}{filename_suffix}"

        success = file_io.save_json_file(filename, Gb.conf_file_data)

    except Exception as err:
        _LOGGER.exception(err)
        return False

    # Update conf_devices devicename index dictionary
    if len(Gb.conf_devices) != len(Gb.conf_devices_idx_by_devicename):
        set_conf_devices_index_by_devicename()

    return success

#--------------------------------------------------------------------
async def async_write_storage_icloud3_configuration_file(filename_suffix=None):
    '''
    Update the config/.storage/.icloud3.configuration file

    Parameters:
        filename_suffix: A suffix added to the filename that allows saving multiple
                            copies of the configuration file
    '''
    _reconstruct_conf_file()

    try:
        if filename_suffix is None: filename_suffix = ''
        filename = f"{Gb.icloud3_config_filename}{filename_suffix}"

        success = await file_io.async_save_json_file(filename, Gb.conf_file_data)

    except Exception as err:
        _LOGGER.exception(err)
        return False

    # Update conf_devices devicename index dictionary
    if len(Gb.conf_devices) != len(Gb.conf_devices_idx_by_devicename):
        set_conf_devices_index_by_devicename()

    return success

#--------------------------------------------------------------------
def _reconstruct_conf_file():
    '''
    Move the Gb.conf_xxx variables back to the file's actual Gb.conf_file_data/
    Gb.conf_xxx[xxx] dictionary items.

    The Gb.conf_tracking[CONF_PASSWORD] field contains the real password
    while iCloud3 is running. This makes it easier logging into PyiCloud
    and in config_flow. Save it, then put the encoded password in the file
    update the file and then restore the real password
    '''
    Gb.conf_profile[CONF_UPDATE_DATE] = datetime_now()

    # Gb.conf_tracking[CONF_PASSWORD] = \
    #         encode_password(Gb.conf_tracking[CONF_PASSWORD])

    # for apple_acct in Gb.conf_apple_accounts:
    #     apple_acct[CONF_PASSWORD] = encode_password(apple_acct[CONF_PASSWORD])

    encode_all_passwords()

    Gb.conf_tracking[CONF_APPLE_ACCOUNTS] = Gb.conf_apple_accounts
    Gb.conf_tracking[CONF_DEVICES]        = Gb.conf_devices
    Gb.conf_data[CF_TRACKING]             = Gb.conf_tracking
    Gb.conf_data[CF_GENERAL]              = Gb.conf_general
    Gb.conf_data[CF_SENSORS]              = Gb.conf_sensors

    Gb.conf_file_data[CF_PROFILE]         = Gb.conf_profile
    Gb.conf_file_data[CF_DATA]            = Gb.conf_data

#--------------------------------------------------------------------
def _restore_config_file_from_backup():

    datetime = datetime_now().replace('-', '.').replace(':', '.').replace(' ', '-')
    json_errors_filename = f"{Gb.icloud3_config_filename}_errors_{datetime}"
    log_msg = ( f"iCloud3 Error > Configuration file failed to load, JSON Errors were encountered. "
                f"Configuration file with errors was saved to `{json_errors_filename}`. "
                f"Will restore from `configuration_backup` file")
    _LOGGER.warning(log_msg)
    file_io.rename_file(Gb.icloud3_config_filename, json_errors_filename)
    success = read_storage_icloud3_configuration_file('_backup')

    if success:
        log_msg = ("Restore from backup configuration file was successful")
        _LOGGER.warning(log_msg)

        write_storage_icloud3_configuration_file()

    else:
        _LOGGER.error(f"iCloud3{RARROW}Restore from backup configuration file failed")
        _LOGGER.error(f"iCloud3{RARROW}Recreating configuration file with default parameters-"
                        f"{Gb.icloud3_config_filename}")
        initialize_icloud3_configuration_file()

#--------------------------------------------------------------------
def initialize_icloud3_configuration_file():
    build_initial_config_file_structure()
    Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()
    write_storage_icloud3_configuration_file()
    read_storage_icloud3_configuration_file()

#--------------------------------------------------------------------
def _add_parms_and_check_config_file():

    try:
        #Add new parameters, check  parameter settings
        update_config_file_flag = False
        update_config_file_flag = _config_file_check_new_ic3_version() or update_config_file_flag
        update_config_file_flag = _update_tracking_parameters()        or update_config_file_flag
        update_config_file_flag = _update_device_parameters()          or update_config_file_flag
        update_config_file_flag = _update_general_parameters()         or update_config_file_flag
        update_config_file_flag = _config_file_check_range_values()    or update_config_file_flag
        update_config_file_flag = _config_file_check_device_settings() or update_config_file_flag
        if update_config_file_flag:
            write_storage_icloud3_configuration_file()

        decode_all_passwords()
        build_log_file_filters()
        set_conf_devices_index_by_devicename()

    except Exception as err:
        _LOGGER.exception(err)
        _LOGGER.error(  "iCloud3 > An error occured verifying the iCloud3 "
                            "Configuration File. Will continue.")

#--------------------------------------------------------------------
def set_conf_devices_index_by_devicename():
    '''
    Update the device name index position in the conf_devices parameter.
    This let you access a devices configuration without searching through
    the devices list to get a specific device.

    idx = Gb.conf_devices_idx_by_devicename('gary_iphone')
    conf_device = Gb.conf_devices.index(idx)
    '''
    Gb.conf_devices_idx_by_devicename = {}
    for index, conf_device in enumerate(Gb.conf_devices):
        Gb.conf_devices_idx_by_devicename[conf_device[CONF_IC3_DEVICENAME]] = index

def get_conf_device(devicename):
    idx = Gb.conf_devices_idx_by_devicename.get(devicename, -1)
    if idx == -1:
        return None

    return Gb.conf_devices[idx]

#-------------------------------------------------------------------------------------------
async def async_load_icloud3_ha_config_yaml(ha_config_yaml):

    Gb.ha_config_yaml_icloud3_platform = {}
    if ha_config_yaml == '':
        return

    ha_config_yaml_devtrkr_platforms = ordereddict_to_dict(ha_config_yaml)['device_tracker']

    ic3_ha_config_yaml = {}
    for ha_config_yaml_platform in ha_config_yaml_devtrkr_platforms:
        if ha_config_yaml_platform['platform'] == 'icloud3':
            ic3_ha_config_yaml = ha_config_yaml_platform.copy()
            break

    Gb.ha_config_yaml_icloud3_platform = ordereddict_to_dict(ic3_ha_config_yaml)

#--------------------------------------------------------------------
def build_log_file_filters():

    return
    try:
        for apple_acct in Gb.conf_apple_accounts:
            if apple_acct[CONF_USERNAME] == '':
                continue
            elif instr(apple_acct[CONF_USERNAME], '@'):
                email_extn = f"{apple_acct[CONF_USERNAME].split('@')[1]}"
                list_add(Gb.log_file_filter, email_extn)

            list_add(Gb.log_file_filter, apple_acct[CONF_PASSWORD])
            list_add(Gb.log_file_filter, Gb.PyiCloud_password_by_username[apple_acct[CONF_USERNAME]])

    except Exception as err:
        _LOGGER.exception(err)

#--------------------------------------------------------------------
def build_initial_config_file_structure():
    '''
    Create the initial data structure of the ic3 config file

    |---profile
    |---data
        |---tracking
            |---devices
        |---general
            |---parameters
        |---sensors

    '''

    Gb.conf_profile   = DEFAULT_PROFILE_CONF.copy()
    Gb.conf_tracking  = DEFAULT_TRACKING_CONF.copy()
    Gb.conf_apple_accounts = []
    Gb.conf_devices   = []
    Gb.conf_general   = DEFAULT_GENERAL_CONF.copy()
    Gb.conf_sensors   = DEFAULT_SENSORS_CONF.copy()
    Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()

    Gb.conf_data[CF_TRACKING] = Gb.conf_tracking
    Gb.conf_data[CF_GENERAL]  = Gb.conf_general
    Gb.conf_data[CF_SENSORS]  = Gb.conf_sensors

    Gb.conf_file_data[CF_PROFILE]  = Gb.conf_profile
    Gb.conf_file_data[CF_DATA]     = Gb.conf_data

    # Verify general parameters and make any necessary corrections
    try:
        if Gb.country_code in APPLE_SPECIAL_ICLOUD_SERVER_COUNTRY_CODE:
            Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX] = Gb.country_code

        if Gb.config and Gb.config.units['name'] != 'Imperial':
            Gb.conf_general[CONF_UNIT_OF_MEASUREMENT] = 'km'
            Gb.conf_general[CONF_TIME_FORMAT] = '24-hour'

        elif Gb.ha_use_metric:
            Gb.conf_general[CONF_UNIT_OF_MEASUREMENT] = 'km'
            Gb.conf_general[CONF_TIME_FORMAT] = '24-hour'

    except:
        pass

#--------------------------------------------------------------------
def conf_apple_acct(idx_or_username):
    '''
    Extract and return the Apple Account configuration item by it's index or
    by username

    Returns:
        - conf_apple_acct = dictionary item
        - conf_apple_acct_idx = index
    '''
    try:
        if len(Gb.conf_apple_accounts) == 0:
            return (DEFAULT_APPLE_ACCOUNTS_CONF.copy(), 0)

        # Get conf_apple_acct by it's index
        if type(idx_or_username) is int:
            if isbetween(idx_or_username, 0, len(Gb.conf_apple_accounts)-1):
                conf_apple_acct = Gb.conf_apple_accounts[idx_or_username].copy()
                conf_apple_acct[CONF_PASSWORD] = decode_password(conf_apple_acct[CONF_PASSWORD])
                return (conf_apple_acct, idx_or_username)

            else:
                return (DEFAULT_APPLE_ACCOUNTS_CONF.copy(), -1)

        # Get conf_apple_acct by it's username
        elif type(idx_or_username) is str:
            conf_apple_acct = [apple_acct   for apple_acct in Gb.conf_apple_accounts
                                            if apple_acct[CONF_USERNAME] == idx_or_username]
            if is_empty(conf_apple_acct):
                return (DEFAULT_APPLE_ACCOUNTS_CONF.copy(), -1)

            # Get it's index
            conf_apple_acct_usernames = [apple_acct[CONF_USERNAME]
                                            for apple_acct in Gb.conf_apple_accounts]
            conf_apple_acct_idx = conf_apple_acct_usernames.index(idx_or_username)

            if conf_apple_acct != []:
                conf_apple_acct = conf_apple_acct[0]
                conf_apple_acct[CONF_PASSWORD] = decode_password(conf_apple_acct[CONF_PASSWORD])
                return (conf_apple_acct, conf_apple_acct_idx)

    except Exception as err:
        log_exception(err)
        pass

    return (DEFAULT_APPLE_ACCOUNTS_CONF.copy(), 0)


#--------------------------------------------------------------------
def apple_acct_username_password(idx):
    '''
    Extract and return the Apple Account username & password

    Note: idx = -1 when adding a new username
    '''
    if idx < 0 or idx > (len(Gb.conf_apple_accounts)-1):
        return ('', '', '', True)

    try:
        return (Gb.conf_apple_accounts[idx][CONF_USERNAME],
            decode_password(Gb.conf_apple_accounts[idx][CONF_PASSWORD]),
            Gb.conf_apple_accounts[idx][CONF_LOCATE_ALL])
    except:
        return ('', '', '' , True)

#--------------------------------------------------------------------
def apple_acct_password_for_username(username):
    '''
    Extract and return the Apple Account password for a username
    '''
    if username is None:
        return ''

    try:
        return [apple_acct[CONF_PASSWORD]
                                for apple_acct in Gb.conf_apple_accounts
                                if apple_acct[CONF_USERNAME] == username][0]
    except:
        return ''

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Verify various configuration file parameters
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def _count_device_tracking_methods_configured():
    '''
    Count the number of devices that have been configured for the icloud,
    fmf and Mobile App tracking methods. This will be compared to the actual
    number of devices returned from iCloud during setup in PyiCloud. Sometmes,
    iCloud does not return all devices in the iCloud list and a refresh/retry
    is needed.
    '''
    try:
        Gb.conf_icloud_device_cnt = 0
        # Gb.conf_fmf_device_cnt    = 0
        Gb.conf_mobapp_device_cnt = 0

        for conf_device in Gb.conf_devices:
            if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
                continue

            if conf_device[CONF_FAMSHR_DEVICENAME].startswith(NONE_FNAME) is False:
                Gb.conf_icloud_device_cnt += 1

            # if conf_device[CONF_FMF_EMAIL].startswith(NONE_FNAME) is False:
            #     Gb.conf_fmf_device_cnt += 1

            if conf_device[CONF_MOBILE_APP_DEVICE].startswith(NONE_FNAME) is False:
                Gb.conf_mobapp_device_cnt += 1

    except Exception as err:
        _LOGGER.exception(err)

#--------------------------------------------------------------------
def _config_file_check_new_ic3_version():
    '''
    Check to see if this is a new iCloud3 version
    '''
    new_icloud3_version_flag = False
    if Gb.conf_profile[CONF_IC3_VERSION] != f"{VERSION}{VERSION_BETA}":
        Gb.conf_profile[CONF_IC3_VERSION] = f"{VERSION}{VERSION_BETA}"
        Gb.conf_profile[CONF_VERSION_INSTALL_DATE] = datetime_now()
        new_icloud3_version_flag = True

    elif Gb.conf_profile[CONF_VERSION_INSTALL_DATE] == DATETIME_ZERO:
        Gb.conf_profile[CONF_VERSION_INSTALL_DATE] = datetime_now()
        new_icloud3_version_flag = True

    if new_icloud3_version_flag and VERSION.startswith('3.1.4'):
        _delete_old_log_files()

    return new_icloud3_version_flag

#--------------------------------------------------------------------
def _delete_old_log_files():
    log_file_0 = Gb.hass.config.path(IC3LOG_FILENAME).replace('.', '-0.')
    log_file_1 = Gb.hass.config.path(IC3LOG_FILENAME).replace('.', '-1.')
    log_file_2 = Gb.hass.config.path(IC3LOG_FILENAME).replace('.', '-2.')
    file_io.delete_file(log_file_0)
    file_io.delete_file(log_file_1)
    file_io.delete_file(log_file_2)

#--------------------------------------------------------------------
def _config_file_check_range_values():
    '''
    Check the min and max value of the items that have a range in config_flow to make
    sure the actual value in the config file is within the min-max range
    '''
    try:
        range_errors = {}
        update_configuration_flag = False

        range_errors.update({pname: DEFAULT_GENERAL_CONF.get(pname, range[MIN])
                            for pname, range in RANGE_GENERAL_CONF.items()
                            if Gb.conf_general[pname] < range[MIN]})
        range_errors.update({pname: DEFAULT_GENERAL_CONF.get(pname, range[MAX])
                            for pname, range in RANGE_GENERAL_CONF.items()
                            if Gb.conf_general[pname] > range[MAX]})
        update_configuration_flag = (range_errors != {})

        for pname, pvalue in range_errors.items():
            log_info_msg(   f"iCloud3 Config Parameter out of range, resetting to valid value, "
                            f"Parameter-{pname}, From-{Gb.conf_general[pname]}, To-{pvalue}")
            Gb.conf_general[pname] = pvalue

        trav_time_factor = Gb.conf_general[CONF_TRAVEL_TIME_FACTOR]
        if Gb.conf_general[CONF_TRAVEL_TIME_FACTOR] in [.25, .33, .5, .66, .75]:
            pass
        elif Gb.conf_general[CONF_TRAVEL_TIME_FACTOR] < .3:
            Gb.conf_general[CONF_TRAVEL_TIME_FACTOR] = .25
        elif Gb.conf_general[CONF_TRAVEL_TIME_FACTOR] < .4:
            Gb.conf_general[CONF_TRAVEL_TIME_FACTOR] = .33
        elif Gb.conf_general[CONF_TRAVEL_TIME_FACTOR] < .6:
            Gb.conf_general[CONF_TRAVEL_TIME_FACTOR] = .5
        elif Gb.conf_general[CONF_TRAVEL_TIME_FACTOR] < .7:
            Gb.conf_general[CONF_TRAVEL_TIME_FACTOR] = .66
        else:
            Gb.conf_general[CONF_TRAVEL_TIME_FACTOR] = .75
        if trav_time_factor != Gb.conf_general[CONF_TRAVEL_TIME_FACTOR]:
            update_configuration_flag = True

        if update_configuration_flag:
            write_storage_icloud3_configuration_file()

    except Exception as err:
        _LOGGER.exception(err)

#--------------------------------------------------------------------
def _config_file_check_device_settings():
    '''
    Cycle thru the conf_devices and verify that the settings are valid
    '''
    update_configuration_flag = False

    for conf_device in Gb.conf_devices:
        if conf_device[CONF_PICTURE] == '':
            conf_device[CONF_PICTURE] = 'None'
            update_configuration_flag = True
        if conf_device[CONF_INZONE_INTERVAL] < 5:
            conf_device[CONF_INZONE_INTERVAL] = 5
            update_configuration_flag = True
        if conf_device[CONF_LOG_ZONES]== []:
            conf_device[CONF_LOG_ZONES] = ['none']
            update_configuration_flag = True
        if conf_device[CONF_TRACK_FROM_ZONES] == []:
            conf_device[CONF_TRACK_FROM_ZONES] = [HOME]
            update_configuration_flag = True
        if isbetween(conf_device[CONF_FIXED_INTERVAL], 1, 2):
            conf_device[CONF_FIXED_INTERVAL] = 3.0
            update_configuration_flag = True

        if update_configuration_flag:
            write_storage_icloud3_configuration_file()

#--------------------------------------------------------------------
def _convert_hhmmss_to_minutes(conf_group):

    time_fields = {pname: _hhmmss_to_minutes(pvalue)
                            for pname, pvalue in conf_group.items()
                            if (pname in CONF_PARAMETER_TIME_STR
                                    and instr(str(pvalue), ':'))}
    if time_fields != {}:
        conf_group.update(time_fields)
        return True

    return False

def _hhmmss_to_minutes(hhmmss):
        hhmmss_parts = hhmmss.split(':')
        return int(hhmmss_parts[0])*60 + int(hhmmss_parts[1])

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Add parameters to the configuration file
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def _update_tracking_parameters():
    '''
    Fix conf_tracking errors or add any new fields
    '''

    update_config_file_flag = False

    # Add tracking.CONF_SETUP_ICLOUD_SESSION_EARLY
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_tracking, CONF_SETUP_ICLOUD_SESSION_EARLY, True)
            or update_config_file_flag)

    # Change icloud to iCloud (3.1)
    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'famshr'):
        Gb.conf_tracking[CONF_DATA_SOURCE] = \
            Gb.conf_tracking[CONF_DATA_SOURCE].replace('famshr', ICLOUD).replace(' ', '')
        update_config_file_flag = True

    # Change mobapp to MobApp (3.1)
    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'mobapp'):
        Gb.conf_tracking[CONF_DATA_SOURCE] = \
            Gb.conf_tracking[CONF_DATA_SOURCE].replace('mobapp', MOBAPP).replace(' ', '')
        update_config_file_flag = True

    # v3.1 Add Apple accounts list
    try:
        if (CONF_APPLE_ACCOUNTS not in Gb.conf_tracking):
            update_config_file_flag = True

            Gb.conf_tracking = _insert_into_conf_dict_parameter(
                                            Gb.conf_tracking,
                                            CONF_APPLE_ACCOUNTS, [],
                                            before=CONF_DEVICES)

            if Gb.conf_tracking[CONF_USERNAME] == '':
                Gb.conf_apple_accounts = Gb.conf_tracking[CONF_APPLE_ACCOUNTS] = []
            else:
                Gb.conf_apple_accounts = Gb.conf_tracking[CONF_APPLE_ACCOUNTS] = [
                    {   CONF_USERNAME: Gb.conf_tracking[CONF_USERNAME],
                        CONF_PASSWORD: encode_password(Gb.conf_tracking[CONF_PASSWORD]),
                        CONF_TOTP_KEY: '',
                        CONF_LOCATE_ALL: True,
                    }]

    except Exception as err:
        _LOGGER.exception(err)

    return update_config_file_flag

#--------------------------------------------------------------------
def _update_device_parameters():
    '''
    Update all device configuration with new/changeditem
    '''
    update_config_file_flag = False
    cd_idx = -1
    conf_devices = Gb.conf_devices.copy()
    for conf_device in conf_devices:
        cd_idx += 1
        # b16 - Remove the stat zone friendly name
        if CONF_STAT_ZONE_FNAME in conf_device:
            conf_device.pop(CONF_STAT_ZONE_FNAME)
            update_config_file_flag = True

        # rc8.2 - Add zones for logging enter/exit activity
        if CONF_LOG_ZONES not in conf_device:
            conf_device[CONF_LOG_ZONES] = ['none']
            update_config_file_flag = True

        # rc8.2 - Add zones for logging enter/exit activity
        if CONF_FIXED_INTERVAL not in conf_device:
            conf_device[CONF_FIXED_INTERVAL] = 0.0
            update_config_file_flag = True

        # rc8.2 - Cleanup a bug introduced in v3.0.rc8
        if 'action_items' in conf_device:
            conf_device.pop('action_items')
            update_config_file_flag = True

        # v3.1 - Add Apple account parameter
        if CONF_APPLE_ACCOUNT not in conf_device:
            conf_device = _insert_into_conf_dict_parameter(
                                    conf_device,
                                    CONF_APPLE_ACCOUNT, Gb.conf_tracking[CONF_USERNAME],
                                    before=CONF_FAMSHR_DEVICENAME)

            update_config_file_flag = True

        # v3.1 - Change Search: to ScanFor: in Mobile App parameter
        if conf_device[CONF_MOBILE_APP_DEVICE].startswith('Search:'):
            conf_device[CONF_MOBILE_APP_DEVICE] = \
                    conf_device[CONF_MOBILE_APP_DEVICE].replace('Search:', 'ScanFor:')
            update_config_file_flag = True

        # v3.1 Remove unused parameters
        if 'evlog_display_order' in conf_device:
            conf_device.pop('evlog_display_order')
            conf_device.pop('unique_id')
            update_config_file_flag = True
        if 'old_devicename' in conf_device:
            conf_device.pop('old_devicename')
            update_config_file_flag = True

        if update_config_file_flag:
            Gb.conf_devices[cd_idx] = conf_device

    return update_config_file_flag

#-------------------------------------------------------------------
def _update_general_parameters():
    '''
    Fix conf_general and conf_sensors  errors or add any new fields
    '''

    update_config_file_flag = False

    # Fix time format from migration (b1)
    if instr(Gb.conf_data[CF_GENERAL][CONF_TIME_FORMAT], '-hour-hour'):
        Gb.conf_data[CF_GENERAL][CONF_TIME_FORMAT].replace('-hour-hour', '-hour')
        update_config_file_flag = True

    if Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY].startswith('www/') is False:
        Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY] = f"www/{Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]}"

    # Remove tracking_from_zone item from sensors list which shouldn't have been added (b3)
    if BATTERY_STATUS in Gb.conf_sensors[CONF_SENSORS_DEVICE]:
        Gb.conf_sensors[CONF_SENSORS_DEVICE].pop(BATTERY_STATUS, None)
        update_config_file_flag = True

    if 'tracking_by_zones' in Gb.conf_sensors:
        Gb.conf_sensors.pop('tracking_by_zones', None)
        update_config_file_flag = True

    # Add sensors.HOME_DISTANCE sensor to conf_sensors
    if HOME_DISTANCE not in Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE]:
        Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)
        update_config_file_flag = True

    # Add sensors.CONF_EXCLUDED_SENSORS
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_sensors, CONF_EXCLUDED_SENSORS, ['None'])
            or update_config_file_flag)

    # Add general.CONF_OLD_LOCATION_ADJUSTMENT
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_OLD_LOCATION_ADJUSTMENT, HHMMSS_ZERO)
            or update_config_file_flag)

    # Add generalCONF_DISTANCE_BETWEEN_DEVICES
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_DISTANCE_BETWEEN_DEVICES, True)
            or update_config_file_flag)

    # Add general.CONF_EXIT_ZONE_INTERVAL
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_EXIT_ZONE_INTERVAL, 3)
            or update_config_file_flag)

    # Add profile.CONF_VERSION_INSTALL_DATE
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_profile, CONF_VERSION_INSTALL_DATE, DATETIME_ZERO)
            or update_config_file_flag)

    # Remove CONF_ZONE_SENSOR_EVLOG_FORMAT, Add CONF_ZONE_SENSOR_EVLOG_FORMAT
    dtf = 'zone'
    if 'zone_sensor_evlog_format' in Gb.conf_general:
        dtf = 'fname' if Gb.conf_general['zone_sensor_evlog_format'] else 'zone'
        Gb.conf_general.pop('zone_sensor_evlog_format')

    # Change Waze server codes
    if Gb.conf_general[CONF_WAZE_REGION].lower() in ['na']:
        Gb.conf_general[CONF_WAZE_REGION] = 'us'
        update_config_file_flag = True
    elif Gb.conf_general[CONF_WAZE_REGION].lower() in ['eu', 'au']:
        Gb.conf_general[CONF_WAZE_REGION] = 'row'
        update_config_file_flag = True

    # Change all time fields from hh:mm:ss to minutes (b12)
    update_config_file_flag = (_convert_hhmmss_to_minutes(Gb.conf_general)
            or update_config_file_flag)
    update_config_file_flag = (_convert_hhmmss_to_minutes(Gb.conf_general[CONF_INZONE_INTERVALS])
            or update_config_file_flag)
    for conf_device in Gb.conf_devices:
        update_config_file_flag = (_convert_hhmmss_to_minutes(conf_device)
                or update_config_file_flag)

    # Change StatZone friendly Name (b16)
    if instr(Gb.conf_general[CONF_STAT_ZONE_FNAME], '[name]'):
        Gb.conf_general[CONF_STAT_ZONE_FNAME] = 'StatZon#'
        update_config_file_flag = True

    # Add general.Display GPS coordinates Flag (b17)
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_DISPLAY_GPS_LAT_LONG, True)
            or update_config_file_flag)

    if 'device_tracker_state_format' in Gb.conf_general:
        Gb.conf_general.pop('device_tracker_state_format')

    # Remove profile.CONF_HA_CONFIG_IC3_URL that is used by EvLog to open Configuration Wizard (b20)
    if 'ha_config_ic3_url' in Gb.conf_profile:
        Gb.conf_profile.pop('ha_config_ic3_url')
        update_config_file_flag = True

    # Add profile.CONF_EVLOG_BTNCONFIG_URL that is used by EvLog to open HA iCloud3 Configure screen (b20)
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_profile, CONF_EVLOG_BTNCONFIG_URL, '')
            or update_config_file_flag)

    # Add profile.event_log_version that is being used, set via action/event_log_version svc call (b20)
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_profile, CONF_EVLOG_VERSION, '')
            or update_config_file_flag)
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_profile, CONF_EVLOG_VERSION_RUNNING, '')
            or update_config_file_flag)

    # Add profile.CONF_PICTURE_WWW_DIRS that is used by Configure Sreen > Update Devices for dir image scan (3.0)
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_profile, CONF_PICTURE_WWW_DIRS, [])
            or update_config_file_flag)

    # Add track from base zone used control on the Special Zones screen (rc9)
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_TRACK_FROM_BASE_ZONE_USED, False)
            or update_config_file_flag)

    # Add log level devices to select the devices that should be used when rawdata is selected (v3.0.3)
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_LOG_LEVEL_DEVICES, ['all'])
            or update_config_file_flag)

    # Add general.CONF_DEVICE_TRACKER_STATE_SOURCE, b20
    update_config_file_flag = (_add_config_file_parameter(Gb.conf_general, CONF_DEVICE_TRACKER_STATE_SOURCE, 'ic3_fname')
            or update_config_file_flag)
    if Gb.conf_general[CONF_DEVICE_TRACKER_STATE_SOURCE] == ICLOUD3:
        Gb.conf_general[CONF_DEVICE_TRACKER_STATE_SOURCE] = 'ic3_fname'
        update_config_file_flag = True

    # Add Local Zone Time display (rc9)
    if CONF_AWAY_TIME_ZONE_1_OFFSET not in Gb.conf_general:
        _add_config_file_parameter(Gb.conf_general, CONF_AWAY_TIME_ZONE_1_OFFSET, 0)
        _add_config_file_parameter(Gb.conf_general, CONF_AWAY_TIME_ZONE_1_DEVICES, ['none'])
        _add_config_file_parameter(Gb.conf_general, CONF_AWAY_TIME_ZONE_2_OFFSET, 0)
        _add_config_file_parameter(Gb.conf_general, CONF_AWAY_TIME_ZONE_2_DEVICES, ['none'])
        update_config_file_flag = True

    # Convert iosapp to mobapp in various parameters (rc10)
    if CONF_IOSAPP_ALIVE_INTERVAL in Gb.conf_general:
        if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'ios'):
            Gb.conf_tracking[CONF_DATA_SOURCE] = \
                Gb.conf_tracking[CONF_DATA_SOURCE].replace('ios', 'mob')

        Gb.conf_general[CONF_INZONE_INTERVALS][NO_MOBAPP] = \
            Gb.conf_general[CONF_INZONE_INTERVALS][NO_IOSAPP]
        del Gb.conf_general[CONF_INZONE_INTERVALS][NO_IOSAPP]

        Gb.conf_general[CONF_MOBAPP_ALIVE_INTERVAL] = \
            Gb.conf_general[CONF_IOSAPP_ALIVE_INTERVAL]
        del Gb.conf_general[CONF_IOSAPP_ALIVE_INTERVAL]

        for conf_device in Gb.conf_devices:
            conf_device[CONF_MOBILE_APP_DEVICE] = conf_device[CONF_IOSAPP_DEVICE]
            del conf_device[CONF_IOSAPP_DEVICE]
        update_config_file_flag = True

    return update_config_file_flag

#--------------------------------------------------------------------
def _add_config_file_parameter(conf_section, conf_parameter, default_value):
    '''
    Update the configuration file with a new field if it is not in the file.

    Return:
        True - File was updated
        False - File was not updated
    '''

    if conf_parameter not in conf_section:
        if conf_section is Gb.conf_tracking:
            Gb.conf_tracking = _insert_into_conf_dict_parameter(
                                            Gb.conf_tracking,
                                            conf_parameter, default_value)
        else:
            conf_section[conf_parameter] = default_value
        return True

    return False

#--------------------------------------------------------------------
def _insert_into_conf_dict_parameter(dict_parameter,
                                    new_item=None,
                                    initial_value=None, before=None, after=None):
    '''
    Add items to the configuration file dictionary parameters

    Input:
        dict_parameter - Dictionary item to be updated
        new_item - Field to be added
        initial_value - Initial value
        before - Insert it before this argument
        after - Insert it after this argument
    '''
    if isinstance(dict_parameter, dict) is False or not new_item:
        return dict_parameter
    if initial_value is None: initial_value = ''

    if before is None and after is None:
        dict_parameter[new_item] = initial_value
        return dict_parameter

    try:
        if before:
            pos = list(dict_parameter.keys()).index(before)
        elif after:
            pos = list(dict_parameter.keys()).index(after) + 1
        items = list(dict_parameter.items())
        items.insert(pos, (new_item, initial_value))
        return dict(items)

    except Exception as err:
        _LOGGER.exception(err)
        dict_parameter[new_item] = initial_value
        return dict_parameter

    return dict_parameter

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Password encode/decode functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def encode_all_passwords():

    Gb.conf_tracking[CONF_PASSWORD] = encode_password(Gb.conf_tracking[CONF_PASSWORD])

    for apple_acct in Gb.conf_apple_accounts:
        apple_acct[CONF_PASSWORD] = encode_password(apple_acct[CONF_PASSWORD])

#--------------------------------------------------------------------
def decode_all_passwords():

    try:
        for apple_acct in Gb.conf_apple_accounts:
            Gb.PyiCloud_password_by_username[apple_acct[CONF_USERNAME]] = \
                decode_password(apple_acct[CONF_PASSWORD])

    except Exception as err:
        _LOGGER.exception(err)

#--------------------------------------------------------------------
def encode_password(password):
    '''
    Determine if the password is encoded.

    Return:
        Decoded password
    '''
    try:
        if (password == ''
                or Gb.encode_password_flag is False
                or password.startswith('««')
                or password.endswith('»»')):
            return password

        return f"««{base64_encode(password)}»»"

    except Exception as err:
        _LOGGER.exception(err)
        password = password.replace('«', '').replace('»', '')
        return password

def base64_encode(password):
    """
    Encode the string via base64 encoder
    """
    # encoded = base64.urlsafe_b64encode(string)
    # return encoded.rstrip("=")

    try:
        password_bytes = password.encode('ascii')
        base64_bytes = base64.b64encode(password_bytes)
        return base64_bytes.decode('ascii')

    except Exception as err:
        _LOGGER.exception(err)
        password = password.replace('«', '').replace('»', '')
        return password

#--------------------------------------------------------------------
def decode_password(password):
    '''
    Determine if the password is encoded.

    Return:
        Decoded password
    '''
    try:
        # If the password in the configuration file is not encoded (no '««' or '»»')
        # and it should be encoded, save the configuration file which will encode it
        if (Gb.encode_password_flag
                and password != ''
                and (password.startswith('««') is False or password.endswith('»»') is False)):
            password = password.replace('«', '').replace('»', '')
            write_storage_icloud3_configuration_file()

        # Decode password if it is encoded and has the '««password»»' format
        if (password.startswith('««') or password.endswith('»»')):
            password = password.replace('«', '').replace('»', '')
            return base64_decode(password)

    except Exception as err:
        _LOGGER.exception(err)
        password = password.replace('«', '').replace('»', '')

    return password

def base64_decode(string):
    """
    Decode the string via base64 decoder
    """
    # padding = 4 - (len(string) % 4)
    # string = string + ("=" * padding)
    # return base64.urlsafe_b64decode(string)

    base64_bytes = string.encode('ascii')
    string_bytes = base64.b64decode(base64_bytes)
    return string_bytes.decode('ascii')

#--------------------------------------------------------------------
def count_lines_of_code(start_directory, total_file_lines=0, total_code_lines=0, begin_start=None):

    if begin_start is None:
        log_info_msg(f"Lines Of Code Count - {start_directory}")
        log_info_msg(" ")
        log_info_msg("---All Lines---     ---Code Lines---   Module")
        log_info_msg("Total     Lines     Total     Lines")
        #           ("11111111  22222222  33333333  44444444

    for file_name in os.listdir(start_directory):
        file_name = os.path.join(start_directory, file_name)
        if file_io.file_exists(file_name):
            if file_name.endswith('.py') or file_name.endswith('.js'):
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    line_cnt = len(lines)
                    total_file_lines += line_cnt
                    code_cnt = 0
                    for line in lines:
                        if line is not None and len(line.strip()) > 3:
                            if (line.startswith("'")
                                    or line.startswith('#')):
                                continue

                        code_cnt += 1

                    total_code_lines += code_cnt

                    if begin_start is not None:
                        reldir_of_file_name = '.' + file_name.replace(begin_start, '')
                    else:
                        reldir_of_file_name = '.' + file_name.replace(start_directory, '')

                    log_info_msg(   f"{total_file_lines:<9} {line_cnt:<9} {total_code_lines:<9} "
                                    f"{code_cnt:<8} {reldir_of_file_name}")

    for file_name in os.listdir(start_directory):
        file_name = os.path.join(start_directory, file_name)
        if os.path.isdir(file_name):
            total_file_lines, total_code_lines = \
                count_lines_of_code(file_name, total_file_lines, total_code_lines, begin_start=start_directory)

    return total_file_lines, total_code_lines