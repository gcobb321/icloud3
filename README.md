# iCloud3 v3

------

### Release Candidate - v3.0.rc10.4 (2/18/2024)

------

[![CurrentVersion](https://img.shields.io/badge/Current_Version-v3.0-blue.svg)](https://github.com/gcobb321/icloud3_v3)  [![Type](https://img.shields.io/badge/Type-Custom_Component-orange.svg)](https://github.com/gcobb321/icloud3_v3)  [![HACS](https://img.shields.io/badge/HACS-Custom_Repository-orange.svg)](https://github.com/gcobb321/icloud3_v3)

[![ProjectStage](https://img.shields.io/badge/Project_Stage-Release_Candidate_10-forestgreen.svg)](https://github/gcobb321/icloud3_v3)  [![Released](https://img.shields.io/badge/Released-February,_2024-forestgreen.svg)](https://github.com/gcobb321/icloud3_v3)



iCloud3 is a device tracker custom component that tracks your iPhones, iPads and Apple Watches. iDevices in the Family Sharing List and the HA Mobile App Integration are trackable. The iDevice requests location data from from Apple's iCloud  Location Services and monitors various triggers sent from the Home Assistant Mobile App to Home Assistant. Sensors are updated with the device's location, distance from zones, travel time to zones, etc. 

Although AirPods and AirTags are in the iCloud Family Sharing list, they can not be tracked. They do not have the internal components to provide location data using cell towers and gps location information to Apple. 

### iCloud3 v3 Highlights

Although Home Assistant has it's own official iCloud component, iCloud3 goes far beyond it's capabilities. The important highlights include:

- **HA Integration** - iCloud3 is a Home Assistant custom integration that is set up and configured from the *HA Settings > Devices & Services > Integrations* screen.
- **Configuration Settings** - Configuration parameters are updated online using various screens and take effect immediately without restarting HA.
- **Track iPhones, iPads and Apple Watches** - Track or monitor your iDevices. 
- **Location data sources** - Location data comes from the iCloud Account and the HA Companion App (Mobile App).
- **Actively track a device** - The device will request it's location on a regular interval based on its distance from Home or another zone. 
- **Passively monitor a device** - The device does not request it's location. It is updated when another tracked device requests theirs.
- **Waze Route Service** - The travel time and distance to Home or another tracked zone is provided by Waze.
- **Waze Route Service History Database** - The travel time and distance data from Waze is saved to a local database and reused when the device is in a previous location. 
- **Track from multiple zones** - Tracking results (location, travel time, distance, arrival time, etc.) are reported from the Home zone or another zone (office, second home, parents, etc.). 
- **Primary Home Zone** - Set another zone as the primary zone for the device and report tracking results based on that location. This is useful when you have two homes, on a vacation at another location, triggering automations at your parents house with true devices, etc.
- **Improved GPS accuracy** - GPS wandering errors leading to incorrect zone exits are eliminated.
- **Monitors Mobile App activity** - Looks for location and trigger changes every 5-seconds. 
- **Enter Zone delay** - Delay processing Zone Enter triggers in case you are just driving through it.
- **Stationary Zone** - A dynamic *Stationary Zone* is created when the device has not moved for a while (doctors office, store, friend's house). This helps conserve battery life.
- **Nearby devices** - The distance to other devices is displayed and used to determine tracking results.
- **Zone monitoring** - The number of devices in each zone is displayed when a device is updated. 
- **Local Time Zone** - Event times are normally displayed using the time zone your HA server is in. If, hoowever, you are away from home and in another time zone can, the Event times can be displayed for the time zone you are in.
- **Zone Activity Log** - A log can be kept for each time you are in a zone. This log file (.csv format) can be imported into a spreadsheet program and used for expense reporting, travel history, device location monitoring, etc. 
- **Sensors and more sensors** - Many sensors are created and updated with distance, travel time, polling data, battery status, zone attributes, etc. Select only the ones you want to use. 
- **Battery status** - Updates the battery level and status (charging/not charging) from iCloud data during a tracking event and from the Mobile App every 5-seconds.
- **Distance Sensor Attributes** - Shows the distance to the center and edge of the Home zone, distance to other zones and distance to other devices. 
- **Event Log** - The current status and event history of every tracked and monitored device is displayed on the iCloud3 Event Log custom Lovelace card. Information about device configuration, errors and alerts, nearby devices, tracking results, debug information and location request results is displayed.
- **Updating and Restarting** - iCloud3 can be restarted without restarting Home Assistant.
- **Restore state values on restart** - The current device_tracker and sensor entity states are restored on a restart. The attributes are not restored but are reset on the first tracking Event. 
- **Device_tracker and sensor entities** - iCloud3 devices and sensors are Home Assistant entities that are added, deleted and changed on the  *Update iCloud3 Devices* and *Sensors* configuration screens.
- **Zone Exits for devices not using the Mobile App** - Devices that do not or can not (Apple Watch) use the Mobile App respond to a zone exit when it detects another nearby device has left a zone.
- **Extensive Documentation** - The iCloud3 User Guide explains the three main components, hot to get started, how to migrate from v2, how to install the integration, each of the screens and special features, the service calls that can request updates, locate iPhones and send notification alerts, examples of how to automate opening your garage door when you arrive home, etc.
- **And More** - Review the following documentation to see if it will help you track and monitor the locations of your iPhones, iPads and Apple Watches.

### Tracking Information Screen with Event Log

The screens below are an example of how the many tracking sensors can be displayed. The screen on the left shows the current tracking formation for Gary while the Event Log on the right shows a history of important tracking events.

![evlimg](https://gcobb321.github.io/icloud3_v3_docs/images/track-evlog-gary-tfz-lillian-home.png)

### iCloud3 Documentation

- Introduces the many features and components of iCloud3
- Describes how to migration from v2.4.7 to v3.0
- Provides step-by-step to install and configure iCloud3, it's components and it's supporting components (iCloud Account and the Mobile App)
- Highlights the configuration screens and parameters
- Provides example screens, automations and scripts
- The User Guide is [here](https://gcobb321.github.io/icloud3_v3_docs/#/)

### Installing or Upgrading to iCloud3 v3

- iCloud3 v3 is now available on the iCloud3 HACS base as a prerelease version. 

### Important Links

- **iCloud3 v3 User Guide** -The User Guide is quite extensive and can be found [here](https://gcobb321.github.io/icloud3_v3_docs/#/)
- **iCloud3 v3 GitHub Repository (Prerelease Version)** - The primary GitHub Repository is [here](https://github.com/gcobb321/icloud3)
- **iCloud3 v3 Development GitHub Repository** - The Development Repository is used for beta  version changes that have not been released yet is [here](https://github.com/gcobb321_v3)
- **Installing as a New Installation** - iCloud3 v3 is available in HACS as a prerelease version.  Installation instructions are [here](https://gcobb321.github.io/icloud3_v3_docs/#/chapters/3.2-installing-and-configuring)
- **Migrating from v2.4.x** - This includes installing iCloud3 v3, migrating your current configuration and reviewing it to insure it was migrated correctly. Instructions are [here](https://gcobb321.github.io/icloud3_v3_docs/#/chapters/3.1-migrating-v2-to-v3)




-----
*Gary Cobb, aka GeeksterGary*

