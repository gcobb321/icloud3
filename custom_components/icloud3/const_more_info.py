
from .const             import (EVLOG_ALERT, EVLOG_NOTICE,
                                CRLF, CRLF_CHK, CRLF_SP3_STAR, CRLF_INDENT,
                                CRLF_DOT, CRLF_SP3_DOT, CRLF_SP5_DOT, CRLF_HDOT,
                                CRLF_RED_X, RED_X, CRLF_STAR, CRLF_DASH_75,
                                RARROW,NBSP3, NBSP4, NBSP6, CIRCLE_STAR, INFO_SEPARATOR,
                                DASH_20, CHECK_MARK,
                                SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,)

more_info_text = {
    'mobapp_error_not_found_msg': (
        f"{CRLF_DASH_75}"
        f"{CRLF}1. If the name of the device was changed on the “Mobile App "
        f"Integration > Devices” screen, the Mobile App Device Name parameter "
        f"on the “iCloud3 Configure Setting > Update Devices” screen "
        f"needs to be updated with the new device name."
        f"{CRLF}2. Check the “Mobile App Integration” devices to see if it is listed."
        f"{CRLF}3. Check the “Mobile App Integration” devices to see if it is enabled."
        f"{CRLF}4. Check the MobApp on the device that was not found to make "
        f"sure it is operational and can communicate with HA. Refresh its location "
        f"by pulling down on the screen."
        f"{CRLF}5. Check the MobApp device_tracker entities on “HA Settings > "
        f"Developer Tools > States” to verify that the devices using the Mobile App are "
        f"listed, enabled and that the data is current."),

    'mobapp_error_search_msg': (
        f"{CRLF_DASH_75}"
        f"{CRLF}1. Check the MobApp Device Entity assigned to the iCloud3 device "
        f"on the “Configure Settings > Update Devices” screen. Change the "
        f"Mobile App device_tracker entity from “Scan for mobile_app device_tracker” "
        f"to a specific device_tracker entity."
        f"{CRLF}2. Check the mobile_app devices in “HA Settings > Devices & "
        f"Services > Devices” screen and delete or rename the devices starting with the "
        f"iCloud3 devicename that should be selected."),

    'mobapp_error_disabled_msg': (
        f"{CRLF_DASH_75}"
        f"{CRLF}1. Go to “HA Devices & Services > Integrations > Mobile App”"
        f"{CRLF}2. Select the disabled device. Then select the 3-dots in the upper "
        f"right corner."
        f"{CRLF}Select Enable device."),

    'mobapp_error_multiple_devices_on_scan': (
        f"{CRLF_DASH_75}"
        f"{CRLF}1. Check the MobApp Device Entity assigned to the iCloud3 device "
        f"on the “iCloud3 Configure Settings > Update Devices” screen. Change the "
        f"Mobile App device_tracker entity from “Scan for mobile_app device_tracker” "
        f"to a specific device_tracker entity."
        f"{CRLF}2. Check the Mobile App devices on the “HA Settings > Devices & "
        f"Services > Devices” screen. Delete or rename the devices starting with the "
        f"iCloud3 devicename that should not be selected."),

    'mobapp_error_mobile_app_msg': (
        f"{CRLF_DASH_75}"
        f"{CRLF}1. Verify that the Mobile App Integration has been added to HA. "
        f"If not, add it. You may have to restart HA."
        f"{CRLF}2. Verify that all of the devices that are using the Mobile App are displayed. "
        f"Review the HA Companion App docs to verify it is set up and can communicate with HA."
        f"{CRLF}3. Under each device is a line reading `1 Device and ## Entities`. "
        f"Select Entities and verify that the _battery_level and _last_update_trigger "
        f"entities are listed and enabled. If disabled, select the “Gear” Icon and enable them. "
        f"If necessary. Review the HA Mobile App docs for more information."
        f"{CRLF}4. Do this for each mobile_app device with a problem."
        f"{CRLF}5. Restart iCloud3 after making any changes (Event Log > Action > Restart)."),

    'mobapp_device_unavailable': (
        f"{CRLF_DASH_75}"
        f"{CRLF}1. Verify that the Mobile App Integration has been added to HA. "
        f"If not, add it. You may have to restart HA."
        f"{CRLF}2. Verify the Mobile App Integration operational status (“HA Settings > Devices "
        f"& Services > Integrations”). Check to see if a `Failed to set up` error message is "
        f"displayed in general or for a specific device. If so, that issue must be corrected "
        f"before the Mobile App can be used for this device."
        f"{CRLF_DASH_75}"
        f"{CRLF}The iCloud tracking method will continue to be used for this device."),

    'mobapp_device_no_location': (
        f"{CRLF_DASH_75}"
        f"{CRLF}1. Verify the Mobile App Integration operational status (“HA Settings > Devices "
        f"& Services > Integrations”). Check to see if an error message is displayed in general "
        f"or for a specific device. If so, that issue should be corrected."
        f"{CRLF}2. Check the device_tracker entity state and attribute values (“HA Developer Tools > "
        f"States”). Verify the device is on-line and location data is being updated by the Mobile App. "
        f"{CRLF}3. Check the Mobile App on the device."
        f"{CRLF}{NBSP3}1. Verify it is online and can connect to HA. "
        f"{CRLF}{NBSP3}2. Verify that the device can be located."
        f"{CRLF}{NBSP3}3. Verify that location services are enabled and the MobApp settings are correct."
        f"{CRLF}{NBSP3}4. Go to the “Mobile App > Location” screen, scroll to the bottom and select "
        f"`Update Location`. Then see if any errors are displayed in the Event Log."),

    'icloud_device_not_available': (
        f"{CRLF_DASH_75}"
        f"{CRLF}1. Check the Family Share devices in the FindMy app on your phone. "
        f"See if any devices have been renamed, are missing or there is more than one "
        f"device with the same name."
        f"{CRLF}2. Have you change phones? The iCloud devicename on the “Configure Settings > Update Device” "
        f"screen may be the old phone, not the new phone. The new one may have a different name."
        f"{CRLF}3. Check the iCloud devices in Stage 4 above. It lists all the iCloud devices that "
        f"have been returned from your Apple Account. Sometimes, Apple does not return "
        f"all of the devices if there is a delay locating it or it is asleep. iCloud3 will "
        f"request the list severan times. Open the missing device so it is available, then restart "
        f"iCloud3 to see if it is found."
        f"{CRLF}4. Check the Apple Account iCloud Device assigned to the iCloud3 device "
        f"on the “Configure Settings > Update Devices” screen. Open the iCloud Devices "
        f"list and review the devicenames available. Make sure the devices are correct and "
        f"there are no duplicates or additional/new devices with a different name."),

    'icloud_dup_devices': (
        f"{CRLF_DASH_75}"
        f"{CRLF}1. Review the Apple Account iCloud Devices in the list above and verify the last "
        f"located device is the one iCloud3 should track or monitor."
        f"{CRLF}2. In the FindMy App, update the devices in your Family List and remove the old, unused "
        f"devices or any devices you no longer have."
        f"{CRLF}{NBSP3}1. Open the FindMy App. Select `Devices`."
        f"{CRLF}{NBSP3}2. Select the device you want to remove. `Remove This Device` is displayed "
        f"at the bottom of the screen if it is not connected to your account. This includes "
        f"AirPods that are asleep and in their case. This is not displayed if the device is "
        f"logged in and connected."
        f"{CRLF}{NBSP3}3. Select `Remove This Device`, then `Yes`"
        f"{CRLF}{NBSP3}4. If your current device has a name with a number suffix, like Gary-iPad(2), "
        f"you can clean up your device names by renaming it. On the device itself, go to “Settings "
        f"App > General > About > Name”. Remove the suffix so it reads something like Gary-iPad."
        f"{CRLF}{NBSP3}5. Do this for all devices that need to be removed and renamed."
        f"{CRLF}{NBSP3}6. Restart HA. The new device names will be identified by iCloud3 and your "
        f"configuration will be updated with the new name."
        f"{CRLF}{NBSP3}7. Go to the “Configure Settings > Update Devices” screen for the "
        f"devices you changed and verify the correct Apple Account iCloud Device is selected from it's list."
        f"Correct any that are wrong."
        f"{CRLF}{NBSP3}8. Restart iCloud3 and verify that the devices are tracked correctly."
        ),

    'icloud_dind_my_phone_alert_error': (
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
        f"{CRLF_DOT}Refresh the Mobile App on iPhones, iPads, etc:"
        f"{CRLF}{NBSP3}1. HA Sidebar, Configuration, Companion App"
        f"{CRLF}{NBSP3}2. Debugging, Reset frontend cache, Settings, Done"
        f"{CRLF}{NBSP3}3. Close Companion App, Redisplay iCloud3 screen"
        f"{CRLF}{NBSP3}4. Refresh, Pull down from the top, Spinning wheel, Done"),

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
        f"{CRLF}Restart iCloud3 (Event Log > Actions > Restart iCloud) and see if the problem reoccurs."),

    'all_devices_inactive': (
        f"Devices can be tracked, monitored or inactive on the “Configure Settings > Update "
        f"Devices” screen. In this case, all of the devices are set to an Inactive status.  "
        f"{CRLF}1. Change the `Tracking Mode` from INACTIVE to Track or Monitor."
        f"{CRLF}2. Verify the Apple Account iCloud Device assigned to the iCloud3 device is correct."
        f"{CRLF}3. Verify the Mobile App Device assigned to the iCloud3 device is correct."
        f"{CRLF}4. Review the other parameters for the device while you are on this screen."
        f"{CRLF}5. Do this for all of your devices."
        f"{CRLF}6. Exit the “Configure Settings” screens and Restart iCloud3."),

    'add_icloud3_integration': (
        f"{CRLF}1. Select {SETTINGS_INTEGRATIONS_MSG}"
        f"{CRLF}2. Select `+Add Integration` to add the iCloud3 integration if it is not dislayed. Then search "
        f"for `iCloud3`, select it and complete the installation."
        f"{CRLF}3. Select {INTEGRATIONS_IC3_CONFIG_MSG} to open “Configure Settings” screens."
        f"{CRLF}4. Review and setup the `iCloud Account` and `Update Devices` configuration screens."
        f"{CRLF}5. Exit the configurator and `Restart iCloud3`."),

    'configure_icloud3': (
        f"{CRLF}1. Click the “Gear” icon at the top right corner on the Event Log screen "
        f"or select “Settings > Devices & Services > Integrations” from the HA sidebar >"
        f"{CRLF}2. Select “iCloud3 > Configuration” to  display the “Configure Settings” screen."
        f"{CRLF}3. Select “Update Data Sources” to add your Apple account that will "
        f"provide location information"
        f"{CRLF}3. Select “Update Devices” to add devices that will be tracked."
        f"{CRLF}3. Review the other configuration screens and update any parameters "
        f"that need to be changed."),

    'unverified_devices_caused_by': (
        f"{CRLF}This can be caused by:"
        f"{CRLF_DOT}iCloud3 Configuration Errors."
        f"{CRLF_DOT}iCloud Location Services may be down or slow."
        f"{CRLF_DOT}The internet may be down."
        f"{CRLF_DOT}The username/password is not set up or incorrect."
        f"{CRLF_DASH_75}"
        f"{CRLF}Check the Event Log error messages. Correct any problems and restart iCloud3."),

    'invalid_msg_key': (
        f"{CRLF_DASH_75}"
        f"{CRLF}Information is not available for "),

    'instructions_already_displayed': (
        f"{CRLF_DASH_75}"
        f"{CRLF}See the instructions that have already been displayed"),

    'password_srp_error': (
        f"{CRLF_DASH_75}"        
        f"{CRLF}The Python module that creates the Secure Remote Password (SRP) "
        f"hash key has calculated an incorrect value for a valid assword. You probably "
        f"will have to change the Apple Account password to be able to log into it. "
        f"{CRLF}{CRLF}For more infornation, go to the iCloud3 GitHub "
        f"issues page. Click the red Bug icon on the Event Log and "
        f"review the{CRLF}`➤ Password SRP Error Message` issue at the top of the screen."),

}
