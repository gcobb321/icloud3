

from ..global_variables     import GlobalVariables as Gb
from ..const                import (RESTORE_STATE_FILE,
                                    DISTANCE_TO_OTHER_DEVICES, DISTANCE_TO_OTHER_DEVICES_DATETIME,
                                    HHMMSS_ZERO, AWAY, AWAY_FROM, NOT_SET, NOT_HOME, STATIONARY, STATIONARY_FNAME, ALERT,
                                    ZONE, ZONE_DNAME, ZONE_FNAME, ZONE_NAME, ZONE_INFO,
                                    LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_FNAME, LAST_ZONE_NAME,
                                    DIR_OF_TRAVEL, )

from ..utils.utils        import (instr, )
from ..utils.file_io      import (file_exists, read_json_file, save_json_file, async_save_json_file, )
from ..utils.messaging    import (log_info_msg, log_debug_msg, log_exception, _evlog, _log, )
from ..utils.time_util    import (datetime_now, time_now_secs, utcnow, s2t, datetime_plus, )

import json
import logging

from homeassistant.core             import (callback, )
from homeassistant.helpers.event    import (async_track_point_in_time, )
import homeassistant.util.dt    as dt_util
from datetime                   import datetime, timedelta, timezone

# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   .STORAGE/ICLOUD3.RESTORE_STATE FILE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def load_icloud3_restore_state_file():

    try:
        if file_exists(Gb.icloud3_restore_state_filename) is False:
            build_initial_restore_state_file_structure()
            write_icloud3_restore_state_file()

        success = read_icloud3_restore_state_file()

        if success is False:
            log_info_msg(f"Invalid icloud3.restore_state File-{Gb.icloud3_restore_state_filename}")
            build_initial_restore_state_file_structure()
            write_icloud3_restore_state_file()
            read_icloud3_restore_state_file()

        return

    except Exception as err:
        log_exception(err)
        build_initial_restore_state_file_structure()
        write_icloud3_restore_state_file()
        read_icloud3_restore_state_file()

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
def read_icloud3_restore_state_file():
    '''
    Read the config/.storage/.icloud3.restore_state file.
        - Extract the data into the Global Variables.
        - Restoreeach device's sensors values
        - Reinitialize sensors that should not be restored
    '''

    try:
        Gb.restore_state_file_data = read_json_file(Gb.icloud3_restore_state_filename)

        if Gb.restore_state_file_data == {}:
            return False

        Gb.restore_state_profile   = Gb.restore_state_file_data['profile']
        Gb.restore_state_devices   = Gb.restore_state_file_data['devices']

        # The sensors here are used in sensor.py to set the device's last sensor state values when
        # the sensors are being set up. They are not related to the Device.sensors{} and the
        # Device.sensors{} are not loaded here. The Device.sensors{} are loaded in the
        # Device._restore_sensors_from_restore_state_file() function when the Device object is created.
        for devicename, devicename_data in Gb.restore_state_devices.items():
            sensors = devicename_data['sensors']
            sensors[DISTANCE_TO_OTHER_DEVICES] = {}
            sensors[DISTANCE_TO_OTHER_DEVICES_DATETIME] = HHMMSS_ZERO
            sensors[ALERT] = ''

            _reset_statzone_values_to_away(sensors)

            from_zones = devicename_data['from_zone']
            for from_zone, from_zone_sensors in from_zones.items():
                _reset_from_zone_statzone_values_to_away(from_zone_sensors)

        return True

    except Exception as err:
        log_exception(err)
        return False

    return False

#--------------------------------------------------------------------
def write_icloud3_restore_state_file():
    '''
    Update the config/.storage/.icloud3.restore_state file when the sensors for
    a device have changed. Since the multiple sensors are updated on one tracking
    update, the update to the restore file is done on a 10-sec delay to catch
    other sensors that have been changed.

    The changes are committed based on the 10-sec timer event being fired in a
    callback function.
    '''

    Gb.restore_state_profile['last_update'] = datetime_now()
    Gb.restore_state_file_data['profile'] = Gb.restore_state_profile
    Gb.restore_state_file_data['devices'] = Gb.restore_state_devices

    Gb.restore_state_commit_cnt += 1
    if Gb.restore_state_commit_time == 0:
        Gb.restore_state_commit_time = time_now_secs() + 10
        Gb.restore_state_commit_cnt  = 0

        async_track_point_in_time(Gb.hass,
                            _async_commit_icloud3_restore_state_file_changes,
                            datetime_plus(utcnow(), secs=10))

#--------------------------------------------------------------------
@callback
async def _async_commit_icloud3_restore_state_file_changes(callback_datetime_struct):
    try:
        Gb.restore_state_profile['last_commit'] = datetime_now()
        Gb.restore_state_profile['recds_changed']  = Gb.restore_state_commit_cnt

        success = await async_save_json_file(Gb.icloud3_restore_state_filename, Gb.restore_state_file_data)

        Gb.restore_state_commit_time = 0
        Gb.restore_state_commit_cnt  = 0
        return success

    except Exception as err:
        log_exception(err)

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
