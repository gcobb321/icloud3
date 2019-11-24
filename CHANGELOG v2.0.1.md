# iCloud3 v2.0.1 Change Log (11/24/2019)

The iCloud3 v2.0 Change Log has been incorporated into the documentation for iCloud3. This only contains the v2.0.1 Maintenance Update changes

- If no location data was available while calculating the distance from Home using Waze, iCloud3 would go into an error correction loop and hang up. This has been corrected.
- If the a location request was made using the icloud3_update service and the notify.mobile_app_devicename service was not available, an unformatted error would be added to the HA log file that did not correctly explain the error. A friendly error message better explaining the problem is now added to the Event Log and HA log file.
- Stationary zone location information was not being refreshed correctly on subsequent polls. It was showing as (None, None) in the HA log file and may have generated an error message or used the wrong location when moving back to the center of the stationary zone. This has been corrected.
- Using the FamShr tracking method generated an 'IndexError: tuple index out of range' error message and would not iCloud3 load. This has been corrected.
- Additional error checking has been added to recover from situations when no location information was available when calculating the distance moved from the last location to the current location. If this happens, the distance moved will be 0 km.
- The 'manifest.json' file was pointing to wrong GitHub repository.
- Changed the 'pyicloud_ic3.py' version to 1.0.

---
[![button_documentation](docs/images/button_documentation.jpg)](https://gcobb321.github.io/icloud3/#/)

[![button_download_long](docs/images/button_download_long.jpg)](https://github.com/gcobb321/icloud3/releases)

[![button_github](docs/images/button_github.jpg)](https://github.com/gcobb321/icloud3)

