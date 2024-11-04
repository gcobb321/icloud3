

from ..global_variables     import GlobalVariables as Gb
from ..const                import (STORAGE_DIR,
                                    DISTANCE_TO_OTHER_DEVICES, DISTANCE_TO_OTHER_DEVICES_DATETIME,
                                    HHMMSS_ZERO, AWAY, AWAY_FROM, NOT_SET, NOT_HOME, STATIONARY, STATIONARY_FNAME, ALERT,
                                    ZONE, ZONE_DNAME, ZONE_FNAME, ZONE_NAME, ZONE_INFO,
                                    LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_FNAME, LAST_ZONE_NAME,
                                    DIR_OF_TRAVEL, )

from ..helpers.common       import (instr, )
from ..helpers.messaging    import (log_info_msg, log_debug_msg, log_exception, post_evlog_greenbar_msg,
                                    _evlog, _log, )
from ..helpers.time_util    import (datetime_now, secs_to_datetime, )
from ..helpers.file_io      import (file_exists, async_read_json_file, )

# import os
import json
import logging
# import asyncio
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(f"icloud3")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   .STORAGE/ICLOUD3.RESTORE_STATE FILE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def check_hacs_icloud3_update_available():

    if Gb.version_hacs == '0.0.0':
        return

    hacs_repository_file = Gb.hass.config.path(STORAGE_DIR, 'hacs.repositories')
    if file_exists(hacs_repository_file) is False:
        return None

    try:
        hacs_ic3_items  = await _async_get_hacs_ic3_data(hacs_repository_file)
        version_hacs_ic3_dev = None
        version_hacs_ic3     = None
        Gb.version_hacs      =  ''

        if 'icloud3_v3' in hacs_ic3_items:
            version_hacs_ic3_dev = hacs_ic3_items['icloud3_v3'].get('last_version')
        if 'icloud3' in hacs_ic3_items:
            version_hacs_ic3 = hacs_ic3_items['icloud3'].get('last_version')

        ic3_dev_newer_running =_is_hacs_version_newer(Gb.version, version_hacs_ic3_dev)
        ic3_newer_running     =_is_hacs_version_newer(Gb.version, version_hacs_ic3)
        dev_newer_ic3         =_is_hacs_version_newer(version_hacs_ic3, version_hacs_ic3_dev)

        if ic3_dev_newer_running:
            Gb.version_hacs = version_hacs_ic3_dev
        elif ic3_newer_running:
            Gb.version_hacs = version_hacs_ic3

    except Exception as err:
        Gb.version_hacs = ''

    return None

#-------------------------------------------------------------------------------------------
async def _async_get_hacs_ic3_data(hacs_repository_file):
    '''
    Read the config/.storage/.icloud3.restore_state file.
        - Extract the data into the Global Variables.
        - Restore each device's sensors values
        - Reinitialize sensors that should not be restored
    '''

    try:
        hacs_repository_file_data = await async_read_json_file(hacs_repository_file)

        if hacs_repository_file_data != {}:
            hacs_ic3_items = {hacs_item_data['full_name'].split('/')[1].replace(' ', '_'): hacs_item_data
                                for hacs_id, hacs_item_data in hacs_repository_file_data['data'].items()
                                if hacs_item_data['full_name'].startswith('gcobb321/icloud3')}

    except json.decoder.JSONDecodeError:
        return {}
    except Exception as err:
        log_exception(err)
        return {}

    return hacs_ic3_items

#--------------------------------------------------------------------
def _is_hacs_version_newer(version_1, version_2):
    '''
    Compare the version_1 and _2 values for the newest one.
    Return:
        True - version_2 is newer than version_1
        False - version_1 is newer than version_2

    version_2   version_1   Result
    v3.0.3      v3.0.2      True
    v3.0.3      v3.0.3      False
    v3.0.3      v3.0.3b1    True
    v3.0a       v3.0.3      False
    v3.0.3.1    v3.0.3      True
    '''

    if version_1 is None or version_2 is None:
        return False

    v1_value, v1_beta  = _get_version_value(version_1)
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
