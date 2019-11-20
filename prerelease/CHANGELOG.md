## iCloud3 v2.0.1a (11/20/2019)

The following changes have been made to iCloud3:
- If no location data was available while calculating the distance from Home using Waze, iCloud3 would go into an error correction mode and not repoll the device for valid location data. This has been corrected.
- If the a `location` request was made using the `icloud3_update` service call and the `notify.mobile_app_devicename` service was not available, did not exist or was named something else, an unformatted error would be added to the HA log file that did not explain the error. Additional error checking added and a friendly error message was added to the Event Log and HA log file that explains the problem.
