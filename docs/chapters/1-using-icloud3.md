# Setting Up your iCloud Account

### What other programs do I need
The `Home Assistant IOS App` is all. You do not need OwnTracks or other location based trackers and you do not need Nmap, netgear, ping or any network monitor. The Home Assistant IOS App will notify Home Assistant when you leave Home or another zone and iCloud3 device tracker will start keeping up with the device's location, the distance to the zones and the time it will take to get each one.

!> The IOS App settings `Zone enter/exit, Background Fetch and Significant Location Change` location settings need to be enabled. 

The iCloud3 platform allows you to detect presence using the  iCloud Location Service. (Go [here](https://www.icloud.com/) for more information). iCloud allows users to track their location on iOS devices. Your device needs to be registered with Find-my-Friends or Family Sharing.

The HA proximity component also determines distance between zones and the device, determines direction of travel, and other device_tracker related functions. Unfortunately, the IOS App reports old location information on a regular basis that is processed by the proximity component. 
​		
!> It is highly recommended to not use the proximity component when using iCloud3. iCloud3 duplicates the proximity functions and discards bad location information where the proximity component does not.

### What if I don't have the IOS App on my device
The Home Assistant IOS App issues zone enter/exits and pushes location updates to HA while the iCloud Find-my-Friends and Family Sharing tracking methods issues location updates and other device information when polled by iCloud3. If the IOS App is not installed on the device, the zone enter/exits will not be picked up when they actually happen.

The device will be updated, however, on the next poll by iCloud3. The problem with not having the IOS app installed is if you are in a zone and on a 2-hour polling interval, it could be 2-hours before the device goes to a not_home state. With the IOS App, the zone exit is pushed to HA where it gets picked up by iCloud3 and the device's state is changed. This happens within 10-seconds of getting the exit notification for the zone. Naturally, if you are in a poor service area, this notification may be delayed.

###  iCloud and 2-Factor Authentication
When you set up an Apple iCloud account, '2-step authentication or 2-factor authentication (2fa)' is normally turned on account. This has an enormous impact on how your iCloud account is accessed. 

#### 2fa is turned on {docsify-ignore}
In order retrieve location information, iCloud3 must establish a computer-to-computer link with the Apple iCloud account and it has to be authenticated every time the account is accessed. Unfortunately, the HA computer can not be set up as a 'Trusted Device', so every 30-minutes, or so, Apple logs the HA computer, and thus iCloud3, out of the account. The result is HA and iCloud3 must log back into the account when it wants new location information. 

  Every time you log into your Apple iCloud account, Apple sends a notification to all of your trusted devices informing you that your account has been logged into for your approval (a map is displayed with an Allow/Don't Allow message), followed by a second notification containing a 6-digit code that you can not do anything with.  

  This gets annoying and makes working with iCloud accounts with 2fa unworkable.

#### 2fa is not turned on {docsify-ignore}
None of the above happens.


### Locating Your Device with iCloud
iCloud Location Services provides 2 methods for locating your iPhone or other device. iCloud3 supports both methods and the one you use will depend on if you are using 2-factor authentication with your Apple iCloud account.


#### Find-my-Friends (FmF) {docsify-ignore}
You set up friends on the `Find My` app (IOS 13) or the `Find-my-Friends` app (IOS12) and iCloud3 will locate them just like the app does. Since your Apple iCloud account probably has 2fa turned on, you need to:

  1. Add a new FmF iCloud account (with different email address) with 2fa turned off. You will use this email address in the `username` configuration parameter.

  2. Add the friends you want to track in the `Contacts` app. You only need to enter their name and email address.

  3. Add them to the `Find My` or `Find-my-Friends` App.

  4. Verify that the `Find My` `Find-my-Friends` app can locate them.

!> This is easier to set up if you do it on a device you will not be locating. 

!> IOS 13 turns on 2fa automatically and it can not be turned off. The non-2fa account will need to be added on a computer instead of an iPhone or iPad.

#### Family Sharing (FmPhn) {docsify-ignore}
If you do not have 2fa turned on on your 'real' iCloud account, you can use FmPhn to locate your device(s). iCloud3 looks for the devices to be tracked in the Family Sharing list. With FmPhn, you can use your 'real' iCloud account email address for the `username`  configuration parameter.

The `tracking_method` and `tracked_devices` configuration parameters are used to indicate how tracking should be done and the devices to be tracked.


![setup_fmf_icloud3](../images/setup_fmf_icloud3.jpg)

### Authenticating Your iCloud Account
iCloud needs to approve Home Assistant, and iCloud3, access to your account. It does this by sending an authentication code via a text message to a trusted device, which is then entered in Home Assistant. The duration of this authentication is determined by Apple, but is now at 2 months.  

When your account needs to be authorized, or reauthorized, you will be notified and will be displayed in the Notifications section on the Home Assistant sidebar in the lower left. Do the following to complete the authorization process:  

1. Press the Notifications on your Home Assistant screen to open the Notification window. A window is displayed, listing the trusted devices associated with your account. It will list an number (0, 1, 2, etc.) next to the phone number that can receive the text message containing the 2-step authentication code number that is used to authenticate the computer running Home Assistant (your Raspberry Pi for example).
1. Type the number for the device. A text message is sent with the 6-digit code.
1. Type the authentication code you receive in the next window that is displayed.

### Associating the iPhone Device Name with Home Assistant using the Home Assistant IOS App
The Device Name field of the device in `Settings App>General>About>Name` field on the iPhone and iPad and in the Apple Watch App for the iWatch is stored in the iCloud account and used by Home Assistant to identify the device. HA converts any special characters found in the Device Name field to an underscore, e.g., `Gary-iPhone` becomes `gary_iphone` in `known_devices.yaml`, automations, sensors, scripts, etc. The way this ties to the iCloud3 tracked_device depends on the version of the HA IOS App you are using on the device.

###### IOS App version 1
The devicename is entered into the Device ID field in the `Home Assistant IOS App>Settings` window, i.e. `gary_iphone` would be typed in the Device Id field.

###### IOS App version 2
You can not specify the device's devicename within the IOS App. When the IOS App is added to the device, a device_tracker entity is added to HA and is assigned a name (`gary_iphone`) followed by a sequence number (`_2`) if `gary_iphone` already exists. 

When HA starts, iCloud3 reads the HA Entity Registry file (./storage/core.entity_registry) and searches for a mobile device entry beginning with the devicename (`gary_iphone`). It picks up the sequence number previously assigned and monitors that device_tracker entity (`device_tracker.gary_iphone_2`) for zone changes.

!> iCloud3 also monitors the sensor.devicename_last_update_trigger entity associated with the device for Background Fetch, Significant Location Update and Manual location triggers.

!> When you have several devices being tracked, one device can use version 1 and the other device can use version 2 of the IOS App.

!> If you have both version 1 and version 2 on the same device, version 2 will be used. You can override this with an entry on the tracked_devices configuration parameter to use version 1.

### What happens if the iCloud Location Service is not available or I don't want to use it
When iCloud3 starts and if the `tracking_method` is 'fmf' of 'famshr', the iCloud account is accessed for device and location information. If the iCloud account can not be accessed (the Apple iCloud service is down, an error authorization error is returned from the iCloud service, the account can not be found, the account name and password are not correct, etc.), iCloud3 will issue an error message and revert to using the IOS App (`tracking_method: iopsapp`). The following occurs:

- iCloud3 will rely on HA IOS app to provide Zone enter/exits, Background Fetch, Significant Location Update and Manual triggers to know where the device is located.
- iCloud3 will not poll the device on a regular basis since it can't access the iCloud Find-My-Friends/Family Sharing Location Service. The decreasing interval as you approach Home or another zone will be not be done. Automations and scripts based on a short distance from home will not trigger. Automations and scripts triggered on a zone change should continue to work.
- The device is not located when HA starts. It may take a few minutes to process the next IOS app notification to locate the device.

!> iCloud3 can be restarted using the service call  `icloud3_update` with the `restart` command or the service call `icloud3_restart`. If you use Find-my-Friends and Family Sharing tracking methods, the iCloud Location Service will be rechecked and used if it is available. 

