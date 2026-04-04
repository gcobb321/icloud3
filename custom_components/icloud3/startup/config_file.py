
from ..global_variables import GlobalVariables as Gb
from ..const            import (
                                ICLOUD3,
                                RARROW, RARROW2, HHMMSS_ZERO, DATETIME_ZERO, NONE_FNAME, INACTIVE,
                                ICLOUD, MOBAPP, NO_MOBAPP, NO_IOSAPP, HOME,
                                CONF_PARAMETER_TIME_STR,
                                CONF_PICTURE_WWW_DIRS, CONF_SENSORS_HASH,
                                CONF_FIXED_INTERVAL, CONF_EXIT_ZONE_INTERVAL,
                                CONF_IC3_VERSION, VERSION, VERSION_BETA,
                                CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_CARD_PROGRAM, CONF_TRAVEL_TIME_FACTOR,
                                CONF_UPDATE_DATE, CONF_VERSION_INSTALL_DATE,
                                CONF_USERNAME, CONF_PASSWORD, CONF_LOCATE_ALL,
                                CONF_SERVER_LOCATION, CONF_SERVER_LOCATION_NEEDED,
                                CONF_DEVICES, CONF_IC3_DEVICENAME, CONF_FNAME,
                                CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT, CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES,
                                CONF_DATA_SOURCE, CONF_LOG_ZONES,
                                CONF_APPLE_ACCOUNT, CONF_FAMSHR_DEVICENAME,
                                CONF_MOBILE_APP_DEVICE, CONF_IOSAPP_DEVICE,
                                CONF_TRACKING_MODE, CONF_PASSWORD_SRP_ENABLED, CONF_EXCLUDED_SENSORS,
                                CONF_PICTURE, CONF_INZONE_INTERVAL, CONF_TRACK_FROM_ZONES,
                                CONF_DISPLAY_TEXT_AS,
                                CONF_TRACK_FROM_BASE_ZONE,
                                CF_DEFAULT_IC3_CONF_FILE,
                                DEFAULT_PROFILE_CONF, DEFAULT_TRACKING_CONF, DEFAULT_GENERAL_CONF, DEFAULT_DEVICE_CONF,
                                DEFAULT_SENSORS_CONF, DEFAULT_DEVICE_SENSORS_CONF, BASE,
                                RANGE_DEVICE_CONF, RANGE_GENERAL_CONF, MIN, MAX, STEP, RANGE_UM,
                                CF_PROFILE, CF_DATA, CF_TRACKING, CF_GENERAL, CF_SENSORS, CF_DEVICE_SENSORS,
                                CONF_DEVICES, CONF_APPLE_ACCOUNTS, DEFAULT_APPLE_ACCOUNT_CONF,
                                IC3LOG_FILENAME,
                                BASE, TRACKED, MONITORED, EXCLUDED, TRACK, MONITOR,
                                NLSP4, ZONE,
                                CONF_SENSORS_MONITORED_DEVICES, CONF_SENSORS_TRACK_FROM_ZONES,

                                )
from ..const_sensor      import (SENSOR_DEFINITION, SENSOR_GROUPS, SENSOR_LIST_DISTANCE,
                                SENSOR_FNAME, SENSOR_TYPE, SENSOR_ICON,
                                SENSOR_ATTRS, SENSOR_DEFAULT, SENSOR_LIST_ALWAYS, ICLOUD3_SENSORS,
                                SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS,
                                CONF_NON_TRACKING_GROUPS,
                                )

from ..startup          import start_ic3
from ..utils.utils      import (instr, is_empty, isnot_empty, ordereddict_to_dict, isbetween,
                                list_add, list_to_str, list_add, list_del, dict_del, get_string_hash,
                                username_id, )
from ..utils.messaging  import (log_exception, _evlog, _log, log_info_msg, add_log_file_filter,
                                log_debug_msg, open_ic3log_file, close_ic3log_file, )
from ..utils.time_util  import (datetime_now, )

from ..utils            import entity_reg_util as er_util
from ..utils            import file_io

#--------------------------------------------------------------------
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
async def async_load_icloud3_configuration_file():
    return await Gb.hass.async_add_executor_job(load_icloud3_configuration_file)

def load_icloud3_configuration_file():

    # Make the .storage/icloud3 directory if it does not exist
    file_io.make_directory(Gb.ha_storage_icloud3)
    file_io.make_directory(Gb.icloud_cookies_directory)

    if file_io.file_exists(Gb.icloud3_config_filename) is False:
        _LOGGER.info(f"Creating Configuration File-{Gb.icloud3_config_filename}")

        initialize_icloud3_configuration_file()

    success = read_icloud3_configuration_file()
    build_conf_device_sensors_from_conf_sensors()

    if success:
        write_icloud3_configuration_file('_backup')
    else:
        _restore_config_file_from_backup()

    _count_device_tracking_methods_configured()

    Gb.www_evlog_js_directory = Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]
    Gb.www_evlog_js_filename  = f"{Gb.www_evlog_js_directory}/{Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]}"

    return

#-------------------------------------------------------------------------------------------
def read_icloud3_configuration_file(filename_suffix=''):
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

        Gb.conf_profile        = Gb.conf_file_data[CF_PROFILE]
        Gb.conf_data           = Gb.conf_file_data[CF_DATA]

        Gb.conf_tracking       = Gb.conf_data[CF_TRACKING]
        Gb.conf_apple_accounts = Gb.conf_tracking.get(CONF_APPLE_ACCOUNTS, [])
        Gb.conf_devices        = Gb.conf_tracking.get(CONF_DEVICES, [])
        Gb.conf_general        = Gb.conf_data[CF_GENERAL]
        Gb.conf_sensors        = Gb.conf_data[CF_SENSORS]
        Gb.conf_device_sensors = Gb.conf_data.get(CF_DEVICE_SENSORS, {})

        Gb.log_level           = Gb.conf_general[CONF_LOG_LEVEL]
        start_ic3.set_log_level(Gb.log_level)

        _add_parms_and_check_config_file()

        return True

    except Exception as err:
        _LOGGER.exception(err)

    return False

#--------------------------------------------------------------------
def write_icloud3_configuration_file(filename_suffix=None, new_file_flag=None):
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

        if new_file_flag is not None:
            file_io.set_write_permission(filename)

    except Exception as err:
        _LOGGER.exception(err)
        return False

    # Update conf_devices devicename index dictionary
    if len(Gb.conf_devices) != len(Gb.conf_devices_idx_by_devicename):
        set_conf_devices_index_by_devicename()

    return success

#--------------------------------------------------------------------
async def async_write_icloud3_configuration_file(filename_suffix=None):
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
        log_debug_msg(f"Configuration File > Update Successful-{success}")

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
    while iCloud3 is running. This makes it easier logging into AppleAcct
    and in config_flow. Save it, then put the encoded password in the file
    update the file and then restore the real password
    '''
    Gb.conf_profile[CONF_UPDATE_DATE] = datetime_now()

    encode_all_passwords()

    Gb.conf_tracking[CONF_APPLE_ACCOUNTS] = Gb.conf_apple_accounts
    Gb.conf_tracking[CONF_DEVICES]        = Gb.conf_devices
    Gb.conf_data[CF_TRACKING]             = Gb.conf_tracking
    Gb.conf_data[CF_GENERAL]              = Gb.conf_general
    Gb.conf_data[CF_SENSORS]              = Gb.conf_sensors
    Gb.conf_data[CF_DEVICE_SENSORS]       = Gb.conf_device_sensors

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
    success = read_icloud3_configuration_file('_backup')

    if success:
        log_msg = ("Restore from backup configuration file was successful")
        _LOGGER.warning(log_msg)

        write_icloud3_configuration_file()

    else:
        _LOGGER.error(f"iCloud3{RARROW}Restore from backup configuration file failed")
        _LOGGER.error(f"iCloud3{RARROW}Recreating configuration file with default parameters-"
                        f"{Gb.icloud3_config_filename}")
        initialize_icloud3_configuration_file()

#--------------------------------------------------------------------
def initialize_icloud3_configuration_file():
    build_initial_config_file_structure()
    Gb.conf_file_data = CF_DEFAULT_IC3_CONF_FILE.copy()
    write_icloud3_configuration_file(new_file_flag=True)
    read_icloud3_configuration_file()

#--------------------------------------------------------------------
def _add_parms_and_check_config_file():

    try:
        #Add new parameters, check  parameter settings
        update_config_file_flag = False
        update_config_file_flag = _config_file_check_new_ic3_version() or update_config_file_flag
        update_config_file_flag = _delete_obsolete_parameters()        or update_config_file_flag
        update_config_file_flag = _update_profile()                    or update_config_file_flag
        update_config_file_flag = _update_sensors()                    or update_config_file_flag
        update_config_file_flag = _update_tracking_parameters()        or update_config_file_flag
        update_config_file_flag = _update_apple_acct_parameters()      or update_config_file_flag
        update_config_file_flag = _update_device_parameters()          or update_config_file_flag
        update_config_file_flag = _update_general_parameters()         or update_config_file_flag

        update_config_file_flag = _verify_general_parameter_values()   or update_config_file_flag
        update_config_file_flag = _verify_tracking_parameters_values() or update_config_file_flag
        update_config_file_flag = _verify_device_parameters_values()   or update_config_file_flag

        if update_config_file_flag:
            Gb.conf_profile[CONF_SENSORS_HASH] = ''
            write_icloud3_configuration_file()

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

#--------------------------------------------------------------------
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

    try:
        aa_idx = 0
        for conf_apple_acct in Gb.conf_apple_accounts:
            aa_idx += 1
            if conf_apple_acct[CONF_USERNAME] == '':
                continue

            add_log_file_filter(conf_apple_acct[CONF_USERNAME], f"**{aa_idx}**")
            add_log_file_filter(conf_apple_acct[CONF_USERNAME].upper(), f"**{aa_idx}**")
            add_log_file_filter(conf_apple_acct[CONF_PASSWORD])
            add_log_file_filter(decode_password(conf_apple_acct[CONF_PASSWORD]))

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
            |---sensor_groups
        |---device_sensors
            |---devices
                |----base
                |----from_zone

    '''

    Gb.conf_profile        = DEFAULT_PROFILE_CONF.copy()
    Gb.conf_tracking       = DEFAULT_TRACKING_CONF.copy()
    Gb.conf_apple_accounts = []
    Gb.conf_devices        = []
    Gb.conf_general        = DEFAULT_GENERAL_CONF.copy()
    Gb.conf_sensors        = DEFAULT_SENSORS_CONF.copy()
    Gb.conf_device_sensors = {}
    Gb.conf_file_data      = CF_DEFAULT_IC3_CONF_FILE.copy()

    Gb.conf_data[CF_TRACKING]       = Gb.conf_tracking
    Gb.conf_data[CF_GENERAL]        = Gb.conf_general
    Gb.conf_data[CF_SENSORS]        = Gb.conf_sensors
    Gb.conf_data[CF_DEVICE_SENSORS] = Gb.conf_device_sensors

    Gb.conf_file_data[CF_PROFILE]  = Gb.conf_profile
    Gb.conf_file_data[CF_DATA]     = Gb.conf_data

    # Verify general parameters and make any necessary corrections
    try:
        if Gb.country_code in ['cn', 'hk']:
            Gb.conf_tracking[CONF_SERVER_LOCATION_NEEDED] = True

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
            return (DEFAULT_APPLE_ACCOUNT_CONF.copy(), 0)

        # Get conf_apple_acct by it's index
        if type(idx_or_username) is int:
            if isbetween(idx_or_username, 0, len(Gb.conf_apple_accounts)-1):
                conf_apple_acct = Gb.conf_apple_accounts[idx_or_username].copy()
                conf_apple_acct[CONF_PASSWORD] = decode_password(conf_apple_acct[CONF_PASSWORD])
                return (conf_apple_acct, idx_or_username)

            else:
                return (DEFAULT_APPLE_ACCOUNT_CONF.copy(), -1)

        # Get conf_apple_acct by it's username
        elif type(idx_or_username) is str:
            if is_empty(Gb.conf_apple_accounts):
                return (DEFAULT_APPLE_ACCOUNT_CONF.copy(), -1)

            conf_apple_acct_idx = -1
            for conf_apple_acct in Gb.conf_apple_accounts:
                conf_apple_acct_idx += 1
                if conf_apple_acct[CONF_USERNAME] == idx_or_username:
                    conf_apple_acct[CONF_PASSWORD] = decode_password(conf_apple_acct[CONF_PASSWORD])
                    return (conf_apple_acct, conf_apple_acct_idx)

    except Exception as err:
        log_exception(err)
        pass

    return (DEFAULT_APPLE_ACCOUNT_CONF.copy(), 0)


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
#   CONFIGURE THE CONF_DEVICE_SENSORS DICTIONARY FRO CONF_SENSORS
#   HANDLE VARIOUS EXCLUDED SENSORS LIST TASKS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_build_conf_device_sensors_from_conf_sensors():

    rebuild_flag = build_conf_device_sensors_from_conf_sensors()
    if rebuild_flag is False:
        return

    await async_write_icloud3_configuration_file()

#--------------------------------------------------------------------
def build_conf_device_sensors_from_conf_sensors():

    if (CF_DEVICE_SENSORS not in Gb.conf_data
            or BASE in Gb.conf_device_sensors):
        Gb.conf_profile[CONF_SENSORS_HASH] = '*'

    conf_sensors_hash = get_string_hash(str(Gb.conf_sensors))
    if (Gb.conf_profile[CONF_SENSORS_HASH] == conf_sensors_hash
            and isnot_empty(Gb.conf_device_sensors)):
        return False

    validate_and_correct_excluded_sensors_list()

    Gb.conf_device_sensors = DEFAULT_DEVICE_SENSORS_CONF.copy()
    Gb.conf_device_sensors[TRACK]   = get_tracked_sensors_from_conf_sensors()
    Gb.conf_device_sensors[MONITOR] = get_monitored_sensors_from_conf_sensors()
    Gb.conf_device_sensors[CONF_TRACK_FROM_ZONES] = get_from_zone_sensors_from_conf_sensors()
    Gb.conf_device_sensors[CONF_EXCLUDED_SENSORS] = get_excluded_sensors()

    log_msg  = (f"Device Sensors List > Rebuilt:"
                f"{NLSP4}SENSORS:"
                f"{NLSP4}{Gb.conf_device_sensors}")
    log_info_msg(log_msg)

    # post_event('Sensors List > Sensor Change Detected, Base List Rebuilt')

    return True

#--------------------------------------------------------------------
def get_tracked_sensors_from_conf_sensors(sensors_list=None):
    '''
    Extract tracked sensors from configuration file
    '''
    try:
        if sensors_list is None:
            sensors_list = Gb.conf_sensors

        sensors = SENSOR_LIST_ALWAYS.copy()
        sensors_from_conf = []
        for sensor_group, sensor_list in sensors_list.items():
            if sensor_group not in CONF_NON_TRACKING_GROUPS:
                sensors_from_conf.extend(sensor_list)

        for sensor in sensors_from_conf:
            if sensor not in SENSOR_DEFINITION:
                continue

            if sensor in SENSOR_GROUPS:
                list_add(sensors, SENSOR_GROUPS[sensor])
            else:
                list_add(sensors, sensor)

        if 'last_zone' in sensors:
            if 'zone' not in sensors_list[ZONE]:   list_del(sensors, 'last_zone')
            if 'zone_name' in sensors_list[ZONE]:  list_add(sensors, 'last_zone_name')
            if 'zone_fname' in sensors_list[ZONE]: list_add(sensors, 'last_zone_fname')

        sensors.sort()

    except Exception as err:
        log_exception(err)

    return sensors

#--------------------------------------------------------------------
def get_monitored_sensors_from_conf_sensors():
    '''
    Extract monitored sensors from configuration file
    '''
    try:
        if is_empty(Gb.conf_sensors[CONF_SENSORS_MONITORED_DEVICES]):
            return []

        sensors = []
        for md_sensor in Gb.conf_sensors[CONF_SENSORS_MONITORED_DEVICES]:
            sensor = md_sensor[3:]

            if md_sensor in SENSOR_GROUPS:
                sensors.extend(SENSOR_GROUPS[md_sensor])
            elif sensor in SENSOR_DEFINITION:
                sensors.append(sensor)

        sensors = list(set(sensors))
        sensors.sort()

    except Exception as err:
        log_exception(err)

    return sensors

#--------------------------------------------------------------------
def get_from_zone_sensors_from_conf_sensors():
    '''
    Extract track_from_zone sensors from configuration file
    '''
    try:
        if is_empty(Gb.conf_sensors[CONF_SENSORS_TRACK_FROM_ZONES]):
            return []

        sensors = []
        for tfz_sensor in Gb.conf_sensors[CONF_SENSORS_TRACK_FROM_ZONES]:
            sensor = tfz_sensor[4:]

            if tfz_sensor in SENSOR_GROUPS:
                sensors.extend(SENSOR_GROUPS[tfz_sensor])
            elif sensor in SENSOR_DEFINITION:
                sensors.append(sensor)

        sensors = list(set(sensors))
        sensors.sort()

    except Exception as err:
        log_exception(err)

    return sensors

#--------------------------------------------------------------------
def get_disabled_sensors_list():
    er_util.scan_entity_reg_for_icloud3_items()
    if 'disabled' not in Gb.entity_reg_items_by_status:
        return []

    disabled_sensors = []
    for devicename, device_sensors in Gb.entity_reg_items_by_status['disabled'].items():
        for sensor, sensor_data_item in list(device_sensors.items()):
            list_add(disabled_sensors, sensor_data_item['entity_id'].split('.')[1])

    return disabled_sensors

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   EXCLUDED SENSORS LIST SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def get_excluded_sensors():
    '''
    Extract a list of devicename_sensors from the excluded sensors in
    Gb.conf_sensors[CONF_EXCLUDED_SENSORS]
    devicename_sensors

    "Gary-AirPods Battery (gary_airpods_battery)" --> gary_airpods_battery

    Return:
        - List of devicename_sensors from Gb.conf_sensors[CONF_EXCLUDED_SENSORS]
    '''
    if is_empty(Gb.conf_sensors[CONF_EXCLUDED_SENSORS]):
        return []

    devicename_sensors = []
    for fname_devicename_sensor in Gb.conf_sensors[CONF_EXCLUDED_SENSORS]:
        devicename_sensor = get_excluded_sensor_devicename_sensor(fname_devicename_sensor)
        list_add(devicename_sensors, devicename_sensor)

    return devicename_sensors

#-------------------------------------------------------------------------------------------
def get_excluded_sensor_devicename_sensor(fname_devicename_sensor):
    if instr(fname_devicename_sensor, '(') is False:
        devicename_sensor = fname_devicename_sensor

    else:
        devicename_sensor = fname_devicename_sensor.split('(')[1]
        devicename_sensor += ')'
        devicename_sensor = devicename_sensor.split(')')[0]
    return devicename_sensor

#-------------------------------------------------------------------------------------------
def rebuild_excluded_sensors_fname_sensors_list(devicename_sensors=None):
    '''
    Build the list of excluded sensors fname (devicename_sensor) from a list of
    devicename_sensors

    gary_airpods_battery --> "Gary-AirPods Battery (gary_airpods_battery)"

    Return:
        - List of fname_devicename_sensors for Gb.conf_sensors[CONF_EXCLUDED_SENSORS]
    '''
    if devicename_sensors is None:
        devicename_sensors = get_excluded_sensors()

    fnames_by_devicename = {conf_device[CONF_IC3_DEVICENAME]: conf_device[CONF_FNAME]
                                    for conf_device in Gb.conf_devices}

    fname_devicename_sensors = []
    excluded_list_changed = False
    for devicename_sensor in devicename_sensors:
        devicename, sensor = er_util.get_devicename_sensor_base(devicename_sensor)

        fname_devicename_sensor = (f"{fnames_by_devicename.get(devicename, devicename)} "
                                    f"{get_sensor_fname(sensor)} "
                                    f"({devicename_sensor})")
        list_add(fname_devicename_sensors, fname_devicename_sensor)

    if Gb.conf_sensors[CONF_EXCLUDED_SENSORS] != fname_devicename_sensors:
        excluded_list_changed = True
        Gb.conf_sensors[CONF_EXCLUDED_SENSORS] = fname_devicename_sensors
        Gb.conf_device_sensors[CONF_EXCLUDED_SENSORS] = devicename_sensors

    return excluded_list_changed

#.........................................................................................
def get_sensor_fname(sensor):
    try:
        return SENSOR_DEFINITION[sensor][SENSOR_FNAME]

    except:
        return sensor.replace('_', ' ').title()

#-------------------------------------------------------------------------------------------
def validate_and_correct_excluded_sensors_list():
    '''
    The excluded sensors list has the fname and the devicename_sensors to be excluded,
    i.e., fname_devicename_sensor = "Lillian-iPad BatteryStatus (lillian_ipad_battery_status)"

    Make sure that the devicename is still being tracked. If not, remove the item from the list.
    '''

    devicenames = [conf_device[CONF_IC3_DEVICENAME]
                        for conf_device in Gb.conf_devices]

    devicename_sensors = get_excluded_sensors()

    valid_devicename_sensors = []
    excluded_list_changed = False
    for devicename_sensor in devicename_sensors:
        devicename, sensor = er_util.get_devicename_sensor_base(devicename_sensor)
        if devicename in devicenames:
            list_add(valid_devicename_sensors, devicename_sensor)

    excluded_list_changed = rebuild_excluded_sensors_fname_sensors_list(valid_devicename_sensors)

    return excluded_list_changed



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Verify various configuration file parameters
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def _count_device_tracking_methods_configured():
    '''
    Count the number of devices that have been configured for the icloud,
    fmf and Mobile App tracking methods. This will be compared to the actual
    number of devices returned from iCloud during setup in AppleAcct. Sometmes,
    iCloud does not return all devices in the iCloud list and a refresh/retry
    is needed.
    '''
    try:
        Gb.conf_icloud_device_cnt = 0
        Gb.conf_mobapp_device_cnt = 0

        for conf_device in Gb.conf_devices:
            if conf_device[CONF_TRACKING_MODE] == INACTIVE:
                continue

            if conf_device[CONF_FAMSHR_DEVICENAME].startswith(NONE_FNAME) is False:
                Gb.conf_icloud_device_cnt += 1

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
def _verify_general_parameter_values():
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

        return update_configuration_flag

    except Exception as err:
        _LOGGER.exception(err)

#--------------------------------------------------------------------
def _verify_tracking_parameters_values():
    '''
    Cycle thru the conf_devices and verify that the settings are valid
    '''
    update_configuration_flag = False

    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'famshr'):
        Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace('famshr', ICLOUD)
        Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace('mobapp', MOBAPP)
        Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace(' ', '')
        update_configuration_flag = True

    return update_configuration_flag

#--------------------------------------------------------------------
def _verify_device_parameters_values():
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

        return update_configuration_flag

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
def _delete_obsolete_parameters():
    update_config_file_flag = False
    if 'external_ip_address' in Gb.conf_profile:
        Gb.conf_profile.pop('external_ip_address')
        update_config_file_flag = update_config_file_flag or True

    return update_config_file_flag

#--------------------------------------------------------------------
def _new_items_in_conf_dict(conf_item, default_conf_item):
    '''
    Cycle through the configuration dictionary and identify items that were
    added

    Return:
        item - Items that were added
        were_items_added - True/False
    '''
    new_items = [item   for item in default_conf_item
                        if item not in conf_item]

    return new_items, isnot_empty(new_items)


#--------------------------------------------------------------------
def _delete_items_from_conf_dict(conf_item, default_conf_item):
    '''
    Cycle through the configuration dictionary and identify items that are
    no longer being used.

    Return:
        conf_item - An updated conf_item
        were_items_deleted - True/False
    '''

    del_items = [item   for item in conf_item
                        if item not in default_conf_item]

    if is_empty(del_items):
        return conf_item, False

    for item in del_items:
        dict_del(conf_item, item)

    return conf_item, True

#--------------------------------------------------------------------
def _update_profile():
    '''
    Update Gb.conf_profile with new fields
    '''

    Gb.conf_profile, were_items_deleted = _delete_items_from_conf_dict(Gb.conf_profile, DEFAULT_PROFILE_CONF)
    new_items, were_items_added         = _new_items_in_conf_dict(Gb.conf_profile, DEFAULT_PROFILE_CONF)

    if were_items_deleted is False and were_items_added is False:
        return False

    log_info_msg(f"Updated Configuration File items (Profile)")

    for item in new_items:
        before_item = _place_item_before(item, DEFAULT_PROFILE_CONF, CONF_PICTURE_WWW_DIRS)

        Gb.conf_file_data[CF_PROFILE][item] = DEFAULT_PROFILE_CONF[item]
        Gb.conf_profile = _insert_into_conf_dict_parameter(
                                            Gb.conf_profile, item,
                                            DEFAULT_PROFILE_CONF[item],
                                            before= before_item)

    return True
#--------------------------------------------------------------------
def _update_sensors():
    '''
    Update Gb.conf_sensors with new fields
    '''

    Gb.conf_sensors, were_items_deleted = _delete_items_from_conf_dict(Gb.conf_sensors, DEFAULT_SENSORS_CONF)
    new_items, were_items_added         = _new_items_in_conf_dict(Gb.conf_sensors, DEFAULT_SENSORS_CONF)

    if were_items_deleted is False and were_items_added is False:
        return False

    log_info_msg(f"Updated Configuration File items (Sensors)")

    for item in new_items:
        before_item = _place_item_before(item, DEFAULT_SENSORS_CONF, CONF_EXCLUDED_SENSORS)

        Gb.conf_file_data[CF_SENSORS][item] = DEFAULT_SENSORS_CONF[item]
        Gb.conf_sensors = _insert_into_conf_dict_parameter(
                                            Gb.conf_sensors, item,
                                            DEFAULT_SENSORS_CONF[item],
                                            before= before_item)

    return True

#--------------------------------------------------------------------
def _update_device_sensors():
    '''
    Update Gb.conf_device_sensors with new fields
    '''
    if (CF_DEVICE_SENSORS not in Gb.conf_data
            or is_empty(Gb.conf_device_sensors)
            or CONF_EXCLUDED_SENSORS not in Gb.conf_device_sensors):
        Gb.conf_device_sensors = DEFAULT_DEVICE_SENSORS_CONF.copy()
        return True

    return False

#-------------------------------------------------------------------
def _update_tracking_parameters():
    '''
    Update Gb.conf_tracking with new fields
    '''
    Gb.conf_tracking, were_items_deleted = _delete_items_from_conf_dict(Gb.conf_tracking, DEFAULT_TRACKING_CONF)
    new_items, were_items_added          = _new_items_in_conf_dict(Gb.conf_tracking, DEFAULT_TRACKING_CONF)

    if were_items_deleted is False and were_items_added is False:
        return False

    log_info_msg(f"Updated Configuration File items (Tracking)")

    for item in new_items:
        Gb.conf_tracking = _insert_into_conf_dict_parameter(
                                    Gb.conf_tracking,
                                    item, DEFAULT_TRACKING_CONF[item],
                                    before=CONF_DEVICES)

    if (CONF_APPLE_ACCOUNTS in new_items
            and Gb.conf_tracking[CONF_USERNAME] != ''):
        conf_apple_acct = DEFAULT_APPLE_ACCOUNT_CONF.copy()
        conf_apple_acct[CONF_USERNAME] = Gb.conf_tracking[CONF_USERNAME]
        conf_apple_acct[CONF_PASSWORD] = Gb.conf_tracking[CONF_PASSWORD]
        Gb.conf_tracking[CONF_APPLE_ACCOUNTS] = Gb.conf_apple_accounts = [conf_apple_acct]

    return True

#--------------------------------------------------------------------
def _update_apple_acct_parameters():
    '''
    Update Gb.conf_apple_account with new fields
    '''

    cd_idx = -1
    conf_apple_accts = Gb.conf_apple_accounts.copy()
    for conf_apple_acct in conf_apple_accts:
        cd_idx += 1

        conf_apple_acct, were_items_deleted = _delete_items_from_conf_dict(conf_apple_acct, DEFAULT_APPLE_ACCOUNT_CONF)
        new_items, were_items_added         = _new_items_in_conf_dict(conf_apple_acct, DEFAULT_APPLE_ACCOUNT_CONF)

        if were_items_deleted is False and were_items_added is False:
            continue

        log_info_msg(f"Updated Configuration File items ({username_id(conf_apple_acct[CONF_USERNAME])})")

        for item in new_items:
            conf_apple_acct = _insert_into_conf_dict_parameter(
                                    conf_apple_acct, item,
                                    DEFAULT_APPLE_ACCOUNT_CONF[item],
                                    before=CONF_DATA_SOURCE)

        Gb.conf_apple_accounts[cd_idx] = conf_apple_acct

    return True

#--------------------------------------------------------------------
def _update_device_parameters():
    '''
    Update Gb.conf_device with new fields
    '''
    cd_idx = -1
    conf_devices = Gb.conf_devices.copy()
    for conf_device in conf_devices:
        cd_idx += 1

        conf_device, were_items_deleted = _delete_items_from_conf_dict(conf_device, DEFAULT_DEVICE_CONF)
        new_items, were_items_added     = _new_items_in_conf_dict(conf_device, DEFAULT_DEVICE_CONF)

        if were_items_deleted is False and were_items_added is False:
            continue

        log_info_msg(f"Updated Configuration File items ({conf_device[CONF_IC3_DEVICENAME]})")

        for item in new_items:
            # v3.1.0 'apple_account' and other fields
            if item == CONF_APPLE_ACCOUNT:
                conf_device = _v310_device_parameter_updates(conf_device)

            else:
                conf_device = _insert_into_conf_dict_parameter(
                                            conf_device, item,
                                            DEFAULT_DEVICE_CONF[item],
                                            before=CONF_TRACK_FROM_BASE_ZONE)

        Gb.conf_devices[cd_idx] = conf_device

    return True

#.....................................................................
def _v310_device_parameter_updates(conf_device):
    # v3.1 - Add Apple account parameter
    if CONF_APPLE_ACCOUNT not in conf_device:
        conf_device = _insert_into_conf_dict_parameter(
                                conf_device, CONF_APPLE_ACCOUNT,
                                Gb.conf_tracking[CONF_USERNAME],
                                before=CONF_FAMSHR_DEVICENAME)


    # v3.1 - Change Search: to ScanFor: in Mobile App parameter
    if conf_device[CONF_MOBILE_APP_DEVICE].startswith('Search:'):
        conf_device[CONF_MOBILE_APP_DEVICE] = \
                conf_device[CONF_MOBILE_APP_DEVICE].replace('Search:', 'ScanFor:')

    # v3.1 Remove unused parameters
    if 'evlog_display_order' in conf_device:
        conf_device.pop('evlog_display_order')
        conf_device.pop('unique_id')
    if 'old_devicename' in conf_device:
        conf_device.pop('old_devicename')

    return conf_device

#-------------------------------------------------------------------
def _update_general_parameters():
    '''
    Update Gb.conf_general with new fields
    '''

    Gb.conf_general, were_items_deleted = _delete_items_from_conf_dict(Gb.conf_general, DEFAULT_GENERAL_CONF)
    new_items, were_items_added         = _new_items_in_conf_dict(Gb.conf_general, DEFAULT_GENERAL_CONF)

    if were_items_deleted is False and were_items_added is False:
        return False

    log_info_msg(f"Updated Configuration File items (General)")

    for item in new_items:
        before_item = _place_item_before(item, DEFAULT_GENERAL_CONF, CONF_DISPLAY_TEXT_AS)

        Gb.conf_data[CF_GENERAL][item] = DEFAULT_GENERAL_CONF[item]
        Gb.conf_general = _insert_into_conf_dict_parameter(
                                            Gb.conf_general, item,
                                            DEFAULT_GENERAL_CONF[item],
                                            before= before_item)

    return True

#--------------------------------------------------------------------
def _place_item_before(item, conf_dict, default_item):
    # Cycle thru conf\dict (ex: DEFAULT_GENERAL_CONF) items and get the name of the next
    # item to place the new one in the same position

    before_item = default_item
    _item_found = False

    for _item in conf_dict:
        if _item_found:
            return _item

        if _item == item:
            _item_found = True

    return default_item


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
    log_info_msg(f" - Parameter-{new_item}, Initial Value-{initial_value}")

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
        # _LOGGER.exception(err)
        dict_parameter[new_item] = initial_value
        return dict_parameter


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Password encode/decode functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def encode_all_passwords():

    try:
        Gb.conf_tracking[CONF_PASSWORD] = encode_password(Gb.conf_tracking[CONF_PASSWORD])

        for apple_acct in Gb.conf_apple_accounts:
            apple_acct[CONF_PASSWORD] = encode_password(apple_acct[CONF_PASSWORD])
    except:
        pass

#--------------------------------------------------------------------
def decode_all_passwords():

    try:
        for apple_acct in Gb.conf_apple_accounts:
            Gb.AppleAcct_password_by_username[apple_acct[CONF_USERNAME]] = \
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
                or Gb.is_password_encoded is False
                or password.startswith('««')
                or password.endswith('»»')):
            return password
        elif password is None:
            return ''

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
        if (Gb.is_password_encoded
                and password != ''
                and (password.startswith('««') is False or password.endswith('»»') is False)):
            password = password.replace('«', '').replace('»', '')
            write_icloud3_configuration_file()

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