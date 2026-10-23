"""iCloud3 log file handling, split out of utils/messaging.py.

messaging.py re-exports these names, so existing callers keep importing them
from .utils.messaging. The messaging helpers used at call time (Gb,
format_startup_header_box, log_exception, ...) are imported inside each
function to keep the module import acyclic.
"""

import logging
import os
import time

from ..const import (CONF_FNAME, CONF_IC3_DEVICENAME, CONF_USERNAME,
                     DASH_50, DOMAIN, EVLOG_ALERT, IC3LOG_FILENAME, ICLOUD3,
                     NL4, NLSP4)


def open_ic3log_file(new_log_file=False):

    # Items will be logged to home-assistane.log until the configuration file has been read
    # if is_empty(Gb.conf_general):
    #     return

    from ..global_variables import GlobalVariables as Gb
    from .messaging       import LoggerFilter, log_exception
    from .utils           import is_empty, isnot_empty

    try:
        ic3logger_file = Gb.hass.config.path(IC3LOG_FILENAME)
        filemode = 'w' if new_log_file else 'a'
        filemode = 'a' if Gb.was_icloud3_reloaded else filemode


        if Gb.iC3Logger is None or new_log_file:
            Gb.iC3Logger = logging.getLogger(DOMAIN)
            Gb.iC3Logger.setLevel(logging.INFO)

            # Reopening the file must replace the previous handler. Adding a
            # second FileHandler writes every line twice and leaks a file
            # descriptor until HA restarts. Only remove the handler this module
            # created; a user-configured handler on the same logger stays.
            for old_handler in list(Gb.iC3Logger.handlers):
                if getattr(old_handler, 'ic3_log_handler', False):
                    Gb.iC3Logger.removeHandler(old_handler)
                    old_handler.close()

            handler   = logging.FileHandler(ic3logger_file, mode=filemode, encoding='utf-8')
            handler.ic3_log_handler = True
            formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            handler.addFilter(LoggerFilter)

            Gb.iC3Logger.addHandler(handler)

        if isnot_empty(Gb.conf_general):
            Gb.iC3Logger.propagate = False

        if is_empty(Gb.conf_general):
            write_ic3log_recd(f"Loading {Gb.icloud3_version_msg}")

        write_ic3log_recd(f"Open iCloud3 Log File ({IC3LOG_FILENAME})")

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def close_ic3log_file():

    from ..global_variables import GlobalVariables as Gb

    if Gb.iC3Logger:
        write_ic3log_recd(f"Close iCloud3 Log File  ({IC3LOG_FILENAME})")
        for handler in list(Gb.iC3Logger.handlers):
            if getattr(handler, 'ic3_log_handler', False):
                Gb.iC3Logger.removeHandler(handler)
                handler.close()
        Gb.iC3Logger = None

#--------------------------------------------------------------------
def write_ic3log_recd(log_msg):
    '''
    Check to make sure the icloud3.log file exists if the last write to it
    was more than 2-secs ago. Recreate it if it does not. This catches deletes
    and renames while iCloud3 is running
    '''
    from ..global_variables import GlobalVariables as Gb

    try:
        if Gb.iC3Logger is None:
            return

        time_now_msecs = time.time()
        if time_now_msecs - Gb.iC3Logger_last_check_exist_secs > 2:
            Gb.iC3Logger_last_check_exist_secs = time_now_msecs

            check_ic3log_file_exists(Gb.hass.config.path(IC3LOG_FILENAME))

        if Gb.iC3Logger:
            Gb.iC3Logger.info(log_msg)
        else:
            open_ic3log_file(new_log_file=True)

            Gb.iC3Logger.info(log_msg)

    except Exception as err:
        return False

#--------------------------------------------------------------------
def check_ic3log_file_exists(ic3logger_file):
    '''
    See if the icloud3-0.log file exists. Recreate it if it does not. This
    catches deletes and renames while iCloud3 is running
    '''
    from ..global_variables import GlobalVariables as Gb
    from .messaging       import format_startup_header_box, log_exception_HA

    try:
        if Gb.iC3Logger is None:
            open_ic3log_file(new_log_file=True)

        elif Gb.iC3Logger and os.path.isfile(ic3logger_file) is False:
            open_ic3log_file(new_log_file=True)

            log_msg = f"{EVLOG_ALERT}Recreated iCloud3 Log File: {ic3logger_file}"
            log_msg = f"{format_startup_header_box(log_msg, 20)}"
            log_msg = log_msg.replace('⡇', '⛔')
            Gb.iC3Logger.info(log_msg)

        return True

    except IndexError:
        pass
    except Exception as err:
        log_exception_HA(err)

    return False

#--------------------------------------------------------------------
def archive_ic3log_file():
    '''
    At midnight, archive the log files and create a new one for the current day
    Remove icloud-2.log,
    rename icloud3-1.log to icloud3_2.log,
    rename icloud3-0.log to icloud3-1.log

    CAN NOT USE FILE_IO ROUTINES BECAUSE OF IMPORT ERRORS
    '''
    from ..global_variables import GlobalVariables as Gb
    from .messaging       import post_event

    try:
        log_file_0 = Gb.hass.config.path(IC3LOG_FILENAME)
        log_file_1 = f"{Gb.hass.config.path(IC3LOG_FILENAME)}-1.log"
        log_file_2 = f"{Gb.hass.config.path(IC3LOG_FILENAME)}-2.log"

        post_event(f"{ICLOUD3} Log File Archived")

        if os.path.isfile(log_file_2): os.remove(log_file_2)
        if os.path.isfile(log_file_1): os.rename(log_file_1, log_file_2)

        if os.path.isfile(log_file_0):
            close_ic3log_file()
            os.rename(log_file_0, log_file_1)

        open_ic3log_file(new_log_file=True)

        # Delete log files with old name
        try:
            os.remove(f"{Gb.hass.config.path(IC3LOG_FILENAME)}.1")
            os.remove(f"{Gb.hass.config.path(IC3LOG_FILENAME)}.2")
        except Exception as err:
            pass

    except Exception as err:
        post_event(f"{ICLOUD3} Log File Archive encountered an error > {err}")

#------------------------------------------------------------------------------
def write_config_file_to_ic3log():

    from ..global_variables import GlobalVariables as Gb
    from .messaging       import SP, log_info_msg

    if Gb.prestartup_log:
        write_ic3log_recd(f"{Gb.prestartup_log}")
        Gb.prestartup_log = ''

    _conf_tracking = Gb.conf_tracking.copy()
    _conf_tracking.pop('devices', None)
    _conf_tracking.pop('apple_accounts', None)

    Gb.trace_prefix = '_INIT_'
    indent = SP(37) if Gb.is_log_level_debug else SP(18)
    log_msg = ( f"iCloud3 Configuration File, {Gb.icloud3_version_msg}")
    log_msg = ( f"{NL4}⛔{DASH_50}{DASH_50}"
                f"{NL4}⛔    {log_msg}"
                f"{NL4}⛔{DASH_50}{DASH_50}")

    # Gb.iC3Logger.info(log_msg)

    # Write the ic3 configuration (general & devices) to the Log file
    log_msg  += (f""
                f"{NLSP4}PROFILE:"
                f"{NLSP4}{Gb.conf_profile}"
                f"{NLSP4}TRACKING:"
                f"{NLSP4}{_conf_tracking}"
                f"{NLSP4}GENERAL CONFIGURAION:"
                f"{NLSP4}{Gb.conf_general}"
                f"{NLSP4}{Gb.ha_location_info}"
                f"{NLSP4}SENSORS:"
                f"{NLSP4}{Gb.conf_sensors}"
                f"{NLSP4}DEVICE SENSORS:"
                f"{NLSP4}{Gb.conf_device_sensors}")

    for conf_apple_accounts in Gb.conf_apple_accounts:
        log_msg += (f"{NLSP4}APPLE ACCOUNT: {conf_apple_accounts.get(CONF_USERNAME)}:"
                    f"{NLSP4}{conf_apple_accounts}")

    for conf_device in Gb.conf_devices:
        log_msg += (f"{NLSP4}DEVICE: {conf_device[CONF_IC3_DEVICENAME]}, {conf_device[CONF_FNAME]}:"
                    f"{NLSP4}{conf_device}")
    log_msg += f"{NLSP4}{DASH_50}{DASH_50}"
    log_info_msg(log_msg)
