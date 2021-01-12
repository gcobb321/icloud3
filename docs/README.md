# iCloud3  Device Tracker Custom Component

[![Version](https://img.shields.io/badge/Version-v2.3-blue.svg)](https://github.com/gcobb321/icloud3)
[![Released](https://img.shields.io/badge/Released-January,_2021-blue.svg)](https://github.com/gcobb321/icloud3)
[![ProjectStage](https://img.shields.io/badge/ProjectStage-General_Availability-red.svg)](https://github.com/gcobb321/icloud3)
[![Type](https://img.shields.io/badge/Type-Custom_Component-orange.svg)](https://github.com/gcobb321/icloud3)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/gcobb321/icloud3)

### Introduction

iCloud3 is an improved version of the *iCloud device_tracker integration* installed with Home Assistant.  It is designed to:

* Connect with the iCloud Location Services using Find-my-Friends and Find-my-Phone tracking methods.
* Provide easy-to-use presence detection that does not rely on any other program, other than Home Assistant and the Home Assistant IOS app.
* Report accurate information, i.e. current zone, location, distance from a zone and travel time on a timely basis that can be used reliably in automations and scripts.
* Use the Home zone and other zones for location based calculations and tracking.
* Conserve the devices battery.
* Correct GPS wandering errors leading to incorrect triggering of automations.
* Provide more distance, travel time, and zone attributes than the base iCloud component and to create sensors for many of the attributes that easily display device information on Lovelace cards.
* Monitor the iOS App for zone and location changes.
* Display activity on the iCloud3 Event Log custom Lovelace card.

Below are some sample Lovelace screenshots showing how iCloud3 information can be displayed (see *ui-lovelace-icloud3.yaml* in the *sample_automations_scripts* directory of the iCloud3 repository). Example configuration files for sensors, switches, badges, automations and scripts are also found in the *sample_automations_scripts* directory that report location information and device status, along with running automations (opening a garage door) when arriving home. Other uses (security, lighting, heating & cooling control, etc.) can be added to the automations to meet your needs.

*Gary Cobb, aka GeeksterGary*


![readme intro](images/readme.jpg)


### What's different

iCloud3 has many features not in the base iCloud device_tracker that is part of Home Assistant. It exposes many new attributes, provides many new features, is based on enhanced route tracking methods, is much more accurate, and includes additional service calls. Lets look at the differences.

| Feature | Original iCloud | iCloud3 |
|---------|-----------------|---------|
| Integration with the HA IOS App            | No                                                           | Yes, Geographic Zone Enter/Exit, Background Fetch, Significant Location Update & Manual transactions are detected and processed immediately after they are issued. |
| Device Selection                           | None                                                         | Specify devices to be tracked by their devicename, i.e., *gary_iphone* or *lillian_iphone* using the *tracked_devices* parameter. |
| Locate device using Family Sharing List                      | Yes | Yes |
| Locate device using Find-my-Friends | No | Yes |
| Locate device using HA IOS App without iCloud Services | No | Yes |
| Minimum Poll Interval | 1 minute | 15 second |
| Zone used to calculate distance and travel time | 'Home' zone only | 'Home' zone and any other HA zone(s) |
| Distance Accuracy | 1 km/mile | .01 km/mile |
| Variable Polling | Yes - Based on distance from home, battery level, GPS Accuracy | Yes, based on distance and Waze travel time to the 'home' or another zone, direction of travel, if the device is in a zone, battery level, GPS Accuracy and 'old location' status. |
| Detects zone changes | No - Also requires other device_trackers (OwnTracks, Nmap, ping, etc. | Yes, no other programs are needed other than the HA IOS App. |
| Detects when leaving Home Zone (or another *base_zone* zone) | Delayed to next polling cycle (default of 30-minutes) | Detects when the Home Assistant IOS app issues a Zone Enter/Exit notification |
| Discards old transactions | No | Yes, if older than 2-minutes or with poor gps accuracy. |
| Fixes 'Not Home' issue when in Sleep Mode | No | Yes, by discarding all transactions that are closer than 1-km when the device is in a zone and by providing zone template sensors that are used to trigger automations rather than device_tracker state changes. |
| Integrates with Waze route/map tracker | No | Yes, the Waze travel time is used to determine the 'polling interval'. Waze can be disabled if not available using configuration parameters. |
| Device Polling Interval when close to the 'home' or another zone | 1+ minutes (?) | 15-seconds |
| Dynamic Stationary Zone | No | Yes, a Stationary Zone is created if no movement has been detected in 8-minutes (configurable). The polling interval is set to 30-minutes (default) until zone exit notification is received. |
| Service call commands | Set polling interval, reset devices | Set polling interval, reset devices, pause/restart polling, change zone, enable/disable Waze Route information usage, information logging (some commands can be for all devices or for a specific device) |
| Track device from more than one location | No, can only track from the 'home' zone | Yes, can track from the Home zone and another *base_zone* zone (office, second home, etc.). |
| Event Log Lovelace Card | No | Yes. Displays significant events as iCloud3 starts up and locates devices. |
| Create Sensors for device attributes | No | Yes. Sensors created for many of the device_tracker attributes. You can also customize the list of sensors to only create the ones you are interested in. |
