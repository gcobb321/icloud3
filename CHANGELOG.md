# iCloud3 Change Log

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

