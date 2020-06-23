# Configuration Parameters

### User and Account Items
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
The Home Assistant Entity Registry stores information about the devices and entities. It is searched when iCloud3 starts to determine if the HA IOS App version 2 is being used for tracking a device, and if it is, to extract the names of the entities to be monitored for the devices being tracked. 

Normally, this parameter will not be used since the name of the entity file is extracted from Home Assistant. However, this parameter can be used if a different file should be searched for device information. 

*Valid values:* Entity registry file name

The following are the path/name of the entirety registry file for Home Assistant running on different platforms:  
- Linux(default): '/.storage/core.entity_registry'
- MacOS: ‘/Users/USERNAME/.homeassistant/.storage/core.entity_registry’  

###### config_ic3_file_name  
iCloud3 parameters can be specified in it's own configuration file (*config_ic3.yaml*) and the paramerers are used when iCloud3 is restarted on the Event Log screen and when HA starts. This lets you change the the parameters and have them take effect without restarting HA. All parameters except the username/password, tracking method and included/excluded sensors and this parameter can be specified. This includes the devices to be tracked, timings, accuracy thresholds, location parameters, log_level, and others. If you want to use a different file, specify it's name with this parameter.   

*Valid Values:* Typical yaml file name. *Default:* config_ic3.yaml   
*Note:* The file is located in the `custom_components/icloud3` directory.
*Note:* A sample file, `config_ic3_sample.yaml`, is installed with iCloud3 and contains the parameters that can be specified in this file..  

### Devices to be tracked
###### tracking_method 
Select the method to be used to track your phone or other device. iCloud3 supports three methods of tracking a device -- iCloud Family Sharing Location Services, iCloud Find-My-Friends Location Services and the HA IOS App version 1 and version 2.  
*Valid values:* fmf, famshr, iosapp.  *Default:* fmf

###### track_devices (or track_device)  
*(Required)*  Identifies the devices to be tracked, their associated email addresses, badge pictures, an IOS App version 2 override control and a name that should be used for the device's sensors.  The parameters required depend on the tracking method.

!> - For the Find-my-Friends tracking method, the devicename and email_address are required.
!> - For the Family Sharing and IOS App tracking methods, only the devicename is required.


| Field              | Description/Notes                                            |
| ------------------ | ------------------------------------------------------------ |
| email_address      | FmF uses the 'real' email address of your 'friends' iCloud account to link it with the FmF account, i.e., `gary-2fa-acct@ email.com`.  <br><br>This parameter is identified as the `email_address` by the '@' character. It is required for Find-my-Friends tracking method and not used by the other tracking methods and can be omitted. |
| badge_picture_name | The file name containing a picture of the person normally associated with the device. See the Badge Sensor in the Sensor chapter for more information about the sensor_badge.<br><br>The file is normally in the `config/www/` directory (referred to as `/local/` in HA). You can use the full name `(/local/gary.png)` or an abbreviated name `(gary.png)`.<br><br>This parameter is identified as the `badge_picture_name` since it ends in '.png' or '.jpg'. |
| IOS App Id Number (version 2) | This only applies if you are using the IOS App version 2 and want to override the device's name discovered by iCloud3 during the entity registry scan. Normally, you will not use this parameter.<br><br>1. Enter the new suffix (_3, _iosappv2, _v2, etc.) to use a different device_tracker.<br>2. Enter 'iosappv1' to use version 1 of the IOS App instead of version 2 when both versions are installed on the device. |
| zone | Name of an additional zone(s) you want to monitor. This will create additional sensors with it's distance and travel time calculations that can be used in automations and scripts. See the Sensors chapter for more information.<br><br>Note: The Home zone information is always calculated. |
| user's name   | The user's name is displayed on the iCloud3 Event Log card, various messages and in the HA log file. It is created by removing the device type (iPhone, iPad, iCloud, etc) and any special characters (-, _, etc) from the devicename.  It is also retrieved from the First Name field on the data returned from iCloud when the devices are authenticated as iCloud3 starts up.<br><br>There may be times when the name is not available or you want to override the name that is extracted from the devicename. If that case, specify the name on the track_devices parameter. |

#### Parameters for Different Tracking Methods
###### Find my Friends:
- devicename > email_address
- devicename > email_address, badge_picture_name, zone
- devicename > email_address, badge_picture_name, iosapp_number, user_name
- devicename > email_address, iosappv1
- devicename > email_address, iosapp_number, zone, user_name
- devicename > email_address, badge_picture_name, user_name
- devicename > email_address, user_name

###### Family Sharing
- devicename
- devicename > badge_picture_name, zone
- devicename > badge_picture_name, user_name
- devicename > iosapp_number
- devicename > iosapp_number, user_name

###### IOS App Version 1
- devicename
- devicename > badge_picture_name, zone
- devicename > badge_picture_name, user_name

###### IOS App Version 2
- devicename
- devicename > iosapp_device_tracker_number
- devicename > badge_picture_name
- devicename > badge_picture_name, zone, user_name

###### Examples of track_devices formats
- gary_iphone > gary-icloud-acct@email.com, /local/gary.png
- gary_iphone > gary-icloud-acct, gary.png, whse
- gary_iphone > gary-icloud-acct, gary.png, GaryC
- gary_iphone > gary.png, iosappv1, GaryC
- gary_iphone > gary.png, _2
- gary_iphone > /local/gary.png
- gary_iphone

!> A greater then sign ('>') separates the devicename from the parameters.

#### Sample Configuration File Parameters

##### tracking_method: Family Sharing (famshr), 2 iPhones, family group:

```yaml
- platform: icloud3
  username: gary-icloud-acct@email.com
  password: gary-icloud-password
  group: family
  tracking_method: famshr
  track_devices:
    - gary_iphone > gary.png, whse
    - lillian_iphone > lillian.png
```

##### 

##### tracking_method: Find-my-Friends (fmf), 2 iPhones: 

```yaml
- platform: icloud3
  username: gary-fmf-acct@email.com
  password: gary-fmf-password
  track_devices:
    - gary_iphone > gary-icloud-acct@email.com, gary.png
    - lillian_iphone > lillian-icloud-acct@email.com, lillian.png
```
##### tracking_method: iosapp, track gary_iphone using home and whse zones,  customize sensors created:
```yaml
- platform: icloud3
  username: gary@email.com
  tracking_method: iosapp
  track_devices:
    - gary_iphone > gary.png, whse
    - lillian_iphone > lillian.png
  gps_accuracy_threshold: 100
  create_sensors: zon,zon1,ttim,zdis,cdis,wdis,nupdt,lupdt,info
```

### Zone, Interval and Sensor Configuration Items
###### inzone_interval 
The interval between location updates when the device is in a zone. This can be in seconds, minutes or hours, e.g., 30 secs, 1 hr, 45 min, or 30 (minutes are assumed if no time qualifier is specified).  
*Default:* 2 hrs

###### center_in_zone   
Specify if the device's location should be changed to the center of the zone when it is in a zone. Previously, would always be moved to the zone center.  
*Valid Values*: True, False  *Default:* False

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

*Valid Values:* latitude-adjustment, longitude-adjustment.  *Default*: 1,0   
*Example:* stationary_zone_offset: (24.738520, -75.380462)  
*Example:* stationary_zone_offset: '2,0'

###### unit_of_measurement 
The unit of measure for distances in miles or kilometers.   
*Valid values:* mi, km. *Default*: mi

###### gps_accuracy_threshold 
iCloud location updates come with some gps_accuracy varying from 10 to 5000 meters. This setting defines the accuracy threshold in meters for a location updates. This allows more precise location monitoring and fewer false positive zone changes. If the gps_accuracy is above this threshold, a location update will be retried again to see if the accuracy has improved.  
*Default*: 125m

###### old_location_threshold
When a device is located, the location's age is calculated and the update is discarded if the age is greater than the threshold. The threshold can be calculated (12.5% of the travel time to the zone with a 5 minute maximum (default)) or you can specify a fixed time using this parameter.  
*Valid values:* Number of minutes *Default*: 2

##### ignore_gps_accuracy_inzone
If the device is in a zone, gps accuracy will be ignored.  
*Valid values:* True, False  *Default:* True

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

### Waze Configuration Items
###### distance_method 
iCloud3 uses two methods of determining the distance between home and your current location — by calculating the straight line distance using geometry formulas (like the Proximity sensor) and by using the Waze Route Tracker to determine the distance based on the driving route.  If you do not have Waze in your area or are having trouble with Waze. change this parameter to `calc` to set the interval using the distance between your current location and home rather than the Waze travel time.  
*Valid values:* waze, calc *Default:* waze

###### waze_min_distance, waze_max_distance 
These values are also used to determine if the polling internal should be based on the Waze distance. If the calculated straight-line distance is between these values, the Waze distance will be requested from the Waze mapping service. Otherwise, the calculated distance is used to determine the polling interval.  
*Default:* min=1, max=1000 

!> The Waze distance becomes less accurate when you are close to home. The calculation method is better when the distances less than 1 mile or 1 kilometer. 

!> If you are a long way from home, it probably doesn't make sense to use the Waze distance. You probably don't have any automations that would be triggered from that far away anyway.

###### waze_realtime 
Waze reports the travel time estimate two ways — by taking the current, real time traffic conditions into consideration (True) or as an average travel time for the time of day (False).  
*Valid values:* True, False. *Default:* False 

###### waze_region 
The area used by Waze to determine the distance and travel time.  
*Valid values:* US (United States), NA (North America), EU (Europe), IL (Israel). *Default:* US

###### travel_time_factor 
When using Waze and the distance from your current location to home is more than 3 kilometers/miles, the polling interval is calculated by multiplying the driving time to home by the travel_time_factor.  
*Default:* .60  

!> Using the default value, the next update will be 3/4 of the time it takes to drive home from your current location. The one after that will be 3/4 of the time from that point. The result is a smaller interval as you get closer to home and a larger one as you get further away.  

### Examples the Configuration Parameters
```yaml
device_tracker:
  - platform: icloud3
    username: !secret gary_famshr_username
    password: !secret gary_famsh_password
    tracking_method: famshr
    track_devices:
      - gary_iphone > gary-icloud-acct@email.com, gary.png
      - lillian_iphone > lillian-icloud-acct@email.com, lillian.png
      
    group: family
    
    inzone_interval: '2 hrs'
    max_interval: '30 min'
    center_in_zone: False
    stationary_inzone_interval: '30 min'
    stationary_still_time: '8 min'
    stationary_zone_offset: '2,0'
    
    gps_accuracy_threshold: 75
    old_location_threshold: '2 min'
    ignore_gps_accuracy_inzone: False
    
    travel_time_factor: .6
    distance_method: calc
    waze_region: US
    waze_min_distance: 1
    waze_max_distance: 9999
    waze_realtime: false
    
    create_sensors: intvl,ttim,zdis,wdis,cdis,lupdt,nupdt,zon,zon1,zon2
    exclude_sensors: cnt,lupdt,zon3,lzon3,alt
    
    log_level: debug+eventlog
    config_ic3_file_name: 'config_ic3.yaml'
```
