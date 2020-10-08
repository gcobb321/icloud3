## iCloud3 Version 2.2.0 Change Log

The following enhancements and changes have been made iCloud3 v2.1.0:

* The best way to monitor new releases is to add HACS (Home Assistant Community Store) to your HA system and set up the HACS/iCloud3 link using the instructions in the iCloud3 documentation [here](https://gcobb321.github.io/icloud3/#/chapters/3-hacs). 
* You can also go to the iCloud3 releases page [here](https://github.com/gcobb321/icloud3/releases) to download the latest version and do a manual update.

------

#### Major Enhancements

* iCloud 2fa accounts live again. The `Family Sharing` tracking method has been rewritten with the new version of iCloud Web Services Interface program (pyicloud-ic3.py). You can now track devices that are shared on your 2fa account without receiving constant account access notifications. You are not forced to set up a non-2fa account and use the Find-my-Friends tracking method any more, although it still works.

* The `last_changed_time` attribute for the iOS App device_tracker entity is now being monitored to detect a location time change. When a change is detected, a new `iOSApp Location Trigger` is issued and the updated location data is processed. This gets around the current problem with the iOS App trigger changes not being picked up by HA and then iCloud3. These include the Geographic Region Enter/Exit, Background Fetch, Significant Location Updates, and others.

* Extensive performance enhancements have been made to minimize the number of calls to the iCloud Web Services for location information and to Authenticate the device's access to the iCloud account. Previously, the account was Authenticated for each request. Now, it only Authenticates when needed. This has cut the number of data requests by over 60% and improves the response time, especially in poor cell areas.

* The Next Update Time determines when the next location request is made for the Family Sharing and Find-my-Friends tracking methods. The location request is now made 5-seconds before the Next Update Time is reached to, hopefully, give more time for the iCloud Web Service to locate all of the devices being tracked and, hopefully, reduce the number of old location being being returned and discarded.

* New versions of the Event Log will be automatically installed when a new version of iCloud3 is started for the first time.

* You can make changes to the iCloud3 configuration parameters and restart iCloud3 without restarting HA. The new configuration file, `config_ic3.yaml` in the iCloud3 custom_component directory, lets you can specify most of the configuration parameters normally found in the HA configuration file. This includes the track_devices, waze parameters, zone parameters, timings, log_level, and others. This file is processed when HA loads and iCloud3 starts and when you restart iCloud3 on the Event Log screen. For example, you can add a new device to be tracked or change the stationary_inzone time without restarting HA. Only changes to the system level parameters, including user account/password, tracking method and sensors, require a HA restart.

* Changes to the Event Log:

  * Improved the readability of the messages. 
  * The iCloud3 Statistics have been improved and provide more information in an easier to read format.
  * HA Themes are supported.
  * Added an Action pulldown list that lets you Restart iCloud3, pause and resume polling, show/hide detailed iOS App and device information, send location requests to the devices, show/hide debug logs, etc.
  * Formatting refinements and enhancements.
  * Automatically updated when a new version of iCloud3 is installed.

* Improved error handling and  notifications in the Event Log.

* And many other *under the covers* refinements and enhancements.

  

#### New configuration parameters:

* **center_in_zone** - Specify if the device's location should be changed to the center of the zone when it is in a zone. Previously, would always be moved to the zone center. Valid Values: True, False  (Default: False)
* **old_location_threshold** - When a device is located, the location's age is calculated and the update is discarded if the age is greater than the threshold. The threshold can be calculated (12.5% of the travel time to the zone with a 5 minute maximum (default)) or you can specify a fixed time using this parameter.
* **config_ic3_file_name** - iCloud3 parameters can be specified in it's own configuration file (*config_ic3.yaml*) and the parameters are used when iCloud3 is restarted on the Event Log screen and when HA starts. This lets you change the the parameters and have them take effect without restarting HA. All parameters except the username/password, tracking method and included/excluded sensors and this parameter can be specified. This includes the devices to be tracked, timings, location parameters, log_level, and others. If you want to use a different file, specify it's name with this parameter. 
  * Note: The file must be in the `custom_components/icloud3` directory.
  * Note: A sample file, `config_ic3_sample.yaml`, is installed with iCloud3.
* **stationary_zone_offset** - The stationary zone is created when iCloud3 starts (or is restarted) and is located 1km north of the Home Zone location. There may be times when this conflicts with your normal driving route and you find yourself going in and out of the stationary zone. With this parameter, you can change it's initial location. The format is:
  * stationary_zone_offset: #,# - Specify the number of kilometers from the Home zone. The first parameter adjusts the latitude (north/south), the second parameter adjusts the longitude (east/west).
    * Example: stationary_zone_offset: 1, 2 (1km North, 2km East)
    * Default: stationary_zone_offset: 1, 0
  * stationary_zone_offset: (latitude, longitude) - Specify the GPS coordinates (you must include the parentheses). 
    * Example: stationary_zone_offset: (27.738520, -75.380462)
* **event_log_card_directory**  - This contains the directory used to store the iCloud3 Event Log Lovelace card. The Event Log version (*'icloud3-event-log-card.js'*) is checked when iCloud3 starts to verify the latest version is installed. If a newer version is available, the newer version in the iCloud3 custom components directory is copied to the Event Log directory. Use this parameter if you are storing your lovelace custom cards in directory other than *'www/custom_cards'*..
- *Valid values:* Standard file name *Default Value:* 'www/custom_cards'
  - *Example:* 'www/community' if you are using the 'community' directory.
- **display_text_as** - There may be times when you do not want your email address or other personal data displayed in the Event Log. This parameter lets you replace the text that is normally displayed with something else. 

#### Other Changes

* The distance used to check if the device has wandered outside the zone is now based on the zone radius and gps accuracy threshold.
* When an iCloud account authentication fails due to the iCloud Web Services being down or the iCloud account login fails due to an invalid username/password, iCloud3 disables the Family Sharing (FamShr) and Find-my-Friends (FmF) tracking method and uses the iOS App tracking method instead. Previously, an iCloud3 restart was needed to retry the authentication and reenable the FamShr and FmF tracking methods. Now, the authentication will be retried in 15-minutes (retries 1-4), 30-minutes (retries 5-8) and then on a 1-hour schedule. If successful, the FamShr or FmF tracking methods will be reactivated.
* The battery level from the iOS App is now displayed when using the Find-my-Friends tracking method.
* Revamped a lot of the error and information messages displayed on the Event Log.

#### Bug Fixes

- Fixed a GPS wandering problem where the device would not be moved back into a zone when there was no zone exit trigger. The zone distance checks was comparing the current distance in meters to the limit distance in kilometers.
- Fixed a problem where an error was being generated and no devices were tracked if the iOS app v1 was being used.
- Fixed some problems with the iOS App tracking method, including zone exit detection, missed triggers and errors trying to access an iCloud account when it should not have been. The password parameter is no longer required when using the iOS App tracking method (the username is still required).
- Fixed a problem where the incorrect polling interval was used for devices experiencing repeated GPS accuracy or Old Location issues.
- When the device was in a zone and then exited the zone without an Exit trigger due to GPS wandering, the trigger update was supposed to be discarded so the state and zone would not change to 'not_home' (Away) when the device had not actually moved. An iOS App trigger was discarding the trigger but it was not discarded if the 'Next Update Time' was reached for FmF or FamShr tracking. This was fixed.

------

Hopefully, you will find this release useful. I am especially excited to be able to use 2fa iCloud accounts again rather than going through the process of setting up non-2fa Find-my-Friends accounts. I hope the tuning and reducing the number of calls to iCloud Web Services for location information will make the program more responsive, especially in poor cell areas.

Version 2.1 was released in March, 2020 and has now been downloaded over 1200 times to users all over the world. If you do find it useful, you don't have to buy me a coffee, beer, gin-and-tonic or a glass of find New Zealand Sauvignon Blanc. But I would appreciate it if you would go to the iCloud repository (https://github.com/gcobb321/icloud3) and click on the star in the upper right corner.

Gary Cobb *(aka geekstergary)*



#### Special Thanks

* A special shout out goes to Quentame in Lyon, France. He has taken over support for the program (pyicloud.py) used to interface the HA/iCloud integration and Apples iCloud Web Services. This is the basis for the customized version used by iCloud3 (pyicloud_ic3.py)
* Another special thanks goes to Z Zeleznick at Berekley for developing the pyicloud.py Find-my-Friends add-on that is incorporated into the customized version (pyicloud_ic3.py) used by iCloud3.