# Configuration Parameters

Configuration parameters for HA components are set up in the *configuration.yaml* file. Some iCloud3 parameters can also be set up in it's own configuration file, *config_ic3.yaml*. How these parameters are used depends on how iCloud3 is started (or restarted)

* When HA starts and iCloud3 is loaded, parameters will be read from both files, *configuration.yaml* and *config_ic3.yaml*. If the same parameter is in both files, the one in *config_ic3.yaml* is used. 
* When iCloud3 is restarted on the Event Log screen, only the parameters in *config_ic3.yaml* are used.  You can change the parameters in *config_ic3.yaml* and then restart iCloud3 without restarting HA. The new parameters are now used to control how iCloud3 operates.

!>The *config_ic3.yaml* file, if used, should be located in the */config* directory, the same directory being used for the HA *configuration.yaml* file.  If it is located in the */config/custom_components/icloud3* directory, it will be deleted when HACS updates iCloud3.

Some parameters must be specified in the *configuration.yaml* file. They are:

* Username & password
* Tracking method -- Family Sharing (famshr), Find-my-Friends (fmf), iOSApp (iosapp)
* config_ic3_file_name if it is a custom name. This parameter is not needed if you are using the *config_ic3.yaml* file name or if your parameters are in *configuration.yaml*.
* create_sensors, exclude_sensors if you are configuring your sensor list.

All other parameters, including track_devices, can be in *config_ic3.yaml*.



### User and Account Items

> The User and Account Items must be included in the HA *configuration.yaml* file. They can not be included in the *config_ic3.yaml* file.

###### username

*(Required)* The username (email address) for the iCloud account.  
*Note:* This is also required for the iOS App tracking method and is used to identify the iCloud3 instance.

###### password

The password for the account.  
*Note:* This is required for Family Sharing & Find-my-Friends tracking method and not required for the iOS App tracking method.

###### group 
The name of the group of devices being tracked for this iCloud3 device_tracker platform.   
*Default:*  'group#' where # is the sequence number of the iCloud3 device_tracker platforms found in the configuration file.

###### entity_registry_file_name
The Home Assistant Entity Registry stores information about the devices and entities. It is searched when iCloud3 starts to extract the names of the entities that are monitored for the devices being tracked. 

Normally, this parameter will not be used since the name of the entity file is extracted from Home Assistant. However, this parameter can be used if a different file should be searched for device information. 

*Valid values:* Entity registry file name

The following are the path/name of the entirety registry file for Home Assistant running on different platforms:  
- Linux(default): '/.storage/core.entity_registry'
- MacOS: ‘/Users/USERNAME/.homeassistant/.storage/core.entity_registry’  

###### config_ic3_file_name  
Many iCloud3 parameters can be specified in the iCloud3 configuration file and, when iCloud3 loads, these parameters  will be processed as if they were in the HA *configuration.yaml* file. The major benefit is the ability to change parameters and have them take effect when iCloud3 is restarted on the `Event Log > Actions` pulldown menu. HA does not need to be restarted. A secondary benefit is keeping several configuration files for special conditions.

The *config_ic3.yaml* file, if used, should be located in the */config* directory, the same directory being used for the HA *configuration.yaml* file.  If it is located in the */config/custom_components/icloud3* directory, it will be deleted when HACS updates iCloud3.

The file name itself, if specified, must be in the HA configuration file, When iCloud3 starts, the file is searched for in the following manner:

- If the file name is fully qualified and contains the directory and filename (it have to has a '/'), that is used.
- If the filename is found in the */config* directory, that file is used.
- Otherwise a file not found error is added to the Event Log. 

*Valid Values:* Typical yaml file name.   
*Default:* 'config/config_ic3.yaml '  
*Note:* A sample file, `config_ic3_sample.yaml`, is installed with iCloud3 into the *custom_components/icloud3* directory. It contains examples of all of the parameters that can be specified in this file.  

###### event_log_card_directory  

This contains the directory used to store the iCloud3 Event Log Lovelace card. The Event Log version (*icloud3-event-log-card.js*) is checked when iCloud3 starts to verify the latest version is installed. If a newer version is available, the newer version in the custom components directory is copied to the Event Log directory. Use this parameter if you are storing your lovelace custom cards in another directory.

- *Valid values:* Standard file name, *Default:* 'www/custom_cards'
- *Example:* 'www/community' if you are using the 'community' directory.

**2sa_verification**

This parameter forces the 2-step-authentication procedure used in previous versions of iCloud3 instead of the 2-factor-authentication using the native Apple ID Verification Code released in iCloud3 v2.2.2.

- *Valid values:* True, False, *Default:* False

### Devices to be tracked

###### tracking_method 
Select the method to be used to track your phone or other device. iCloud3 supports three methods of tracking a device -- iCloud Family Sharing Location Services, iCloud Find-My-Friends Location Services and the HA IOS App version 1 and version 2.  
*Valid values:* fmf, famshr, iosapp.  *Default:* fmf

###### track_devices
*(Required)*  Identifies the devices to be tracked, their associated email addresses, badge pictures and a custom name that can be used for naming the device's sensors.  The parameters required depend on the tracking method.

!> - For the Find-my-Friends tracking method, the devicename and email_address are required.
!> - For the Family Sharing and IOS App tracking methods, only the devicename is required.


| Field              | Description/Notes                                            |
| ------------------ | ------------------------------------------------------------ |
| email_address<br>(Required for FmF, Optional for other tracking methods) | FmF uses the email address of your 'friends' iCloud account to link it with the FmF account, i.e., `gary-icloud-acct@email.com`.  <br><br>This parameter is identified as the `email_address` by the '@' character. It is required for Find-my-Friends tracking method and ignored by the other tracking methods. You do not need to remove it from the track_deices parameter line if you switch between tracking methods. |
| badge_picture_name<br>(Optional) | The file name containing a picture of the person normally associated with the device. See the Badge Sensor in the Sensor chapter for more information about the sensor_badge.<br><br>The file is normally in the `config/www/` directory (referred to as `/local/` in HA). You can use the full name `(/local/gary.png)` or an abbreviated name `(gary.png)`.<br><br>This parameter is identified as the `badge_picture_name` since it ends in '.png' or '.jpg'. |
| zone<br>(Optional) | Name of an additional zone(s) you want to monitor. This will create additional sensors with it's distance and travel time calculations that can be used in automations and scripts. See the Sensors chapter for more information.<br><br>Note: The Home zone information is always calculated. |
| user's name<br>(Optional) | The user's name is displayed on the iCloud3 Event Log card, various messages and in the HA log file. It is created by removing the device type (iPhone, iPad, iCloud, etc) and any special characters (-, _, etc) from the devicename.  It is also retrieved from the First Name field on the data returned from iCloud when the devices are authenticated as iCloud3 starts up.<br><br>There may be times when the name is not available or you want to override the name that is extracted from the devicename. If that case, specify the name on the track_devices parameter. |
| iOS App device_tracker entity name or suffix to be monitored<br>(Optional) | Name (or suffix) of the iOS App device_tracker entity to be monitored for state and trigger changes. The device's iOS App entity name must start with the name on the iCloud3 `track_devices`. <br><br>When iCloud3 starts (or restarts), it searches the HA Entity Registry for all mobile app device tracker entities that start with the devicename on the track devices parameter. <br>* If it finds only one entity, that entity is monitored and the suffix (`_xxx` part after the devicename) is displayed on the tracked deices item on the Event Log for your reference. <br>* If more than one is found, an error message is displayed in the Event Log, all of the mobile app entities are listed and the last entity found is monitored. Add the suffix for the correct entity to the track devices parameter. <br>* If no mobile app entity, an error is displayed on the Event Log and iCloud3 will not be able to monitor any iOS App Region Enter/Exit, Significant Location Updates, Background Fetch, triggers.<br><br>*Note:* This is only needed if there is more than one device_tracker entity associated with the device,<br>*Example (Suffix):* `_iosapp`, `_app`, `_2`<br>*Example (iOS App device tracker entity):* `gary_iphone_iosapp`, `lillian_iphone_2` |
| 'noiosapp' | The iOS App is not installed on this tracked device. Do not monitor any device_tracker or sensors entities associated with the device for zone enter/exit or location events. |

#### Parameters for Different Tracking Methods
>Find my Friends  
><br>
>
>- devicename > email_address
>- devicename > email_address, badge_picture_name, zone
>- devicename > email_address, badge_picture_name, iosapp_number, user_name
>- devicename > email_address, iosappv1
>- devicename > email_address, iosapp_number, zone, user_name
>- devicename > email_address, badge_picture_name, user_name
>- devicename > email_address, user_name

>Family Sharing  
><br>
>
>- devicename
>- devicename > badge_picture_name, zone
>- devicename > badge_picture_name, user_name
>- devicename > iosapp_number
>- devicename > iosapp_number, user_name

>IOS App  
><br>
>
>- devicename
>- devicename > iosapp_device_tracker_number
>- devicename > badge_picture_name
>- devicename > badge_picture_name, zone, user_name

>Examples of track_devices formats  
><br>
>
>- gary_iphone > gary-icloud-acct@email.com, /local/gary.png
>- gary_iphone > gary-icloud-acct, gary.png, whse
>- gary_iphone > gary-icloud-acct, gary.png, GaryC
>- gary_iphone > gary.png, iosappv1, GaryC
>- gary_iphone > gary.png
>- gary_iphone > /local/gary.png
>- gary_iphone

!> A greater then sign ('>') separates the devicename from the parameters.

#### Sample Configuration File Parameters

>tracking_method: Family Sharing (famshr), 2 iPhones, family group:
>```yaml
>- platform: icloud3
>  username: gary-icloud-acct@email.com
>  password: gary-icloud-password
>  group: family
>  tracking_method: famshr
>  track_devices:
>    - gary_iphone > gary.png, whse
>    - lillian_iphone > lillian.png
>```

>tracking_method: Find-my-Friends (fmf), 2 iPhones: 
>```yaml
>- platform: icloud3
>  username: gary-fmf-acct@email.com
>  password: gary-fmf-password
>  track_devices:
>    - gary_iphone > gary-icloud-acct@email.com, gary.png
>    - lillian_iphone > lillian-icloud-acct@email.com, lillian.png
>```

>tracking_method: iosapp, track gary_iphone using home and whse zones,  customize sensors created:
>```yaml
>- platform: icloud3
>  username: gary@email.com
>  tracking_method: iosapp
>  track_devices:
>    - gary_iphone > gary.png, whse
>    - lillian_iphone > lillian.png
>  gps_accuracy_threshold: 100
>  create_sensors: zon,zon1,ttim,zdis,cdis,wdis,nupdt,lupdt,info
>```

### Formatting Parameters

###### unit_of_measurement

The unit of measure for distances in miles or kilometers.   
*Valid values:* mi, km. *Default*: mi  

###### display_zone_format

The *device_tracker.[DEVICENAME]* state field displays the zone the device is in or *Away* if it is not in a zone. The one can be displayed in several formats. See chapter *2.4 Using Sensors, Zone Sensors* [here](./2-sensors?id=zone-sensors) for more examples of how the zones are formatted.

- `name` - A reformatted zone name. Example: 'the_shores' is displayed as 'TheShores' 
- `title` - A reformatted zone name. Example: 'the_shores' is displayed as 'The Shores'
- `fname` - The zones Friendly Name. Example: 'The Shores Development'
- `zone` - The actual zone name is displayed. Example: 'the_shores' is displayed as 'the_shores'

*Valid values:* : name, title, fname, zone,  *Default:* name

###### time_format

This parameter overrides the unit_of_measurement time format.  

*Valid values:* 12/24. *Default:* Depends on the unit_of_measurement (mi=12, km=24). 

###### display_text_as

There may be times when you do not want your email address or other personal data displayed in the Event Log. This parameter lets you replace the text that is normally displayed with something else. For example:

```
display_text_as:
  - gcobb-icloud-account@gmail.com > gary-2fa@email.com
  - lillian-icloud-account@gmail.com > lillian-2fa@email.com
```

In this example, the *gary-icloud-account@gmail.com* will be displayed as *gary-2fa@emal.com* in the Event Log.

### Zone, Interval and Sensor Configuration Items

###### inzone_interval 
The interval between location updates when the device is in a zone. This can be in seconds, minutes or hours, e.g., 30 secs, 1 hr, 45 min, or 30 (minutes are assumed if no time qualifier is specified).  
*Default:* 2 hrs

###### max_interval

The distance from home is used to calculate the interval. If you are a long way from Home, the interval might be very large. If the calculated value is greater than the max_interval value, the max_interval will be used and iCloud3 will be able to update the phone's location on a regular basis. This also keeps the HA map tracking current.  
*Default:* 4 hrs

###### center_in_zone   

Specify if the device's location should be changed to the center of the zone when it is in a zone. Previously, would always be moved to the zone center.  
*Valid values*: True, False,  *Default:* False

###### stationary_inzone_interval 
The interval between location updates when the device is in a Dynamic Stationary Zone. See Special Zones chapter for more information about stationary zones. This can be minutes or hours, e.g., 1 hr, 45 min, or 30 (minutes are assumed if no time qualifier is specified).  
*Default:* 30 min

###### stationary_still_time 
The number minutes with little movement (1.5 times the Home zone radius) before the device will be put into its Dynamic Stationary Zone.   
*Valid values:* Number. *Default:* 8

###### stationary_zone_offset  
The stationary zone is created when iCloud3 starts (or is restarted) and is located 1km north of the Home Zone location. There may be times when this conflicts with your normal driving route and you find yourself going in and out of the stationary zone. With this parameter, you can change it's initial location. The format is:

* latitude-adjustment, longitude-adjustment - Specify the number of kilometers from the Home zone. The first parameter adjusts the latitude (north/south), the second parameter adjusts the longitude (east/west).
* (latitude, longitude) - Specify the actual GPS coordinates (the parentheses are required). 

*Valid values:* latitude-adjustment, longitude-adjustment,  *Default*: 1,0   
*Example:* stationary_zone_offset: (24.738520, -75.380462)  
*Example:* stationary_zone_offset: '2,0'

###### gps_accuracy_threshold

iCloud location updates come with some gps_accuracy varying from 10 to 5000 meters. This setting defines the accuracy threshold in meters for a location updates. This allows more precise location monitoring and fewer false positive zone changes. If the gps_accuracy is above this threshold, a location update will be retried again to see if the accuracy has improved.  
*Default*: 125m

###### old_location_threshold

When a device is located, the location's age is calculated and the update is discarded if the age is greater than the threshold. The threshold can be calculated (12.5% of the travel time to the zone with a 5 minute maximum (default)) or you can specify a fixed time using this parameter.  
*Valid values:* Number of minutes, *Default*: 2

###### ignore_gps_accuracy_inzone

If the device is in a zone, gps accuracy will be ignored.  
*Valid values:* True, False,  *Default:* True

###### create_sensors 
Specify only the sensors that should be created. See Customizing sensors in the Sensor chapter for more information.

###### exclude_sensors 
Create all sensors except the ones specified. See Customizing sensors in the Sensor chapter for more information.

!> If you are customizing the sensors that are created, you should use either the create_sensors parameter or the exclude_sensors parameter but not both.  

###### log_level

Display iCloud3 debug information in the HA Log file and, optionally, on the iCloud3 Event Log Card.  The following parameters are available:  

* `debug` -  Entries related to device_tracker location operations  
* `debug+rawdata` -  Entries related to device_tracker location operations  and the raw data that is returned from the PyiCloud Apple Web Services interface program. This raw data can sometimes help identify a problem with information stored on the iCloud Location Servers when devices are not tracked, when accounts are not set up correctly and an error is displayed by iCloud3.
* `intervalcalc` -The methods and calculations related to the interval, next update time, zone, etc.
* `eventlog` - Display the logged information on the iCloud3 Event Log Card.  
*  `info` - Display the current log_level options on the iCloud3 Event Log Card and the Info status line for the devices being tracked.  

*Valid values:* debug, intervalcalc, eventlog, info

*Note:* More than one parameter can be specified on the parameter line. For example `log_level: debug, eventlog`.

>The HA 'logger' parameter must be specified in the HA 'configuration.yaml' file or the 'log_level' parameter will not add anything to the HA log file (config/home-assistant.log).   
>```yaml
>logger:
>  default: info
>```

### Waze Configuration Items

> The Waze Route Calculator component is use to calculate driving distance and time from your location to your Home or another zone). Normally, it is installed with the Home Assistant and Hass.io framework. However, if it is not installed on your system, you can go [here](https://github.com/kovacsbalu/WazeRouteCalculator) for instructions to download and install Waze. If you don't want to use Waze or are in an area where Waze is not available, you can use the 'direct distance' method of calculating your distance and time from the Home or another zone. Add the *distance_method: calc* parameter to your icloud3 configuration file (see the Parameters, Attributes and Sensors section for more information).

###### distance_method 
iCloud3 uses two methods of determining the distance between home and your current location — by calculating the straight line distance using geometry formulas (like the Proximity sensor) and by using the Waze Route Tracker to determine the distance based on the driving route.  If you do not have Waze in your area or are having trouble with Waze. change this parameter to `calc` to set the interval using the distance between your current location and home rather than the Waze travel time.  
*Valid values:* waze, calc, *Default:* waze

###### waze_min_distance, waze_max_distance 
These values are also used to determine if the polling internal should be based on the Waze distance. If the calculated straight-line distance is between these values, the Waze distance will be requested from the Waze mapping service. Otherwise, the calculated distance is used to determine the polling interval.  
*Default:* min=1, max=1000 

!> The Waze distance becomes less accurate when you are close to home. The calculation method is better when the distances less than 1 mile or 1 kilometer. 

!> If you are a long way from home, it probably doesn't make sense to use the Waze distance. You probably don't have any automations that would be triggered from that far away anyway.

###### waze_realtime 
Waze reports the travel time estimate two ways — by taking the current, real time traffic conditions into consideration (True) or as an average travel time for the time of day (False).  
*Valid values:* True, False, *Default:* False 

###### waze_region 
The area used by Waze to determine the distance and travel time.  
*Valid values:* US (United States), NA (North America), EU (Europe), IL (Israel), *Default:* US

###### travel_time_factor 
When using Waze and the distance from your current location to home is more than 3 kilometers/miles, the polling interval is calculated by multiplying the driving time to home by the travel_time_factor.  
*Default:* .60  

!> Using the default value, the next update will be 3/4 of the time it takes to drive home from your current location. The one after that will be 3/4 of the time from that point. The result is a smaller interval as you get closer to home and a larger one as you get further away.  

### List of the Configuration Parameters
>```yaml
>device_tracker:
>- platform: icloud3
>  username: !secret gary_famshr_username
>  password: !secret gary_famsh_password
>  tracking_method: famshr
>  track_devices:
>    - gary_iphone > gary-icloud-acct@email.com, gary.png
>    - lillian_iphone > lillian-icloud-acct@email.com, lillian.png
>    
>  #-- General Parameters -----------------------------------------
>  group: family
>  event_log_card_directory: 'www/custom_cards'
>  config_ic3_file_name: '/config/config_ic3.yaml'
>
>  #-- Formatting Parameters---------------------------------------
>  unit_of_measurement: km
>  time_format: 24
>  display_zone_fname: True
>  display_text_as:
>    - gary-real-email@gmail.com > gary-email@email.com
>    - lillian-real-email@gmail.com > lillian-emailt@email.com
>    
>  #--Zone/Tracking Parameters-----------------------------------------
>  inzone_interval: '60 min'
>  max_interval: '4 hrs'
>  center_in_zone: True
>  stationary_inzone_interval: '30 min'
>  stationary_still_time: '8 min'
>  stationary_zone_offset: 1, 0
>  travel_time_factor: .6
>  distance_method: waze
>
>  #--Accuracy Parameters-------------------------------------
>  gps_accuracy_threshold: 100
>  ignore_gps_accuracy_inzone: True
>  old_location_threshold: '3 min'
>
>  #--Waze Parameters-----------------------------------------
>  distance_method: waze
>  waze_region: US
>  waze_min_distance: 1
>  waze_max_distance: 9999
>  waze_realtime: False
>  
>  #-- Debug/Logging Parameters---------------------------------------
>  log_level: debug
>  log_level: debug+rawdata
>
>```
