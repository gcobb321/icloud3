## [iCloud3 v3 iDevice Tracker](https://github.com/gcobb321/icloud3_v3)

iCloud3 is an advanced iDevice tracker that reports location and other information from your Apple iCloud account and the HA Companion App that can be used for presence detection and zone automation activities.

Some of the features of iCloud3:

- **Track devices from several sources** - Family members in your iCloud Account Family Sharing list and devices that have installed the HA Companion App (iOS App) are tracked.
- **Actively track a device** - The device will request it's location on a regular interval.
- **Passively monitor a device** - The device does not request it's location but is tracked when another tracked device requests theirs.
- **Waze Route Service** - The travel time and route distance to a tracked zone (Home) is provided by Waze.
- **Stationary Zone** - A dynamic *Stationary Zone* is created when the device has not moved for a while (doctors office, store, friend's house). This helps conserve battery life.
- **Sensors and more sensors** - Many sensors are created and updated with distance, travel time, polling data, battery status, zone attributes, etc. The sensors that are created is customizable.
- **Nearby Devices** - The location of all devices is monitored and the distance between devices is determined. Information from devices close to each other is shared.
- **Event Log** - The current status and event history of every tracked and monitored device is displayed on the iCloud3 Event Log custom Lovelace card. It shows information about devices that can be tracked, errors and alerts, nearby devices, tracking results, debug information and location request results.

### Installing iCloud3

iCloud3 is still in beta and has not been added to the HACS base integration list. It needs to be added to HACS as a custom repository and then downloaded.

1. Open HACS.

2. Select **Integrations**, then select the 3-dots (**︙**) in the upper-right corner, then select **Custom Repositories**.

3. Type **gcobb321/icloud3_v3** in the Repository field, then select **Integration** in the Category dropdown list, then select **Add**.

4. Select **Integrations** again, then select **+ Explore & Download Repositories**.

5. Select *iCloud3 v3 iDevice Tracker*, then select **Download**.

### Useful Links

* [Brief Overview](https://github.com/gcobb321/icloud3_v3/blob/master/README.md)
* [Extensive Documentation](https://gcobb321.github.io/icloud3_v3/#/)
* [GitHub Repository](https://github.com/gcobb321/icloud3_v3)

