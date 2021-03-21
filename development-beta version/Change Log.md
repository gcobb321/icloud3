#### v2.3.6b4 (3/21/2021)



<u>Configuration Parameters:</u>

1. General Parameters:

   **inzone_intervals**

   The interval between location updates when the device is in a zone for specific device types, for devices that are not using the iOS App and the default *inzone_interval* value. This parameter lets you set different inzone_intervals for different devices. You can, for example, have a 2-hour interval for iPhones and a 15-minute interval for watches and devices that are not using the iOS App. For devices not being monitored, a shorter interval will update the location more often and identify when the device has exited a zone sooner than the regular 2-hour inzone_interval would,

   *Valid values:* inzone_interval, iphone, ipad, pod, watch, no_iosapp

   *Note:* The default, *inzone_interval* parameter can be specified on the *inzone_intervals* list or as a stand alone parameter.

   *Example*:

   ```
   inzone_intervals:
     - inzone_interval: 2 hrs
     - ipad: 1 hrs
     - watch: 15 min
     - no_iosapp: 15 min
   ```

2. Parameters added to the *devices/device_name* parameter:

   **iosapp_installed**  

   Indicates if iCloud3 should monitor the iOS App. 

   *Valid values:* True, False,  *Default:* True

   *Note:* This is the same as *noiosapp: True* but a little more meaningful. Both parameters work and do the same thing.

   **inzone interval**   

   The interval between location updates when the device is in a zone.  This can be in seconds, minutes or hours, e.g., 30 secs, 1 hr, 45 min, or 30 (minutes are assumed if no time qualifier is specified).

   *Notes:* If this value is not specified for the device, *inzone_intervals* parameter will be used to set the time. The interval will be set to the device_type's time, then the inzone_interval time and then the global *inzone_interval* time, in that order.
   
     
   
   Examples:
	```
	devices:
	  - device_name: gary_iphone
	    name: Gary
	    picture: gary.jpg
	    inzone_interval: 30 min			<-- New parameter
	  - device_name: lillian_iphone
	    name: Lillian
       picture: lillian.jpg
       iosapp_installed: False			<-- New parameter to replace the 'noiosapp' parameter
	  - device_name: john_watch
	    name: John
	  - device_name: sally_iphone
	    name: Sally
	    
	inzone_intervals:
	  - inzone_interval: 2 hrs
	  - ipad: 1 hrs
	  - watch: 15 min
	  - no_iosapp: 15 min
	```


In the above examples, the inzone_intervals are:

- gary_iphone = 30-minutes since inzone_interval was specified for that device_name.

- lillian_iphone = 15-minutes since the iOS App is not monitored and the *no_iosapp: 15 min* parameter is on *inzone_intervals* list.

- john_watch = 15 minutes since the *watch* device type is on *inzone_intervals* list.

- sally_iphone = 2 hours (the default *inzone_interval*) since the 'iphone' device type is not on *inzone_intervals* list.

<u>Other Changes</u>

1. Fixed a problem where excessive old location errors would continue to add entries to the Event Log. Tracking will now be paused if there are more than 300 discarded location requests in one day or the phone has not been successfully located in over 26-hours. This may be caused by the phone being offline, is no longer associated with the iCloud account, is turned off, etc. Tracking can be restarted using the Event Log > Actions > Resume Polling option.

#### v2.3.6b3 (3/14/2021)

<u>iCloud3</u>

1. The *device_tracker last_located, last_update and next_update time* attributes now display the timestamp (2021-03-11 14:23:30) instead of only the time (2:23:30 or 14:23:30). The sensors created by iCloud3 for these items still show only the time. This is helpful when the times of these items are for the previous or the next day. Sensors for these timestamps are not created by iCloud3. To create them, create a template sensor and extract the device_tracker's attribute value.
2. Reduced the size of the Next Update countdown timer to better fit on smaller width screens.
3. Corrected an invalid variable name (EVA_NOTICE --> EVLOG_NOTICE). This error was displayed when sending a notification to a device was not successful.
4. Fixed a problem calculating the iCloud time/locate that is displayed in the Event Log Statistics table every 3-hours.

<u>Event Log:</u>

1. Expanded single line size of zone names from 10 to 12 letters.
2. Support for the version number change.
3. Added *Start/Stop Logging Rawdata* to the Actions menu.

#### v2.3.6b2 (3/9/2021)

1. Fixed a problem where the Event Log would not display when the iOS App and iC3 Zone names contained an 's (e.g., Barry'sHouse). 
2. Updated the Event Log card version number check to support the v#.#.#b# (e.g., v2.3.6b2) numbering scheme.

#### v2.3.6b1 (2/28/2021)

1. Revamped the way the configuration parameters are retrieved from HA, how they are processed and how iCloud3 is set up based on the parameters.
2. Combined the processing of the parameters from configuration.yaml and config_ic3.yaml to use common routines. They are edited using common routines and invalid values are reset to the default value.
3. The track_from_zone parameter can now accept multiple zones using the zone name or the friendly name.

```

```