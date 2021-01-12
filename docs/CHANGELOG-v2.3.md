# iCloud3 Version 2.3 Change Log

The following enhancements and changes have been made iCloud3:

* The best way to monitor new releases is to add HACS (Home Assistant Community Store) to your HA system and set up the HACS/iCloud3 link using the instructions in the iCloud3 documentation [here](https://gcobb321.github.io/icloud3/#/chapters/3-hacs). 
* You can also go to the iCloud3 releases page [here](https://github.com/gcobb321/icloud3/releases) to download the latest version and do a manual update.

------

## Major enhancements

#### iCloud3 now works with Apple ID Verification and supports iCloud 2-factor-authentication

This is significant update to iCloud3. It supports true 2fa verification using the 6-digit Apple ID Verification Code sent from Apple when you log into iCloud.

When iCloud3 starts, you will get the standard Apple Login warning and the 6-digit Apple ID Verification Code notification. YOU WILL USE THAT 6-DIGIT CODE IN THE ID ENTRY SCREEN ON THE HA NOTIFICATIONS AREA. Select the Verification Code entry window like you always have from the HA Notifications area and enter the 6-digit code. This will create the Trusted Device token like other apps and browsers. iCloud3 will then continue starting as it usually does. Go [here](/1-getting-started?id=authenticating-your-icloud-account) for more information on entering the 6-digit authentication code.

#### The Find-my-Friends and Family Sharing tracking methods have been combined

You no longer need to assign a tracking method to use iCloud Location Services. The Find-my-Friends (fmf) and the Family Sharing (famshr) have been combined into a single tracking method (icloud) and operates on a per device basis. When iCloud3 starts, all the devices in iCloud account are retrieved and matched with those in the configuration file. They are retrieved from the *FindMy People* list, the *FindMy Me* screen (your device), and the *Family Sharing List*. Each phone will automatically select the appropriate tracking method based on how the phone's parameters are configured in the following manner:

- If the email address is specified for the phones and all phones are in the *FindMy* list, the location of all the phones in the *FindMy* list are located with one request. 
- If the email address is specified for the phones and one phone is not in the *FindMy* list but all are in the *Family Sharing List*, the location of all of the phones in the *Family Sharing* list are located with one request. Actually, iCloud locates all phones in the list, whether-or-not the phone is being tracked. If you have a large list, it will take a slightly longer for iCloud to locate all the phones than the above method.
- If the email address is specified for the phones and one phone is not in the *FindMy* list and another phone is not in the *Family Sharing List*, then it will take two requests to locate all the phones being tracked.

#### Enhancement to the method of configuring the devices to be tracked 

The *track_devices* configuration parameter has been depreciated and it is recommended that the *devices/device_name* parameter be used. Although ithe *track_devices* parameter can still be used to specify the devices, it will no longer be updated to support new parameters. 

The following example shows how the track_devices is converted to the devices/device_name parameters.

From:

```
track_devices:
  - gary_iphone > gary456@email.com, gary.png, _app
  - lillian_iphone > lillian678@email.com, lillian.jpg, noiosapp
```

To:

```yaml
devices:
  - device_name: gary_iphone
    email: gary456@email.com
    name: Gary
    iosapp_suffix: -app
  - device_name: lillian_iphone
    email: lillian678@email.com
    name: Lillian
    picture: lillian.jpg
    noiosapp: True
```

Other parameters include:

- *iosapp_entity* to specify the device_tracker.entity_id to be used for the device.
- *zone* to specify additional zones to be used in the tracking calculations.



## Other Changes

- **New Configuration Parameter**
  *display_zone_format: name/title/fname/zone, Default: name*

  This parameter indicates how the zone should be displayed in the device_tracker.[DEVICENAME] states field and on the Event Log. The zone is formatted as follows:
  
  - name - A reformatted zone name. Examples: 'the_shores' is displayed as 'TheShores'
  - title - A reformatted zone name. Example: 'the_shores' is displayed as 'The Shores'
  - fname - The zones Friendly Name. Example: 'The Shores Development'
  - zone - The actual zone name is displayed. Example: 'the_shores' is displayed as 'the_shores'
  
- **New Configuration Parameter:**

  *2sa_verification: True/False, Default: False*

  This parameter forces the 2-step-authentication procedure used in previous versions of iCloud3 instead of the 2-factor-authentication using the native Apple ID Verification Code released in iCloud3 v2.2.2.

- **Changed the priority order of searching for the config_ic3.yaml  configuration file to:**  

  This is based on the *config_ic3_file_name* parameter specified (or not specified) in *configuration.yaml*.

  1. *DirectorySpecified/FileNameSpecified*

  2. /config/*FileNameSpecified*

  3. /config/custom_components/icloud3/*FileNameSpecified*

  4. /config/config_ic3.yaml

  5. /config/custom_components/icloud3/config_ic3.yaml

- **Breaking Change - *icloud3_lost_phone* service**

  The *device_tracker.icloud3_lost_phone* service call as changed to *device_tracker.icloud3_find_iphone_alert* to match what the service call actually does and eliminate any confusion with the Apple's lost phone process. This service call uses the iCloud native process when using the Family Sharing tracking method and sends an alert (with sound) when using the Find-my-Friends and iOS App tracking method.

- **Battery Status**

  If the battery state is less than 10%, the polling interval is set to the *stationary_zone_interval* value (default is 30-minutes), regardless of the distance from home. If it is less than 5%, and the distance from Home is less than 1km, it will be set to 15-seconds. This change should help preserve battery life when the phone is in a low power mode.

- **Event Log Actions**

  - Reorganized the list of Actions
  
- Enhanced the information displayed in the Event Log when iCloud3 starts -- available devices, errors during initialization, current operations, status checks, etc.
  - Added the *Reset iCloud Interface* Action that removes the current iCloud communications sessions and restarts the iCloud interface program (pyicloud_ic3.py) that handles iCloud3 Location requests. It will:

    1. Rename the current cookies and session files in the */config/.storage/icloud* directory to save them.
    2. Create new cookies and session files.
    3. Request iCloud authorization which will send the Apple Id Verification Code notification to the trusted phone with the 6-digit Verification Code
    4. Set up the configuration form in the HA Notifications area for entering the 6-digit verification code.
    5. Restart iCloud3 and reinitialize the iCloud Interface program.  

- Added additional error checking and reporting 

  

## Bug Fixes

- Fixed a problem calculating the default *old_location_threshold* value.
- Fixed a problem where iOS App was reporting a state change when it had not changed.
- Fixed a problem that occurred when the device's name was 'iPhone'.
- Fixed other minor problems.





Gary Cobb *(aka geekstergary)*

January, 2021

------

#### Special Thanks

* A special thanks goes to Noccolo Zapponi, London for updating *pyicloud.py* to support true Apple iCloud 2-factor-authentication. His changes have been incorporated into *pyicloud_ic3.py* used by iCloud3. ?