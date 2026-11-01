***Total downloads for v3.7.x - 17,447 (as of 11/1/2026).
Number of coffee buyers - 169 (thanks again). If you appreciate my work and find iCloud3 useful, one cup would really be appreciated.***
<a href="https://www.buymeacoffee.com/gcobb321" target="_blank">
<img src="https://gcobb321.github.io/icloud3_v3_docs/images/buymeacoffee-docs-button-icon.png" width="150" height="35"></a>

***Thanks***,
***Gary Cobb, aka geekstergary***

-----
## 🍎 iCloud3 v3.8.0 Beta 3 (10/25/2026)

❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗
## 🎉 Semi-Breaking Change
**Marketplace HA v2026.11**:
Future iCloud3 beta versions will only be published as **pre-releases in the main iCloud3 repository** (`gcobb321/icloud3`). This beta/development repository (`gcobb321/icloud3_v3`) is being retired. This beta release is the last one that will be released there.

This prepares for Home Assistant 2026.11, where the built-in **Marketplace** integration replaces HACS.  HACS supported multiple repos that with the same HA Domain (`iCloud3`), that is the main and beta repo  (`gcobb321/icloud3 and icloud3_v3`) could both provide the code for iCloud3. With Marketplace, that changed. The `iCloud3` domain can only be tied to one GitHub Repo (`gcobb321/icloud3`).

After installing and restarting HA, a Repair issue **iCloud3: Beta Versions are moving to the iCloud3 Repo**. Open that Repair Issue, read the notes and click **Submit**. A complete description of this is found at the end of these Release Notes.
❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗

### 🐞 Bug Fixes
1. **Mobile App Watch Battery** - Fixed a rare problem where an old (Series 7) Watch's *_battery_level* sensor was being assigned incorrectly to another device when the Watch's sensor name started with the other device's name.
2. **Disabling or Deleting iCloud3** - The 5-second polling loop kept running after iCloud3 was disabled or deleted on the *Settings > Devices & Services* screen, and continued polling the Apple Accounts until HA was restarted. It is now stopped. (@Sinojen)
3. **Time Zone Offset** - The UTC offset sign was applied twice, so a negative offset (UTC-05:00) was stored as positive (+05:00). This did not affect any displayed times, but it has been corrected. (@Sinojen)
4. **Waze Empty Route** - If Waze returned an empty route (0 min/0 km) instead of an error, it was used as a valid route and the device appeared to be at the zone. It is now handled as a 'No Route' result and the calculated distance is used instead. (@Sinojen)
5. **Sensors with a '_2' Suffix** - When HA created a sensor with a '_2' suffix (sensor.gary_iphone_home_distance_2), the old sensor was not removed so the '_2' sensor could not be renamed back to its correct name. This has been fixed. An entity that belongs to another integration is not removed. (@Sinojen)
6. **Reload on the Integrations screen** - Selecting *Settings > Devices & Services > iCloud3 > Reload* the first time after HA was started failed with a 'Restart Home Assistant to finish' message and the iCloud3 entities were unavailable until HA was restarted. It now reloads iCloud3 the same way the iCloud3 Restart action does. (@Sinojen)
7. **Apple Device not linked to an iCloud3 Device** - Fixed a rare error ('NoneType' object has no attribute 'devicename') that could stop the location update for all of the devices in an Apple Account. (@Sinojen)
8. **Rejected Location for an Offline Device** - Fixed an error when a tracked device was offline and its old location was rejected several times. The update was stopped with an error instead of setting the next retry interval. (@Sinojen)
9. **Waze History Database not available** - If the Waze History Database could not be opened, an internal error was displayed on every update and the Waze Route Service was not used. The Waze Route Service is now used without the history database. (@Sinojen)
10. **Zone Names ending in '_x'** - A sensor for a zone whose name ended in an underscore and one character (zone.terminal_x, zone.office_2) was treated as a duplicate '_2' sensor and renamed every time iCloud3 was started (sensor.gary_iphone_zone_distance_terminal_x was changed to sensor.gary_iphone_zone_distance_terminal). If a zone with that name also existed (zone.terminal), its sensor was deleted. These sensors are no longer changed. They, and devices whose name ends in an underscore and one character (gary_iphone_2), are also no longer listed as errors on the *Configure > Tools > Cleanup Registry Errors* screen. (@matanmesika)
11. **All Devices 'Not in Apple Acct'** - If an Inactive device or a device disabled in HA was not in the Apple Account data, an error stopped the Apple Device setup. All of the devices in that Apple Account were then displayed as 'Not in Apple Acct' and were not tracked. Inactive and disabled devices are now skipped when checking for missing Apple devices. (@OldSmurf56)
12. **Monitored Devices and Stationary Zones** - When a Stationary Zone was created near a monitored device, or removed while a monitored device was in it, the monitored device was not updated until its next normal update. It is now updated within a few seconds. (@Sinojen)
13. **Mobile App Updates for Monitored Devices** - A Mobile App location update (launching the app, a manual update, entering or exiting a zone) was ignored for a monitored device. The device was only updated when its next update time was reached or it had moved more than 50m. A device located only by the Mobile App (no Apple Account) could go a long time without being updated. Monitored devices are now updated when the Mobile App sends a location update.


-----

## 🍎 iCloud3 v3.8.0 Beta 2 (10/25/2026)
### 🎉 New and Improved Items
1. **Apple Account login/password verification** - A major code reorganization for logging into and authenticating account access to prevent 503 Service Unavailable errors and lockout issues. This includes reduction in the number of password verification requests, delaying requests when errors were encountered to prevent Apple throttling, improved error handling and reporting.
2. **HA Repair Issues** - Configuration errors are identified during startup (Unknown Apple Accounts, Apple Devices and Mobile Apps, Terms of Service approvals, icloud3_alert sensor updates and Event Log messages, etc). An HA Repair Issue is now created with the ability to immediately correct the error without going into the iCloud3 Configure program.
3. **Dashboard Cards that can Authenticate Apple Accounts** - Using this new feature, you can enter the  Authentication Code from the Dashboard without going into the *iCloud3 Configure > Authenticate Apple Account Sign-in* screen. New HA Text/Button entities are created for each Apple Account that can be added to any Dashboard. They can request a new authentication code and then enter and send to Apple. Using the *Build User Authentication Dashboard Cards* screen (selected from the Authentication screen), the raw_yaml code for these entities can be generated. Then just copy and paste the code onto a Dashboard card. See the iCloud3 Docs [here](https://gcobb321.github.io/icloud3_v3_docs/#/chapters/3_apple-acct-auth?id=authenticating-an-apple-account-from-a-dashboard-card) for more information and screenshots.
4. iCloud3 startup now runs completely in its own thread. The iCloud3 Dashboard is updated much earlier in the startup process and there is no longer any impact on the HA Startup process.


### 🐞 Bug Fixes
1. **Rawdata Logging** - Data fields longer than 20-characters are shrunk to a 12-character to reduce the size of the log file and improve readability.  However, fields within a list were not being shrunk when they should have been. This has been corrected. (@dbl-0)
2. **Error Code/Reason** - Fixed a problem displaying the error description when the error code was not in the description message table. (@banister4728)
3. **Apple Account Startup Error** - If there was a problem starting up and the Configure screens were not initialized, a 'Apple Acct Login Error' will now be displayed correctly.
4. **Restart Action** - Fixed a bug in the iCloud3 Restart Action so it works again.
5. **Android Only & Mac Mobile App** - Fixed a problem where the *_last_update_trigger* and *battery_level* entity_id was not being detected.
6. **HA becoming unresponsive (Executor exhaustion)** - The 1-minute Apple request timeout timer could be orphaned when several requests were made at the same time. An orphaned timer ran a blocking Internet connection check every minute forever, and each check started another timer. Over time these used up all of the HA background worker threads and HA stopped responding until it was restarted. The timer now fires only once and is protected against simultaneous requests. (@timk75)

### 📢 Other Updates
1. **Apple Terms of Use** - Improved the handling of Apple's Terms-of-Use Approval Needed request:
    - A message is now listed at the top of the Event Log in the greenbar alert area
    - The iCloud3 Alert Sensor (*sensor.icloud3_alert*) is updated
    - The message appears once in the Event Log at restart instead of every 2-5 minutes
    - Improved notifications on the iCloud3 Configure Settings screens
    - A Repair Issue is created (@26jateen)
2. **Locked Apple Account** - Improved notification when an Apple Account is locked:
    - A locked check is now done at startup and when the data is refreshed.
    - A Repair issue is created,
    - A message is displayed in the Event Log Greenbar Alert area.
3. **Configuration Menus**:
    - Added a separator line between the Menu Items (screen you are selecting) and the Menu Actions (Menu #1/2, Exit) for clarity.
    - Moved the *Away Time Zone* to Menu #1 - Devices and Sensors
    - Added **Default inZone Intervals** and *iCloud3 Analytics** to Menu #2 - Parameters.
4. **Event Log**:
    - Reorganized Stage 4 - Apple Account Device to setup each Apple account individually instead of first logging into all of the accounts, combining all of the devices into one list and then setting them up. The results are easier to review and errors are clearer.
    - Devices are now sorted by name instead of listed in the order they were added to iCloud3.
    - Fixed the Event Log staying blank after an HA restart until another sidebar item was selected and the iCloud3 dashboard was reselected.
    - Various tweaks for clarity.
5. **Stale device location** - If the device's location is older than 5×old_location_threshold (15-min):
    - A 'Device has not been located since' message is added to the icloud3_alert sensor (@oskar)
    - 'OLD LOC' is displayed in the *Next Update* dashboard item.
6. **Internal Changes** - A lot of code reorganization, internal variable name consolidation and other conventions were made to simplify the code and improve its readability.
7. **Battery Information** - The handling of battery information has been improved. Several internal bugs have been corrected.
8. **iCloud3 Theme** - The Light and Dark Themes have been improved to to provide improved color contrast.

-----
### Beta versions now come from the iCloud3 repository

iCloud3 beta versions are now published as **pre-releases in the main iCloud3 repository** (`gcobb321/icloud3`). The separate beta repository (`gcobb321/icloud3_v3`) is being retired, and this is the last beta that will be released there.

This also prepares for Home Assistant 2026.11, where the built-in **Marketplace** integration replaces HACS.

#### If you installed the beta from the icloud3_v3 repository

After you update to this version and restart Home Assistant, a Repairs issue is shown:

**iCloud3: Switch to the iCloud3 Repository**

To switch:
1. Go to **Settings > Repairs** and select the issue.
2. Select **Submit**.

iCloud3 then switches your HACS or Marketplace installation from the beta repository to the iCloud3 repository. You don't need to reinstall anything or set iCloud3 up again. It also:
- Removes the *iCloud3 Beta* repository entry.
- Turns on the **Pre-release** switch for iCloud3, so you keep getting new beta versions.
- Leaves your iCloud3 configuration, devices and entities unchanged.

#### If the switch can't be done automatically

The Repairs dialog shows a message instead. Make the change manually:
1. **Settings > Devices & Services > iCloud3 > Delete**. Your iCloud3 configuration is saved and will be used again.
2. In HACS or Marketplace, uninstall **iCloud3 Beta**.
3. In HACS or Marketplace, open **iCloud3** and turn on its **Pre-release** switch (see *Installing beta versions*), then download the latest version.
4. Restart Home Assistant.
5. **Settings > Devices & Services > Add Integration > iCloud3**.

#### If you installed from the iCloud3 repository

You don't need to do anything. To try beta versions, see *Installing beta versions* in the iCloud3 documentation.
