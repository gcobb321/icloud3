

from ..global_variables import GlobalVariables as Gb
from ..const            import (
                                EVLOG_CARD_WWW_DIRECTORY, EVLOG_CARD_WWW_JS_PROG,
                                IPHONE, IPAD, WATCH,  AIRPODS, NO_IOSAPP, NO_MOBAPP,
                                DEVICE_TYPES,
                                NAME,
                                NAME, BADGE,
                                TRIGGER, INACTIVE_DEVICE,
                                ZONE, ZONE_DATETIME, LAST_ZONE,
                                INTERVAL,
                                BATTERY, BATTERY_STATUS,
                                ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, MOVED_DISTANCE,
                                LAST_UPDATE,
                                NEXT_UPDATE,
                                LAST_LOCATED,
                                INFO, GPS_ACCURACY, POLL_COUNT, VERTICAL_ACCURACY, ALTITUDE,
                                ZONE_NAME, ZONE_FNAME, LAST_ZONE_NAME, LAST_ZONE_FNAME,
                                CONFIG_IC3, CONF_VERSION_INSTALL_DATE,
                                CONF_CONFIG_IC3_FILE_NAME,
                                CONF_VERSION, CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_CARD_PROGRAM,
                                CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES, CONF_APPLE_ACCOUNT,
                                CONF_TRACK_FROM_ZONES, CONF_TRACKING_MODE,
                                CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVALS,
                                CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT, CONF_MAX_INTERVAL, CONF_OFFLINE_INTERVAL,
                                CONF_GPS_ACCURACY_THRESHOLD, CONF_OLD_LOCATION_THRESHOLD,
                                CONF_TRAVEL_TIME_FACTOR,
                                CONF_LOG_LEVEL,
                                CONF_DISPLAY_ZONE_FORMAT, CONF_CENTER_IN_ZONE, CONF_DISCARD_POOR_GPS_INZONE,
                                CONF_WAZE_USED, CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                                CONF_WAZE_REALTIME,
                                CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                CONF_STAT_ZONE_BASE_LATITUDE,
                                CONF_STAT_ZONE_BASE_LONGITUDE, CONF_DISPLAY_TEXT_AS,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME,
                                CONF_MOBILE_APP_DEVICE, CONF_PICTURE,
                                CONF_TRACK_FROM_ZONES, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                                CONF_NAME,
                                NAME, BADGE, BATTERY, BATTERY_STATUS, INFO,
                                DEFAULT_DEVICE_CONF, DEFAULT_GENERAL_CONF,
                                WAZE_SERVERS_BY_COUNTRY_CODE,
                                )

CONF_DEVICENAME       = 'device_name'
CONF_NO_IOSAPP        = 'no_iosapp'
CONF_NOIOSAPP         = 'noiosapp'
CONF_IOSAPP_INSTALLED = 'iosapp_installed'
CONF_IOSAPP_SUFFIX    = 'iosapp_suffix'
CONF_IOSAPP_ENTITY    = 'iosapp_entity'
CONF_EMAIL            = 'email'
CONF_CONFIG           = 'config'
CONF_SOURCE           = 'source'
CONF_TRACKING_METHOD  = 'tracking_method'

VALID_CONF_DEVICES_ITEMS = [CONF_DEVICENAME, CONF_EMAIL, CONF_PICTURE, CONF_NAME,
                            CONF_INZONE_INTERVAL, 'track_from_zone', CONF_IOSAPP_SUFFIX,
                            CONF_IOSAPP_ENTITY, CONF_IOSAPP_INSTALLED,
                            CONF_NO_IOSAPP, CONF_NOIOSAPP, CONF_TRACKING_METHOD, ]

TIME_PARAMETER_ITEMS = [    CONF_MAX_INTERVAL, CONF_OLD_LOCATION_THRESHOLD,
                            CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                            CONF_INZONE_INTERVAL, ]

V2_EVLOG_CARD_WWW_DIRECTORY = 'www/custom_cards'
SENSOR_ID_NAME_LIST = {
        'zon': ZONE,
        'lzon': LAST_ZONE,
        'zonn': ZONE_NAME,
        'zont': ZONE_NAME,
        'zonfn': ZONE_FNAME,
        'lzonn': LAST_ZONE_NAME,
        'lzont': LAST_ZONE_NAME,
        'lzonfn': LAST_ZONE_FNAME,
        'zonts': ZONE_DATETIME,
        'zdis': ZONE_DISTANCE,
        'cdis': CALC_DISTANCE,
        'wdis': WAZE_DISTANCE,
        'tdis': MOVED_DISTANCE,
        'ttim': TRAVEL_TIME,
        'mtim': TRAVEL_TIME_MIN,
        'dir': DIR_OF_TRAVEL,
        'intvl':  INTERVAL,
        'lloc': LAST_LOCATED,
        'lupdt': LAST_UPDATE,
        'nupdt': NEXT_UPDATE,
        'cnt': POLL_COUNT,
        'info': INFO,
        'trig': TRIGGER,
        'bat': BATTERY,
        'batstat': BATTERY_STATUS,
        'alt': ALTITUDE,
        'gpsacc': GPS_ACCURACY,
        'vacc': VERTICAL_ACCURACY,
        'badge': BADGE,
        'name': NAME,
        }

CONF_SENSORS_DEVICE_LIST            = ['name', 'badge', 'battery', 'battery_status', 'info',]
CONF_SENSORS_TRACKING_UPDATE_LIST   = ['interval', 'last_update', 'next_update', 'last_located']
CONF_SENSORS_TRACKING_TIME_LIST     = ['travel_time', 'travel_time_min']
CONF_SENSORS_TRACKING_DISTANCE_LIST = ['zone_distance', 'home_distance', 'dir_of_travel', 'moved_distance']
CONF_SENSORS_TRACKING_BY_ZONES_LIST = []
CONF_SENSORS_TRACKING_OTHER_LIST    = ['trigger', 'waze_distance', 'calc_distance', 'pll_count']
CONF_SENSORS_ZONE_LIST              = ['zone', 'zone_fname', 'zone_name', 'zone_timestamp', 'last_zone']
CONF_SENSORS_OTHER_LIST             = ['gps_accuracy', 'vertical_accuracy', 'altitude']

from ..helpers.common       import (instr, )
from ..helpers.file_io      import (file_exists, )
from ..helpers.messaging    import (_log, log_info_msg, log_warning_msg, log_exception,)
from ..helpers.time_util    import (time_str_to_secs, datetime_now, datetime_for_filename, )
from .                      import config_file

import json
import yaml
from   homeassistant.util    import slugify
import homeassistant.util.yaml.loader as yaml_loader
import logging
_LOGGER = logging.getLogger(__name__)

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3_v2v3ConfigMigration(object):


    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    #   EXTRACT ICLOUD3 PARAMETERS FROM THE CONFIG_IC3.YAML PARAMETER FILE.
    #
    #   The ic3 parameters are specified in the HA configuration.yaml file and
    #   processed when HA starts. The 'config_ic3.yaml' file lets you specify
    #   parameters at HA startup time or when iCloud3 is restarted using the
    #   Restart-iC3 command on the Event Log screen. When iC3 is restarted,
    #   the parameters will override those specified at HA startup time.
    #
    #   1. You can, for example, add new tracked devices without restarting HA.
    #   2. You can specify the username, password and tracking method in this
    #      file but these items are onlyu processed when iC3 initially loads.
    #      A restart will discard these items
    #
    #   Default file is config/custom_components/icloud3/config-ic3.yaml
    #   if no '/' on the config_ic3_filename parameter:
    #       check the default directory
    #       if not found, check the /config directory
    #
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def initialize_configuration(self):
        self.conf_parm_devices = []
        self.devicename_list = []

        self.conf_parm_general  = Gb.conf_general.copy()
        self.conf_parm_tracking = Gb.conf_tracking.copy()
        self.conf_parm_sensors  = Gb.conf_sensors.copy()

        try:
            self.log_filename_name  = Gb.hass.config.path(f"icloud3-migration_{datetime_for_filename()}.log")
            self.migration_log_file = open(self.log_filename_name, 'w', encoding='utf8')
        except Exception as err:
            log_exception(err)

 #-------------------------------------------------------------------------
    def convert_v2_config_files_to_v3(self):
        DEBUG_LOG_LINE_TABS = "\t\t\t\t\t\t\t\t\t\t"

        self.initialize_configuration()
        self.write_migration_log_msg(f"\nMigration Started, {datetime_now()}\n")
        log_warning_msg('iCloud3 - Migrating Configuration Parameters')
        self._extract_config_parameters(Gb.ha_config_yaml_icloud3_platform)

        config_ic3_records = self._get_config_ic3_records()
        self._extract_config_parameters(config_ic3_records)
        self._set_data_fields_from_config_parameter_dictionary()

        Gb.conf_profile[CONF_VERSION_INSTALL_DATE] = datetime_now()

        try:
            self.write_migration_log_msg("\nMigration Complete, Writing Configuration File")
            self.write_migration_config_items('Profile', Gb.conf_profile)
            self.write_migration_config_items('Tracking', Gb.conf_tracking)
            self.write_migration_config_items('General', Gb.conf_general)
            self.write_migration_config_items('Sensors', Gb.conf_sensors)
            self.remove_ic3_devices_from_known_devices_yaml_file()

        except Exception as err:
            self.log_exception(err)

        log_warning_msg('iCloud3 - Migration Complete')

        config_file.write_storage_icloud3_configuration_file()
        self.migration_log_file.close()

        log_info_msg(f"Profile:\n{DEBUG_LOG_LINE_TABS}{Gb.conf_profile}")
        log_info_msg(f"General Configuration:\n{DEBUG_LOG_LINE_TABS}{Gb.conf_general}")
        log_info_msg(f"{DEBUG_LOG_LINE_TABS}{Gb.ha_location_info}")
        log_info_msg("")

        for Gb.conf_device in Gb.conf_devices:
            log_info_msg(   f"{Gb.conf_device[CONF_FNAME]}, {Gb.conf_device[CONF_IC3_DEVICENAME]}:\n"
                                        f"{DEBUG_LOG_LINE_TABS}{Gb.conf_device}")
        log_info_msg("")
        log_info_msg("iCloud3 - Migration Complete")

    #-------------------------------------------------------------------------
    def _extract_config_parameters(self, config_yaml_recds):
        '''
        OrderedDict([('devices', [OrderedDict([('device_name', 'Gary-iPhone'),
        ('name', 'Gary'), ('email', 'gcobb321@gmail.com'),
        ('picture', 'gary.png'), ('track_from_zone', 'warehouse')]), OrderedDict([('device_name', 'lillian_iphone'),
        ('name', 'Lillian'), ('picture', 'lillian.png'), ('email', 'lilliancobb321@gmail.com')])]),
        ('display_text_as', ['gcobb321@gmail.com > gary_2fa@email.com', 'lilliancobb321@gmail.com > lillian_2fa@email.com',
        'twitter:@lillianhc > twitter:@lillian_twitter_handle', 'gary-real-email@gmail.com > gary_secret@email.com',
        'lillian-real-email@gmail.com > lillian_secret@email.com']),
        ('inzone_interval', '30 min'),
        ('display_zone_format', FNAME)])
        '''

        if config_yaml_recds == {}:
            return

        if CONF_DISPLAY_TEXT_AS in config_yaml_recds:
            display_text_as = DEFAULT_GENERAL_CONF[CONF_DISPLAY_TEXT_AS].copy()
            cdta_idx = 0
            for dta_text in config_yaml_recds[CONF_DISPLAY_TEXT_AS]:
                if dta_text.strip():
                    display_text_as[cdta_idx] = dta_text
                    cdta_idx += 1

            config_yaml_recds[CONF_DISPLAY_TEXT_AS] = display_text_as

        self.write_migration_log_msg(f"\nExtracting parameters")

        for pname, pvalue in config_yaml_recds.items():
            if pname == CONF_PASSWORD:
                self.write_migration_log_msg(f"-- {pname}: ********")
            else:
                self.write_migration_log_msg(f"-- {pname}: {pvalue}")

            if pname == CONF_DEVICES:
                pvalue = json.loads(json.dumps(pvalue))
                self.conf_parm_devices.extend(\
                        self._get_devices_list_from_config_devices_parm(pvalue, CONFIG_IC3))

            else:
                self._set_non_device_parm_in_config_parameter_dictionary(pname, pvalue)

        return

    #-------------------------------------------------------------------------
    def _get_config_ic3_records(self):
        try:
            config_yaml_recds = {}

            # Get config_ic3.yaml file name from parameters, then reformat since adding to the '/config/ variable
            config_ic3_filename = Gb.ha_config_yaml_icloud3_platform.get(CONF_CONFIG_IC3_FILE_NAME, CONFIG_IC3)
            config_ic3_filename = config_ic3_filename.replace("config/", "")
            if config_ic3_filename.startswith('/'):
                config_ic3_filename = config_ic3_filename[1:]
            if config_ic3_filename.endswith('.yaml') is False:
                config_ic3_filename = f"{config_ic3_filename}.yaml"

            if instr(config_ic3_filename, "/"):
                pass

            elif file_exists(f"{Gb.ha_config_directory}{config_ic3_filename}"):
                config_ic3_filename = (f"{Gb.ha_config_directory}{config_ic3_filename}")

            elif file_exists(f"{Gb.icloud3_directory}/{config_ic3_filename}"):
                config_ic3_filename = (f"{Gb.icloud3_directory}/{config_ic3_filename}")

            config_ic3_filename = config_ic3_filename.replace("//", "/")

            self.write_migration_log_msg(f"Converting parameters, Source: {config_ic3_filename}")
            if file_exists(config_ic3_filename) is False:
                self.write_migration_log_msg(f" -- Skipped, {config_ic3_filename} not used")
                return {}

            Gb.config_ic3_yaml_filename = config_ic3_filename
            config_yaml_recds = yaml_loader.load_yaml(config_ic3_filename)

        except Exception as err:
            self.log_exception(err)

        return config_yaml_recds

    #-------------------------------------------------------------------------
    def _get_devices_list_from_config_devices_parm(self, conf_devices_parameter, source_file):
        '''
        Process the CONF_DEVICES parameter. This is the general routine for parsing
        the parameter and creating a dictionary (devices_list) containing values
        associated with each device_name.

        Input:      The CONF_DEVICES parameter
        Returns:    The dictionary with the fields associated with all of the devices
        '''
        devices_list = []
        for device in conf_devices_parameter:
            devicename = slugify(device[CONF_DEVICENAME])
            if devicename in self.devicename_list:
                continue
            self.devicename_list.append(devicename)
            conf_device = DEFAULT_DEVICE_CONF.copy()
            conf_device[CONF_MOBILE_APP_DEVICE] = f"Search: {devicename}"
            conf_device[CONF_TRACKING_MODE]= INACTIVE_DEVICE

            self.write_migration_log_msg(f"Extracted device: {devicename}")
            for pname, pvalue in device.items():
                self.write_migration_log_msg(f"    -- {pname}: {pvalue}")
                if pname in VALID_CONF_DEVICES_ITEMS:
                    if pname == CONF_DEVICENAME:
                        devicename = slugify(pvalue)

                        fname, device_type = self._extract_name_device_type(pvalue)
                        conf_device[CONF_IC3_DEVICENAME]    = devicename
                        conf_device[CONF_FNAME]             = fname
                        conf_device[CONF_APPLE_ACCOUNT]     = self.conf_parm_tracking[CONF_USERNAME]
                        conf_device[CONF_FAMSHR_DEVICENAME] = devicename
                        conf_device[CONF_DEVICE_TYPE]       = device_type

                    #You can track from multiple zones, cycle through zones and check each one
                    #The value can be zone name or zone friendly name. Change to zone name.
                    elif pname == 'track_from_zone':
                            if instr(pvalue, 'home') is False:
                                pvalue += ',home'
                            pvalue = pvalue.replace(', ', ',').lower()
                            tfz_list = pvalue.split(',')
                            conf_device[CONF_TRACK_FROM_ZONES] = tfz_list

                    # elif pname == CONF_EMAIL:
                    #     conf_device[CONF_FMF_EMAIL] = pvalue

                    elif pname == CONF_NAME:
                        conf_device[CONF_FNAME] = pvalue

                    elif pname == CONF_IOSAPP_SUFFIX:
                        if pvalue.startswith('_') is False:
                            pvalue = f"_{pvalue}"
                        conf_device[CONF_MOBILE_APP_DEVICE] = f"{devicename}{pvalue}"

                    elif pname == CONF_IOSAPP_ENTITY:
                            conf_device[CONF_MOBILE_APP_DEVICE] = pvalue

                    elif pname == CONF_NO_IOSAPP and pvalue:
                        conf_device[CONF_MOBILE_APP_DEVICE] = 'None'

                    elif pname == CONF_IOSAPP_INSTALLED and pvalue is False:
                        conf_device[CONF_MOBILE_APP_DEVICE] = 'None'

                    elif pname == CONF_TRACKING_METHOD:
                        # if pvalue == 'fmf':
                        #     conf_device[CONF_FAMSHR_DEVICENAME] = 'None'
                        if pvalue == 'iosapp':
                            conf_device[CONF_FAMSHR_DEVICENAME] = 'None'
                            # conf_device[CONF_FMF_EMAIL] = 'None'


                    elif pname == CONF_PICTURE:
                        if instr(pvalue, 'www') is False:
                            pvalue = f"www/{pvalue}"

                        conf_device[CONF_PICTURE] = pvalue

                    elif pname == CONF_INZONE_INTERVAL:
                        conf_device[CONF_INZONE_INTERVAL] = time_str_to_secs(pvalue) / 60
                    else:
                        conf_device[pname] = pvalue

            if "cancel_update" in conf_device:
                conf_device.pop("cancel_update")
            devices_list.append(conf_device)

        return devices_list

    #-------------------------------------------------------------------------
    def _set_non_device_parm_in_config_parameter_dictionary(self, pname, pvalue):
        '''
        Set the config_parameters[key] master parameter dictionary from the
        config_ic3 parameter file

        Input:      parameter name & value
        Output:     Valid parameters are added to the config_parameter[pname] dictionary
        '''
        try:
            if pname == "":
                return

            if pname == 'stationary_still_time':      pname = CONF_STAT_ZONE_STILL_TIME
            if pname == 'stationary_inzone_interval': pname = CONF_STAT_ZONE_INZONE_INTERVAL

            if pname in self.conf_parm_general:
                self.conf_parm_general[pname] = pvalue

            elif pname in self.conf_parm_tracking:
                self.conf_parm_tracking[pname] = pvalue

            elif pname in ['exclude_sensors', 'create_sensors']:
                self._set_sensors(pname, pvalue)

            elif pname == CONF_INZONE_INTERVALS:
                iztype_iztime = {}
                for iztype_iztimes in pvalue:
                    for iztype, iztime in iztype_iztimes.items():
                        iztype_iztime[iztype] = iztime

                inzone_intervals = {}
                inzone_intervals['default'] = iztype_iztime.get('inzone_interval', 240)
                inzone_intervals[IPHONE]    = iztype_iztime.get(IPHONE, 240)
                inzone_intervals[IPAD]      = iztype_iztime.get(IPAD, 240)
                inzone_intervals[WATCH]     = iztype_iztime.get(WATCH, 15)
                inzone_intervals[AIRPODS]   = iztype_iztime.get(AIRPODS, 15)
                inzone_intervals[NO_MOBAPP] = iztype_iztime.get(NO_IOSAPP, 15)
                self.conf_parm_general[CONF_INZONE_INTERVALS] = inzone_intervals.copy()

            elif pname == 'stationary_zone_offset':
                sz_offset = pvalue.split(',')
                self.conf_parm_general[CONF_STAT_ZONE_BASE_LATITUDE]  = float(sz_offset[0])
                self.conf_parm_general[CONF_STAT_ZONE_BASE_LONGITUDE] = float(sz_offset[1])


        except Exception as err:
            self.log_exception(err)
            pass

        return

    #--------------------------------------------------------------------
    def _set_sensors(self, pname, pvalue):
        device_list            = []
        tracking_update        = []
        tracking_time_list     = []
        tracking_distance_list = []
        tracking_other_list    = []
        zone_list              = []
        other_list             = []

        sensor_list = []
        pvalue = f",{pvalue.replace(' ', '')},"
        if pname == 'exclude_sensors':
            for sensor_abbrev, sensor in SENSOR_ID_NAME_LIST.items():
                if instr(pvalue, f",{sensor_abbrev},") is False:
                    sensor_list.append(sensor)

        elif pname == 'create_sensors':
            for sensor_abbrev, sensor in SENSOR_ID_NAME_LIST.items():
                if instr(pvalue, f",{sensor_abbrev},"):
                    sensor_list.append(sensor)

        for sname in sensor_list:
            if sname in ['name', 'badge', 'battery', 'info',]:
                device_list.append(sname)
            if sname in ['interval', 'last_update', 'next_update', 'last_located']:
                tracking_update.append(sname)
            if sname in ['travel_time', 'travel_time_min']:
                tracking_time_list.append(sname)
            if sname in ['zone_distance', 'home_distance', 'dir_of_travel', 'moved_distance']:
                tracking_distance_list.append(sname)
            if sname in ['trigger', 'waze_distance', 'calc_distance', 'pll_count']:
                tracking_other_list.append(sname)
            if sname in ['zone', 'zone_fname', 'zone_name', 'zone_title', 'zone_timestamp']:
                if sname not in zone_list:
                    zone_list.append(sname)
            if sname in ['last_zone', 'last_zone_fname', 'last_zone_name', 'last_zone_title']:
                if 'last_zone' not in zone_list:
                    zone_list.append('last_zone')
            if sname in ['gps_accuracy', 'vertical_accuracy',   'altitude']:
                other_list.append(sname)

        Gb.conf_sensors['device']            = device_list
        Gb.conf_sensors['tracking_update']   = tracking_update
        Gb.conf_sensors['tracking_time']     = tracking_time_list
        Gb.conf_sensors['tracking_distance'] = tracking_distance_list
        Gb.conf_sensors['tracking_other']    = tracking_other_list
        Gb.conf_sensors['zone']              = zone_list
        Gb.conf_sensors['other']             = other_list

        return

    #--------------------------------------------------------------------
    def write_migration_log_msg(self, msg):
        '''
        Write a status message to the icloud3_migration.log file
        '''
        self.migration_log_file.write(f"{msg}\n")

    #--------------------------------------------------------------------
    def write_migration_config_items(self, dict_title, dict_items):
        '''
        Cycle through the dictionary. Write each item to the migration log
        '''
        self.write_migration_log_msg(f"{dict_title}")

        for pname, pvalue in dict_items.items():
            if type(pvalue) is list:
                self.write_migration_config_list_items(pname, pvalue)
                continue

            if pvalue == '':
                continue

            if pname == CONF_PASSWORD:
                self.write_migration_log_msg(f"  -- {pname}: ********")
            else:
                self.write_migration_log_msg(f"  -- {pname}: {pvalue}")

    #--------------------------------------------------------------------
    def write_migration_config_list_items(self, pname, pvalues):
        '''
        Cycle through the dictionary. Write each item to the migration log
        '''
        if pvalues == []:
            self.write_migration_log_msg(f"  -- {pname}: {pvalues}")

        elif type(pvalues[0]) is dict:
            for pvalue in pvalues:
                self.write_migration_config_items(pname.title(), pvalue)
        else:
            self.write_migration_log_msg(f"  -- {pname}: {pvalues}")

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    #   INITIALIZE THE GLOBAL VARIABLES WITH THE CONFIGURATION FILE PARAMETER
    #   VALUES
    #
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _set_data_fields_from_config_parameter_dictionary(self):
        '''
        Set the iCloud3 variables from the configuration parameters
        '''

        # Convert operational parameters
        Gb.conf_profile[CONF_VERSION]                    = 0
        Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]       = self.conf_parm_general.get(CONF_EVLOG_CARD_DIRECTORY, V2_EVLOG_CARD_WWW_DIRECTORY)
        if instr(Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY], 'www') is False:
            Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]   = f"www/{Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]}"
        Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]         = self.conf_parm_general.get(CONF_EVLOG_CARD_PROGRAM, EVLOG_CARD_WWW_JS_PROG)

        # Convert iCloud Account Parameters
        Gb.conf_tracking[CONF_USERNAME]                  = self.conf_parm_tracking[CONF_USERNAME]
        Gb.conf_tracking[CONF_PASSWORD]                  = self.conf_parm_tracking[CONF_PASSWORD]
        Gb.conf_devices                                  = self.conf_parm_devices

        # Convert General parameters
        Gb.conf_general[CONF_UNIT_OF_MEASUREMENT]        = self.conf_parm_general[CONF_UNIT_OF_MEASUREMENT].lower()
        Gb.conf_general[CONF_TIME_FORMAT]                = (f"{self.conf_parm_general[CONF_TIME_FORMAT]}-hour").replace('-hour-hour', '-hour')
        Gb.conf_general[CONF_TRAVEL_TIME_FACTOR]         = self.conf_parm_general[CONF_TRAVEL_TIME_FACTOR]
        Gb.conf_general[CONF_MAX_INTERVAL]               = time_str_to_secs(self.conf_parm_general[CONF_MAX_INTERVAL]) / 60
        Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]     = self.conf_parm_general[CONF_GPS_ACCURACY_THRESHOLD]
        Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD]     = time_str_to_secs(self.conf_parm_general[CONF_OLD_LOCATION_THRESHOLD]) / 60
        Gb.conf_general[CONF_DISPLAY_ZONE_FORMAT]        = self.conf_parm_general[CONF_DISPLAY_ZONE_FORMAT].lower()
        Gb.conf_general[CONF_CENTER_IN_ZONE]             = self.conf_parm_general[CONF_CENTER_IN_ZONE]
        Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]    = self.conf_parm_general.get(CONF_DISCARD_POOR_GPS_INZONE, False)
        Gb.conf_general[CONF_DISPLAY_TEXT_AS]           = self.conf_parm_general[CONF_DISPLAY_TEXT_AS]

        # Convert Waze Parameters
        if CONF_WAZE_USED in self.conf_parm_general:
            Gb.conf_general[CONF_WAZE_USED]              = self.conf_parm_general[CONF_WAZE_USED]
        elif 'distance_method' in self.conf_parm_general:
            Gb.conf_general[CONF_WAZE_USED]              = self.conf_parm_general['distance_method'].lower() == 'waze'

        Gb.conf_general[CONF_WAZE_REGION]                = WAZE_SERVERS_BY_COUNTRY_CODE.get(Gb.country_code, 'row')
        Gb.conf_general[CONF_WAZE_MIN_DISTANCE]          = self.conf_parm_general[CONF_WAZE_MIN_DISTANCE]
        Gb.conf_general[CONF_WAZE_MAX_DISTANCE]          = self.conf_parm_general[CONF_WAZE_MAX_DISTANCE]
        Gb.conf_general[CONF_WAZE_REALTIME]              = self.conf_parm_general[CONF_WAZE_REALTIME]

        # Convert Stationary Zone Parameters
        if instr(self.conf_parm_general[CONF_STAT_ZONE_STILL_TIME], ':'):
            Gb.conf_general[CONF_STAT_ZONE_STILL_TIME]   = self.conf_parm_general[CONF_STAT_ZONE_STILL_TIME]
        else:
            Gb.conf_general[CONF_STAT_ZONE_STILL_TIME]   = time_str_to_secs(self.conf_parm_general[CONF_STAT_ZONE_STILL_TIME]) / 60
        if instr(self.conf_parm_general[CONF_STAT_ZONE_INZONE_INTERVAL], ':'):
            Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL] = self.conf_parm_general[CONF_STAT_ZONE_INZONE_INTERVAL]
        else:
            Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL] = time_str_to_secs(self.conf_parm_general[CONF_STAT_ZONE_INZONE_INTERVAL]) / 60
        Gb.conf_general[CONF_STAT_ZONE_BASE_LATITUDE]   = self.conf_parm_general[CONF_STAT_ZONE_BASE_LATITUDE]
        Gb.conf_general[CONF_STAT_ZONE_BASE_LONGITUDE]  = self.conf_parm_general[CONF_STAT_ZONE_BASE_LONGITUDE]

        self.write_migration_log_msg(f"\nCreated iCloud3 configuration file: {Gb.icloud3_config_filename}")

    #--------------------------------------------------------------------
    def _extract_name_device_type(self, devicename):
        '''Extract the name and device type from the devicename'''

        try:
            devicename = fname = devicename.lower()
            device_type = ""
            for ic3dev_type in DEVICE_TYPES:
                if devicename == ic3dev_type:
                    return (devicename, devicename)

                elif instr(devicename, ic3dev_type):
                    fnamew = devicename.replace(ic3dev_type, "")
                    fname  = fnamew.replace("_", "").replace("-", "").title().strip()
                    device_type = ic3dev_type
                    break

            if device_type == "":
                device_type = 'other'
                fname  = fname.replace("_", "").replace("-", "").title().strip()

        except Exception as err:
            # log_exception(err)
            pass

        return (fname, device_type)


#--------------------------------------------------------------------
    def remove_ic3_devices_from_known_devices_yaml_file(self):
        '''
        Remove the ic3 devicenames from the known_devices.yaml file if any are
        found
        '''
        try:

            known_devices_file = Gb.hass.config.path('known_devices.yaml')

            if file_exists(known_devices_file) is False:
                return

            ic3_devicenames = []
            new_kdf_devicenames = {}
            ic3_devicename_found_flag = False
            for conf_device in Gb.conf_devices:
                ic3_devicenames.append(conf_device["ic3_devicename"])

            log_info_msg(f"{ic3_devicenames}")
            with open(known_devices_file, 'r') as kdf:
                kdf_devicenames = yaml.safe_load(kdf)

                log_info_msg(f"{kdf_devicenames}")
                for kdf_devicename in kdf_devicenames:
                    log_info_msg(f"{kdf_devicename} {kdf_devicenames[kdf_devicename]}")
                    if kdf_devicename in ic3_devicenames:
                        ic3_devicename_found_flag = True
                        continue

                    new_kdf_devicenames[kdf_devicename] = kdf_devicenames[kdf_devicename]
            log_info_msg(f"{new_kdf_devicenames=}")

            if ic3_devicename_found_flag:
                with open(f"{known_devices_file}", 'w') as kdf:
                    yaml.dump(new_kdf_devicenames, kdf)

                Gb.restart_ha_flag = True
                log_info_msg(f'Restart ha {Gb.restart_ha_flag=}')
            return

        except Exception as err:
            log_exception(err)
            pass


    #--------------------------------------------------------------------
    def log_exception(self, err):
        _LOGGER.exception(err)
