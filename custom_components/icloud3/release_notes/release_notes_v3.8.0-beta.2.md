***Total downloads for v3.7.x - 18,145 (as of 10/25/2026).
Number of coffee buyers - 168 (thanks again). If you appreciate my work and find iCloud3 useful, one cup would really be appreciated.***
<a href="https://www.buymeacoffee.com/gcobb321" target="_blank">
<img src="https://gcobb321.github.io/icloud3_v3_docs/images/buymeacoffee-docs-button-icon.png" width="150" height="35"></a>

***Thanks***,
***Gary Cobb, aka geekstergary***

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
    - Various tweaks for clarity.
5. **Stale device location** - If the device's location is older than 5×old_location_threshold (15-min):
    - A 'Device has not been located since' message is added to the icloud3_alert sensor (@oskar)
    - 'OLD LOC' is displayed in the *Next Update* dashboard item.
6. **Internal Changes** - A lot of code reorganization, internal variable name consolidation and other conventions were made to simplify the code and improve its readability.
7. **Battery Information** - The handling of battery information has been improved. Several internal bugs have been corrected.
8. **iCloud3 Theme** - The Light and Dark Themes have been improved to to provide improved color contrast.