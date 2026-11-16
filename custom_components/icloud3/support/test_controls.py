'''
Define global variables used to enable testing iCloud3 functions

from ..support              import test_controls as TEST

Add a new test control to test_controls_enabled_msg at the end of this module so
it is listed in the Event Log greenbar when it is enabled.
'''
from ..const_char import (RED_ALERT, CRLF_DOT, )

DISABLE_UPW_FILTER = False # Disable filtering passwords in the icloud3.log file
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
NEWER_DEV_SIMULATED_NEW_DEVICE_NAME   = None
NEWER_DEV_SIMULATED_NEW_RAW_MODEL     = None
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
# APPLE ACCT LOCKED
#
# Simulate Apple's 'This Apple Account has been locked for security reasons' response
# (403, serviceError -20209) for this Apple Acct apple_id (full apple_id or apple_user).
# The next Password SRP signin/complete request for it is not sent to Apple, the locked
# response is returned instead (icloud_session._request). It is done once. A signin is
# done when the Apple Acct is saved/logged into in Configure or validated at startup
# after a password change. None=Off
ACCT_LOCKED_USERNAME = None
# ACCT_LOCKED_USERNAME = 'geekstergary@gmail.com'

#--------------------------------------------------------------------
# APPLE ACCOUNT ERRORS
#
APPLE_ACCT_ERROR = None
# APPLE_ACCT_ERROR = 'UNKNOWN APPLE ACCT'

#--------------------------------------------------------------------
# This will simulate the apple_acct_upw check/validate_via_srp failing and returning
# a response code=401 (invalid apple_id) in startup/Stage 3. A check is made to see
# if the apple_user being validated should fail.
UPW_VIA_SRP_CHECK_INVALID = []
# UPW_VIA_SRP_CHECK_INVALID = ['geekstergary@']

#--------------------------------------------------------------------
# Simulate the first signin/init of the Username/Password validation (validate_upw_via_srp)
# returning 400 (-900007) for this Apple Acct (full apple_id or apple_user). The first init
# is not sent, the retry is the real request. It is done once. None=Off
SRP_INIT_400_USERNAME = None
# SRP_INIT_400_USERNAME = 'geekstergary@'

#--------------------------------------------------------------------
# Simulate the startup Username/Password validation (validate_apple_id_password) ending
# with 400 (-900007) for this Apple Acct (full apple_id or apple_user), before Method-0.
# Nothing is sent to Apple. The startup login is still done (start_ic3.log_into_apple_accounts),
# it is retried later if it fails. It is done once. None=Off
UPW_VALIDATION_400_USERNAME = None
# UPW_VALIDATION_400_USERNAME = 'geekstergary@'

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
#
MOBAPP_BATTERY_ENTITY_ERROR = False
MOBAPP_DISABLED             = False
SCAN_FOR_DUPLICATES         = False

#--------------------------------------------------------------------
# EVENT LOG TABLE SIZE
#
# Override the Event Log table's maximum record count (normally 2000 per track from
# zone) so the table is shrunk every few minutes instead of every few days/weeks. This
# tests the EvLog table shrink, grouping and event_recds_lock. 1/3 of the records are
# deleted on each shrink (500 normally). It is set when the devices are set up in
# Stage 4 (setup_event_log_trackable_device_info). None=Off
EVLOG_MAX_RECDS = None
# EVLOG_MAX_RECDS = 300

#--------------------------------------------------------------------
# MOBAPP NOTIFY MESSAGE
#
# Send a test message to all MobApp devices  in Startup Stage 7
MOBAPP_NOTIFY_MSG = False



#--------------------------------------------------------------------
def test_controls_enabled_msg():
    '''
    Return the Event Log greenbar alert listing the test controls that are enabled,
    '' if none are. They must be off for a release.
    '''
    test_controls_msg = ''
    if DISABLE_UPW_FILTER:
        test_controls_msg += f"{CRLF_DOT}Password Log Filter Disabled (DISABLE_UPW_FILTER)"
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
    if ACCT_LOCKED_USERNAME:
        test_controls_msg += (f"{CRLF_DOT}Apple Acct Locked, "
                                f"{ACCT_LOCKED_USERNAME} (ACCT_LOCKED_USERNAME)")
    if MOBAPP_DISABLED or MOBAPP_BATTERY_ENTITY_ERROR:
        test_controls_msg += f"{CRLF_DOT}Mobile App Error (MOBAPP_DISABLED/MOBAPP_BATTERY_ENTITY_ERROR)"
    if UPW_VIA_SRP_CHECK_INVALID:
        test_controls_msg += (f"{CRLF_DOT}Test UPW SRP Invalid, "
                                f"{UPW_VIA_SRP_CHECK_INVALID} (UPW_VIA_SRP_CHECK_INVALID:)")
    if SRP_INIT_400_USERNAME:
        test_controls_msg += (f"{CRLF_DOT}SRP signin/init 400 (-900007), "
                                f"{SRP_INIT_400_USERNAME} (SRP_INIT_400_USERNAME)")
    if UPW_VALIDATION_400_USERNAME:
        test_controls_msg += (f"{CRLF_DOT}UPW Validation 400 (-900007), "
                                f"{UPW_VALIDATION_400_USERNAME} (UPW_VALIDATION_400_USERNAME)")
    if SRP_SIGNIN_INTERVAL_USERNAME:
        test_controls_msg += (f"{CRLF_DOT}SRP Signin Interval Wait, "
                                f"{SRP_SIGNIN_INTERVAL_USERNAME} (SRP_SIGNIN_INTERVAL_USERNAME)")
    if MOBAPP_NOTIFY_MSG:
        test_controls_msg += (f"{CRLF_DOT}MobApp Test Notify Msg, "
                                f"{MOBAPP_NOTIFY_MSG} (MOBAPP_NOTIFY_MSG)")
    if EVLOG_MAX_RECDS:
        test_controls_msg += (f"{CRLF_DOT}Event Log Max Recds, "
                                f"{EVLOG_MAX_RECDS} (EVLOG_MAX_RECDS)")


    if test_controls_msg == '':
        return ''

    return f"{RED_ALERT}TEST CONTROLS ENABLED{test_controls_msg}"