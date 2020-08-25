## iCloud3 Version 2.2.0 - Release Candidate Change Log

> iCloud3 Documentation, with the new features (well most of them), is almost done and can be found [here](https://gcobb321.github.io/icloud3_docs/#/).



#### Installation Instructions

- **Download only changed programs** - Download the programs that have been changed into the `\config\custom_components\icloud3`directory on the device running Home Assistant. 

- **Download all Release Candidate programs** - Click on the icloud3-v2.2.0-rc#.zip zip file. Then click 'Download' on the right side of the screen. Then unzip the downloaded zip file into the `\config\custom_components\icloud3`directory on the device running Home Assistant. 

When iCloud3 starts, the *icloud3-event-log-card.js* file will be copied to the `\config\www\custom_cards` directory (or the directory you have specified on the *event_log_card_directory* configuration file parameter). 

##### iCloud3 v2.2.0 Documentation

The documentation for v2.2.0 is undergoing a major reorganization to better explain how to:

- Prepare for using iCloud3
- Install and configure the support programs needed for iCloud3
- Install iCloud3
- Set up iCloud3 to begin tracking devices
- Trouble shoot issues getting iCloud3 up-and-running, when devices are not being tracked, etc.

It is a work in process and can be viewed in the iCloud3-docs repository [here](https://https://gcobb321.github.io/icloud3_docs/#/).



If you want to run the Release Candidate from another directory and still keep your 'production' version of iCloud3, see the instructions [here](https://github.com/gcobb321/icloud3/blob/master/v2.2.0-Release%20Candidate/CHANGELOG.md).

------
#### Release Candidate 11e (8/25/2020)

- The iOS App state will be updated when it becomes available after the initial iCloud locate.
- Fixed a bug related to the Waze Region not being decoded correctly. Example: The valid Europe code is EU but iCloud3 was using a validation code 'eu' causing it to default to US.
- Added back the max_interval parameter. If the interval is greater than the max_interval and you are not in a zone, the interval is set to the max_interval. This is useful if you are a far from Home and want to refresh your location data on a shorter interval than one based on the Waze travel time. Default: '4 hrs'
- Changed the nature of the *config_ic3.yaml* file handling. 
  - If the file name is fully qualified and contains the directory and filename (it have to has a '/'), that is used
  - If the filename is found in */config/custom_components* directory, that file is used.
  - If the filename is found in the */config* directory, that file is used.
  - Otherwise a file not found error is added to the Event Log. 



#### Release Candidate 11d (8/24/2020)

- If no data is available from the iOS App (no Latitude attribute), the iCloud3 data will be used instead of restarting iCloud3. This potentially solves a timing issue where iCloud3 starts before the iOS App has been initialized. A message is added to the Event Log every 2-minutes until the iOS App data becomes available.
- Fixed a bug where an iOS App trigger was not being processed when the last_update_trigger change time was the same as the iOS App's device_tracker state change time.
- All iOS App location data, except enter/exit triggers, is now validated for GPS accuracy and to determine if the location is old. Previously, only triggers in a specific list of triggers, based on the iOS App documentation, were validated. This eliminates needing to update iCloud3 if new triggers are added to the iOS App.



#### Release Candidate 11c (8/22/2020)

- Added error checking in the mobile_app notify services extraction routine.

- If this was a new installation and the icloud user account has not been authenticated with the 6-digit verification code, accessing the iCloud account when icloud3 was starting was generating errors, preventing the account from being authenticated.This has been fixed (I hope).

- Reverted resetting the stationary zone timer on an old Location or bad gps item. Now, the timer will not be reset and the location must be good when the time is reached to move into a stationary zone.



#### Release Candidate 11b (8/19/2020)

- iCloud3 now scans the hass.services/notify list and extracts the iOS App Device Name for the phone that is used to send locations requests to. This eliminates the need to make any changes to the Device Name on the phone. They are listed in the Event Log iCloud3 Initialization Stage 3 for reference.

- The 'move into stationary zone' timer is reset if an old location or poor gps trigger is discarded.

- If an iCloud3 configuration file is specified (config_ic3.yaml), the file locations checked are /config & /config/custom_components/icloud3 directories/

#### Release Candidate 11a (8/18/2020)

- When iCloud3 starts, a test message is sent to the phone to make sure the Device Name onf the phone matches the device name of the device_tracker entity being monitored. If an error was encountered, an error message is displayed with the device name, including 'mobile_app'. The 'mobile_app' text is not part of the device name and should not habe been displayed. This has been corrected.

- Fixed an error generated by an invalid variable name 'devicenme' displaying another error message.

- Fixed a problem decoding the version number in the Event Log.

  


#### Release Candidate 11 (8/17/2020)

This release has been tested with the latest version of the iOS App on the Apple App Store (2020.5.2) and the latest with the beta release (2020.6 (4)).

- Tracking method FmF now works with the normal 2f iCloud account.
- A request_location_update message is sent to the tracked_device during initilization to see if a notify can be successfully sent or if it generates an error. If an error is found, an iCloud3 Error message is displayed with instructions on changing the Device Name on the phone to correct the error.
- Cleaned up and optimized code in the Event Log.
- Validating the iOS App device to be tracked was from iC3 initialiation Stage 2 to Stage 3. Errors are clearer and correction instruction are clearer.
- Changed the way the iOS App monitor is displayed in the Event Log. It now displays if an update will be triggered or not and the reason. The iOS App Monitor is refreshed if you do a 'Refresh' in the Event Log so it will then display if you select ehe 'Show Event Log Tracking Details'.
- Added a 'display_as' configuration parameter that changes one text value to another in the Event Log before it is displayed. For example, you can display your email address as' gary-2fa@email.com' instead of your real email address.

  

#### Release Candidate 10 (7/20/2020)

[Programs changed: *device_tracker.py, icloud3-event-log-card.js*]

* Added the `Actions` selection list to the Event Log card. This list contains iCloud3 commands that interact with and control iCloud operations. The commands include Restart iCloud3, Pause and Resume polling, Show/Hide tracking details, Start/Stop adding debug records to the HA Log file, Export the Event Log to a text file. Some commands can be used on the selected device.
* Added the ability to export the Event Log to a tab delimited file suitable for importing into Excel or another spreadsheet program. The file, `\config\icloud3-event-log.log` , is created using a command on the `Actions` selection list on the Event Log.
* The iOS App has been changed to issue a zone Region Enter trigger before it has really entered the zone if the zone's radius is less than 100m. Since the distance to the zone was greater than the zone's radius, the device was really outside the zone and iCloud3 would keep the device in an Away state instead of accepting the trigger. This has been changed to support the new way the iOS App determines when a device is close enough to a zone to issue a Region Enter trigger.
* When iCloud3 starts, it matches the track_devices devicenames with the iOS App device_tracker entities. To help solve problems when iCloud3 starts and the entities can not be matched, all of the mobile_app device_tracker entities are now displayed in the Event Log. 



#### Release Candidate 9b (7/11/2020)

[Programs changed: *device_tracker.py*]

- Update reason was sometimes not displayed on messages
- Added back Moving into Stationary Zone time check to use iCloud update rather that the iOS App update routines. This will recheck any movement and retest moving into the Stationary Zone.
- When selecting the zone, the Stationary Zone is now bypassed if it is set to it's base location (radius = 1m)
- Fixed a problem where an update was discarded if the it was trigged by a state or trigger change and the Location was old or the gps was poor. It should have verified the location using iCloud and it was not. This could cause Region Enter/Exit triggers to be delayed until the next update time was reached.
- Fixed the old location/poor gps accuracy test in the main polling loop..
- Removed debug code left in by mistake when testing the old location/poor gps accuracy value. The debug code always returned True and would fill the HA log file and Event Log with incorrect Discarded messages when it shouldn't have.
- Changed the formatting of Old Location/Poor GPS Accuracy messages.
- Change the formatting of the GPS Location in the Event Log to show the GPS Accuracy value. <br>Example: GPS-(27.4343, -84.343434)/65m) where the accuracy is 65m

#### Release Candidate 9 (7/9/2020)

[Programs changed: *device_tracker.py, icloud3-event-log-card.js*]

* The iOS App v2020.3 Added the Device Name setting to the General Tab option. This may have created a new device_tracker entity for the updated app. When this occurred, there may now be 2 device_tracker entities for the same iPhone or other device. iCloud3 scans the Entity Registry to determine the device_tracker entity to monitor for state & trigger changes. It stops scanning when it finds one a match. This may result in iCloud3 monitoring an entity that is no longer updated by the iOS App and not monitoring the entity that is updated. This has been fixed. Rather than stopping at the first one, it looks for all entities that can be monitored. If there is only one, that one is used. If there is more than one, iCloud3 looks at the track_devices parameter to see if an entity has been specified. If one has been specified, it is used. If one has not been specified, an error message is displayed in the Event Log and the last entity found is used rather than the first one found.

		To select the entity in case of duplicates, add the complete entity name or it's iOS App suffix to the track_devices parameter. For example:

		```
		gary_iphone > gary.jpg, Gary, _iosapp
		gary_iphone > gary.jpg, _iosapp_2
		gary_iphone > gary.jpg, gary_iphone_iosapp
		gary_iphone > gary_2fa@email.com, gary.png, _2
		```
		Note: The iOS App suffix is the full entity name without the devicename, e.g., Entity name=gary_iphone_iosapp , Suffix=_iosapp

* When several phones were in a Stationary Zone and one left and then came back, the iOS App issues a Region Enter trigger for the phone coming back with another phone's Stationary Zone. Since each phone has their own Stationary Zone, this phone's Stationary Zone is now in the wrong location and it was not handling location triggers correctly. Also, since the iOS App has the phone in 2 Stationary Zones and iCloud3 only has it in one, any Exit triggers would be discarded and iCloud3 would keep the phone in the Stationary Zone rather than changing it to not_home. This has been corrected.

* Added status messages that are displayed in the *sensor.devicename_info*' field during iCloud3 startup and when locating devices.

* Added a friendly error message when the connection to Waze (www.wazw.com) was not available. If this occurs, Waze will be turned off.

* Changed the way long text items are displayed in the Event Log.

* Added a test of the device_status before determining is the location is old. If not 'online' (offline or pending), the device interval will be immediately set to 15-minutes. This prevents getting into the cycle of discarding the location update because the location is actually not available.

* Added more debug messages to the Event Log.

   


#### Release Candidate 8 (6/25/2020)

- Added checks to make make sure the initial stationary zone would not be selected when entering a zone.

- Changed the location of the Stationary Zone back to it's base location when it is Exited rather than keeping it at it's current location, hiding it and reducing it's size.

- Fixed a problem where the Stationary Zone not was being relocated before the device's distance and polling calculations were done. This lead to selecting the Stationary Zone in error when it had really been exited from.

- Adjusted some column sizes on the Event Log.

  

#### Release Candidate 7 (6/23/2020)

- If iCloud did not return device data for a device being tracked when iCloud3 is being initialized, the iCloud account will be reauthenticated, the iCloud device will be requested again. and the devices will be reverified. If a device (devicename) is still not found, an iCloud Error will be generated and the devicename will not be tracked.

* iCloud3 was updating the iOS App's last_trigger_update entity when a location update was done. It would add the time the update was done and the change the reason for the update if it was triggered by iCloud3. HA and the iOS App had been changed so updating the last_update_trigger entity by iCloud3 broke the link between last_update_trigger and the iOS App. The result is HA would throw away the triggers generated by the iOS App. These triggers included the zone Enter/Exit, Significant Location Update, Background Fetch, etc. This has been fixed.

* Added more checks to make make sure the initial stationary zone would not be selected when entering a zone.

* Corrected the Event Log column formatting for the iPhone, iPad (more to be done here) and in a browser.

  

#### Release Candidate 6 (6/12/2020)

* Added an Event Log card version check. When iCloud3 starts, the version of the Event Log in the *custom_components /icloud3* directory is compared to the Event Log in the *www/custom_cards* directory. If the version in the custom_components directory is newer, it will be copied to the custom cards directory and a message is displayed in the Event Log indicating that the Event Log was updated and the browser and the iOS App cache's need to be cleared and refreshed. See the Change Log for more details.

#### Release Candidate 5 (6/2/2020)

* The initial stationary zone's location is 1 km north of your home zone and, if your normal driving route takes you through the stationary zone, you will trigger zone enters/exits. This update lets you move the initial stationary zone to avoid this situation using the `stationary_zone_offse`t parameter. With it, you can specify the exact GPS coordinates of the Initial Stationary Zone or specify a 1km offset multiplier (north or south, east or west) of the Home zone. 
  
  * Examples: '1,0' - Offset 1km North, '2,-1' - Offset 2km North, 1km East of Home, '(27.738520, -75.380462)' - Specify the GPS coordinates
  
    

#### Release Candidate 4 (5/31/2020)

* The Event Log will only show the state/zone/interval/travel time/distance line when the values change. This reduces the size of the Event Log and improves it's readability.

* Cleaned up the Event Log code and made several visual changes.

* Errors encountered when sending a message to a device are now caught. The error and message are displayed in the HA log and on the Event Log.

* Increased the number of records that will be displayed in the Event Log.

* When the account needed to be authenticated in the Web Services Program (pyicloud-ic3.py), an 'Error 450' error message was displayed in the HA Log. This has been changed to an Info message that describes that the authentication is needed.

* The battery level from the iOS App is now displayed when using the Find-my-Friends tracking method or when the battery level is not available when using the Family Sharing tracking method.

* Cleaned up and tuned some more code.

  

#### Release Candidate 3 (5/27/2020)

* Fixed an issue where the iOS App location request time was not set available, creating an error when restarting ic3 multiple of times on the Event Log screen.

* iCloud3 was using legacy HA DeviceScanner code that was made available for people running HA versions before 0.95. iCloud3 will now use the current code rather than legacy code.

* Changed the "Error 450" error message generated by pyicloud_ic3.py when the iCloud account needed to be authenticated from an 'error' message to an 'info' message. It now just indicates a reauthentication is needed, which is then done by iCloud3.

  

#### Release Candidate 2 (5/26/2020)

* Fixed the error generated if running older versions of HA that do not have the zone.reload service call.

* Revamped the Trusted Device selection and code entry forms to fix some issues where the Trusted Devices were not displayed.

* Did some home house keeping and added a few error trapping routines.