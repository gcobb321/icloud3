## The iCloud3 Event Log Card

This chapter explains:

- About the iCloud3 Event Log 
- What can be done using the Actions Command pulldown menu

### About the Event Log

As iCloud3 runs, various entries are written to the HA log file that show device information, how it is tracked, operational errors, startup information and other items that may help determine what is going on if there is a problem and to monitor when the device's information is determined and updated. A lot of this information is also written to the `iCloud3 Event Log` which can be viewed using the `iCloud3 Event Log Lovelace Card`. 

##### Event Log during iCloud Initialization

![evlog](../images/evlog_initializing.jpg)

##### Event Log locating devices


![event_log](../images/evlog.jpg) 



Typically Lovelace custom cards are stored in their own directory that is within the `config/www/` directory. iCloud3 and the instructions below, use the `www/custom_cards` directory although you may be storing them in another location (e.g.,`www/community`). 

!>If you are not using the `www/custom_cards` directory, use your directory name (e.g., `www/community`) instead of `www/custom_cards` in the following instructions. Then specify your directory name using the *event_log_card_directory: www/yourcustomcarddirectoryname* configuration parameter.

### The Actions Command 

The Actions Command lets you interact with iCloud3 while it is running. 

###### Global Actions - Actions performed on all tracked devices

- Restart iCloud3 - Restart iCloud3 and reload the config_ic3.yaml file configuration file with any changes you have made.
- Pause Polling - Pause polling on all phones
- Resume Polling - Resume polling
- Request iOS App Locations - Request the location from the iOS App for all phones being tracked.
- Show/Hide Tracking Monitors - Show/Hide location tracking, state and trigger data from the iOS App. It also shows the results of the last update for the phone. (see below)
- Show Startup Log, Errors, Alerts - Only show these items from the Event Log, do not show any tracking entries. This easily lets you view errors and alerts that may have happened hours ago. (see below)
- Export Event Log - Export the Event Log data to the *config/icloud3-event-log.log* file. (see below)
- Start HA Debugging - Start/Stop additional debugging logs. (see below)

###### Device Actions - Actions performed on the selected device

- Pause Polling - Pause polling on the selected phone
- Resume Polling - Resume polling on the selected phone
- Request iOS App Location - Request the selected phone's location from the iOS App



#### Show/Hide Tracking Monitors

As iCloud3 runs, the state, trigger and location information is added to the Event Log when it changes.  The *iOS App Monitor* shows information from the iOS App device_tracker entities being monitored and the *Device Monitor* shows the results of the last location update.

![evlog_debug](../images/evlog_debug.jpg)



#### Show Startup Log, Errors, Alerts

iCloud3 may encounter an error while starting up, while tracking a device, while communicating with the iOS App, with the iCloud Location Service, etc. An error message is added to the Event Log for important errors and Alert messages are added to notify you of a problem iCloud3 has encountered and will retry. This Action only shows events related to starting up, to errors and to alerts. No phone tracking events are shown. 

![evlog](../images/evlog_errors_alerts.jpg)

Select the Person/phone to redisplay tracking events again.

#### Export Event Log

The Event Log can be exported to the */config/icloud3-event-log.log* file. It is a tab delimited text file that shows the start up events first, followed by each of the tracked devices. It can be opened by a text editor such as Notepad++ or imported into a spreadsheet file.

![evlog](../images/evlog-export.jpg)

