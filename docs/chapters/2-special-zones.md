# Special Zones

There are two zones that are special to the iCloud3 device tracker - the `Dynamic Stationary Zone` and the `NearZone` zone.

### Dynamic Stationary Zone  

A Dynamic Stationary Zone is a zone that iCloud3 creates when the device has not moved much over a period of time. Examples include when you are at a mall, doctor's office, restaurant, friend's house, etc. If the device is stationary, it's Stationary Zone location (latitude and longitude) is automatically updated with the device's gps location, the device state is changed to Stationary and the interval time is set to the `stationary_inzone_interval` value (default is 30 mins). This almost eliminates the number of times the device must be polled to see how far it is from home when you haven't moved for a while. When you leave the Stationary Zone, the IOS App notifies Home Assistant that the Stationary Zone has been exited and the device tracking begins again.

You do not have to create the Stationary Zone in the `zones.yaml` file, the iCloud3 device tracker automatically creates one for every device being tracked when Home Assistant is started. The initial location is latitude 90°, longitude 180° (the North Pole). It's name is `devicename_stationary`.  

Details about the Stationary Zone:
- You must be at least 2.5 times the Home zone radius before you can be put into a stationary zone.
- The Stationary Zone radius is 2 times the Home zone radius.
- If your distance from a zone (Home) is less than 4 times the zone's radius and you haven't moved for one-half of the `stationary_still_time` (4-minutes if using the default value), you will be put into the Stationary Zone. Normally, the polling interval will be 15-seconds at this distance. This reduces the number of polls if you are close to but not in a zone and are not moving.
- The maximum distance you can move in a specific amount of time is 1.5 times the Home zone radius.
- The amount of time you must be still is specified in the `stationary_still_time` configuration parameter (default is 8 minutes).


### 'near_zone' Zone  

There may be times when the Home zone's (or another zone's) cell service is poor and does not track the device adequately when the device gets near the zone. This can create problems triggering automations when the device enters the zone since the Find-My-Friends location service has problems monitoring it's location.  

To solve this, a special 'near_zone' zone can be created that is a short distance from the real zone that will/may wake the device up. The IOS App stores the zone's location on the device and will trigger a zone enter/exit notification which will then change the device's device_tracker state to the 'near_zone' zone and then change the polling interval to every 15-secs. It is not perfect and might not work every time but it is better than automations never being triggered when they should.

You can have more than one 'near_zone' zone in the `zones.yaml` file. Set them up with a unique name that starts with 'near_zone', e.g., `near_zone_home`, `near_zone_quail`, `near_zone_work`, etc. The `friendly_name` attribute should be `NearZone` for each one.

