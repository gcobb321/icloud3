## iCloud3 Version 2.2.0 - Release Candidate Change Log

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