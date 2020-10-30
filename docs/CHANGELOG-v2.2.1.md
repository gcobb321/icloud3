## iCloud3 Version 2.2.1 Change Log

The following enhancements and changes have been made iCloud3 v2.2.0:

* The best way to monitor new releases is to add HACS (Home Assistant Community Store) to your HA system and set up the HACS/iCloud3 link using the instructions in the iCloud3 documentation [here](https://gcobb321.github.io/icloud3/#/chapters/3-hacs). 
* You can also go to the iCloud3 releases page [here](https://github.com/gcobb321/icloud3/releases) to download the latest version and do a manual update.

------

#### Major Enhancements

* Updated the iOS App tracking method to request the phone's location when the Next Update Time is reached in the same manner as the iCloud tracking methods. Using the tracking method *iosapp* eliminates all iCloud account polling, relies only on the data provided by the iOS app and provides a reliable tracking method when access to the iCloud accounts is limited due to 2fa authentication/verification issues. 

  At night, the iOS App usually shuts down when the phone is asleep. When the phone becomes inactive and is not responding to location requests, a message is displayed in the Event Log and on the iCloud3 information screen, the interval is increased to reduce polling until the phone wakes up and the iOS App becomes active again. When iOS App wakes up and begins responding to the location request, polling will automatically resume. 

  *Note:* If the iOS App is running in the background, it still may not wake up and respond to the location requests. In that case, the iOS App must be restarted. iCloud3 will detect the *launch* trigger issued by the iOS App and begin polling as normal.

#### Other Changes

* Changed the way zones are handled to better support overlapping zones, particularly when you have two zones with a center at the same location with different sizes. For example, your Home zone has a radius of 100m and you have a second zone (your neighborhood, town or city) at the Home zone's location with a radius of 500m. The neighborhood zone will help wake up the iOS App before you reach the Home zone. A town or city size zone will display the town or city's name in the Zone and State entities on the Event Log and iCloud3 information screen instead of 'Away'.

* Added error handling to the iCloud authentication/verification process.

* A location will now not be considered old if it's age is less than 1-minute to reduce the number of location updates that are discarded.

* Updated the icons for the sensors created by iCloud3.

* HACS deletes all files in the iCloud3 directory before installing the new version. For this reason the *config_ic3.yaml* file should be located in the */config* directory. An Alert message will be displayed in the Event Log if the *config_ic3.yaml* file is found in the iCloud3 directory.

* Added the interval calculation method to the Event Log Tracking Monitors when *HA Debug Logging* was started

* Added the *noiosapp* value to the track_devices parameter to indicate the devicename does not have the iOS App installed on it and to not scan the *entity registry* looking for a mobile_app integration entry. 

  **Example:*   ``- gary_iphone > gary-456@email.com, gary.png, noiosapp`

* Changed *Event Log > Actions > Request iOS App Location* to *Event Log > Actions > Update Location* to issue location requests to iCloud or the iOS App based on the tracking method being used.

* Added some logger debug statements to *pyicloud_ic3.py* to display iCloud Request/Response events that show the communication between *pyicloud.py* and iCloud Location Services.

  To turn this on, add the following to your configuration.yaml file:

  ```yaml
  logger:
    default: info
    logs:
      custom_components.icloud3.pyicloud_ic3: debug
  ```

#### New Parameters

- **display_zone_fname** - Display the zone's friendly name rather than it's actual name in the Zone and iOS App state fields on the Event Log and the iCloud3 information screen. If the friendly name is too long to be displayed, it will overflow to the next line and then be truncated.

  *Note:* The zone's actual name will be reformatted before it is displayed. 

  *Examples:* The zone *the_shores* is displayed as *TheShores*, *school* is displayed as *School*.

  *Valid Values:* : True (display the zone friendly name), False (display the zone's actual name).  *Default:* False 

  **time_format** - This parameter overrides the unit_of_measurement time format.  

  *Valid Values:* 12/24. *Default:* Depends on the unit_of_measurement (mi=12, km=24). 

#### Bug Fixes

- Fixed a problem where the iOS App device_tracker entity contained the zone's friendly name on enter/exit events while iCloud3 uses the zone name for it's device_tracker entity, which led to extra zone triggers and zone mismatch errors because the names were different.
- Fixed a problem where iCloud3 would hang up in a 5-second update loop and polling iCloud for location data when none was available because If the phone was turned off and not available when HA restarted or became unreachable for an extended period of time while HA/iCloud3 was running (cell service down, turned off, airplane mode, etc.). The phone would be stuck in a *NotSet* state or the location would become older and older.  It will now retry the data request 4-times at a 15-second interval. The interval will increase to 1, 5, 15, 30, 1 hr and finally 4-hrs and remain there until the phone comes back online.  If the phone is then turned on, it will be picked up on the next successful location data request and then be tracked as it normal is.
- Fixed a problem when the *unit_of_measurement* parameter was in the *config_ic3.yaml* file,. It was not being decoded correctly and *mi* was being used in error.
- Fixed a problem when the phone's name started with iPhone (or iPad), causing the first character of the sensor.xxx friendly_name attribute to be a '-'. 
- Fixed a Region Entered trigger being discarded when the distance to the center of the zone is between the zone's radius and 100m when the radius is less than 100m. The iOS App issues the Region Enter trigger when the distance is  100m, regardless of the actual zone size. 
- Fixed the *Lost Phone* notification. It will now work with all tracking methods using the iOS App Notifications platform.
- Fixed the Event Log iOS App monitor so it would show the iOS App gps accuracy rather than the last iCloud value.
- Fixed a problem where iCloud3 would not receive location information from iCloud Location Services on the next poll after the iCloud account was verified with the 6-digit authentication code. iCloud3 will now automatically restart to reinitialize location information after the verification is completed.
- Fixed a problem determining the polling interval if the last poll was from iCloud data was discarded due to poor gps accuracy and the next poll was from the iOS App with good gps accuracy.



Gary Cobb *(aka geekstergary)*

November, 2020

------

#### Special Thanks

* A special shout out goes to Quentame in Lyon, France. He has taken over support for the program (pyicloud.py) used to interface the HA/iCloud integration and Apples iCloud Web Services. This is the basis for the customized version used by iCloud3 (*pyicloud_ic3.py*).
* Another special thanks goes to Z Zeleznick at Berekley for developing the *pyicloud.py Find-my-Friends* add-on that is also incorporated into *pyicloud_ic3.py* used by iCloud3.