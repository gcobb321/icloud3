***If you appreciate my work, could you buy me a coffee?***
<a href="https://www.buymeacoffee.com/gcobb321" target="_blank">
<img src="https://gcobb321.github.io/icloud3_v3_docs/images/buymeacoffee-docs-button-icon.png" width="150" height="35"></a>

***Thanks***,
***Gary Cobb, aka geekstergary***

-----
## 🍎 iCloud3 v3.7.6 Beta 3 (10/2/2026)
### 🎉 New and Improved Items
1. **iCloud3 Analytics**: (Menu #2 - Parametes)
    -  The iCloud3 Analytics collects version, location (country/region), usage and various counts from the 15,000+ iCloud3 users. It's purpose is to report summary information showing where users are located, what version is being used and various counts (Apple Account, tracked devices, comments, etc.). The data you will send is shown below. Summary reports can be selected on *Reports* screen. Hopefully, you will Enable *Send iCloud3 Analytics Data* on the Configure *iCloud3 Analytics* screen and participate in this project.
    - No personal data is sent; data that is sent from your iCloud3 installation is displayed on the screen. An example is:
        - {'uuid': 'HA Installation ID', 'version': '3.7.6', 'version_date': '2026-09-17', 'country': 'US', 'region': 'FL', 'apple_accts': 2, 'mobapp_devices': 3, 'devices': 8, 'tracked': 3, 'monitored': 3, 'inactive': 2, 'comment': 'To open my garage door when I arrive Home'}
    - The Analytics is an opt-in and it defaults to disabled. A message is displayed on the Configure Menu screens until you either enable or disable participating.
    - The *Analytics Reports* screen lets you view Analytic data multiple ways (by country, by version, comments, usage, etc.). The reports are displayed on the screen and show the most current data.
    - The data is sent once a day around 01:00:00/1:00am.
    - The data is stored using the same global database (CloudFlare) that is used by the HA Analytics program.
2. **Newer Apple Account Device detection**:
    - When iCloud3 starts and when the Apple iCloud location data is refreshed, devices that have been added to the Apple Account are now detected. Each new device is analyzed to determine if it is a new unknown device or an updated version of a device already being tracked. It uses the device name, type, version and current status to determine this.
    - New devices that appear to match one already tracked fall into three categories:
        - The new device was setup from the old device and the device names match. The configuration is automatically updated to the new device and it is now tracked. An HA Repair issue is created informing you of the configuration change.
        - The new device was set up as a new device and the device names can be associated with each other (old=Lillian-Watch, new=Lillian's Apple Watch). An HA Repair issue is created requesting you to confirm the newer device that was detected. The configuration is updated when you confirm (Submit) the device.
        - More than one device with the same type (one name may be similar) as a tracked device is detected and a choice can not be determined. An HA Repair issue is created requesting you to select the correct device on the *Update iCloud3 Devices* screen.
    - Notifications are displayed as HA Repair issues, in the Event Log and as an iCloud3 Alert (sensor.icloud3_alert).
3. **Default inZone Intervals** - (Menu #2 - Parameters)
    -   This screen is used to set the default inZone interval value assigned to a new device. The Device's value can be changed after it is added.

### 🐞 Bug Fixes
1. **Email Filter** - Fixed a problem creating the filter for a password when it contains an '@' in the first 3-letters. (@jata1, @celsojunior75)
2. **Disable/Delete Device** - Disabling/Deleting devices directly in HA was creating problems within iCloud3 and leading to device registry conflicts. This has been fixed. (@amiel-35)
3. **device_entity_id_2 suffix** - Fixed several problems correcting this condition during the *device_entity_id_2 → device_entity_id* process. (@amiel-35)
4. **Reload from HA Settings** - Fixed problems with reloading iCloud3 from the Devices & settings screen. (@amiel-35)
4. **Waze** - Fixed a problem where Waze would not be used if the distance > HistoryDB Max distance when it should be the Waze Max distance. (@celsojunior75)

### 📢 Other Updates
1. **Apple Terms of Use** - Improved the handling of Apple's Terms-of-Use Approval Needed request:
    - A message is now listed at the top of the Event Log in the greenbar alert area
    - The iCloud3 Alert Sensor (*sensor.icloud3_alert*) is updated
    - The message appears once in the Event Log at restart instead of every 2-5 minutes
    - Improved notifications on the iCloud3 Configure Settings screens
2. **Configuration Menus**:
    - Added a separator line between the Menu Items (screen you are selecting) and the Menu Actions (Menu #1/2, Exit) for clarity.
    - Moved the *Away Time Zone* to Menu #1 - Devices and Sensors
    - Added **Default inZone Intervals** and *iCloud3 Analytics** to Menu #2 - Parameters.
3. **Event Log**:
    - Reorganized Stage 4 - Apple Account Device to setup each Apple account individually instead of first logging into all of the accounts, combining all of the devices into one list and then setting them up. The results are easier to review and errors are clearer.
    - Devices are now sorted by name instead of listed in the order they were added to iCloud3.
    - Various tweaks for clarity.