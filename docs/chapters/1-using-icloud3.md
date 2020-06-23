# Setting Up your iCloud Account

### What other programs do I need
The `Home Assistant iOS App` is all. You do not need OwnTracks or other location based trackers and you do not need Nmap, netgear, ping or any network monitor. The Home Assistant iOS App will notify Home Assistant when you leave Home or another zone and iCloud3 device tracker will start keeping up with the device's location, the distance to the zones and the time it will take to get each one.

!> The iOS App settings `Zone enter/exit, Background Fetch and Significant Location Change` location settings need to be enabled. 

The iCloud3 platform allows you to detect presence using the  iCloud Location Service. (Go [here](https://www.icloud.com/) for more information). iCloud allows users to track their location on iOS devices. Your device needs to be registered with Find-my-Friends or Family Sharing.

The HA proximity component also determines distance between zones and the device, determines direction of travel, and other device_tracker related functions. Unfortunately, the iOS App reports old location information on a regular basis that is processed by the proximity component. 
​		
!> It is highly recommended to not use the proximity component when using iCloud3. iCloud3 duplicates the proximity functions and discards bad location information where the proximity component does not.

### What if I don't have the iOS App on my device
The Home Assistant iOS App issues zone enter/exits and pushes location updates to HA while the iCloud Find-my-Friends and Family Sharing tracking methods issues location updates and other device information when polled by iCloud3. If the iOS App is not installed on the device, the zone enter/exits will not be picked up when they actually happen.

The device will be updated, however, on the next poll by iCloud3. The problem with not having the iOS app installed is if you are in a zone and on a 2-hour polling interval, it could be 2-hours before the device goes to a not_home state. With the iOS App, the zone exit is pushed to HA where it gets picked up by iCloud3 and the device's state is changed. This happens within 10-seconds of getting the exit notification for the zone. Naturally, if you are in a poor service area, this notification may be delayed.


### Locating Your Device with iCloud
iCloud Location Services provides 2 methods for locating your iPhone or other device. The `tracking_method` and `track_devices` configuration parameters are used to indicate how tracking should be done and the devices to be tracked.

#### Family Sharing (FamShr) {docsify-ignore}
This is the easiest of the two iCloud Web Services methods to set up. iCloud3 looks for the devices to be tracked in the list of people that are in the Family Sharing list on your iCloud account. With Family Sharing, you use your iCloud account email address for the `username`  configuration parameter.

#### Find-my-Friends (FmF) {docsify-ignore}

You set up friends on the `Find My` app (iOS 13) or the `Find-my-Friends` app (iOS12) and iCloud3 will locate them just like the app does. Since your Apple iCloud account probably has 2fa turned on, you need to:

    1. Add a new iCloud account with a different email address with 2fa turned off. You will use this email address in the `username` configuration parameter.

!> This is easier to set up if you do it on a device you will not be locating. 

!> iOS 13 turns on 2fa automatically and it can not be turned off. The non-2fa account should be added on a computer instead of an iPhone or iPad.

2. Add the 'friends', the people that use the devices you want to track, in the `Contacts` app when you are signed into this new account. You only need to enter their name and the email address of their actual iCloud account. 

!> Only one device can be tracked for each email address. You can not track both an iPhone and an iPad used by the same person.

3. Add them to the `Find My` app (iOS 13) or the `Find-my-Friends` (iOS 12) app. You will need to send friend requests and then confirm them on each device so you will need to have access to their devices. 
4. Verify that the `Find My` or the `Find-my-Friends` app and your iCloud account at icloud.com can locate your 'friends' before continuing to set up iCloud3. They should be displayed on the map in the app when signed into the new non-2fa account and the 'Sharing With ...'  message should be displayed in the app when you are signed into the 2fa account. 

!> If the devices can not be seen in the app, they will not be located by iCloud3.

5. Now that you have verified that everything is set up correctly, sign out of the non-2fa account and sign back into your 2fa account. You will only need to sign back into the non-2fa account if you want to track another device.




![setup_fmf_icloud3](../images/setup_fmf_icloud3.jpg)

### Authenticating Your iCloud Account
iCloud needs to approve Home Assistant, and iCloud3, access to your account. It does this by sending an authentication code via a text message to a trusted device, which is then entered in Home Assistant. The duration of this authentication is determined by Apple, but is now at 2 months.  

When your account needs to be authorized, or reauthorized, you will be notified and will be displayed in the Notifications section on the Home Assistant sidebar in the lower left. Do the following to complete the authorization process:  

1. Press the Notifications on your Home Assistant screen to open the Notification window. A window is displayed, listing the trusted devices associated with your account. It will list an number (0, 1, 2, etc.) next to the phone number that can receive the text message containing the 2-step authentication code number that is used to authenticate the computer running Home Assistant (your Raspberry Pi for example).
1. Type the number for the device. A text message is sent with the 6-digit code.
1. Type the authentication code you receive in the next window that is displayed.

### Associating the iPhone Device Name with Home Assistant using the Home Assistant iOS App
The Device Name field of the device in `Settings App>General>About>Name` field on the iPhone and iPad and in the Apple Watch App for the iWatch is stored in the iCloud account and used by Home Assistant to identify the device. HA converts any special characters found in the Device Name field to an underscore, e.g., `Gary-iPhone` becomes `gary_iphone` in `known_devices.yaml`, automations, sensors, scripts, etc. The way this ties to the iCloud3 tracked_device depends on the version of the HA iOS App you are using on the device.

###### iOS App version 1
The devicename is entered into the Device ID field in the `Home Assistant iOS App>Settings` window, i.e. `gary_iphone` would be typed in the Device Id field.

###### iOS App version 2
You can not specify the device's devicename within the iOS App. When the iOS App is added to the device, a device_tracker entity is added to HA and is assigned a name (`gary_iphone`) followed by a sequence number (`_2`) if `gary_iphone` already exists. 

When HA starts, iCloud3 reads the HA Entity Registry file (./storage/core.entity_registry) and searches for a mobile device entry beginning with the devicename (`gary_iphone`). It picks up the sequence number previously assigned and monitors that device_tracker entity (`device_tracker.gary_iphone_2`) for zone changes.

!> iCloud3 also monitors the sensor.devicename_last_update_trigger entity associated with the device for Background Fetch, Significant Location Update and Manual location triggers.

!> When you have several devices being tracked, one device can use version 1 and the other device can use version 2 of the iOS App.

!> If you have both version 1 and version 2 on the same device, version 2 will be used. You can override this with an entry on the track_devices configuration parameter to use version 1.

### What happens if the iCloud Location Service is not available or I don't want to use it
When iCloud3 starts and if the `tracking_method` is 'fmf' of 'famshr', the iCloud account is accessed for device and location information. If the iCloud account can not be accessed (the Apple iCloud service is down, an error authorization error is returned from the iCloud service, the account can not be found, the account name and password are not correct, etc.), iCloud3 will issue an error message and revert to using the iOS App (`tracking_method: iopsapp`). The following occurs:

- iCloud3 will rely on HA iOS app to provide Zone enter/exits, Background Fetch, Significant Location Update and Manual triggers to know where the device is located.
- iCloud3 will not poll the device on a regular basis since it can't access the iCloud Find-My-Friends/Family Sharing Location Service. The decreasing interval as you approach Home or another zone will be not be done. Automations and scripts based on a short distance from home will not trigger. Automations and scripts triggered on a zone change should continue to work.
- The device is not located when HA starts. It may take a few minutes to process the next iOS app notification to locate the device.

!> iCloud3 can be restarted using the service call  `icloud3_update` with the `restart` command or the service call `icloud3_restart`. If you use Find-my-Friends and Family Sharing tracking methods, the iCloud Location Service will be rechecked and used if it is available. 

