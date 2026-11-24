## 🍎 iCloud3 v3.8.1
### 🎉 New and Improved Items
1. **Home Icon** - The Home icon (🏠) is displayed on the devices tab when that device is in the Home zone. An alternate Home icon (🏡) is now displayed if the device is in it's PrimaryHomeZone alternate Home zone at another location.
2. **Mobapp Setup Logging** - When iCloud3 is starting and setting up the Mobapp devices, additional data is added to the log file that will help identify any setup problems.
3. **Rawdata logging** - When log level is changed to RawData on the *Configure > Tools > Log Level* screen, the current log file is closed, a new one is created and iCloud3 restarts. You no longer have to change it and then restart HA when I ask for a RawData log file to help roubleshoot a problem.

### 🐞 Bug Fixes
1. **Adding the first Apple Account** - Fixed a problem where an *Internal error 500* message was displayed when the Update Apple Account was selected from the menu to add the first Apple Account.
2. **travel_time_hhmm** - Fixed a problem where a travel time was not displayed correctly. For example, a travel time of 233 minutes would be displayed as -2969w3d instead of the correct 3:53 value.
