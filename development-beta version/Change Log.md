##### v2.3.6b3 (3/14/2021)

<u>iCloud3</u>

1. The *device_tracker last_located, last_update and next_update time* attributes now display the timestamp (2021-03-11 14:23:30) instead of only the time (2:23:30 or 14:23:30). The sensors created by iCloud3 for these items still show only the time. This is helpful when the times of these items are for the previous or the next day. Sensors for these timestamps are not created by iCloud3. To create them, create a template sensor and extract the device_tracker's attribute value.
2. Reduced the size of the Next Update countdown timer to better fit on smaller width screens.
3. Corrected an invalid variable name (EVA_NOTICE --> EVLOG_NOTICE). This error was displayed when sending a notification to a device was not successful.
4. Fixed a problem calculating the iCloud time/locate that is displayed in the Event Log Statistics table every 3-hours.

<u>Event Log:</u>

1. Expanded single line size of zone names from 10 to 12 letters.
2. Support for the version number change.
3. Added *Start/Stop Logging Rawdata* to the Actions menu.

##### v2.3.6b2 (3/9/2021)

1. Fixed a problem where the Event Log would not display when the iOS App and iC3 Zone names contained an 's (e.g., Barry'sHouse). 
2. Updated the Event Log card version number check to support the v#.#.#b# (e.g., v2.3.6b2) numbering scheme.

##### v2.3.6b1 (2/28/2021)

1. Revamped the way the configuration parameters are retrieved from HA, how they are processed and how iCloud3 is set up based on the parameters.
2. Combined the processing of the parameters from configuration.yaml and config_ic3.yaml to use common routines. They are edited using common routines and invalid values are reset to the default value.
3. The track_from_zone parameter can now accept multiple zones using the zone name or the friendly name.
