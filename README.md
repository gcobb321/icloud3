# iCloud3 v3 Device Tracker Custom Component

------

### Prerelease Version - v3.0-pr1 (8/20/2023)

------

[![CurrentVersion](https://img.shields.io/badge/Current_Version-v3.0-blue.svg)](https://github.com/gcobb321/icloud3_v3)  [![Type](https://img.shields.io/badge/Type-Custom_Component-orange.svg)](https://github.com/gcobb321/icloud3_v3)  [![HACS](https://img.shields.io/badge/HACS-Custom_Repository-orange.svg)](https://github.com/gcobb321/icloud3_v3)

[![ProjectStage](https://img.shields.io/badge/Project_Stage-Prerelease-forestgreen.svg)](https://github/gcobb321/icloud3_v3)  [![Released](https://img.shields.io/badge/Released-August,_2023-forestgreen.svg)](https://github.com/gcobb321/icloud3_v3)



iCloud3 is a device tracker custom component that tracks your iPhones, iPads, Apple Watches, AirPods and other Apple devices. It requests location data from Apple's iCloud  Location Services and monitors various triggers sent from the Home Assistant Companion App (iOS App) to Home Assistant. Sensors are updated with the device's location, distance from zones, travel time to zones, etc. 

### iCloud3 v3 Highlights

Although Home Assistant has it's own official iCloud component, iCloud3 goes far beyond it's capabilities. The important highlights include:

- **HA Integration** - iCloud3 is a Home Assistant custom integration that is set up and configured from the *HA Settings > Devices & Services > Integrations* screen.
- **Configuration Settings** - All of the parameters are updated on configuration screens selected from the *iCloud3 Integrations* entry.
- **Track devices from several sources** - Family members on the iCloud Account Family Sharing list, those who are sharing their location on FindMy App and devices that have installed the HA Companion App (iOS App) can be tracked.
- **Actively track a device** - The device will request it's location on a regular interval.
- **Passively monitor a device** - The device does not request it's location but is tracked when another tracked device requests theirs.
- **Waze Route Service** - The travel time and route distance to a tracked zone (Home) is provided by Waze.
- **Waze Route Service History Database** - The travel time and route distance received from Waze is saved to a local database to improve performance and eliminate the response delay due to poor cell service and slow internet speed. 
- **Track from Multiple Zones** - The device is always tracked from the Home Zone. Now it can also be tracked from another zone (office, second home, parents, etc.). Travel time and distance to the other zone is reported just like the Home zone. Additionally, another zone can act as the primary 'Home' zone (vacation home, parents home, etc). This can be configured by device or globally. 
- **Improved GPS Accuracy** - GPS wandering errors leading to incorrect zone exits are eliminated.
- **Passthru Zone** - Delay processing an Enter Zone trigger in case you are just driving through it.
- **Stationary Zone** - A dynamic *Stationary Zone* is created when the device has not moved for a while (doctors office, store, friend's house). This helps conserve battery life.
- **Sensors and more sensors** - Many sensors are created and updated with distance, travel time, polling data, battery status, zone attributes, etc. The sensors that are created is customizable.
- **Event Log** - The current status and event history of every tracked and monitored device is displayed on the iCloud3 Event Log custom Lovelace card. It shows information about devices that can be tracked, errors and alerts, nearby devices, tracking results, debug information and location request results.
- **Detailed debugging information** - Several levels location history transactions can be displayed in the Event Log or in the Home Assistant Log File. These include general information, debug data and the raw device location data received from iCloud Location Services.
- **Updating and Restarting** - iCloud3 can be restarted without restarting Home Assistant. The current device_tracker and sensor entity states are restored on a restart. It can also be reloaded from the *Configure Settings > Action* screen without restarting Home Assistant.
- **Device_tracker and sensor entities** - iCloud3 devices and sensors are true Home Assistant entities. They are added, deleted and updated using *Configuration Settings > Sensors* selection screens.
- **Nearby Devices** - The location of all devices is monitored and the distance between devices is determined. Information from devices close to each other is shared.
- **Zone Exits for devices not using the iOS App** - Devices that do not or can not (Apple Watch) use the iOS App respond to a zone exit when it detects another nearby device has left a zone.
- **And More** - Review the following documentation to see if it will help you track and monitor the locations of your family members and friends.

### Tracking Information Screen with Event Log

The screens below are an example of how the many tracking sensors can be displayed. The screen on the left shows the current tracking formation for Gary while the Event Log on the right shows a history of important tracking events.

![](./docs/images/track-evlog-gary-tfz-away-lillian-home.png)

### iCloud3 Documentation

- Introduces the many features and components of iCloud3
- Describes how to migration from v2.4.7 to v3.0
- Provides step-by-step to install and configure iCloud3, it's components and it's supporting components (iCloud Account and the iOS App)
- Highlights the configuration screens and parameters
- Provides example screens, automations and scripts
- The [User Guide is here](https://gcobb321.github.io/icloud3_v3/#/).

### Installing or Upgrading to iCloud3 v3

- iCloud3 v3 is now available on the iCloud3 HACS base as a prerelease version.  Instructions are in the [*iCloud3 User Guide > Migrating iCloud3 from v2.4.x to v3* here](./docs/chapters/0.1-migrating-v2.4-to-v3.0.md). There are also instructions on doing a manual download.

### Important Links

- **iCloud3 GitHub Repository (Prerelease Version)** - The  [GitHub Repository is here.](https://github.com/gcobb321/icloud3_v3)
- **Install using HACS ** - iCloud3 v3 is now available on the HACS base as a prerelease version.  Instructions are in the [*iCloud3 User Guide > Migrating iCloud3 from v2.4.x to v3* here](./docs/chapters/0.1-migrating-v2.4-to-v3.0.md).
- **Download and Install Manually** - This is also described in the iCloud3 User Guide. Select the above link.
- **Migrating from v2.4._** - See [here](https://gcobb321.github.io/icloud3_v3/#/chapters/0.1-migrating-v2.4-to-v3.0?id=migrating-icloud3-from-v24x-to-v30) for instructions on migrating from from an older version.
- **iCloud3 v3 User Guide** -The User Guide is quite extensive and can be found [here](https://gcobb321.github.io/icloud3_v3/#/).



-----
*Gary Cobb, aka GeeksterGary*

