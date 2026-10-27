'''
Define global variables used to enable testing iCloud3 functions

from ..support              import test_controls as TEST

Add a new test control to test_controls_enabled_msg at the end of this module so
it is listed in the Event Log greenbar when it is enabled.
'''
from ..const_char import (RED_ALERT, CRLF_DOT, )

DISABLE_UPW_FILTER = False # Disable filtering passwords in the icloud3.log file
HWKEY_AUTH_ENABLED = True
COUNT_LINES_OF_CODE = False

#--------------------------------------------------------------------
# INTERNET ERROR
#
# This variable provides a mechanism of testing Internet Connection Errors when iCloud3 is
# starting without an actual error.
# Setting to True will raise an ConnectionError error in 'icloud_requests'
# that sets Gb.internet_error to True. Then in the 'icloud3_main' 5-sec loop, the Gb.internet_error
# flag is tested and then calls the start_internet_error_handler function
# below that handles internet errors.
INTERNET_ERROR = False
INTERNET_ERROR_COUNTER = 2

# This variable provides a mechanism of testing Internet Connection Errors after iCloud3 has
# starting without an actual error.
# Set this to True, then select 'EvLog > Actions > Locate All Devices using iCloud'. This will set the
# 'internet_error_test' to True and set this variable to False. A Locate will then be issued
# and caught as described above.
INTERNET_ERROR_AFTER_STARTUP = False

#--------------------------------------------------------------------
# NEWER APPLE DEVICE DETECTED
#
# Add copies of a real device to the Apple data with another name and
# device_id to test replacement device detection. None=Off
#
#   NEWER_DEV_EXISTING_DEVICE_NAME     - Name of a REAL Apple device to copy (the tracked device)
#   NEWER_DEV_SIMULATED_NEW_DEVICE_NAME - Name of the copy, a list adds a copy for each name.
#                               The name must reduce to the tracked device's name key
#                               (device_name_parser.name_device_type_key) to be a
#                               name match, "Lillian-Watch" -> lillian-watch
#   NEWER_DEV_SIMULATED_NEW_RAW_MODEL   - rawDeviceModel of the copies. A copy is only a candidate
#                               if its model number is higher than the tracked device's
#                               (Watch8,4 -> 8). None=Same model as the device, never
#                               a candidate.
#       1 name               - device_replaced (Submit tracks the copy)
#       2 or more names      - device_replaced_multiple

NEWER_DEV_EXISTING_DEVICE_NAME        = None                     # Disable duplicate device test
# NEWER_DEV_EXISTING_DEVICE_NAME        = "Lillian's Apple Watch"    # Real device to copy
# NEWER_DEV_SIMULATED_NEW_DEVICE_NAME   = "Lillian-Watch (Test)"     # device_replaced
# NEWER_DEV_SIMULATED_NEW_DEVICE_NAME = [
#         "Lillian-Watch (Test)", "Lillian-Watch (Test-2)"]             # device_replaced_multiple
# NEWER_DEV_SIMULATED_NEW_RAW_MODEL     = "Watch99,4"                # Newer than Watch8,4 (S12)

#--------------------------------------------------------------------
# MISSING APPLE DEVICE
#
# Remove a REAL tracked Apple device from the Apple data on every refresh after
# iCloud3 has started to simulate a device that was wiped or removed from the Apple
# acct (apple_acct_devices._request_restart_if_tracked_device_missing). None=Off
#       1st refresh          - Apple Device Missing event, next update in 15-mins
#       After 1-hour         - Restart iCloud3. The device is not removed during
#                              startup so it is found and the test starts again.
MISSING_DEV_DEVICE_NAME = None                                 # Disable missing device test
# MISSING_DEV_DEVICE_NAME = "Lillian's Apple Watch"             # Real device to remove

#--------------------------------------------------------------------
# TERMS OF USE NEEDED
#
# Simulate Apple asking for the Terms of Use for this Apple Acct apple_id
# (full apple_id or apple_user). It is done once, the next time iCloud3 starts, so
# the restart after Submit shows the issue was removed. None=Off
TERMS_OF_USE_NEEDED_USERNAME = None
# TERMS_OF_USE_NEEDED_USERNAME = 'geekstergary@'

#--------------------------------------------------------------------
# Apple Account Errors
APPLE_ACCT_ERROR = None
# APPLE_ACCT_ERROR = 'UNKNOWN APPLE ACCT'

#--------------------------------------------------------------------
# This will simulate the apple_acct_upw check/validate_via_srp failing and returning
# a response code=401 (invalid apple_id) in startup/Stage 3. A check is made to see
# if the apple_user being validated should fail.
UPW_VIA_SRP_CHECK_INVALID = []
# UPW_VIA_SRP_CHECK_INVALID = ['geekstergary@']

#--------------------------------------------------------------------
# SRP SIGNIN MINIMUM INTERVAL
#
# Act as if a Password SRP signin/complete was just sent for this apple_user so the
# next SRP signin waits SRP_SIGNIN_MIN_INTERVAL_SECS (AppleAcctManager.
# _wait_for_srp_signin_interval). It is done once. An SRP signin must actually be
# attempted - remove the password from the apple_id's .tpw file so the Stage 3
# Username/Password validation does not use the TokenPW match. None=Off
SRP_SIGNIN_INTERVAL_USERNAME = None
# SRP_SIGNIN_INTERVAL_USERNAME = 'geekstergary@'
#--------------------------------------------------------------------
# Mobile App Errors
MOBAPP_BATTERY_ENTITY_ERROR = False
MOBAPP_DISABLED             = False
SCAN_FOR_DUPLICATES         = False


#--------------------------------------------------------------------
def test_controls_enabled_msg():
    '''
    Return the Event Log greenbar alert listing the test controls that are enabled,
    '' if none are. They must be off for a release.
    '''
    test_controls_msg = ''
    if DISABLE_UPW_FILTER:
        test_controls_msg += f"{CRLF_DOT}Password Log Filter Disabled (DISABLE_UPW_FILTER)"
    if HWKEY_AUTH_ENABLED is False:
        test_controls_msg += f"{CRLF_DOT}Hardware Key Auth Disabled (HWKEY_AUTH_ENABLED)"
    if INTERNET_ERROR or INTERNET_ERROR_AFTER_STARTUP:
        test_controls_msg += f"{CRLF_DOT}Internet Error (INTERNET_ERROR)"
    if NEWER_DEV_EXISTING_DEVICE_NAME:
        test_controls_msg += (f"{CRLF_DOT}Newer Apple Device, "
                                f"{NEWER_DEV_EXISTING_DEVICE_NAME} (NEWER_DEV_EXISTING_DEVICE_NAME)")
    if MISSING_DEV_DEVICE_NAME:
        test_controls_msg += (f"{CRLF_DOT}Missing Apple Device, "
                                f"{MISSING_DEV_DEVICE_NAME} (MISSING_DEV_DEVICE_NAME)")
    if TERMS_OF_USE_NEEDED_USERNAME:
        test_controls_msg += (f"{CRLF_DOT}Terms of Use Needed, "
                                f"{TERMS_OF_USE_NEEDED_USERNAME} (TERMS_OF_USE_NEEDED_USERNAME)")
    if MOBAPP_DISABLED or MOBAPP_BATTERY_ENTITY_ERROR:
        test_controls_msg += f"{CRLF_DOT}Mobile App Error (MOBAPP_DISABLED/MOBAPP_BATTERY_ENTITY_ERROR)"
    if UPW_VIA_SRP_CHECK_INVALID:
        test_controls_msg += (f"{CRLF_DOT}Test UPW SRP Invalid, "
                                f"{UPW_VIA_SRP_CHECK_INVALID} (UPW_VIA_SRP_CHECK_INVALID:)")
    if SRP_SIGNIN_INTERVAL_USERNAME:
        test_controls_msg += (f"{CRLF_DOT}SRP Signin Interval Wait, "
                                f"{SRP_SIGNIN_INTERVAL_USERNAME} (SRP_SIGNIN_INTERVAL_USERNAME)")


    if test_controls_msg == '':
        return ''

    return f"{RED_ALERT}TEST CONTROLS ENABLED{test_controls_msg}"