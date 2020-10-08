# Quick Start Guide

### The Basics - How iCloud3 works

iCloud3 operates on a 5-second cycle, looking for transactions from the HA IOS App. It looks for Geographic Zone Enter/Exit, Background Fetch, Significant Location Update and Manual transactions. When one is detected, it determines if the transaction is current before it is processed. Transactions older than 2-minutes are discarded. Additionally, to minimize GPS wandering and out-of-zone state changes, transactions within 1km of a zone are discarded when the device is in a zone.  Every 15-seconds, it determines if any devices needed to be polled using the iCloud Location Services Find-my-Friends or family-sharing methods as described below.

iCloud3 polls the device on a dynamic schedule and determines the polling interval time based on:

- If the device is in a zone or not in a zone. The zones include those you have configured and the special *Stationary Zone* created by iCloud3 and used to minimize polling if you haven't changed your location in a while (shopping center, friends house, doctors office, etc.).
- A 'line-of-sight' calculated distance from the Home or other zone to your current location using the GPS coordinates.
- The driving time and distance between Home or another zone and your current location using the [Waze Route Calculator](http://www.waze.com) map/driving/direction service.
- The direction you are going — towards Home or other zone, away from the zone or stationary.
- The battery level of the device if the battery level is available.
- The accuracy of the GPS location and if the location returned by the iCloud Location Service or the iOS App is 'old'.

The above analysis results in a polling interval. The further away from Home or other zone and the longer the travel time back to the zone, the longer the interval; the closer to the zone, the shorter the interval. The polling interval checks each device being tracked every 15-seconds to see if it's location should be updated. If so, it and all of the other devices being tracked with iCloud3 are updated. With a 15-second interval, you track the distance down 1/10 of a mile/kilometer. This gives a much more accurate distance number that can used to trigger automations. You no longer limited to entering or exiting a zone. 

Another custom component module (`pyicloud_ic3.py`) is responsible for communicating with the iCloud Location Services to authenticate the iCloud account and to locate the devices associated with the account using either Find-my-Friends or Family Sharing tracking methods.

### Guide to installing, setting up and using iCloud3

There are a number of steps you must take to get iCloud3 installed, track your devices, interface with your iCloud account and the iOS App you have installed on your phones, configure iCloud3, use the Event Log to help monitor location changes and solve tracking and set up problems, etc. This guide will help you get going with iCloud3. 

The following steps will guide you through setting up and using iCloud3:

| Steps                                                        | Chapter                                                |
| ------------------------------------------------------------ | ------------------------------------------------------ |
| 1. Review how iCloud3 uses location information from your iCloud account and the iOS App. | [1.1 Getting Started]()                                |
| 2. Review the tracking methods and decide which one you want to use - Find-my-Friends (fmf) , Family Sharing (famshr) or the iOS App (iosapp). | [1.1 Getting Started]()                                |
| 3. Review how to authenticate your iCloud account so iCloud3 can locates your phones (devices). | [1.1 Getting Started]()                                |
| 4. Set up the Find-my-Friends tracking method using the iPhone's FindMy app or the Family Sharing tracking method using the iPhone's Settings App to access the iCloud account Family Sharing list. | [1.3 Preparing for iCloud3?id=]())                     |
| 5. Set up the iOS App on every device you want to track. Add a suffix to the iOS App device_tracker entity name to prevent conflicts with iCloud and iCloud3 device_tracker entities. | [1.4 Setting up the iOS App]()                         |
| 6. Understand how to set up iCloud3 to track devices and review how the Event Log will help troubleshoot startup errors. | [1.5 Setting up iCloud3]()                             |
| 7. Install iCloud3 from HACS or install it manually. Set up a minimal configuration and restart Home Assistant to load iCloud3 the first time. | [1.6 Installing and Starting iCloud3]()                |
| 8. Set up a Lovelace card to show the iCloud3 tracking information for each phone. | [1.7 Setting up a Lovelace Card for tracked devices]() |
| 9. Review the iCloud3 Event Log Card screens and the Actions command menu. Install the Event Log on a Lovelace Dashboard, | [1.8 Setting up and Using the Event Log]()             |
| 10. Review the iCloud3 configuration parameters that let you specify how you can tracked devices, use zones, configure the Waze Route Tracking program, and tailor iCloud3's operations. | [2.1  Configuration Parameters]()                      |
| 11. Review the iCloud3 sensors and select the ones you want to create for your automations, scripts and Lovelace cards. | [2.3 Special Zones, 2.4 Sensors]()                     |
| 12. Review the Event Log screens and Actions pull down commands that let you restart iCloud3, pause and resume tracking. and display data and tracking monitors helpful in troubleshooting problems and issues. | [2.5 The Event Log]()                                  |
|                                                              |                                                        |