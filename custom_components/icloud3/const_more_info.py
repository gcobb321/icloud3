
from .const             import (EVLOG_ALERT, EVLOG_NOTICE,
                                SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,)
from .const_char        import (CRLF, CRLF_CHK, CRLF_SP3_STAR, CRLF_INDENT, CRLF_DOT, CRLF_SP3_DOT,
                                CRLF_SP5_DOT, CRLF_HDOT, CRLF_RED_X, RED_X, CRLF_STAR,
                                CRLF_DASH_75, RARROW, NBSP3, NBSP4, NBSP6, CIRCLE_STAR,
                                INFO_SEPARATOR, DASH_20, CHECK_MARK, )

more_info_text = {
    'icloud_find_my_phone_alert_error': (
        f"{CRLF_DASH_75}"
        f"{CRLF}1. Review the Event Log Stages 3 & 4 for this device and make sure the iCloud "
        f"device you selected is correct and has been verified."
        f"{CRLF}2. Review the “Configure Settings > Update Devices” screen for this device and "
        f"verify it has been assigned correctly, is not still assigned to an old device and "
        f"there are no error messages."
        f"{CRLF}3. Review the FindMy App devices screen and verify the device can be located."
        f"{CRLF}4. Review the Event Log for this device and make sure it is being tracked with the "
        f"iCloud tracking method."
        ),

    'refresh_browser': (
        f"{CRLF_DOT}Refresh your browser (Chrome, MacOS, Edge):"
        f"{CRLF}{NBSP3}1. Press Ctrl+Shift+Del, Clear Data, Refresh"
        f"{CRLF}{NBSP3}2. On Settings tab, check Clear Images and File, then Click Clear Data, Refresh"
        f"{CRLF}{NBSP3}3. Select the Home Assistant tab, then Refresh the display"
        f"{CRLF}{CRLF_DOT}Refresh the Mobile App on iPhones, iPads, etc:"
        f"{CRLF}{NBSP3}1. HA Sidebar, Configuration, Companion App"
        f"{CRLF}{NBSP3}2. Debugging, Reset frontend cache, Settings, Done"
        f"{CRLF}{NBSP3}3. Close Companion App, Redisplay iCloud3 screen"
        f"{CRLF}{NBSP3}4. Refresh, Pull down from the top, Spinning wheel, Done"
        ),

    'unverified_device': (
        f"{CRLF_DASH_75}"
        f"{CRLF}This can be caused by:"
        f"{CRLF}1. iCloud3 Device configuration error. Check the “Configure Settings > "
        f"Update Devices” screen and verify the iCloud and Mobile App Device selections are correct."
        f"{CRLF}2. No iCloud or Mobile App device have been selected. See #1 above."
        f"{CRLF}3. This device is no longer in your iCloud Family Sharing device list. Review "
        f"the devices in the FindMy App on your phone and on your Apple Account. Review the list of "
        f"devices returned from your Apple Account when iCloud3 was starting up in the Event Log Stage 4."
        f"{CRLF}4. iCloud or Mobile App are not being used to locate devices. Verify that your Apple Account "
        f"is a data source and is set up on the “Configure Settings > iCloud Account” screen. Also verify that "
        f"Apple Account iCloud Devices have been assigned correctly to iCloud3 devices on the “Configure "
        f"Settings Update Devices” screen."
        f"{CRLF}5. iCloud is down. The network is down. iCloud is not responding to location requests."
        f"{CRLF}6. An internal code error occurred. Check “HA Settings > System > Logs” for errors."
        f"{CRLF_DASH_75}"
        f"{CRLF}Restart iCloud3 (Event Log > Actions > Restart iCloud) and see if the problem reoccurs."
        ),

    'all_devices_inactive': (
        f"Devices can be tracked, monitored or inactive on the “Configure Settings > Update "
        f"Devices” screen. In this case, all of the devices are set to an Inactive status.  "
        f"{CRLF}1. Change the `Tracking Mode` from INACTIVE to Track or Monitor."
        f"{CRLF}2. Verify the Apple Account iCloud Device assigned to the iCloud3 device is correct."
        f"{CRLF}3. Verify the Mobile App Device assigned to the iCloud3 device is correct."
        f"{CRLF}4. Review the other parameters for the device while you are on this screen."
        f"{CRLF}5. Do this for all of your devices."
        f"{CRLF}6. Exit the “Configure Settings” screens and Restart iCloud3."
        ),

    'invalid_msg_key': (
        f"{CRLF_DASH_75}"
        f"{CRLF}Information is not available for "),

    'instructions_already_displayed': (
        f"{CRLF_DASH_75}"
        f"{CRLF}See the instructions that have already been displayed"
        ),

}
