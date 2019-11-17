# Configuration Parameters

### User and Account Items
###### username 
*(Required)* The username (email address) for the iCloud account. 

###### password 
*(Required)* The password for the account.

###### group 
The name of the group of devices being tracked for this iCloud3 device_tracker platform.   
*Default:*  'group#' where # is the sequence number of the iCloud3 device_tracker platforms found in the configuration file.

###### entity_registry_file_name
The Home Assistant Entity Registry stores information about the devices and entities. It is searched when iCloud3 starts to determine if the HA IOS App version 2 is being used for tracking a device. This can be used if a different file should be searched for device informaion. Normally, you should not have to specify this parameter.  
*Valid value:*  valid file name for the Home Assistant entity registry file  
*Default:* '/.storage/core.entity_registry'

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
| sensor_name_prefix            | Sensors entities created by iCloud3 are prefixed with the devicename or zone_devicename (`sensor.gary_iphone_travel_time` or `sensor.whse_gary_iphone_travel_time`). The prefix replaces the devicename with the value specified (`sensor.garyc_travel_time` or `sensor.whse_garyc_travel_time`).<br><br>See the Naming Sensors in the Sensor chapter for a complete description of this field. <br><br>This parameter is identified as the `sensor_name_prefix` since it is none of the above. |

#### Parameters for Different Tracking Methods
###### Find my Friends:
- devicename > email_address
- devicename > email_address, badge_picture_name, zone
- devicename > email_address, badge_picture_name, iosapp_number, sensor_prefix_name
- devicename > email_address, iosappv1
- devicename > email_address, iosapp_number, zone, sensor_prefix_name
- devicename > email_address, badge_picture_name, sensor_prefix_name
- devicename > email_address, sensor_prefix_name

###### Family Sharing
- devicename
- devicename > badge_picture_name, zone
- devicename > badge_picture_name, sensor_prefix_name
- devicename > iosapp_number
- devicename > iosapp_number, sensor_prefix_name
- devicename > sensor_prefix_name

###### IOS App Version 1
- devicename
- devicename > badge_picture_name, zone
- devicename > badge_picture_name, sensor_prefix_name

###### IOS App Version 2
- devicename
- devicename > iosapp_device_tracker_number
- devicename > badge_picture_name
- devicename > badge_picture_name, zone, sensor_prefix_name

###### Examples of tracked_devices formats
- gary_iphone > gary-icloud-acct@email.com, /local/gary.png
- gary_iphone > gary-icloud-acct, gary.png, whse
- gary_iphone > gary-icloud-acct, gary.png, garyc
- gary_iphone > gary.png, iosappv1, garyc
- gary_iphone > gary.png, _2
- gary_iphone > /local/gary.png
- gary_iphone

!> A greater then sign ('>') separates the devicename from the parameters.

#### Sample Configuration File Parameters

##### tracking_method: Find-my-Friends (fmf), 2 iPhones: 
```yaml
- platform: icloud3
  username: gary-fmf-acct@email.com
  password: gary-fmf-password
  track_devices:
    - gary_iphone > gary-icloud-acct@email.com, gary.png
    - lillian_iphone > lillian-icloud-acct@email.com, lillian.png
```
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

##### tracking_method: Find-my-Friends (fmf), 2 iPhones, do not use waze, also track 'whse' zone:
```yaml
- platform: icloud3
  username: gary-fmf-acct@email.com
  password: gary-fmf-password
  track_devices:
    - gary_iphone > gary.png, whse
    - lillian_iphone > lillian.png
  gps_accuracy_threshold: 100
  distance_method: calc
```

##### tracking_method: iosapp, gary_iphone uses IOS App version 1, customize sensors created:
```yaml
- platform: icloud3
  username: gary-fmf-acct@email.com
  password: gary-fmf-password
  tracking_method: iosapp
  track_devices:
    - gary_iphone > gary.png, iosapp1, whse
    - lillian_iphone > lillian.png
  gps_accuracy_threshold: 100
  create_sensors: zon,zon1,ttim,zdis,cdis,wdis,nupdt,lupdt,info
```

### Zone, Interval and Sensor Configuration Items
###### inzone_interval 
The interval between location updates when the device is in a zone. This can be in seconds, minutes or hours, e.g., 30 secs, 1 hr, 45 min, or 30 (minutes are assumed if no time qualifier is specified).  
*Default:* 2 hrs

###### stationary_inzone_interval 
The interval between location updates when the device is in a Dynamic Stationary Zone. See Special Zones chapter for more information about stationary zones. This can be minutes or hours, e.g., 1 hr, 45 min, or 30 (minutes are assumed if no time qualifier is specified).  
*Default:* 30 min

###### stationary_still_time 
The number minutes with little movement (1.5 times the Home zone radius) before the device will be put into its Dynamic Stationary Zone.   
*Valid values:* Number. *Default:* 8

###### unit_of_measurement 
The unit of measure for distances in miles or kilometers.   
*Valid values:* mi, km. *Default*: mi

###### gps_accuracy_threshold 
iCloud location updates come with some gps_accuracy varying from 10 to 5000 meters. This setting defines the accuracy threshold in meters for a location updates. This allows more precise location monitoring and fewer false positive zone changes. If the gps_accuracy is above this threshold, a location update will be retried again to see if the accuracy has improved.  
*Default*: 125m

###### old_location_threshold
When the device is located, it’s location coordinates and the time it was located are updated. If the time is older than this value (in minutes), the transaction is discarded and the device is repolled until a current location is available. It is repolled on a 15-second interval, followed by a 1-minute, 5-minute and 15-minute interval.  
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

### Examples of all Configuration Parameters
```yaml
device_tracker:
  - platform: icloud3
    username: !secret gary_fmf_username
    password: !secret gary_fmf__password
    track_devices:
      - gary_iphone > gary-icloud-acct@email.com, gary.png
      - lillian_iphone > lillian-icloud-acct@email.com, lillian.png
      
    group: family
    
    inzone_interval: '2 hrs'
    max_interval: '30 min'
    stationary_inzone_interval: '30 min'
    stationary_still_time: '8 min'
    
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
    
    log_level: debug, eventlog
```
