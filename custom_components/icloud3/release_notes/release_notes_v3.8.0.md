***Total downloads for v3.7.x and the v3.8.0 betas - 20,057 (as of 11/18/2026).
Number of coffee buyers - 182 (Thanks Again!). If you appreciate my work and find iCloud3 useful, one cup would really be appreciated.***
<a href="https://www.buymeacoffee.com/gcobb321" target="_blank">
<img src="https://gcobb321.github.io/icloud3_docs/images/buymeacoffee-docs-button-icon.png" width="150" height="35"></a>

***Thanks***,
***Gary Cobb, aka geekstergary***

-----
## 🍎 iCloud3 v3.8.0
### 🎉 New Feature
1. ❗ **Marketplace HA v2026.11 - Semi-Breaking Change** ❗ - Future iCloud3 beta versions will only be published as **pre-releases in the main iCloud3 repository** (`gcobb321/icloud3`). This beta/development repository (`gcobb321/icloud3_v3`) is being retired. This beta release is the last one that will be released there.

    This prepares for Home Assistant 2026.11, where the built-in **Marketplace** integration replaces HACS.  HACS supported multiple repos that with the same HA Domain (`iCloud3`), that is the main and beta repo  (`gcobb321/icloud3 and icloud3_v3`) could both provide the code for iCloud3. With Marketplace, that changed. The `iCloud3` domain can only be tied to one GitHub Repo (`gcobb321/icloud3`).

    After installing and restarting HA, a Repair issue **iCloud3: Beta Versions are moving to the iCloud3 Repo**. Open that Repair Issue, read the notes and click **Submit**. A complete description of this is found at the end of these Release Notes.
2. **Dashboard Builder** - iCloud3 dashboarads can now be deleted from the Dashboard Builder screen.
3. **iCloud3 Analytics**: (Menu #2 - Parameters)
    - The iCloud3 Analytics collects version, location (country/region), usage and various counts from the 20,000+ iCloud3 users. Its purpose is to report summary information showing where users are located, what version is being used and various counts (Apple Account, tracked devices, comments, etc.). Summary reports can be selected on the *Reports* screen. Hopefully, you will Enable *Send iCloud3 Analytics Data* and participate in this project.
    - The Analytics is an opt-in and it defaults to disabled. Until you either enable or disable participating:
        - An HA Repair issue (**iCloud3: iCloud3 Analytics, Approval Requested**) is created. Open it, select *Enable* or *Disable*, then select **Submit**.
        - A message is displayed on the Configure Menu screens, and the *iCloud3 Analytics* item is listed at the top of the menu.
    - No personal data is sent. The data that is sent from your iCloud3 installation is displayed on the Repair issue and the *iCloud3 Analytics* screen. An example is:
        - {'uuid': 'HA Installation ID', 'version': '3.8.0', 'country': 'US', 'region': 'FL', 'apple_accts': 2, 'mobapp_devices': 3, 'devices': 8, 'tracked': 3, 'monitored': 3, 'inactive': 2, 'comment': 'To open my garage door when I arrive Home'}
    - The *Analytics Reports* screen lets you view Analytic data multiple ways (by country, by version, comments, usage, etc.). The reports are displayed on the screen and show the most current data.
    - The data is sent once a day around 01:00:00/1:00am.
    - The data is stored using the same global database (CloudFlare) that is used by the HA Analytics program.


### 🎉 New and Improved Items
1. **Apple Account login/password verification** - A major code reorganization for logging into and authenticating account access to prevent 503 Service Unavailable errors and lockout issues. This includes reduction in the number of password verification requests, delaying requests when errors were encountered to prevent Apple throttling, improved error handling and reporting.
2. **HA Repair Issues** - An HA Repair Issue was only created when a replaced Apple device was detected. Configuration errors identified during startup (Unknown Apple Accounts, Apple Devices and Mobile Apps, Terms of Service approvals, etc) now also create an HA Repair Issue, with the ability to immediately correct the error without going into the iCloud3 Configure program. The icloud3_alert sensor and Event Log messages are also updated.
3. **Dashboard Cards that can Authenticate Apple Accounts** - Using this new feature, you can enter the  Authentication Code from the Dashboard without going into the *iCloud3 Configure > Authenticate Apple Account Sign-in* screen. New HA Text/Button entities are created for each Apple Account that can be added to any Dashboard. They can request a new authentication code and then enter and send to Apple. Using the *Build User Authentication Dashboard Cards* screen (selected from the Authentication screen), the raw_yaml code for these entities can be generated. Then just copy and paste the code onto a Dashboard card. See the iCloud3 Docs [here](https://gcobb321.github.io/icloud3_v3_docs/#/chapters/3_apple-acct-auth?id=authenticating-an-apple-account-from-a-dashboard-card) for more information and screenshots.
4. **Setting up Mobile App Devices**:
    - Changed the way iCloud3 associated the Mobile App device sensors (_update_trigger, _battery_level, _battery_status) with the iCloud3 device so it uses the same method as HA
    - Improved the messages to better describe an error encountered during setp (not found, disabled in HA, etc) in the Event Log, iCloud3 alerts and Repair issues
    - Changed method of identfying when a device was charging and not charging. Charging info is now coming from the _battery_state sensor.
    - Impoved the formatting of the Mobile App Device/Sensor assignment in Startup Stage 5
5. **Excluded Sensors** - The excluded sensors are now displayed at the end of the configuration setup process.
6. **Show/Hide Apple RawData Traffic**
    - The *Show/Hide Tracking Monitors* has been changed to show *RawData Logging* information in the Event Log. Showing Apple iCloud and Mobile App traffic can help troubleshoot problems and understand the data sent to iCloud3. It shows:
    - The Apple Account login and data request status codes/messages
    - Apple location data times of all data sent to iCloud3
    - Mobile App zone enter/exit and other triggers and location data times
7. **Fewer Waze Route Requests (HTTP 429-Too Many Requests)** - Waze was limiting requests when several devices were traveling together. The number of Waze requests has been reduced by about half:
    - The distance moved since the last update now uses the straight line distance instead of a Waze route request.
    - When devices are traveling together, a device now uses the Waze route of another device that requested it in the last 60-secs if it is within 150m and going the same direction. The time and distance are adjusted for the difference.
    - A Mobile App *Signaled* or *Periodic* trigger (sent every 5-mins while driving) no longer does an update before the next update time if the device is moving away from the zone or has moved less than 1km.
8. **Apple Account Keep Alive** - Apple ends an Apple Account's session if it is not used for a while. The next request then needs a password sign-in, which Apple may refuse (400 Bad Request, 503 Service Unavailable). An Apple Account that has not been refreshed by one of its devices for 30-mins is now refreshed so its session stays valid. This is needed when all of the account's devices are Monitored, all of its tracked devices are paused, or its devices have a long inZone interval (2-hrs). An account whose devices are updated more often is not affected.
    - The battery level of the devices in that Apple Account is also updated every 30-mins.
    - An iCloud-only device (no Mobile App) that is tracked and in a zone with a long inZone interval is updated as soon as the new location shows it has left the zone. Only an accurate location is used so GPS wandering does not cause a false zone exit. Moving around inside the zone does not cause an update.
9. **Apple Account Login Retry** - If the Apple Account sign-in fails, it is now retried in 15-mins, 30-mins and then every hour instead of waiting for the next HA restart. A failed sign-in when iCloud3 starts is also retried, and iCloud3 is restarted when it is successful so the account's devices are set up. A 503 (Apple refused the sign-in) waits at least 30-mins. An invalid password is retried once, and a locked account is not retried. The Event Log shows the retry time and results.
    - *Configure > Apple Accounts > Update Apple Account* now has a *Stop Retrying Login* action while a retry is scheduled.
10. **Text Message Auth Code** - When the Authentication method is a Text Message, Apple also displays the Push Popup window code on your Apple devices. That code was always refused because it was being sent to Apple as a Text Message code. If a code is refused as an incorrect Text Message code, it is now sent to Apple again as the Push Popup window code. Either code can now be entered. Note that each incorrect code is counted by Apple, a mistyped code is now counted twice.
11. **Updating an Apple Account in Configure** - When you log into an Apple Account on the *Update Apple Account* screen, the account's devices are paused until iCloud3 restarts when you close Configure. iCloud3 no longer refreshes or signs into the account in the background while Configure is being used, so it does not interfere with the new login.
12. **Authentication Code Needed Reminder** - When Apple asks for an authentication code, the alert and the HA *Reconfigure* button were only displayed when the code was first needed. If the code was not entered, nothing else reminded you, sometimes for days. If the code has not been entered after 12-hrs, a reminder is now posted, then again every 24-hrs until it is entered:
    - An error in the HA log and an alert in the Event Log
    - The HA *Reconfigure* button is displayed again
    - A Mobile App notification (*Apple Acct Auth Needed*) is sent to the Apple Account owner's device. The 12-hr reminder goes to the first device, the later ones to all of the owner's devices. It is not sent to Family Sharing devices.
    - Tracking continues while waiting for the code. A password sign-in is not done more than once every 15-mins while the code is needed.
13. **Reinstalling iCloud3** - When iCloud3 is added again and a previous configuration is found, a new *Reinstall* screen is displayed instead of the new installation screen. It describes the previous configuration (Apple Accounts, Devices and settings) and you select what to do with it:
    - *Keep the previous configuration* (default) - The previous Apple Accounts, Devices and settings are used.
    - *Delete & Start Over* - The configuration file is first saved as *configuration_before_reset_<date-time>* in the *.storage/icloud3* directory, then all of the Apple Accounts and Devices are deleted. The Apple Account session files are no longer deleted, so an authentication code is not needed when the account is added again. To undo it, copy the saved file over */config/.storage/icloud3/configuration*, then restart HA.
14. **Error Descriptions** - A 400 error was described as an *Invalid authentication code* even when no authentication code was involved. It is now described as *Request rejected by Apple*, and the Apple error number is shown with it in the log (Code-400 (-900007)). The incorrect Text Message code message now says that either the Text Message code or the Push Popup window code can be entered.
15. **Apple Terms of Use** - Improved the handling of Apple's Terms-of-Use Approval Needed request:
    - A message is now listed at the top of the Event Log in the greenbar alert area
    - The iCloud3 Alert Sensor (*sensor.icloud3_alert*) is updated
    - The message appears once in the Event Log at restart instead of every 2-5 minutes
    - Improved notifications on the iCloud3 Configure Settings screens
    - A Repair Issue is created (@26jateen)
16. **Locked Apple Account** - Improved notification when an Apple Account is locked:
    - A locked check is now done at startup and when the data is refreshed.
    - A Repair issue is created,
    - A message is displayed in the Event Log Greenbar Alert area.
17. **Event Log**:
    - Reorganized Stage 4 - Apple Account Device to setup each Apple account individually instead of first logging into all of the accounts, combining all of the devices into one list and then setting them up. The results are easier to review and errors are clearer.
    - Devices are now sorted by name instead of listed in the order they were added to iCloud3.
    - Fixed the Event Log staying blank after an HA restart until another sidebar item was selected and the iCloud3 dashboard was reselected.
    - Various tweaks for clarity.
18. **Stale device location** - If the device's location is older than 5×old_location_threshold (15-min):
    - A 'Device has not been located since' message is added to the icloud3_alert sensor (@oskar)
    - 'OLD LOC' is displayed in the *Next Update* dashboard item.
19. **Internal Changes** - A lot of code reorganization, internal variable name consolidation and other conventions were made to simplify the code and improve its readability.
20. **Battery Information** - The handling of battery information has been improved. Several internal bugs have been corrected.
21. **iCloud3 Theme** - The Light and Dark Themes have been improved to to provide improved color contrast.


### 🐞 Bug Fixes
1. **Rawdata Logging** - Data fields longer than 20-characters are shrunk to a 12-character to reduce the size of the log file and improve readability.  However, fields within a list were not being shrunk when they should have been. This has been corrected. (@dbl-0)
2. **Error Code/Reason** - Fixed a problem displaying the error description when the error code was not in the description message table. (@banister4728)
3. **Apple Account Startup Error** - If there was a problem starting up and the Configure screens were not initialized, a 'Apple Acct Login Error' will now be displayed correctly.
4. **Restart Action** - Fixed a bug in the iCloud3 Restart Action so it works again.
5. **Android Only & Mac Mobile App** - Fixed a problem where the *_last_update_trigger* and *battery_level* entity_id was not being detected.
6. **HA becoming unresponsive (Executor exhaustion)** - The 1-minute Apple request timeout timer could be orphaned when several requests were made at the same time. An orphaned timer ran a blocking Internet connection check every minute forever, and each check started another timer. Over time these used up all of the HA background worker threads and HA stopped responding until it was restarted. The timer now fires only once and is protected against simultaneous requests. (@timk75)
7. **Mobile App Watch Battery** - Fixed a rare problem where an old (Series 7) Watch's *_battery_level* sensor was being assigned incorrectly to another device when the Watch's sensor name started with the other device's name.
8. **Disabling or Deleting iCloud3** - The 5-second polling loop kept running after iCloud3 was disabled or deleted on the *Settings > Devices & Services* screen, and continued polling the Apple Accounts until HA was restarted. It is now stopped. (@Sinojen)
9. **Time Zone Offset** - The UTC offset sign was applied twice, so a negative offset (UTC-05:00) was stored as positive (+05:00). This did not affect any displayed times, but it has been corrected. (@Sinojen)
10. **Waze Empty Route** - If Waze returned an empty route (0 min/0 km) instead of an error, it was used as a valid route and the device appeared to be at the zone. It is now handled as a 'No Route' result and the calculated distance is used instead. (@Sinojen)
11. **Sensors with a '_2' Suffix** - When HA created a sensor with a '_2' suffix (sensor.gary_iphone_home_distance_2), the old sensor was not removed so the '_2' sensor could not be renamed back to its correct name. This has been fixed. An entity that belongs to another integration is not removed. (@Sinojen)
12. **Reload on the Integrations screen** - Selecting *Settings > Devices & Services > iCloud3 > Reload* the first time after HA was started failed with a 'Restart Home Assistant to finish' message and the iCloud3 entities were unavailable until HA was restarted. It now reloads iCloud3 the same way the iCloud3 Restart action does. (@Sinojen)
13. **Apple Device not linked to an iCloud3 Device** - Fixed a rare error ('NoneType' object has no attribute 'devicename') that could stop the location update for all of the devices in an Apple Account. (@Sinojen)
14. **Rejected Location for an Offline Device** - Fixed an error when a tracked device was offline and its old location was rejected several times. The update was stopped with an error instead of setting the next retry interval. (@Sinojen)
15. **Waze History Database not available** - If the Waze History Database could not be opened, an internal error was displayed on every update and the Waze Route Service was not used. The Waze Route Service is now used without the history database. (@Sinojen)
16. **Zone Names ending in '_x'** - A sensor for a zone whose name ended in an underscore and one character (zone.terminal_x, zone.office_2) was treated as a duplicate '_2' sensor and renamed every time iCloud3 was started (sensor.gary_iphone_zone_distance_terminal_x was changed to sensor.gary_iphone_zone_distance_terminal). If a zone with that name also existed (zone.terminal), its sensor was deleted. These sensors are no longer changed. They, and devices whose name ends in an underscore and one character (gary_iphone_2), are also no longer listed as errors on the *Configure > Tools > Cleanup Registry Errors* screen. (@matanmesika)
17. **All Devices 'Not in Apple Acct'** - If an Inactive device or a device disabled in HA was not in the Apple Account data, an error stopped the Apple Device setup. All of the devices in that Apple Account were then displayed as 'Not in Apple Acct' and were not tracked. Inactive and disabled devices are now skipped when checking for missing Apple devices. (@OldSmurf56)
18. **Monitored Devices and Stationary Zones** - When a Stationary Zone was created near a monitored device, or removed while a monitored device was in it, the monitored device was not updated until its next normal update. It is now updated within a few seconds. (@Sinojen)
19. **Mobile App Updates for Monitored Devices** - A Mobile App location update (launching the app, a manual update, entering or exiting a zone) was ignored for a monitored device. The device was only updated when its next update time was reached or it had moved more than 50m. A device located only by the Mobile App (no Apple Account) could go a long time without being updated. Monitored devices are now updated when the Mobile App sends a location update.
20. **Exclude Sensors** - A sensor selected on the *Configure > Sensors > Exclude Sensors* screen was not removed when the Sensors screen was saved. The Sensors screen was displayed again with an error. The excluded sensor was also dropped from the list the next time iCloud3 was started and the sensor was created again. Excluded sensors are now removed when the Sensors screen is saved and stay excluded. (@CookieChief)
21. **Add Device Tracking Mode** - When a device was added on the *Configure > Devices* screen, a Monitor tracking mode was changed back to the default for the device type (Track). The selected tracking mode is now kept. A device that is not an Apple device and is located only by the Mobile App now defaults to an iPhone that is tracked. (@CookieChief)
22. **Tools > Reset General Parameters** - Selecting *YES* to reset the General Parameters did not save the reset parameters or restart iCloud3. They are now saved and iCloud3 is restarted. (@CookieChief)
23. **Inactive or Disabled Devices** - Deleting an Apple Account, deleting the last device, removing all devices or renaming a device failed with an error when a device was Inactive or disabled in HA. These devices are now removed correctly. A device that is disabled in HA can no longer be renamed. Enable it first, then rename it. (@CookieChief)
24. **HA Reauthenticate Dialog** - The Reauthenticate dialog that HA displays from *Settings > Devices & Services* failed with an error when the Terms of Use were displayed, and some of its text was missing. The Terms of Use are no longer displayed on that dialog (they are accepted on the Repair issue), and the missing text was added. Deleting the Apple Account that needed to be reauthenticated now also clears the reauthentication notice. (@CookieChief)
25. **Deleted iCloud3 Dashboard** - If an iCloud3 dashboard was deleted on the *Settings > Dashboards* screen after the Dashboard Builder had created one, adding or deleting a device failed with an error when Configure was closed. The other dashboards were not updated and iCloud3 was not restarted until HA was restarted. Deleted (using HA) dashboards are now skipped, and a new dashboard no longer reuses a deleted dashboard's name. (@CookieChief)
26. **Read-only iCloud3 Installation** - When iCloud3 was installed from a read-only location (NixOS package), the iCloud3 Theme and the Event Log Card files were copied as read-only files. They could not be updated after that, and a 'Permission denied' error was displayed on every HA restart. The file contents are now copied without the read-only permission, and files that were already copied as read-only are corrected on the next restart. (@nimakalantar)
27. **Apple Account Password Sign-in after a Failed Sign-in** - When the Apple Account session had expired and the password sign-in was needed, the sign-in session information saved from an earlier sign-in (or one Apple refused) was sent again. Apple then rejected the new sign-in (400 Bad Request) and the Apple Account was not logged in until HA was restarted. A new sign-in session is now started each time a password sign-in is needed, and the first part of the sign-in is retried once if Apple rejects it. An authentication code is not requested.
28. **Too Many Sign-in Requests (503)** - When a device refresh found the Apple Account session had expired and the password sign-in then failed, the refresh and the complete sign-in were done a second time a second later. Apple refused the extra sign-in (503 Service Unavailable). A failed sign-in is now not repeated, it is retried later (see Apple Account Login Retry).
29. **Apple Account Stayed 'Not Logged In'** - After a failed sign-in (for example, a Request Auth Code Apple refused), the Apple Account kept a 'not logged in' status even after a later sign-in was successful. On the next iCloud3 restart its Family Sharing devices were listed as *Not in Apple Acct* and were not tracked. The status is now reset when a sign-in or a device refresh is successful.
30. **Adding an Apple Account Again** - The session files of an Apple Account that was removed some other way than *Delete Apple Account* (for example, by changing the Apple Account username) were left behind. When the account was added again, the authentication code was not requested for 30-secs. These files are now deleted when iCloud3 starts.
31. **HA Reauthenticate Dialog** - The Reauthenticate dialog that HA displays from *Settings > Devices & Services* failed with an error after the authentication code was accepted when one of the configured devices used an Apple Account that was not logged in. The code was accepted and the Apple Account was authenticated.
32. **Apple Account with an Invalid Password** - When the Apple Account username/password failed verification when iCloud3 started, the account was not listed on the *Configure > Apple Accounts* screen. It could only be corrected from the HA Repair issue. The account is now listed with the reason (*Invalid Apple_ID/Password*, *Apple Refused Rqst* or *Login Failed*) and can be selected to correct it on the *Update Apple Account* screen. Also, when Apple rejected the verification request before the password was checked (400 Bad Request), it was reported as an *Invalid Username/Password*. It is now reported as *Apple Refused the Signin Request, Try again later*, and the request is retried once.


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
