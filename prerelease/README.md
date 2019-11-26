## iCloud3 v2 Change Log - Prerelease Updates

### Installation Instructions
Copy `device_tracker.py` to the `config/custom_components/icloud3` directory.

#### v2.0.2 (Prerelease Status 11/26/2019)

- Fixed problem calculating distance and intervals for a second zone.
- If the device_tracker.state is 'stationary' when the next update time is reached and you have moved into another zone that is not stationary, the 'zone' attribute is correct because it is based on the device's location values but the device_tracker.state is still 'stationary' instead of the zone the device is now in. This has been fixed.

#### v2.0.1 (General Availability on 11/23/2019)

- If no location data was available while calculating the distance from Home using Waze, iCloud3 would go into an error correction loop and hang up. This has been corrected.
- If the a `location` request was made using the `icloud3_update` service and the `notify.mobile_app_devicename` service was not available, an unformatted error would be added to the HA log file that did not correctly explain the error. A friendly error message better explaining the problem is now added to the Event Log and HA log file.
- Stationary zone location information was not being refreshed correctly on subsequest polls. It was showing as (None, None) in the HA log file and may have generated an error message or used the wrong location when moving back to the center of the stationary zone. This has been corrected.
- Using the FamShr tracking method generated an 'IndexError: tuple index out of range' error message and would not iCloud3 load. This has been corrected.
- Additional error checking has been added to recover from situations when no location information was available when calculating the distance moved from the last location to the current location. If this happens, the distance moved will be 0km.