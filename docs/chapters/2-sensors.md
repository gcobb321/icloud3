# Sensors Created from the Device's Attributes

### How the sensors are used

Normally in HA, a template sensor is used to convert one entity's attributes into a state that can be used in automations or displayed on Lovelace cards. The `device_tracker.gary_iphone.attributes.zone_distance`  value is converted to an `sensor.gary_iphone_zone_distance` entity using a template sensor. To do this, HA to monitors the attribute's value to see if it has been changed, and if it has, convert the template to the new value and then update the sensor entity while it is doing all the other stuff it does.  

iCloud3 creates and updates sensor entities without the need for template sensors. This makes the device_tracker's attribute values easier to reference in automations and scripts, and immediately available without waiting on HA to do the conversion.

Below is a sample automation using the sensors created and updated by iCloud3 .

```yaml
automation:
  - alias: Gary Arrives Home
    id: gary_arrives_home
    trigger:
    - platform: state
      entity_id: sensor.gary_iphone_zone_name1
      to: 'Home'
    - platform: template
      value_template: '{{states.sensor.gary_iphone_zone_distance.state | float <= 0.2}}'
```

The following sensors are updated using the device_tracker's attributes values:

| Tracking Sensors | Special Sensors | Device Sensors  |
| ---------------- | --------------- | --------------- |
| interval        | zone             | battery        |
| travel_time     | zone_name1       | battery_status |
| zone_distance   | zone_name2       | gps_accuracy   |
| waze_distance   | zone_name3      | trigger        |
| calc_distance   | zone_timestamp   |                |
| last_update     | last_zone        | name (user's name) |
| next_update     | last_zone_name1 |                |
| last_located    | last_zone_name2 |                |
| poll_count      | last_zone_name3 |                |
| info            | badge            |                |

### Naming the sensors

The devicename is added to the beginning of each sensor ; e.g., `gary_iphone_zone_distance`. 

The above example is for the Home zone. If you are also tracking another zone, the zone name will be added onto the sensor name before the devicename. For example, if you are also tracking information for the 'whse' zone, the zone distance sensor becomes `whse_gary_iphone_zone_distance`.

### The Badge Sensor

The `badge` sensor displays either the zone name or distance from the Home zone and the person's picture that is associated with the device.  The name of the file containing the person's picture is also entered on the `track_devices` configuration parameter for the device. The picture must be located in the `www/local/` directory and end with '.jpg' or '.png'.

Example:

- gary_iphone > gary-2fa-acct, gary.png    
  The `sensor.gary_iphone_badge` sensor is created with the picture file `/local/gary.png`.

!> The '/local/' directory refers to '/config/www/' directory.

![badge](../images/badge.jpg)

### Zone Sensors

Zone sensors provide different formats for the zone name. 

| zone value          | zone_name1 | zone_name    | zone_name3    |
| ------------------- | ---------- |     -------- | ------------- |
| home                | Home       | Home         | Home          |
| not_home            | Away       | Not Home     | NotHome       |
| whse                | Whse       | Whse         | Whse          |
| gary_iphone_stationary | Stationary | Gary Iphone Stationary | GaryIphoneStationary |

!> `zone_name1` is the recommended sensor for triggering zone changes in automations and scripts.

### Zone exits due to GPS wandering

There are times when gps wanders and you receive a zone exit state change when the device has not moved in the middle of the night. The sequence of events that takes place under the covers is:
1. A zone change notification is sent by the IOS App based on bad gps information.
1. The device's state and location is changed, triggering an automation that runs when you exit the Home zone.
1. iCloud3 sees the new state and location and processes the data and sees the notification data is old and it was caused an incorrect state change. 
1. iCloud3 then puts the device back into the Home zone where it belongs.

The net effect is HA triggers the automation before iCloud3 gets control so the correction takes place after the automation has already run.

The solution to eliminating this problem is to not trigger automations based on device state changes but to trigger them on zone changes. A `zone` and `last_zone` sensor, updated by iCloud3, is used to do this. These sensors are only updated by iCloud3 so they are not effected by incorrect device state changes.  See the example `gary_leaves_zone` automation in the `sn_home_away_gary.yaml` sample file where the `sensor.gary_iphone_zone` is used as a trigger. 


### Customizing sensors that are created by iCloud3

A lot of sensors are created by iCloud3. If you have several devices you are tracking and also have a second, base_zone, the list gets even longer. The configuration parameters `create_sensors` and `exclude sensors` let you select only the sensors you want to create. A special code (see table below) is used to identify the sensors you want to create or exclude.

###### create_sensors
This configuration parameter lets you select only the sensors to be created. 

Example: 
- `create_sensors: zon,zon1,ttim,zdis,cdis,wdis,nupdt,lupdt,info`  
  Create the zone, zone_name1, zone_distance, calc_distance, waze_distance, next_update, last_update, and info sensors.

###### exclude_sensors
This configuration parameter is the opposite of the `create_sensors` parameter. All sensors except the ones you specify are created.

Example:
- `exclude_sensors: zon2,zon3,lzon2,lzon3,zon,zonts,bat`  
  Create all sensors except zone_name2, zone_name3, last_zone2, last_zone3, zone_timestamp and battery_status.


The following sensors are updated using the device_tracker's attributes values:

| Tracking Sensors | Code  |      | Special Sensors  | Code  |      | Device Sensors         | Code   |
| ---------------- | ----- | ---- | ---------------- | ----- | ---- | ---------------------- | ------ |
| interval        | intvl |      | zone            | zon   |      | battery               | bat    |
| travel_time     | ttim  |      | zone_name1      | zon1  |      | battery _status | batstat |
| zone_distance   | zdis  |      | zone_name2      | zon2  |      |  |  |
| waze_distance   | wdis  |      | zone_name3      | zon3  |      | gps_accuracy      | gpsac   |
| calc_distance   | cdis  |      | zone_timestamp  | zonts |      | altitude          | alt     |
| travel_distance | tdis  |      | last_zone       | lzon  |      | vertical_accuracy | vacc    |
| dir_of_travel   | dir   |      | last_zone_name1 | lzon1 |      |                   |         |
| last_update     | lupdt |      | last_zone_name2 | lzon2 |      | trigger           | trig    |
| next_update     | nupdt |      | last_zone_name3 | lzon3 |      | badge | badge |
| last_located    | lloc  |      | last_zone_name3 | lzon3 |      | name | name |
| poll_cnt        | cnt   |      |                  |       |      |            |  |
| info            | info  |      | base_zone       | bzon  |      |          | |


