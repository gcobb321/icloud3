## iCloud3 v2 Change Log - Prerelease Updates

### Installation Instructions
Copy `device_tracker.py` to the `config/custom_components/icloud3` directory.

#### v2.0.1e (11/23/2019)

- Stationary zone location information was not being refreshed correctly on subsequent polls. It was showing as (None, None) in the HA log file and may have generated an error message or used the wrong location when moving back to the center of the zone. This has been corrected.
- Using the FamShr tracking method generated an 'IndexError: tuple index out of range' error message and would not work. This has been corrected.
- Additional error checking has been added to recover from situations when no location information was available when calculating the distance moved from the last location. If this happens, the distance moved will be 0km.

- iCloud3 has been added to the list of HACS default repositories/integrations. The iCloud3 documentation was updated to provide installation instructions using HAS.

#### v2.0.1b (11/21/2019)

- Added additional checks for valid location data.

#### v2.0.1a (11/20/2019)
- If no location data was available while calculating the distance from Home using Waze, iCloud3 would go into an error correction mode and not repoll the device for valid location data. This has been corrected.
- If the a `location` request was made using the `icloud3_update` service call and the `notify.mobile_app_devicename` service was not available, did not exist or was named something else, an unformatted error would be added to the HA log file that did not explain the error. Additional error checking added and a friendly error message was added to the Event Log and HA log file that explains the problem.

- 