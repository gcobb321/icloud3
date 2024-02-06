

from ..global_variables     import GlobalVariables as Gb
from ..const                import (RESTORE_STATE_FILE,
                                    DISTANCE_TO_OTHER_DEVICES, DISTANCE_TO_OTHER_DEVICES_DATETIME,
                                    HHMMSS_ZERO, AWAY, AWAY_FROM, NOT_SET, NOT_HOME, STATIONARY, STATIONARY_FNAME,
                                    ZONE, ZONE_DNAME, ZONE_FNAME, ZONE_NAME, ZONE_INFO,
                                    LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_FNAME, LAST_ZONE_NAME,
                                    DIR_OF_TRAVEL, )

from ..helpers.common       import (instr, )
from ..helpers.messaging    import (log_info_msg, log_debug_msg, log_exception, _trace, _traceha, )
from ..helpers.time_util    import (datetime_now, )

import os
import json
import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   .STORAGE/ICLOUD3.RESTORE_STATE FILE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def load_storage_icloud3_restore_state_file():

    try:
        if os.path.exists(Gb.icloud3_restore_state_filename) is False:
            build_initial_restore_state_file_structure()
            write_storage_icloud3_restore_state_file()

        success = read_storage_icloud3_restore_state_file()

        if success is False:
            log_info_msg(f"Invalid icloud3.restore_state File-{Gb.icloud3_restore_state_filename}")
            build_initial_restore_state_file_structure()
            write_storage_icloud3_restore_state_file()
            read_storage_icloud3_restore_state_file()

        return

    except Exception as err:
        log_exception(err)
        build_initial_restore_state_file_structure()
        write_storage_icloud3_restore_state_file()
        read_storage_icloud3_restore_state_file()

#--------------------------------------------------------------------
def build_initial_restore_state_file_structure():
    '''
    Create the initial data structure of the ic3 config file

    |---profile
    |---devices
        |---sensors
            |---actual sensor names & values
        |---from_zone
            |---home
                |---actual sensor names & values
            |---warehouse
                |---actual sensor names & values
        .
        .
        .
    '''

    log_info_msg(f"Creating iCloud3 Restore State File - {Gb.icloud3_restore_state_filename}")
    Gb.restore_state_file_data = RESTORE_STATE_FILE.copy()
    Gb.restore_state_profile = Gb.restore_state_file_data['profile']
    Gb.restore_state_devices = Gb.restore_state_file_data['devices']

#-------------------------------------------------------------------------------------------
def clear_devices():
    Gb.restore_state_devices = {}

#-------------------------------------------------------------------------------------------
def read_storage_icloud3_restore_state_file():
    '''
    Read the config/.storage/.icloud3.restore_state file and extract the
    data into the Global Variables
    '''

    try:
        with open(Gb.icloud3_restore_state_filename, 'r') as f:
            Gb.restore_state_file_data = json.load(f)
            Gb.restore_state_profile   = Gb.restore_state_file_data['profile']
            Gb.restore_state_devices   = Gb.restore_state_file_data['devices']

            for devicename, devicename_data in Gb.restore_state_devices.items():
                sensors = devicename_data['sensors']
                sensors[DISTANCE_TO_OTHER_DEVICES] = {}
                sensors[DISTANCE_TO_OTHER_DEVICES_DATETIME] = HHMMSS_ZERO

                _reset_statzone_values_to_away(sensors)

                from_zones = devicename_data['from_zone']
                for from_zone, from_zone_sensors in from_zones.items():
                    _reset_from_zone_statzone_values_to_away(from_zone_sensors)

        return True

    except json.decoder.JSONDecodeError:
        pass
    except Exception as err:
        log_exception(err)
        return False

    return False

#--------------------------------------------------------------------
def write_storage_icloud3_restore_state_file():
    '''
    Update the config/.storage/.icloud3.restore_state file
    '''

    try:
        with open(Gb.icloud3_restore_state_filename, 'w', encoding='utf8') as f:
            Gb.restore_state_profile['last_update'] = datetime_now()
            Gb.restore_state_file_data['profile'] = Gb.restore_state_profile
            Gb.restore_state_file_data['devices'] = Gb.restore_state_devices

            json.dump(Gb.restore_state_file_data, f, indent=4)

        return True

    except Exception as err:
        log_exception(err)

    return False

#--------------------------------------------------------------------
def _reset_statzone_values_to_away(sensors):
    '''
    Sensors with a StatZone value needs to be set to Away since the StatZone is
    not restored on an HA restart. The data structure is:

    "sensors": {
        "zone": "ic3_stationary_1",
        "zone_display_as": "StatZon1",
        "zone_fname": "StatZon1",
        "zone_name": "Ic3Stationary1",
        "last_zone": "ic3_statzone_2",
        "last_zone_display_as": "StatZon2",
        "last_zone_fname": "StatZon2",
        "last_zone_name": "Ic3Statzone2",
        "dir_of_travel": "@StatZon1",
    }
    '''
    statzone_fname = Gb.statzone_fname.replace('#', '')

    _reset_sensor_value(sensors, ZONE, "ic3_stationary_", NOT_HOME)
    _reset_sensor_value(sensors, ZONE_DNAME, statzone_fname, AWAY)
    _reset_sensor_value(sensors, ZONE_FNAME, statzone_fname, AWAY)
    _reset_sensor_value(sensors, ZONE_NAME, "Ic3Stationary", AWAY)
    _reset_sensor_value(sensors, LAST_ZONE, "ic3_stationary_", NOT_SET)
    _reset_sensor_value(sensors, LAST_ZONE_DNAME, statzone_fname, NOT_SET)
    _reset_sensor_value(sensors, LAST_ZONE_FNAME, statzone_fname, NOT_SET)
    _reset_sensor_value(sensors, LAST_ZONE_NAME, "Ic3Stationary", NOT_SET)
    _reset_sensor_value(sensors, DIR_OF_TRAVEL, f"@{statzone_fname}", AWAY)
    _reset_sensor_value(sensors, DIR_OF_TRAVEL, STATIONARY, AWAY)
    _reset_sensor_value(sensors, DIR_OF_TRAVEL, STATIONARY_FNAME, AWAY)

#--------------------------------------------------------------------
def _reset_from_zone_statzone_values_to_away(sensors):
    '''
    Sensors with a StatZone value needs to be set to Away since the StatZone is
    not restored on an HA restart. The data structure is:

    "from_zone": {
        "zone_name_1": {
            "dir_of_travel": "Stationary",
            "zone_info": "@StatZon1"
        },
        "zone_name_2": {
            "dir_of_travel": "Stationary",
            "zone_info": "@StatZon1"
        }
    }
    '''
    statzone_fname = Gb.statzone_fname.replace('#', '')

    _reset_sensor_value(sensors, ZONE_INFO, f"@{statzone_fname}", NOT_SET)
    _reset_sensor_value(sensors, DIR_OF_TRAVEL, f"@{statzone_fname}", AWAY)
    _reset_sensor_value(sensors, DIR_OF_TRAVEL, STATIONARY, AWAY)
    _reset_sensor_value(sensors, DIR_OF_TRAVEL, STATIONARY_FNAME, AWAY)

#--------------------------------------------------------------------
def _reset_sensor_value(sensors, sensor, statzone_value, initial_value):

    try:
        if sensor in sensors and instr(sensors[sensor], statzone_value):
            sensors[sensor] = initial_value

    except Exception as err:
        #log_exception(err)
        pass
