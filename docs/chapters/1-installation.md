# Installation

### How iCloud3 works

iCloud3 operates on a 5-second cycle, looking for transactions from the HA IOS App. It looks for Geographic Zone Enter/Exit, Background Fetch, Significant Location Update and Manual transactions. When one is detected, it determines if the transaction is current before it is processed. Transactions older than 2-minutes are discarded. Additionally, to minimize GPS wandering and out-of-zone state changes, transactions within 1km of a zone are discarded when the device is in a zone.  Every 15-seconds, it determines if any devices needed to be polled using the iCloud Location Services Find-my-Friends or family-sharing methods as described below.

iCloud3 polls the device on a dynamic schedule and determines the polling interval time based on:

- If the device is in a zone or not in a zone. The zones include the ones you have set up in `zone.yaml` and a special Dynamic Stationary Zone that is created by iCloud3 when you haven't changed your location in a while (shopping center, friends house, doctors office, etc.)
- A 'line-of-sight' calculated distance from the Home or other zone to your current location using the GPS coordinates.
- The driving time and distance between Home or another zone and your current location using the [Waze Route Calculator](http://www.waze.com) map/driving/direction service.
- The direction you are going — towards Home or other zone, away from the zone or stationary.
- The battery level of the device if the battery level is available.
- The accuracy of the GPS location and if the last poll returned a location that the iCloud service determined was 'old'.

The above analysis results in a polling interval. The further away from Home or other zone and the longer the travel time back to the zone, the longer the interval; the closer to the zone, the shorter the interval. The polling interval checks each device being tracked every 15-seconds to see if it's location should be updated. If so, it and all of the other devices being tracked with iCloud3 are updated (more about this below). With a 15-second interval, you track the distance down 1/10 of a mile/kilometer. This gives a much more accurate distance number that can used to trigger automations. You no longer limited to entering or exiting a zone.

Another custom component module (`pyicloud_ic3.py`) is responsible for communicating with the iCloud Location Services to authenticate the iCloud account and to locate the devices associated with the account using either Find-my-Friends or family-sharing methods (see the Using iCloud3 chapter for more information about these tracking methods). If the iCloud account is associated with several devices, the location information for the all of the devices in the account is returned on the same poll, whether or not the device is being tracked by Home Assistant.

### Installing iCloud3

iCloud3 uses the GitHub Releases framework to download all the necessary installation files (iCloud3 custom component, documentation, sample configuration files, sample Lovelace cards, etc). Go to the 'Releases' tab at the top of this repository, select the version of iCloud3 you want and download the .zip file.

1. Create a `config/custom_components/icloud` directory on the device (Raspberry Pi) running Home Assistant. Copy the five component files in the `custom_components-icloud3` GitHub directory (`device_tracker.py, pyicloud_ic3.py, init.py, manifest.json, services.yaml`) into that directory so the directory structure looks like:

```yaml
config/
  custom_components/
    icloud3/
      device_tracker.py
      pyicloud_ic3.py
      __init__.py
      manifest.json
      services.yaml
```

2. Install the `iCloud3 Event Log` card using the [procedures below](#installing-the-icloud3-event-log-custom-card).

3. Set up the iCloud3 device_tracker configuration parameters. Instructions, including examples, are found in the Setting up iCloud3 chapter.

4. Restart Home Assistant.

### Installing iCloud3 with HACS (Home Assistant Community Store)

iCloud3 is listed on the default HACS Repositories/Integrations page and can be to Home Assistant using HACS. Do the following:

1. Display the HACS control panel. Then type `icloud3` in the 'Please enter a search term...' field.
2. The `iCloud3 Device Tracker` card is displayed, Select it.
3. Click `Install`. This will install all of the custom component files above into the 'config/custom_components/icloud3' directory on your Raspberry Pi or the device you are running Home Assistant on.
4. Log onto your Pi.
5. Install the `iCloud3 Event Log` card using the [procedures below](#installing-the-icloud3-event-log-custom-card). The `icloud3-event-log-card.js` file is installed in the `config/custom_components/icloud3` directory with the other files.
6. Set up the iCloud3 device_tracker configuration parameters. Instructions, including examples, are found in the Setting up iCloud3 chapter.
7. Restart Home Assistant.

!> The Waze Route Calculator component is use to calculate driving distance and time from your location to your Home or another zone). Normally, it is installed with the Home Assistant and Hass.io framework. However, if it is not installed on your system, you can go [here](https://github.com/kovacsbalu/WazeRouteCalculator) for instructions to download and install Waze. If you don't want to use Waze or are in an area where Waze is not available, you can use the 'direct distance' method of calculating your distance and time from the Home or another zone. Add the `distance_method: calc` parameter to your device_tracker: icloud3 configuration setup (see the Parameters, Attributes and Sensors section for more information).

!> iCloud3 logs information to the HA log file and to an internal table that can be viewed using the iCloud3 Event Log Lovelace Custom Card. Information about this custom card, and installation instructions are in the Support Programs chapter.

### About the iCloud3 Event Log Custom Card
As iCloud3 runs, various entries are written to the HA log file that show device information, how it is tracked, operational errors, startup information and other items that may help determine what is going on if there is a problem and to monitor when the device's information is determined and updated. A lot of this information is also written to the `iCloud3 Event Log` which can be viewed using the `iCloud3 Event Log Lovelace Card`.

Below are 3 screens. The one on the left shows iCloud3 starting up, the middle one shows arriving Home and the one on the right shows entering the 'Whse' zone.

![event_log](../images/event_log_initializing.jpg)

---
### Installing the iCloud3 Event Log Custom Card
Custom Lovelace cards are typically stored in the `config/www/custom_cards` directory. Do the following:

1. Create the `config/www/custom_cards` directory if it does not exist.

2. Copy `icloud3-event-log-card.js` into the `config/www/custom-cards` directory. If you are installing iCloud3 using HACS, the source file is in the `config/custom_components/icloud3` directory. If you are already using custom cards and they are in a different directory, copy `icloud3-event-log-card.js` into the one you are using.

3. Open the file `configuration.yaml`, and add similar lines below to the lovelace section to add the new resource.

   ```
   lovelace:
     mode: yaml
     resources:
       - url: /local/custom_cards/icloud3-event-log-card.js?v=1.000
         type: module
   ```

4. Open the `ui-lovelace.yaml` file and add the following lines to the `ui-lovelace.yaml` file to create the custom card.

   ```
    - title: iCloud Event Log
       icon: mdi:information-outline
       cards:
         - type: "custom:icloud3-event-log-card"
           entity: sensor.icloud3_event_log
   ```

If you are not using YAML mode for the user interface, please refernce the Home Assistant Lovelace documentation regarding setting up and using custom cards [here](https://community.home-assistant.io/t/how-do-i-add-custom-cards-with-the-lovelace-ui/97902).

------

### What to do next

The next thing to do is set up your iCloud account so you can get location information for the devices you want to track. This is described in the next chapter, Setting Up iCloud Account.
