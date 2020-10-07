# Set up a Lovelace Card for iCloud3

There are many sensors created by iCloud3 that can be used in scripts, in automations and on Lovelace cards. These sensors are described in [Chapter - 2.4 Using Sensors](). A sample of one of the cards is shown below to get you going. Other examples are shown [Chapter - 3.1 Sample Lovelace Cards](). 

The sample lovelace cards also show the raw yaml code that generates them. You can use these cards as a starting place for the devices you are tracking by copying and customizing the setup in the *HA Sidebar > Lovelace* windows.



![lovelace_gc_lc_5x2](../images/lovelace_gc_lc_5x2.jpg)

```yaml
  - title: Location (Gary)
    icon: mdi:cellphone-iphone
    cards:
      - type: vertical-stack
        cards:
          - type: glance
            title: Location Info - Gary
            column_width: 20%
            entities:
              - entity: device_tracker.gary_iphone
                name: Gary
              - entity: sensor.gary_iphone_interval
                name: Interval
                icon: mdi:clock-start
              - entity: sensor.gary_iphone_travel_time
                name: TravTime
                icon: mdi:clock-outline
              - entity: sensor.gary_iphone_zone_distance
                name: Home
                icon: mdi:map-marker-distance 
              - entity: sensor.gary_iphone_next_update
                name: NextUpdt
                icon: mdi:update
         
          - type: glance
            column_width: 20%
            entities:
              - entity: sensor.gary_iphone_waze_distance
                name: WazeDist
                icon: mdi:map-marker-distance
              - entity: sensor.gary_iphone_calc_distance
                name: CalcDist
                icon: mdi:map-marker-distance
              - entity: sensor.gary_iphone_dir_of_travel
                name: Direction
                icon: mdi:compass-outline
              - entity: sensor.gary_iphone_last_located
                name: Located
                icon: mdi:map-clock
              - entity: sensor.gary_iphone_last_update
                name: LastUpdt
                icon: mdi:history
              
          - type: horizontal-stack
            cards:
            - type: entities
              entities:
                - entity: sensor.gary_iphone_info
                  name: Info
                  icon: mdi:information-outline 

#-------------------------------------------------------------------------              
      - type: vertical-stack
        cards:
          - type: glance
            title: Location Info - Lillian
            column_width: 20%
            entities:
              - entity: device_tracker.lillian_iphone
                name: Gary
              - entity: sensor.lillian_iphone_interval
                name: Interval
                icon: mdi:clock-start
              - entity: sensor.lillian_iphone_travel_time
                name: TravTime
                icon: mdi:clock-outline
              - entity: sensor.lillian_iphone_zone_distance
                name: HomeDist
                icon: mdi:map-marker-distance 
              - entity: sensor.lillian_iphone_next_update
                name: NextUpdt
                icon: mdi:update
         
          - type: glance
            column_width: 20%
            entities:
              - entity: sensor.lillian_iphone_waze_distance
                name: WazeDist
                icon: mdi:map-marker-distance
              - entity: sensor.lillian_iphone_calc_distance
                name: CalcDist
                icon: mdi:map-marker-distance
              - entity: sensor.lillian_iphone_dir_of_travel
                name: Direction
                icon: mdi:compass-outline
              - entity: sensor.lillian_iphone_last_located
                name: Located
                icon: mdi:map-clock
              - entity: sensor.lillian_iphone_last_update
                name: LastUpdt
                icon: mdi:history
          - type: entities
            entities:
              - entity: sensor.lillian_iphone_info
                name: Info
                icon: mdi:information-outline 

```