# Device Tracker Services

Four services are available for the iCloud3 device tracker component that are used in automations. 

| Service | Description |
|---------|-------------|
| icloud3_update | Send commands to iCloud3 that change the way it is running (pause, resume, Waze commands, etc.) |
| icloud3_set_interval | Override the dynamic interval calculated by iCloud3. |
| icloud3_find_iphone_alert | Display the *Find My iPhone Alert* notification and play an alert sound on the specified phone. |
| icloud3_restart | Restart the iCloud3 custom component. Restart iCloud3.This will recheck the availability of the iCloud Location Service and relocate all devices. |

### *icloud3_update* Service

This service allows you to change the way iCloud3 operates. The following parameters are used:

| Parameter | Description |
|-----------|-------------|
| device_name | Name of the device to be updated. All devices will be updated if this parameter is not specified.  All instances of the device_name are updated if it is in several groups. update *(Optional)* |
| command | The action to be performed (see below). *(Required)* |
| parameter | Additional parameters for the command. |

The following describe the commands that are available. 

| Command/Parameter |  Description |
|-----------------|-------------|
| pause |  Stop updating/locating a device (or all devices). Note: You may want to pause location updates for a device if you are a long way from home or out of the country and it doesn't make sense to continue locating your device. |
| resume |  Start updating/locating a device (or all devices) after it has been paused. |
| resume |  Reset the update interval if it was overridden the 'icloud3_set_interval' service. |
| location | Send a 'location update' request to the iOS App. This is done using the iOS App's notify service call. |
| zone zonename | service call) and immediately update the device interval and location data. Note: Using the device_tracker.see service call instead will update the device state but the new interval and location data will be delayed until the next 15-second polling iteration (rather than immediately). |
| waze on | Turn on Waze. Use the `waze` method to determine the update interval. |
| waze off | Turn off Waze. Use the `calc` method to determine the update interval. |
| waze toggle |  Toggle waze on or off |
| waze reset_range | Reset the Waze range to the default distances (min=1, max=99999). |
| log_level | Display iCloud3 debug information in the HA Log file and, optionally, on the iCloud3 Event Log Card. <br>The following parameters are available:<br>- `eventlog` = Display additional details about the iCloud3 events and operations that are in the iCloud3 Event Log Card.<br>- `debug` =  Add entries related to iCloud3 location operations to the HA log file <br>- `rawdata` = Add the actual raw data records returned from iCloud Web/Location Services to the HA Log file when devices are located.<br>- `intervalcalc` = The methods and calculations related to the interval, next update time, zone, etc. |
| restart | Restart the iCloud3 custom component. Restart iCloud3.This will recheck the availability of the iCloud Location Service and relocate all devices. |
| counts | Display the Device Information and the iCloud/iOS App counters in the Event Log. |

#### Example Automations or Scripts

```yaml
# Commands that control how iCloud3 operates

icloud3_command_restart:
  alias: 'Restart iCloud (Command)'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: restart
       
icloud3_command_resume_polling:
  alias: 'Resume Polling'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: resume
        
icloud3_command_pause_polling:
  alias: 'Pause Polling'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: pause

icloud3_command_pause_polling_gary:
  alias: 'Pause (Gary)'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        device_name: gary_iphone
        command: pause

icloud3_update_location:
  alias: 'Update Location (all)'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: location

icloud3_command_garyiphone_zone_home:
  alias: 'Gary - Zone Home'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        device_name: gary_iphone
        command: zone home      

icloud3_command_garyiphone_zone_not_home:
  alias: 'Gary - Zone not_home'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        device_name: gary_iphone
        command: zone not_home
```

```yaml
#Commands to that change the Waze Tracking Service

icloud3_command_toggle_waze:
  alias: 'Toggle Waze On/Off'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: waze toggle
        
icloud3_command_reset_waze_range:
  alias: 'Reset Waze Range'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: waze reset_range
```

```yaml
#Commands that change the log_level options that write debug information to the HA Log File and the iCloud3 Event Log

icloud3_command_loglevel_debug:
  alias: 'LogLevel-Debug Info to HA Log (Toggle)'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: log_level debug
        
icloud3_command_loglevel_intervalcalc:
  alias: 'LogLevel-Interval Calc (Toggle)'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: log_level intervalcalc
        
icloud3_command_loglevel_eventlog:
  alias: 'LogLevel-Event Log (Toggle)'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: log_level eventlog

icloud3_command_loglevel_debug_eventlog:
  alias: 'LogLevel-Debug Info to HA Log & EventLog(Toggle)'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: log_level debug, eventlog
 
icloud3_command_loglevel_intervalcalc_eventlog:
  alias: 'LogLevel-Interval Calc & EventLog (Toggle)'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: log_level intervalcalc, eventlog

icloud3_command_loglevel_info:
  alias: 'LogLevel-Display Flags'
  sequence:
    - service: device_tracker.icloud3_update
      data:
        command: log_level info
```

### *icloud3_set_interval* Service

This service allows you to override the interval between location updates to a fixed time. It is reset when a zone is entered or when the icloud3_update service call is processed with the 'resume' command. The following parameters are used:

| Parameter | Description |
|-----------|-------------|
| device_name | Name of the device to be updated. All devices will be updated if this parameter is not specified. All instances of the device_name are updated if it is in several groups.*(Optional)* |
| interval | The interval between location updates. This can be in seconds, minutes or hours. Examples are 30 sec, 45 min, 1 hr,  2 hrs, 30 (minutes are assumed if no time descriptor is specified). *(Required)* |

```yaml
#Change Intervals

icloud3_set_interval_15_sec_gary:
  alias: 'Set Gary to 15 sec'
  sequence:
    - service: device_tracker.icloud3_set_interval
      data:
        device_name: gary_iphone
        interval: '15 sec'
 
icloud3_set_interval_1_min_gary:
  alias: 'Set Gary to 1 min'
  sequence:
    - service: device_tracker.icloud3_set_interval
      data:
        device_name: gary_iphone
        interval: 1

icloud3_set_interval_5_hrs_all:
  alias: 'Set interval to 5 hrs (all devices)'
  sequence:
    - service: device_tracker.icloud3_set_interval
      data:
        interval: '5 hrs'
```

### *icloud3_find_iphone_alert*  Service

This service will display a notification and play on the specified device based on the tracking method:

- Family Sharing - Display the alert using the Find My iPhone Alert process build into iOS.
- Find-my-Friends, iOS App - Send a notification with sound to the iOS App on the specified device .

| Parameter | Description |
|-----------|-------------|
| device_name | Name of the device *(Required)* |

```
#Send the Find My iPhone Alert message

icloud3_find_phone_alert_gary:
  alias: 'Find iPhone Alert (Gary)'
  sequence:
    - service: device_tracker.icloud3_find_iphone_alert
      data:
        device_name: gary_iphone

    - service: script.notify_gary_iphone
      data_template:
        title: 'Find iPhone Alert'
        message: 'Find iPhone Alert was triggered for Gary (gary_icloud/gary_iphone)'
```



### *icloud3_restart* Service

This service will restart iCloud3 and refresh all of the devices being handled by iCloud3. It does the same action as the `icloud3_command` with the `restart` option described above. You will have to restart Home Assist if you have made changes to the configuration parameters (new device type, new device name, etc.) 

```yaml
#Commands to Restart iCloud3

icloud3_command_restart:
  alias: 'iCloud3 Restart'
  sequence:
    - service: device_tracker.icloud3_restart
```