# Sample Automations & Scripts
The automations and scripts are examples of using iCloud3 for presence detection, 

My set up is as follows:

- A SmartThings Hub with a Z-Wave sensor that detects if the garage door is open or closed and a Z-Wave switch that opens and closes the garage door. 
- Raspberry Pi running Home Assistant that is connected to the SmartThings hub using MQTT transactions.

My goal is to open the garage door when I arrive home, detect if the garage door is open when it should not be, display badges showing the stage of the garage door and location of people, be able to check the status of the garage door and to close it manually if it is open when it should not be.

The following automations and scripts does this reliably as long as I have a good cell signal and the GPS accuracy is within limits. These automations and scripts can be adapted for many other tasks (lights, security system, locks, camera operations, etc). 


##### Arriving Home Automation & Script
If Gary arrives home, open the garage door if the `gary_driving flag` is set, the garage door is closed, and the `sensor.gary_iphone_zone_name1` changes to Home or the `sensor.gary_iphone_zone_distance` is less than .2 miles.

```yaml
################################################################
#
#	HOME/AWAY AUTOMATIONS - GARY  (au_home_away_gary.yaml)
#
################################################################
#--------------------------------------------------------------
#   Gary arrives home
#--------------------------------------------------------------
- alias: Gary Arrives Home
  id: gary_arrives_home
  trigger:
    - platform: state
      entity_id: sensor.gary_iphone_zone_name1
      to: 'Home'

    - platform: template
      value_template: '{{states("sensor.gary_iphone_zone_distance") | float <= 0.2}}'
      
  condition: 
    - condition: state
      entity_id: input_boolean.gary_driving_flag
      state: 'on'
      
  action:
    - service: script.notify_gary_iphone
      data_template:
        title: 'Gary Arrives Home'
        message: 'Zone: {{ trigger.from_state.state }} --> {{ trigger.to_state.state }}, Distance: {{ states.sensor.gary_iphone_zone_distance.state }}' 
            
    - service: script.gary_arrives_home
```
```yaml
#--------------------------------------------------------------
#   Gary leaves home zone
#--------------------------------------------------------------
- alias: Gary Leaves Home
  id: gary_leaves_home
  trigger:
    - platform: state
      entity_id: sensor.gary_iphone_zone_name1
      to: 'Away'
      
  condition: 
    - condition: template
      value_template: '{{trigger.from_state.state == "Home"}}'
      
    - condition: template
      value_template: '{{states("sensor.gary_iphone_zone_distance") | float > 0}}'
    
    - condition: state
      entity_id: input_boolean.ha_started_flag
      state: 'on'    
  action:
    - service: script.gary_leaves_home
 
    - service: script.notify_gary_iphone
      data_template:
        title: 'Gary Leaves Home'
        message: 'Zone: {{ trigger.from_state.state }} --> {{ trigger.to_state.state }}, Distance: {{ states("sensor.gary_iphone_zone_distance") }}' 
        
    - service: script.gary_leaves_zone
```
```yaml
#--------------------------------------------------------------
#   Gary leaves a zone
#--------------------------------------------------------------
- alias: Gary Leaves Zone
  id: gary_leaves_zone
  trigger:
    - platform: state
      entity_id: sensor.gary_iphone_zone_name1
      to: 'Away'
      
  condition: 
    - condition: template
      value_template: '{{trigger.from_state.state != "Home"}}'
      
    - condition: template
      value_template: '{{states("sensor.gary_iphone_zone_distance") | float > 0}}'
    
    - condition: state
      entity_id: input_boolean.ha_started_flag
      state: 'on'    
  action:
    - service: script.notify_gary_iphone
      data_template:
        title: 'Gary Leaves Zone'
        message: 'Zone: {{ trigger.from_state.state }} --> {{ trigger.to_state.state }}, Distance: {{ states.sensor.gary_iphone_zone_distance.state }}' 
```
```yaml
##############################################################
#
#   HOME/AWAY SCRIPTS - GARY (sc_home_away_ary.yaml)
#
##############################################################

gary_status:
  alias: Send Gary Status
  sequence:
    - service: script.notify_gary_iphone
      data_template:
        title: 'Gary Status'
        message: 'Zone={{states("sensor.gary_iphone_zone")}}, 
                  Zone1={{states("sensor.gary_iphone_zone_name1")}}, 
                  Zone2={{states("sensor.gary_iphone_zone_name2")}}, 
                  Distance={{states("sensor.gary_iphone_zone_distance")}},
                  DriveFlag={{states("input_boolean.gary_driving_flag")}},
                  FarFlag={{states("input_boolean.gary_far_away_flag")}}'
```
```yaml
#-------------------------------------------------------------
#   Arrive Home
#-------------------------------------------------------------
gary_arrives_home:
  alias: 'Gary Arrives Home (script)'
  sequence:
    #Open garage door if driving flag is on
    - service: script.open_garage_door 
    
    #Turn off 'Away' flags
    - service: input_boolean.turn_off
      entity_id: input_boolean.gary_driving_flag
    - service: input_boolean.turn_off
      entity_id: input_boolean.gary_far_away_flag

```
##### General Notification Script
Send notifications to `gary_iphone`

```yaml
#-------------------------------------------------------------
#   Send Message to Gary - Central Notify Command
#-------------------------------------------------------------
notify_gary_iphone:
  alias: 'Send Message to Gary'
  sequence:
    - service: notify.mobile_app_gary_iphone
      data_template:
        title: "{{ title }} (mobile_app)"
        message: "{{ message }}"
```

##### Garage Door Automations
Scripts to support opening and closing the garage door if various conditions are met.

```yaml
#########################################################
#
#   SCRIPTS
#   -------
#
#   GARAGE DOOR/SET LOCATION SCRIPTS (sc_garage_door.yaml)
#
#########################################################
toggle_garage_door:
  alias: Toggle Garage Door
  sequence: 
    - service: switch.turn_on
      entity_id: switch.garage_door
```
```yaml
#--------------------------------------------------------------- 
#   If garage door is closed and Gary's driving flag is true
#   open the Garage Door, turn off Gary's driving flag and notify Gary
#   Called from automation_old/garage_door.yaml
#--------------------------------------------------------------- 
open_garage_door:
  alias: 'Open Garage Door'
  sequence:
    
    - condition: state
      entity_id: input_boolean.ha_started_flag
      state: 'on'
      
    - condition: state
      entity_id: sensor.garage_door_state
      state: 'closed'
      
    - condition: template 
      value_template: '{{states("sensor.gary_iphone_zone_distance")  | float <= 0.30}}'
   
    - condition: state
      entity_id: input_boolean.gary_driving_flag
      state: 'on'
 
    - condition: state
      entity_id: input_boolean.gary_far_away_flag
      state: 'off'
      
    - service: script.show_garage_door_status
  
    - service: switch.turn_on
      entity_id: switch.garage_door
      
    - service: script.turn_on
      entity_id: binary_sensor.garage_door_moving

    - service: script.notify_gary_iphone
      data_template:
        title: 'Garage Door Action'
        message: 'Garage Door Opened'
```
```yaml
open_close_garage_door:
  alias: 'Press Garage Door Button'
  sequence:
    - service: switch.turn_on
      entity_id: switch.garage_door
```
```yaml
show_garage_door_status:
  alias: 'Show Garage Door Status'
  sequence:
    - service: script.notify_gary_iphone
      data_template:
        title: 'Garage Door Control Status'
        message: 'Door={{states("sensor.garage_door_state")}},  DriveFlag={{states("input_boolean.gary_driving_flag")}}, Distance={{states("sensor.gary_iphone_zone_distance")}}, FarAway={{states("input_boolean.gary_far_away_flag")}}, Zone=<{{states("sensor.gary_iphone_zone") }}'
```

##### Garage Door Utility Scripts
The garage door should not be open after 8pm or if Gary is far from home.

```yaml
#--------------------------------------------------------------
#  Garage Door Utility Scripts (cov_garage_door.yaml()
#--------------------------------------------------------------
#   If the Garage Door is open after 8pm, close it
#--------------------------------------------------------------
- alias: Close Garage Door (Open after 8pm)
  id: close_garage_door_after_8pm
  trigger:
    platform: time
    at: '20:00:00'
    
  condition:
    condition: state
    entity_id: sensor.garage_door
    state: 'Open'
    
  action:
    - service: switch.turn_on
      entity_id: switch.garage_door
      
    - service: script.notify_gary_iphone
      data:
        title: Garage Door Closed
        message: After 8pm - Close Door Automation Triggered
```
```yaml
#--------------------------------------------------------------
#   If the Garage Door is open and no one is home, close it
#--------------------------------------------------------------
- alias: Close Garage Door (No One Home)
  id: close_garage_door_no_one_home
  trigger:
    platform: state
    entity_id: sensor.someone_home_flag
    to: 'all away'
    
  condition:
    condition: state
    entity_id: sensor.garage_door
    state: 'Open'
    
  action:
    - service: switch.turn_on
      entity_id: switch.garage_door
      
    - service: script.notify_gary_iphone
      data:
        title: Garage Door Closed
        message: No One Home - Close Door Automation Triggered
```


##### Open/Close Garage via SmartThings Hub
A `Garage Door Badge` is displayed non a Lovelace Card that  shows if door is open or closed. Determine it's state and display the correct picture image.
```yaml
#--------------------------------------------------------------
#   Garage Door ZWave Switch via Smarthings Hub (cov_garage_door.yaml)
#--------------------------------------------------------------
- platform: template
  covers:
    garage_door:
      open_cover:
#        service: script.show_garage_door_status
        service: switch.turn_on
        data:
          entity_id: switch.garage_door
      close_cover:
#        service: script.show_garage_door_status
        service: switch.turn_on
        data:
          entity_id: switch.garage_door         
```

##### Set/Clear Driving Flags
These flags are used to check if Gary was driving and if he is far away from home. 

- The `far away flag` is set if `gary_iphone` is more than 5-miles from Home. The garage door should not be open if Gary is more than 5-miles away.
- The `driving_flag` is set if `gary_iphone` is more than 2-miles away from Home. It is tested in the `gary arrives home` automation to not open the garage door if Gary is arriving home but was not far away from Home.

```yaml
#--------------------------------------------------------------
#   Turn on Gary's Driving Flag
#--------------------------------------------------------------
- alias: Gary Driving Flag Turn On
  id: gary_driving_flag_turn_on
        
  trigger:
    - platform: template
      value_template: '{{states("sensor.gary_iphone_zone_distance") | float > 2}}'
      #value_template: '{{states.sensor.gary_iphone_zone_distance.state | float > 2}}'

  condition:
    - condition: state
      entity_id: input_boolean.gary_driving_flag
      state: 'off'
       
  action:
    - service: input_boolean.turn_on
      entity_id: input_boolean.gary_driving_flag
```
```yaml
#--------------------------------------------------------------
#   Turn off Gary's Driving Flag if Home for 15 minutes if still on
#--------------------------------------------------------------
- alias: Gary Driving Flag Turn Off
  id: gary_driving_flag_turn_off
  trigger:
    - platform: state
      entity_id: device_tracker.gary_iphone
      to: 'home'
      for:
        minutes: 15
    
  condition:
    - condition: state
      entity_id: input_boolean.gary_driving_flag
      state: 'on'
      
  action:
    - service: input_boolean.turn_off
      entity_id: input_boolean.gary_driving_flag
```
```yaml
#--------------------------------------------------------------
#   Turn on Gary's Far Away Flag
#--------------------------------------------------------------
- alias: Gary Far Away Flag Turn On
  id: gary_far_away_flag_turn_on
  trigger:
    - platform: template
      value_template: '{{states("sensor.gary_iphone_zone_distance") | float > 5}}'
      #value_template: '{{states.sensor.gary_iphone_zone_distance.state | float > 5}}'
      
  condition:
    - condition: state
      entity_id: input_boolean.gary_far_away_flag
      state: 'off'
      
  action:
    - service: input_boolean.turn_on
      entity_id: input_boolean.gary_driving_flag

    - service: input_boolean.turn_on
      entity_id: input_boolean.gary_far_away_flag
```
```yaml
#--------------------------------------------------------------
#   Turn off Gary's Far Away Flag
#--------------------------------------------------------------
- alias: Gary Far Away Flag Turn Off
  id: gary_far_away_flag_turn_off
  trigger:
    - platform: template
      value_template: '{{states("sensor.gary_iphone_zone_distance") | float <= 5}}'
      #value_template: '{{states.sensor.gary_iphone_zone_distance.state | float <= 5}}'

  condition:
    - condition: state
      entity_id: input_boolean.gary_far_away_flag
      state: 'on'
      
  action:
    service: input_boolean.turn_off
    entity_id: input_boolean.gary_far_away_flag
```


##### Set Badge Sensors
```yaml
#--------------------------------------------------------------
#   Set Gary, Lillian, Garage Door Badge Info (sn_badges.yaml)
#--------------------------------------------------------------
#--- Gary/Lillian location badge --------------------
- platform: template
  sensors:
    gary_badge:  
      friendly_name: Gary
      value_template: '{{states("sensor.gary_iphone_badge")}}'
      entity_picture_template: /local/gary.png
```
```yaml
#--- Garage Door Open/Closed Badge--------------------
- platform: template
  sensors:
    garage_door_badge:
      value_template: >-
        {{states("sensor.garage_door_state") | title}}
      entity_picture_template: >-
        {% if is_state("sensor.garage_door_state", "open") %}
          /local/garage-door-open.png
        {% else %}
          /local/garage-door-closed.png 
        {% endif %}
```

##### Garage Door MQTT Switch Setup for SmartThings
```yaml
#-------------------------------------------------------------
#   Garage Door ZWave Switch for SmartThings (sw_garage_door.yaml)
#--------------------------------------------------------------

#---- Garage Door Z-Wave switch ----------------------------
- platform: mqtt
  name: "garage_door"
  state_topic: "smartthings/Garage Door/switch/state"
  command_topic: "smartthings/Garage Door/switch/cmd"
  payload_on: "on"
  payload_off: "off"
  retain: false
```