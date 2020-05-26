# iCloud3 Version 2.2.0 Change Log

The following enhancements and changes have been made iCloud3 v2.1.0

Note: You can set up this prerelease version in another custom_components directory and still keep the v2.1.0 version maintained by HACS that you are currently using. Instructions on doing this are at the end of the Change Log.

------

#### Major Enhancements

* iCloud 2fa accounts live again. The `Family Sharing` tracking method has been rewritten with the new version of iCloud Web Services Interface program (pyicloud-ic3.py). You can now track devices that are shared on your 2fa account without receiving constant account access notifications. You are not forced to set up a non-2fa account and use the Find-my-Friends tracking method any more, although it still works.
* The *last_changed_time* for the iOS App device_tracker entity is now being monitored to detect a location time change. When a change is detected, a new `iOSApp Location Trigger` is issued and the updated location data is processed. This gets around the current problem with the iOS App trigger changes not being picked up by HA and then iCloud3. These include the Geographic Region Enter/Exit, Background Fetch, Significant Location Updates, and others.
* Extensive performance enhancements have been made to minimize the number of calls to the iCloud Web Services for location information and to Authenticate the device's access to the iCloud account. Previously, the account was Authenticated for each request. Now, it only Authenticates when needed. This has cut the number of data requests by over 60% and improves the response time, especially in poor cell areas.
* The Next Update Time determines when the next location request is made for the Family Sharing and Find-my-Friends tracking methods. The location request is now made 5-seconds before the Next Update Time is reached to, hopefully, give more time for the iCloud Web Service to locate all of the devices being tracked and, hopefully, reduce the number of old location being being returned and discarded.
* The Event Log has had some enhancements that improve the readability of the messages. The iCloud3 Statistics have been improved and provide more information in an easier to read format.
* You can make changes to the iCloud3 configuration parameters and restart iCloud3 without restarting HA. The new configuration file, `config_ic3.yaml` in the iCloud3 custom_component directory, lets you can specify most of the configuration parameters normally found in the HA configuration file. This includes the track_devices, waze parameters, zone parameters, timings, log_level, and others. This file is processed when HA loads and iCloud3 starts and when you restart iCloud3 on the Event Log screen. For example, you can add a new device to be tracked or change the stationary_inzone time without restarting HA. Only changes to the system level parameters, including user account/password, tracking method and sensors, require a HA restart.
* New configuration parameters:
  * `center_in_zone` - Specify if the device's location should be changed to the zone's location when the device in in a zone. Previously, this was not an option and it would always be moved to the zone center. Default: False
  * `old_location_threshold` - The timestamp age for the location is checked to insure it is timely. It the location is older than the threshold, it is discarded. The threshold can be calculated (12.5% of the travel time to the zone with a 5 minute maximum (default)) or you can specify a fixed time.
  * `config_ic3_file_name` - The name of the special iCloud3 configuration file. Default: *config_ic3.yaml*.
* The distance used to check if the device has wandered outside the zone is now based on the zone radius and gps accuracy threshold.
* Revamped a lot of the error and information messages displayed on the Event Log.

#### Bug Fixes

- Fixed a GPS wandering problem where the device would not be moved back into a zone when there was no zone exit trigger. The zone distance checks was comparing the current distance in meters to the limit distance in kilometers.

- Fixed a problem where an error was being generated and no devices were tracked if the iOS app v1 was being used.
- Fixed some problems with the iOS App tracking method, including zone exit detection, missed triggers and errors trying to access an iCloud account when it should not have been. The password parameter is no longer required when using the iOS App tracking method (the username is still required).
- Fixed a problem where the incorrect polling interval was used for devices experiencing repeated GPS accuracy or Old Location issues.
- When the device was in a zone and then exited the zone without an Exit trigger due to GPS wandering, the trigger update was supposed to be discarded so the state and zone would not change to 'not_home' (Away) when the device had not actually moved. An iOS App trigger was discarding the trigger but it was not discarded if the 'Next Update Time' was reached for FmF or FamShr tracking. This was fixed.

#### Special Notice for iOS App Version 1 users

* This version of iCloud3 still supports the iOS App version 1, which was discontinued over 6-months ago. This will be removed on the next update.

#### Special Thanks

* A special shout out goes to Quentame in Lyon, France. He has taken over support for the program (pyicloud.py) used to interface the HA/iCloud integration and Apples iCloud Web Services. This is the basis for the customized version used by iCloud3 (pyicloud_ic3.py)
* Another special thanks goes to Z Zeleznick at Berekley for developing the pyicloud.py Find-my-Friends add-on that is incorporated into the customized version (pyicloud_ic3.py) used by iCloud3.

#### Installing the iCloud3 Development Version into another custom_components directory

1. Change to the `config\custom_components` directory. You should see the `icloud3` directory listed.
2. Create the `icloud3_dev` iCloud3 Development directory.
3. Download all of the files in the GitHub `icloud3\development v2.2.0` into the `icloud3_dev` directory you just created on your HA system.
4. Copy the `icloud3-event-log.js` file into the `config\www\custom_cards` directory or into the directory you are currently using for the Event Log lovelace card.
5. In the HA configuration.yaml file defining the icloud3 platform, change `-platform: icloud3` to `-platform: icloud3_dev`. This points to the directory created in step 2 above.





Hopefully, you will find this release useful. I am especially excited to be able to use 2fa iCloud accounts again rather than going through the process of setting up non-2fa Find-my-Friends accounts. I hope the tuning and reducing the number of calls to iCloud Web Services for location information will make the program more responsive, especially in poor cell areas.

Version 2.1 was released in March, 2020 and has now been downloaded over 1000 times to users all over the world. If you do find it useful, you don't have to buy me a coffee, beer, gin-and-tonic or a glass of find New Zealand Sauvignon Blanc. But I would appreciate it if you would go to the iCloud repository (https://github.com/gcobb321/icloud3) and click on the star in the upper right corner.





Gary Cobb *(aka geekstergary)*

