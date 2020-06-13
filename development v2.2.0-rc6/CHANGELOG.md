## iCloud3 Version 2.2.0 Change Log

The following enhancements and changes have been made iCloud3 v2.1.0

Note: You can set up this prerelease version in another custom_components directory and still keep the v2.1.0 version maintained by HACS that you are currently using. Instructions on doing this are at the end of the Change Log.

------

#### Major Enhancements

* iCloud 2fa accounts live again. The `Family Sharing` tracking method has been rewritten with the new version of iCloud Web Services Interface program (pyicloud-ic3.py). You can now track devices that are shared on your 2fa account without receiving constant account access notifications. You are not forced to set up a non-2fa account and use the Find-my-Friends tracking method any more, although it still works.
* The *last_changed_time* attribute for the iOS App device_tracker entity is now being monitored to detect a location time change. When a change is detected, a new `iOSApp Location Trigger` is issued and the updated location data is processed. This gets around the current problem with the iOS App trigger changes not being picked up by HA and then iCloud3. These include the Geographic Region Enter/Exit, Background Fetch, Significant Location Updates, and others.
* Extensive performance enhancements have been made to minimize the number of calls to the iCloud Web Services for location information and to Authenticate the device's access to the iCloud account. Previously, the account was Authenticated for each request. Now, it only Authenticates when needed. This has cut the number of data requests by over 60% and improves the response time, especially in poor cell areas.
* The Next Update Time determines when the next location request is made for the Family Sharing and Find-my-Friends tracking methods. The location request is now made 5-seconds before the Next Update Time is reached to, hopefully, give more time for the iCloud Web Service to locate all of the devices being tracked and, hopefully, reduce the number of old location being being returned and discarded.
* The Event Log has had some enhancements that improve the readability of the messages. The iCloud3 Statistics have been improved and provide more information in an easier to read format.
* You can now make changes to most of the iCloud3 configuration parameters without restarting HA. The iCloud3 parameters are normally specified in the HA configuration file; changes to the parameters requires restarting HA. Now, you can also specify the iCloud3 configuration parameters in it's own configuration file, *config_ic3.yaml*. Parameters from this file are read when HA starts and when iCloud3 is restarted on the Event Log screen. The file is stored in the iCloud3 custom_components directory although you can specify another directory/file name using the `config_ic3_file_name` parameter in the normal HA configuration file. The parameters that can be specified in this file include the track_devices, waze parameters, zone parameters, timings, log_level, and others. System level parameters (username/password, tracking method, sensor includes/excludes and the configuration file name) must be in the HA configuration file, A sample file (*config_ic3_sample.yaml*) is installed with iCloud3 updates.
* The components of iCloud3 are stored in two directories, namely the iCloud3 is in the *custom_components/icloud3* directory and the Event Log is in the directory you use for your custom Lovelace cards. HACS can be used to install and update iCloud3, but, HACS can not install the Event Log in the custom cards directory; it can only install it in the custom components directory. iCloud3 now checks to see if the custom card version is older than the one in the custom components directory when it starts. If an older version is found, it will be automatically updated. A note is displayed in the Event Log when it is updated so you can refresh your browser pages and the iOS App. The `event_log_card_directory` configuration parameter lets you specify the directory containing the Event Log card if it is in a directory other than *config/www/custom_cards. The Lovelace>Resources parameter in your HA configuration file also has the directory name.

#### New configuration parameters:

* `center_in_zone` - Specify if the device's location should be changed to the center of the zone when it is in a zone. Previously, would always be moved to the zone center. Valid Values: True, False  (Default: False)
* `old_location_threshold` - When a device is located, the location's age is calculated and the update is discarded if the age is greater than the threshold. The threshold can be calculated (12.5% of the travel time to the zone with a 5 minute maximum (default)) or you can specify a fixed time using this parameter.
* `stationary_zone_offset` - The stationary zone is created when iCloud3 starts (or is restarted) and is located 1km north of the Home Zone location. There may be times when this conflicts with your normal driving route and you find yourself going in and out of the stationary zone. With this parameter, you can change it's initial location. The format is:
  * stationary_zone_offset: #,# - Specify the number of kilometers from the Home zone. The first parameter adjusts the latitude (north/south), the second parameter adjusts the longitude (east/west).
    * Example: stationary_zone_offset: 1, 2 (1km North, 2km East)
    * Default: stationary_zone_offset: 1, 0
  * stationary_zone_offset: (latitude, longitude) - Specify the GPS coordinates (you must include the parentheses). 
    * Example: stationary_zone_offset: (27.738520, -75.380462)
* `config_ic3_file_name` - iCloud3 parameters can be specified in it's own configuration file (*config_ic3.yaml*) and the parameters are used when iCloud3 is restarted on the Event Log screen and when HA starts. This lets you change the the parameters and have them take effect without restarting HA. All parameters except the username/password, tracking method and included/excluded sensors and this parameter can be specified. This includes the devices to be tracked, timings, location parameters, log_level, and others. If you want to use a different file, specify it's name with this parameter. 
  * *Valid values:* Standard file name   *Default Value:* 'config_ic3.yaml'
  * Note: This file is optional and will only be processed if it is found in the custom components directory or in another location specified by this parameter.
  * Note: An entry is displayed in the Event Log when iCloud3 starts with the name of the file, if found, is processed..
  * Note: A sample file, `config_ic3_sample.yaml`, is installed with iCloud3.
* `event_log_card_directory` This contains the directory used to store the iCloud3 Event Log Lovelace card. The Event Log version (*icloud3-event-log-card.js*) is checked when iCloud3 starts to verify the latest version is installed. If not, the version in the custom components directory is copied to the Event Log directory.
  * *Valid values:* Standard file name   *Default Value:* 'www/custom_cards'



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

#### Installing the iCloud3 Development Version into another custom_components directory

1. Change to the `config\custom_components` directory. You should see the `icloud3` directory listed.
2. Create the `icloud3_dev` iCloud3 Development directory.
3. Download all of the files in the GitHub `icloud3\development v2.2.0` into the `icloud3_dev` directory you just created on your HA system.
4. In the HA *configuration.yaml* file that defines the icloud3 platform, change `-platform: icloud3` to `-platform: icloud3_dev`. This points to the directory created in step 2 above.
5. Copy the `icloud3-event-log.js` file into the `config\www\custom_cards` directory or into the directory you are currently using for the Event Log lovelace card. 
6. Refresh your browser so the new Event Log will load when you select it. You can do the following:
   1. Chrome: 
      1. Select the 3-dots in the upper-right corner of the Chrome window next to your picture (Customize and Control Google Chrome).
      2. Select  `More Tools`.
      3. Select `Clear Browsing Data`.  Check `Cached Images and Data`. Then click `Clear Data`.
      4. Reload the HA window as you normally do.
      5. Select the Lovelace window containing the Event Log card. 
      6. Click the `Refresh` button on the Chrome Title bar to refresh the page.
   2. iPhone or iPad:
      1. Open the iOS App.
      2. Touch the `App Configuration` in the HA Sidebar on the left side of the screen.
      3. Scroll to the bottom. Touch `Reset Frontend cache`
      4. Touch `Done` to close the App Configuration window.
      5. Close the Sidebar. Scroll down from the top of the screen to reload Lovelace on the iPhone or iPad. 

------

#### Special Notice for iOS App Version 1 users

* This version of iCloud3 still supports the iOS App version 1, which was discontinued over 6-months ago. This will be removed on the next update.

------

Hopefully, you will find this release useful. I am especially excited to be able to use 2fa iCloud accounts again rather than going through the process of setting up non-2fa Find-my-Friends accounts. I hope the tuning and reducing the number of calls to iCloud Web Services for location information will make the program more responsive, especially in poor cell areas.

Version 2.1 was released in March, 2020 and has now been downloaded over 1000 times to users all over the world. If you do find it useful, you don't have to buy me a coffee, beer, gin-and-tonic or a glass of find New Zealand Sauvignon Blanc. But I would appreciate it if you would go to the iCloud repository (https://github.com/gcobb321/icloud3) and click on the star in the upper right corner.

Gary Cobb *(aka geekstergary)*



#### Special Thanks

* A special shout out goes to Quentame in Lyon, France. He has taken over support for the program (pyicloud.py) used to interface the HA/iCloud integration and Apples iCloud Web Services. This is the basis for the customized version used by iCloud3 (pyicloud_ic3.py)
* Another special thanks goes to Z Zeleznick at Berekley for developing the pyicloud.py Find-my-Friends add-on that is incorporated into the customized version (pyicloud_ic3.py) used by iCloud3.