# Installing and Starting iCloud3

This chapter explains how to:

- Install the iCloud3 custom component.
- Install the iCloud3 Event Log.

### Install iCloud3

iCloud3 is a custom component and is stored in the `config/custom_components/icloud3` directory. Another part of iCloud3, the Event Log, is a Lovelace card that is stored in the directory you use for your custom lovelace cards. Typically this is in the `/config/www/custom_cards` or`config/www/community`  directory. iCloud3 can be installed manually or through HACS. The Event Log card file (*icloud3-event-log-catd.js*) will be copied to the `www/custom card` directory the first time you launch iCloud3.

The following sections explain how to install iCloud3.

#### HACS (Home Assistant Community Store) Installation

iCloud3 is listed on the default HACS Repositories/Integrations page and can be to Home Assistant using HACS. Do the following:

1. Display the HACS control panel. Then type **icloud3** in the *Please enter a search term...* field.
2. The *iCloud3 Device Tracker* card is displayed, Select it.
3. Select **Install**. This will install all of the custom component files above into the *config/custom_components/icloud3* directory on the computer running Home Assistant.
4. iCloud3 copies the Event Log card (*icloud3-event-log-card.js*) to the `www/custom_cards` directory the first time you start iCloud3.  If you store your Lovelace custom cards in another location, you can change it's location using the *event_log_card_directory* parameter described in Chapter 2.1 Configuration Parameter. Also see Chapter 1.8 Installing the Event Log.
5. Set up the iCloud3 device_tracker configuration parameters. A minimum example configuration is shown below to get iCloud3 started for the first time. More instructions, with more detailed examples, are found in the Setting up iCloud3 chapter.
6. Restart Home Assistant.

#### Manual Installation

The iCloud3 programs, files and documentation can be found on the iCloud3 GitHub repository [here](https://github.com/gcobb321/icloud3). It uses the GitHub Releases framework to download all the necessary installation files (iCloud3 custom component, documentation, sample configuration files, sample Lovelace cards, etc). Go to the `GitHub > Releases` tab at the top of this repository and download the icloud3.zip file. 

1. Create a `config/custom_components/icloud3` directory on the computer running Home Assistant. Unzip the six component files in the icloud3.zip file (`device_tracker.py, pyicloud_ic3.py, init.py, manifest.json, services.yaml, config_ic3.yaml, icloud3-event-log-card.js`)  into that directory so the directory structure looks like:

```yaml
config
  custom_components
    icloud3
      device_tracker.py
      pyicloud_ic3.py
      __init__.py
      manifest.json
      services.yaml
      config_ic3.yaml
      icloud3-event-log-card.js
```

2. iCloud3 copies the Event Log card (*icloud3-event-log-card.js*) to the `www/custom_cards` directory the first time you start iCloud3.  If you store your Lovelace custom cards in another location, you can change it's location using the *event_log_card_directory* parameter described in Chapter 2.1 Configuration Parameter. Also see Chapter 1.8 Installing the Event Log.

3. Set up the iCloud3 device_tracker configuration parameters. A minimum example configuration is shown below to get iCloud3 started for the first time. More instructions, with more detailed examples, are found in the Setting up iCloud3 chapter.
4. Restart Home Assistant.

### iCloud3 Configuration Parameters - Minimal Installation

You have probably reviewed the information in the Setting up iCloud3 chapter. As a summary, the following examples show the iCloud3 parameters necessary to start iCloud3 with a minimal configuration. Copy the parameters for the tracking method you want to use to the HA configuration.yaml file. Naturally, use your iCloud account name and password and the names of your phones where appropriate. More extensive examples are found in the next chapter.

###### Family Sharing tracking method  

Gary and Lillian are in the Family Sharing list on the [gary-icloud-account@email.com]() iCloud account

```yaml
device_tracker:
  - platform: icloud3
    username: gary-icloud-acct@email.com
    password: gary-icloud-password
    tracking_method: famshr
    track_devices:
      - gary_iphone
      - lillian_iphone
```

###### Find-my-Friends tracking method   

Gary and Lillian are on the gary-icloud-account@email.com FindMy App people list that are sharing their location information

```yaml
device_tracker:
  - platform: icloud3
    username: gary-icloud-acct@email.com
    password: gary-icloud-password
    tracking_method: fmf
    track_devices:
      - gary_iphone > gary-icloud-acct@email.com
      - lillian_iphone > lillian-icloud-acct@email.com
```
###### iOS App tracking method  

The iOS App is installed on Gary and Lillian's phone

```yaml
device_tracker:
  - platform: icloud3
    username: icloud3_iosapp
    tracking_method: iosapp
    track_devices:
      - gary_iphone
      - lillian_iphone
```



