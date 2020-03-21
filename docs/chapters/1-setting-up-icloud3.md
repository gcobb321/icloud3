# Setting up iCloud3

iCloud3 uses the device_tracker platform entity in your `configuration.yaml` file.


### Setting up the device_tracker entity 

The minimum information you need to get iCloud3 running is the username/password of your Apple iCloud account and the devices you want to track. Below are some examples of the configuration parameters that set up a platform using the Find-my-Friends tracking method.

- username/password - The Apple iCloud account to use to locate the device.
-  track_devices - The devices you want to track.

See the Configuration Section for more examples and information about these parameters.

!> You can have more than one iCloud3 device_tracker platform using different iCloud accounts to track different devices. When iCloud3 requests location information for an iCloud account, the location of all of the devices associated with that account (friends or family members) are returned. Knowing this, it does not make sense to have different iCloud3 platforms access the same iCloud account. All devices to be tracked should be grouped together.


### Examples of the iCloud3 platform

###### Tracking gary and lillian's iPhone using the gary-fmf-acct.
```yaml
device_tracker:
  - platform: icloud3
    username: gary-fmf-acct@email.com
    password: gary-fmf-password
    track_devices:
      - gary_iphone > gary-icloud-acct@email.com, gary.png
      - lillian_iphone > lillian-icloud-acct@email.com, lillian.png
```

###### Tracking devices using two icloud3 platforms.
```yaml
device_tracker:
  - platform: icloud3
    username: gary-fmf-acct@email.com
    password: gary-fmf-password
    track_devices:
      - gary_iphone > gary-icloud-acct@email.com, gary.png
      - lillian_iphone > lillian-icloud-acct@email.com, lillian.png

device_tracker:
  - platform: icloud3
    username: sydney-fmf-acct@email.com
    password: sydney-fmf-password
    track_devices:
      - sydney > sydney-icloud-acct@email.com, sydney.png
```

###### Tracking devices with the Family Sharing tracking method
```yaml
device_tracker:
  - platform: icloud3
    username: gary-icloud-acct@email.com
    password: gary-icloud-password
    tracking _method: famshr
    track_devices:
      - gary_iphone > gary.png
      - lillian_iphone > lillian.png
```

### How location information is used

- iCloud3 updates the device_tracker platform's attributes with a lot of information related to the device's location.
- iCloud3 also creates sensors for most of the attributes associated with a device. They can be used on Lovelace cards and in automations and scripts. Using configuration parameters, you can specify what sensors you want to create and not create. See the Sensors chapter for more information.
- When a device's location is polled, the GPS coordinates are returned. This is passed to the Waze Route Calculator to get distance and the travel time to Home or another zone. The data returned from the Waze Route Calculator is saved and later by other devices close to your current location.

!> When you first install iCloud3, the Stationary Zone will also be created. Since the iOS App does not automatically update information about new zones, you must force close the iOS App using the iPhone App Switcher and then restart it to reload the zone information, which will include the Stationary Zone.

------

### What to do next

The next thing to do is review the following chapters that discuss the configuration parameters used to specify how iCloud3 operates, the attributes and sensors that iCloud3 updates when a device's location changes, the iCloud3 services which control iCloud3 and the example Lovelace cards that display the device's tracking data.