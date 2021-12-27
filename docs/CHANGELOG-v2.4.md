# iCloud3 Version 2.4 Change Log

The following enhancements and changes have been made iCloud3:

* The best way to monitor new releases is to add HACS (Home Assistant Community Store) to your HA system and set up the HACS/iCloud3 link using the instructions in the iCloud3 documentation [here](https://gcobb321.github.io/icloud3/#/chapters/3.3-hacs). 
* You can also go to the iCloud3 releases page [here](https://github.com/gcobb321/icloud3/releases) to download the latest version and do a manual update.

------

### v2.4.7 (12/27/2011) - Fix Waze Issue

1. Fixes a Waze Route Tracking issue where no information or an error was reported from Waze Servers. This was caused by a variable name change on the Waze side.

### v2.4.6 (10/11/2021) - HA cellphone icon update, Lovelace Sensor Alignment, Increase Waze retry count

1. Changed the icon for zones from mdi:cellphone-iphone to mdi:cellphone because of Home Assistant mdi update.
2. Changed the sensor state values for Travel Time, Distance, Next Update Time, etc. from an empty field to a value to address a Lovelace display change. The fields that were empty were not aligned with the field next to them. Travel Time will now display 0 min when in a zone. Other fields will display '___' when empty.
3. Increased the Waze Route Server retry requests from 3 times to 6 times to try to resolve 'No response from Waze Server, Calc will be used instead' message. 



### v2.4.5 (10/6/2021) - Fix to restore the WazeRouteCalculator function

1. Fixed a problem where the Waze Route Calculator was being disabled and the distance method-calc was being used. The problem started when the WazeRouteCalculator module in the Home Assistant standard Python library was changed. This update uses a modified version of the WazeRouteCalculator that is part of the Python Standard library that was developed by Kovács Bálint, Budapest, Hungary. It has been customized to better support iCloud3.

### v2.4.4 (9/25/2021) - Update to support iCloud+ change that broke Find-my-Friends tracking method

1. Coordinated update with pyicloud_ic3.py to support Apple iCloud url changes to access iCloud+ for location & device info for Find-my-Friends tracking method.

### v2.4.3c - Sensor Update 

1. Added sensor '[devicename]_travel_time_min' -- This is the unformatted waze travel time in minutes. It can be included or excluded using the 'mtim' code.

### v2.4.3a, v2.4.3b - Bug Fix Update 

1. An undefined variable 'invalid_code_text' was displayed after entering an invalid iCloud account verification code or taking to long to enter it. This has been corrected.

1. 2dded Event Log items for each step of the iCloud Verification code notice, entry and authentication 

### v2.4.2 - Bug Fix Updates 

- Added 'AU' to the list of valid Waze Regions.

### v2.4.1 - Bug Fix Updates 

- Fixed a bug where the create_sensor was not creating any sensors and the exclude_sensor was not excluding the specified sensors.
- Fixed coding spelling error bugs related to (1) iCloud 2fa reauthorization requests after a failure and (2) determining if a beta version of the the Event Log was installed and needed to be updated when iCloud3 was starting.

### v2.4.0 - Bug Fix Updates 

- Fixed a problem where excessive old location errors would continue to add entries to the Event Log. Tracking is now paused if there are more than 400 discarded location requests in one day or the phone has not been successfully located in over 26-hours. This may be caused by the phone being offline, is no longer associated with the iCloud account, is turned off, etc. Tracking can be restarted using the Event Log > Actions > Resume Polling option.
- Corrected an invalid variable name (EVA_NOTICE --> EVLOG_NOTICE). This error was displayed when sending a notification to a device was not successful.
- Fixed a problem calculating the iCloud time/locate that is displayed in the Event Log Statistics table every 3-hours.
- A zone name with an *'s* will now be displayed correctly (e.g., Barry'sHouse, Barry's House). 

------

### v2.4.0 - Parameter Changes 

- *inzone_intervals* parameter - The interval between location updates when the device is in a zone can be specified for specific device types (iPhone, iPad, Watch, etc.), for devices that are not using the iOS App (iosapp_installed: False, noiosapp: True) and for the default *inzone_interval* for devices that are not specified. For example, can have a 2-hour interval for iPhones and a 15-minute interval for watches and devices that are not using the iOS App.   
- *inzone_interval* parameter for a specific *device_name* - You can now specify the inzone_interval for each device on the devices/device_name parameter.
- *iosapp_installed* parameter - This replaces the depreciated *noiosapp* parameter and is more meaningful. 
  For example, *iosapp_installed: False* indicates the iOS App is not installed on the device.
- *noiosapp* parameter - Depreciated and replaced with the *iosapp_installed* parameter.
- *track_devices* parameter -  Depreciated and will be removed on the next release of iCloud3

### v2.4.0 - Other Changes 

- The *device_tracker last_located, last_update and next_update time* attributes now display the timestamp (2021-03-11 14:23:30) instead of only the time (2:23:30 or 14:23:30). The sensors created by iCloud3 for these items still show only the time. This is helpful when the times of these items are for the previous or the next day. Sensors for these timestamps are not created by iCloud3. To create them, create a template sensor and extract the device_tracker's attribute value.
- Event Log Changes
  1. Expanded single line size of zone names from 10 to 12 letters.
  2. Added *Start/Stop Logging Rawdata* to the Actions menu.
  3. The Event Log card version number check now supports the v#.#.#b# (e.g., v2.3.6b2) numbering scheme.
- Revamped the way the configuration parameters are retrieved from HA, how they are processed and how iCloud3 is set up based on the parameters.
- Combined the processing of the parameters from configuration.yaml and config_ic3.yaml to use common routines. They are edited using common routines and invalid values are reset to the default value.
- The track_from_zone parameter can now accept multiple zones using the zone name or the friendly name.
- Reduced the size of the Next Update countdown timer to better fit on smaller width screens.
- Support for the version number requirement in Home Assistant in the *manifest.json* file.

------

Gary Cobb *(aka geekstergary)*

April, 2021

