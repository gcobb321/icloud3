<a href="https://www.buymeacoffee.com/gcobb321" target="_blank">
<img src="https://gcobb321.github.io/icloud3_v3_docs/images/buymeacoffee-docs-button-icon.png" width="150" height="50"></a>


-----
## 🍎 iCloud3 v3.7.5 (9/8/2026)
### 🐞 Bug Fixes
1. **Configure Screens** - Fixed a problem opening the Configure Setting screen when the Log Level mode was Info (default). It worked if the Log Level was Debug.
2. **Dashboard Builder** - Fixed a problem creating a new dashboard.
3. **Email Filter** - Devicenames that contained the first part of the email address (before the @) were filtered when they shouldn't be. For example, devicename=*ipad_mickeymouse*, Apple email_id=*mickeymouse@apple.net*, FilterText=*mic\*\*2\*\*se@*. DisplayedDevicename=*ipad_mic\*\*2\*\*se@*, CorrectValue=*ipad_mickeymouse*

### 📢 Other Updates
1. **Dashboard Builder** - Changed the icons assigned to a new dashboard.
2. **Display Text-as screen** - Changed the Action Options text for clarity.
3. **Tools > Cleanup HA Registries** - When active devices (Tracked, Monitored) were deleted from the registry, their Tracking Mode was set to Inactive to prevent a conflict with the HA registry and iCloud3 where the HA registry showed disabled and iCloud3 did not. This has been changed so an iCloud3 device will only be set to Inactive if the device was disabled on the HA devices > disable device screen.
4. **Startup** - The iCloud3 Configuration file was backed up when a new version was installed, leading to multiple version backups. Old backup files are now deleted and only the latest one is kept.