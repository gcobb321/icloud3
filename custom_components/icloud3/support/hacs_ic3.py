

from ..global_variables     import GlobalVariables as Gb
from ..const                import (STORAGE_DIR, EVLOG_ALERT,
                                    DISTANCE_TO_OTHER_DEVICES, DISTANCE_TO_OTHER_DEVICES_DATETIME,
                                    HHMMSS_ZERO, AWAY, AWAY_FROM, NOT_SET, NOT_HOME, STATIONARY, STATIONARY_FNAME, ALERT,
                                    ZONE, ZONE_DNAME, ZONE_FNAME, ZONE_NAME, ZONE_INFO,
                                    LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_FNAME, LAST_ZONE_NAME,
                                    DIR_OF_TRAVEL, )

from ..helpers.common       import (instr, is_empty, isnot_empty, )
from ..helpers.messaging    import (log_info_msg, log_debug_msg, log_exception,
                                    post_event, post_evlog_greenbar_msg,
                                    _evlog, _log, )
from ..helpers.time_util    import (datetime_now, secs_to_datetime, )
from ..helpers.file_io      import (file_exists, async_read_json_file, )
from ..helpers              import entity_io

# import os
import json
import logging
# import asyncio
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

HACS_FNAME_ICLOUD3     = 'update.icloud3_device_tracker_update'
HACS_FNAME_ICLOUD3_DEV = 'update.icloud3_v3_development_version_update'


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   .STORAGE/ICLOUD3.RESTORE_STATE FILE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def check_hacs_icloud3_update_available(event_time):

    if Gb.version_hacs == '0.0.0':
        return

    hacs_repository_file = Gb.hass.config.path(STORAGE_DIR, 'hacs.repositories')
    if file_exists(hacs_repository_file) is False:
        return None

    try:
        hacs_ic3_items  = await _async_get_hacs_ic3_data(hacs_repository_file)
        Gb.version_hacs = None

        version_hacs_ic3    = hacs_ic3_items.get('icloud3')
        version_hacs_ic3dev = hacs_ic3_items.get('icloud3_v3')

        hacs_ic3_newer    =_is_2nd_version_newer(Gb.version, version_hacs_ic3)
        hacs_ic3dev_newer =_is_2nd_version_newer(Gb.version, version_hacs_ic3dev)
        dev_newer_ic3     =_is_2nd_version_newer(version_hacs_ic3, version_hacs_ic3dev)

        hacs_ic3_newer_msg    = ' (Newer)' if hacs_ic3_newer else ''
        hacs_ic3dev_newer_msg = ' (Newer)' if hacs_ic3dev_newer else ''

        if hacs_ic3dev_newer:
            Gb.version_hacs = f"{version_hacs_ic3dev}"
        elif hacs_ic3_newer:
            Gb.version_hacs = version_hacs_ic3

        hacs_update_avail_msg = f", Hacs Update Available-{Gb.version_hacs}" if Gb.version_hacs else ""

        log_info_msg(   f"Checking HACS for new iCloud3 Version, "
                        f"{hacs_update_avail_msg}"
                        f"Running-{Gb.version}, "
                        f"HACS/iCloud3-{version_hacs_ic3}{hacs_ic3_newer_msg}, "
                        f"HACS/iCloud3_Dev-{version_hacs_ic3dev}{hacs_ic3dev_newer_msg}")

    except Exception as err:
        log_exception(err)
        Gb.version_hacs = ''

    return None

#-------------------------------------------------------------------------------------------
async def _async_get_hacs_ic3_data(hacs_repository_file):
    '''
    Read the config/.storage/.icloud3.restore_state file.
        - Extract the data into the Global Variables.
        - Restore each device's sensors values
        - Reinitialize sensors that should not be restored

    Return the HACS version:
        - hacs_ic3_items={'icloud3': 'v3.1.4.1', 'icloud3_v3': 'v3.1.4.1'}
        - hacs_ic3_items={'icloud3': 'v3.1.4.1'}
        - hacs_ic3_items={}
    '''
    # update_ic3_attrs    = entity_io.get_attributes(HACS_FNAME_ICLOUD3)
    # update_ic3dev_attrs = entity_io.get_attributes(HACS_FNAME_ICLOUD3_DEV)

    # if isnot_empty(update_ic3_attrs) or isnot_empty(update_ic3dev_attrs):
    #     return {'icloud3': update_ic3_attrs.get('latest_version'),
    #             'icloud3_v3': update_ic3dev_attrs.get('latest_version')}

    try:
        hacs_repository_file_data = await async_read_json_file(hacs_repository_file)

        if hacs_repository_file_data != {}:
            hacs_ic3_items = {_component_name(hacs_item_data):
                                    hacs_item_data.get('last_version')
                                for hacs_id, hacs_item_data in hacs_repository_file_data['data'].items()
                                if hacs_item_data['full_name'].startswith('gcobb321/icloud3')}

            return hacs_ic3_items

    except Exception as err:
        # log_exception(err)
        pass
        
    return {}

#...................................................................
def _component_name(hacs_item_data):
    try:
        return hacs_item_data['full_name'].split('/')[1].replace(' ', '_')
    except:
        return 'unknown'

#--------------------------------------------------------------------
def _is_2nd_version_newer(version_1, version_2):
    '''
    Compare the version_1 and _2 values for the newest one.
    Return:
        True - version_2 is newer than version_1
        False - version_1 is newer than version_2

    version_1   version_2   Result
    v3.0.2      v3.0.23      True
    v3.0.3      v3.0.3       False
    v3.0.3b1    v3.0.3       True
    v3.0.3      v3.0a        False
    v3.0.4      v3.0.3.1     True
    '''

    if version_1 is None or version_2 is None:
        return False

    v1_value, v1_beta = _get_version_value(version_1)
    v2_value, v2_beta = _get_version_value(version_2)

    # version_2 is newer
    if  (v2_value > v1_value):
        return True

    # version_2 is the same as version_1 but not beta or beta is newer
    elif v2_value == v1_value:
        if ((v2_beta == 0 and v1_beta > 0)
                or v2_beta > v1_beta):
            return True

    return False

#--------------------------------------------------------------------
def _get_version_value(version):

    version = version.replace('v', '')
    if instr(version, 'b') is False: version += 'b0'
    v_base, v_beta = version.split('b')
    v_parts = (f"{v_base}.0.0.0").split('.')
    v_value = 0

    try:
        v_beta   = int(v_beta)
        v_value += int(v_parts[0])*100000
        v_value += int(v_parts[1])*1000
        v_value += int(v_parts[2])*10
        v_value += int(v_parts[3])
    except:
        pass

    return v_value, v_beta
