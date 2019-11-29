# iCloud3 Change Log

#### v2.0.4 (11/29/2019)
- When the device's location, interval and next poll information were being updated, there were times when the state was 'stationary' but it had actualy moved into another zone. This might be caused by zones being close together, by no zone exit notification from the ios app or by the next update trigger being processed before the zone exit trigger had been received. This caused the device's location to be reset to the old location instead of the new location. This has been fixed.
- Waze history data is used to avoid calling Waze for route information when you are near another device or in a stationary zone with accurate Waze route information. If you were in a stationary zone and entered another zone without a zone exit trigger, the Waze history was still pointing to the old stationary zone. The old location information was being used for distance and interval calculations instead of the new location information.  A check was added to always refresh the Waze route information when the state changes.
- Made some corrections to the iCloud3 documentation.

#### v2.0.3 (11/27/2019)

- Fixed a problem with a malformed message that displayed old location information in the Event Log.
- Added a list of devices that are tracked and not tracked for the Family Sharing (famshr) tracking method. This is creaed when the iCloud account is scanned looking for the devices in the `track_devices` configuration parameter.

#### v2.0.2 (11/27/2019)

- Fixed problem calculating distance and intervals for a second zone.
- Reformatted some Event Log messages.

#### v2.0.1 (11/26/2019)

- If no location data was available while calculating the distance from Home using Waze, iCloud3 would go into an error correction loop and hang up. This has been corrected.
- If the a location request was made using the icloud3_update service and the notify.mobile_app_devicename service was not available, an unformatted error would be added to the HA log file that did not correctly explain the error. A friendly error message better explaining the problem is now added to the Event Log and HA log file.
- Stationary zone location information was not being refreshed correctly on subsequent polls. It was showing as (None, None) in the HA log file and may have generated an error message or used the wrong location when moving back to the center of the stationary zone. This has been corrected.
- Using the FamShr tracking method generated an 'IndexError: tuple index out of range' error message and would not iCloud3 load. This has been corrected.
- Additional error checking has been added to recover from situations when no location information was available when calculating the distance moved from the last location to the current location. If this happens, the distance moved will be 0 km.
- The 'manifest.json' file was pointing to wrong GitHub repository.
- Changed the 'pyicloud_ic3.py' version to 1.0.

---

A comprehensive list of all of the new features and enhancements for iCloud3 v2.0 is in the Change Log in the iCloud3 Documentatiioon.



[![button_documentation](docs/images/button_documentation.jpg)](https://gcobb321.github.io/icloud3/#/)

[![button_download_long](docs/images/button_download_long.jpg)](https://github.com/gcobb321/icloud3/releases)

[![button_github](docs/images/button_github.jpg)](https://github.com/gcobb321/icloud3)

