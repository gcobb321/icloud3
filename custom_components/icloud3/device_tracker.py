"""Support for tracking for iCloud devices."""

from .global_variables  import GlobalVariables as Gb
from .const             import (DOMAIN, PLATFORM_DEVICE_TRACKER,ICLOUD3, ICLOUD3_VERSION_MSG,
                                DISTANCE_TO_DEVICES,
                                NOT_SET, HOME,
                                DEVICE_TYPE_ICONS,
                                BLANK_SENSOR_FIELD, DEVICE_TRACKER_STATE,
                                INACTIVE_DEVICE,
                                NAME, FNAME, PICTURE, ICON, ALERT,
                                DEVICE_TRACKER, LATITUDE, LONGITUDE, GPS, LOCATION_SOURCE, TRIGGER,
                                ZONE, ZONE_DATETIME,  LAST_ZONE, FROM_ZONE, ZONE_FNAME,
                                BATTERY, BATTERY_LEVEL,
                                MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
                                HOME_DISTANCE, ZONE_DISTANCE,
                                DEVICE_STATUS,
                                LAST_UPDATE, LAST_UPDATE_DATETIME, WENT_3KM,
                                NEXT_UPDATE, NEXT_UPDATE_DATETIME,
                                LOCATED, LAST_LOCATED, LAST_LOCATED_SECS, LAST_LOCATED_DATETIME,
                                GPS_ACCURACY, ALTITUDE, VERT_ACCURACY,
                                CONF_DEVICE_TYPE, CONF_RAW_MODEL, CONF_MODEL, CONF_MODEL_DISPLAY_NAME,
                                CONF_TRACKING_MODE,
                                CONF_IC3_DEVICENAME,
                                )

from .utils.utils       import (instr, is_number, is_statzone, zone_dname, is_empty, list_to_str, )
from .utils.messaging   import (post_event,
                                log_info_msg, log_debug_msg, log_error_msg, log_exception,
                                log_exception_HA, log_info_msg_HA, log_stack,
                                _evlog, _log, )
from .utils.time_util   import (adjust_time_hour_values, datetime_now, )
from .startup           import start_ic3
from .startup           import config_file

#--------------------------------------------------------------------
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker import device_trigger
from homeassistant.config_entries       import ConfigEntry
from homeassistant.core                 import HomeAssistant
from homeassistant.helpers.entity       import DeviceInfo
from homeassistant.helpers              import (entity_registry as er,
                                                device_registry as dr,
                                                area_registry as ar)
# from homeassistant.const                import (CONF_DEVICE_ID, CONF_DOMAIN, CONF_ENTITY_ID, CONF_EVENT,
#                                                 CONF_PLATFORM, CONF_TYPE, CONF_ZONE, )

# PLATFORM    = PLATFORM_DEVICE_TRACKER

#--------------------------------------------------------------------
EVENT_ENTER = "enter"
EVENT_LEAVE = "leave"
EVENT_DESCRIPTION = {EVENT_ENTER: "entering", EVENT_LEAVE: "leaving"}


#-------------------------------------------------------------------------------------------
async def async_setup_scanner(hass: HomeAssistant, config, see, discovery_info=None):
    """Old way of setting up the iCloud tracker with platform: icloud3 statement."""

    Gb.ha_config_platform_stmt = True if config.get('platform') == 'icloud3' else False

    return True

#-------------------------------------------------------------------------------------------
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up iCloud3 device tracker component."""
    # Save the hass `add_entities` call object for use in config_flow for adding devices

    PLATFORM = PLATFORM_DEVICE_TRACKER
    Gb.hass = hass
    Gb.async_add_entities_device_tracker = async_add_entities

    try:
        if Gb.conf_file_data == {}:
            start_ic3.initialize_directory_filenames()
            # config_file.load_icloud3_configuration_file()
            await config_file.async_load_icloud3_configuration_file()

        try:
            Gb.conf_devicenames = [conf_device[CONF_IC3_DEVICENAME]
                                        for conf_device in Gb.conf_devices
                                        if conf_device[CONF_IC3_DEVICENAME] != '']

            get_ha_device_ids_from_device_registry(hass)

        except Exception as err:
            log_exception(err)

        NewDeviceTrackers = []
        Gb.device_trackers_cnt = 0
        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]
            if devicename == '':
                continue

            if (devicename in Gb.DeviceTrackers_by_devicename
                    or conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE):
                continue

            DeviceTracker = iCloud3_DeviceTracker(devicename, conf_device)

            if DeviceTracker:
                Gb.DeviceTrackers_by_devicename[devicename] = DeviceTracker
                NewDeviceTrackers.append(DeviceTracker)


        log_devices_added_deleted('', Gb.DeviceTrackers_by_devicename)

        # Set the total count of the device_trackers that will be created
        if Gb.device_trackers_cnt == 0:
            Gb.device_trackers_cnt = len(NewDeviceTrackers)
            post_event(f"Device Tracker Entities > Created-{Gb.device_trackers_cnt}")

        if NewDeviceTrackers != []:
            async_add_entities(NewDeviceTrackers, True)

            get_ha_device_ids_from_device_registry(hass)
            log_info_msg_HA(f"{ICLOUD3} Device Tracker entities: {Gb.device_trackers_cnt}")


    except Exception as err:
        log_exception(err)
        log_msg = f"►INTERNAL ERROR (Create device_tracker loop-{err})"
        log_error_msg(log_msg)

#....................................................................
def log_devices_added_deleted(base_name, devices_list):
    if is_empty(devices_list):
        return

    _devices = list(devices_list.keys()) if type(devices_list) is dict else devices_list
    _devices_msg = {'BaseName': f"device_tracker.{base_name}",
                    'Count': len(devices_list),
                    'Entities': list_to_str(_devices)}
    log_info_msg(f"DEVICE TRACKERS ADDED: {_devices_msg}")

#-------------------------------------------------------------------------------------------
def get_ha_device_ids_from_device_registry(hass):
    '''
    Cycle thru the ha device registry, extract the iCloud3 entries and associate the
    ha device_id with the ic3_devicename parameters

    Check deleted entries first in case it was readded
    '''
    try:
        dev_reg = dr.async_get(hass)

        icloud3_dev_reg = {device: device_entry for device, device_entry in dev_reg.deleted_devices.items()
                                                if _icloud3_dev_reg_item(device_entry)}

        for device, device_entry in icloud3_dev_reg.items():
            _get_ha_device_id_from_device_entry(hass, device, device_entry)

        icloud3_dev_reg = {device: device_entry for device, device_entry in dev_reg.devices.items()
                                                if _icloud3_dev_reg_item(device_entry)}

        for device, device_entry in icloud3_dev_reg.items():
            _get_ha_device_id_from_device_entry(hass, device, device_entry)

    except Exception as err:
        log_exception(err)
        pass

def _icloud3_dev_reg_item(device_entry):
    ''' See if icloud3 is in the identifiers field'''
    # identifiers={('icloud3', 'gary_airpods')}
    try:
        de_identifiers = list(device_entry.identifiers)
        de_identifiers = list(de_identifiers[0])
        return 'icloud3' in de_identifiers

    except:
        return False

#-------------------------------------------------------------------------------------------
def _get_ha_device_id_from_device_entry(hass, device, device_entry):
    '''
    For each entry in the device registry, determine if it is an iCloud3 entry (iCloud3 is in
    the device_entry.identifiers field. If so, check the other items, determine if one is a
    tracked devicename and, if so, extract the device_id for that tracked devicename. This is
    used to associate the sensors with the device in sensor.py.
    )

    DeviceEntry(area_id=None, config_entries={'4ff81e71befd8994712d56eadf7232ae'},
        configuration_url=None, connections=set(), disabled_by=None, entry_type=None,
        hw_version=None,
        id='306278916dc4a3b7bcc73b66dcd565b3',
        identifiers={('icloud3', 'gary_iphone')}, manufacturer='Apple',
        model='iPhone 14 Pro', name_by_user=None, name='Gary', suggested_area=None, sw_version=None,
        via_device_id=None, is_new=False)
    DeletedDeviceEntry(config_entries={'4ff81e71befd8994712d56eadf7232ae'},
        connections=set(), identifiers={('iCloud3', 'gary_ihone', 'iPhone 14 Pro')},
        id='9045bf3f0363c28957353cf2c47163d0', orphaned_timestamp=None
    '''
    try:
        if device_entry.name in [DOMAIN, DOMAIN, f'{ICLOUD3} Integration']:
            Gb.ha_device_id_by_devicename[DOMAIN] = device_entry.id
            Gb.ha_area_id_by_devicename[DOMAIN]   = device_entry.area_id
            return
    except:
        pass

    try:
        de_identifiers = list(device_entry.identifiers)
        de_identifiers = list(de_identifiers[0])

        for item in de_identifiers:
            if item in Gb.conf_devicenames:
                Gb.ha_device_id_by_devicename[item] = device_entry.id
                Gb.ha_area_id_by_devicename[item]   = device_entry.area_id
                # _log(f"{device_entry.id=}")
                # _log(f"{device_entry.name=}")
                # _log(f"{device_entry.name_by_user=}")
                # _log(f"{device_entry.identifiers=}")
                # _log(f"{device_entry.is_new=}")
                # _log(f"{device_entry.disabled_by=}")

        # _log(f"{Gb.ha_device_id_by_devicename=}")

    except Exception as err:
        #log_exception(err)
        pass


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3_DeviceTracker(TrackerEntity):
    """iCloud3 device_tracker entity definition."""

    def __init__(self, devicename, conf_device, data=None):
        """Set up the iCloud3 device_tracker entity."""

        try:

            PLATFORM    = PLATFORM_DEVICE_TRACKER
            self.hass            = Gb.hass
            self.devicename      = devicename
            self.Device          = None   # Filled in after Device object has been created in start_ic3
            self.entity_id       = f"{PLATFORM_DEVICE_TRACKER}.{devicename}"
            self.ha_device_id    = Gb.ha_device_id_by_devicename.get(self.devicename)
            self._attr_unique_id = f"{DOMAIN}_{self.devicename}"

            self.ha_area_id      = Gb.ha_area_id_by_devicename.get(self.devicename)

            self.device_fname    = conf_device[FNAME]
            self.device_type     = conf_device[CONF_DEVICE_TYPE]
            self.tracking_mode   = conf_device[CONF_TRACKING_MODE]
            self.raw_model       = conf_device[CONF_RAW_MODEL]                # iPhone15,2
            self.model           = conf_device[CONF_MODEL]                    # iPhone
            self.model_display_name = conf_device[CONF_MODEL_DISPLAY_NAME]  # iPhone 14 Pro

            try:
                self.default_value = Gb.restore_state_devices[devicename]['sensors'][ZONE]
            except:
                self.default_value = BLANK_SENSOR_FIELD

            self.triggers           = None
            self.from_state_zone    = ''
            self.to_state_zone      = ''
            self._state             = self.default_value
            self._data              = data          # Used by .see to issue change triggers
            self._attr_force_update = True
            self._unsub_dispatcher  = None
            self._on_remove         = [self.after_removal_cleanup]
            self.remove_device_flag = False
            self.entity_removed_flag = False

            self.extra_attrs_track_from_zones      = 'home'
            self.extra_attrs_primary_home_zone     = 'Home'
            self.extra_attrs_away_time_zone_offset = 'HomeZone'

            Gb.device_trackers_created_cnt += 1
            # log_debug_msg(f'Device Tracker entity created: {self.entity_id}, #{Gb.device_trackers_created_cnt}')

        except Exception as err:
            log_exception(err)
            log_msg = f"►INTERNAL ERROR (Create device_tracker object-{err})"
            log_error_msg(log_msg)

#-------------------------------------------------------------------------------------------
    # @property
    # def unique_id(self) -> str:
    #     """Return a unique ID."""
    #     return self._attr_unique_id

    @property
    def should_poll2(self):
        return False

    @property
    def force_update(self):
        return True

    @property
    def name(self):
        """Return the name of the device."""
        return self.device_fname

    @property
    def get_device_id(self):
        return self.device_id

    @property
    def get_area_id(self):
        """Return the area_id of the device."""
        # if self.ha_area_id is None:
        #     self.ha_area_id = Gb.ha_area_id_by_devicename[self.devicename] = \
        #         Gb.area_id_personal_device
        return self.area_id

    @property
    def location_name(self):
        """Return the location name of the device."""
        try:
            return self.Device.sensors.get(DEVICE_TRACKER_STATE, None)
        except:
            return None

    @property
    def location_accuracy(self):
        """Return the location accuracy of the device."""
        return self._get_sensor_value(GPS_ACCURACY, number=True)

    @property
    def latitude(self):
        """Return latitude value of the device."""
        return self._get_sensor_value(LATITUDE, number=True)

    @property
    def longitude(self):
        """Return longitude value of the device."""
        return self._get_sensor_value(LONGITUDE, number=True)

    @property
    def battery_level(self):
        """Return the battery level of the device."""
        return self._get_sensor_value(BATTERY, number=True)

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return "gps"

    @property
    def icon(self):
        """Return an icon based on the type of the device."""
        return self._get_sensor_value(ICON)

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        return self._get_extra_attributes()

    @property
    def device_info(self):
        """Return the device information."""

        return DeviceInfo(  identifiers  = {(DOMAIN, self.devicename)},
                            manufacturer = "Apple",
                            model        = self.raw_model,
                            name         = f"{self.device_fname} ({self.devicename})",
                        )

#-------------------------------------------------------------------------------------------
    def _get_extra_attributes(self):
        '''
        Get the extra attributes for the device_tracker
        '''
        try:
            if self.Device:
                if self.Device.track_from_zones != [HOME]:
                    self.extra_attrs_track_from_zones = ', '.join(self.Device.track_from_zones)
                if self.Device.track_from_base_zone != HOME:
                    self.extra_attrs_primary_home_zone = zone_dname(self.Device.track_from_base_zone)
                if self.Device.away_time_zone_offset != 0:
                    plus_minus = '+' if self.Device.away_time_zone_offset > 0 else ''
                    self.extra_attrs_away_time_zone_offset = \
                                f"HomeZone {plus_minus}{self.Device.away_time_zone_offset} hours"

            icloud3 = ICLOUD3.lower()
            extra_attrs = {}
            extra_attrs[GPS]            = f"({self.latitude}, {self.longitude})"
            extra_attrs[LOCATED]        = self._get_sensor_value(LAST_LOCATED_DATETIME)
            alert                       = self._get_sensor_value(ALERT)
            extra_attrs[ALERT]          = alert if alert != BLANK_SENSOR_FIELD else ''

            extra_attrs[f"{'-'*5} DEVICE CONFIGURATION {'-'*20}"] = ''
            extra_attrs['integration']  = icloud3

            if self.Device:
                if self.Device.AppleAcct:
                    extra_attrs['apple_account'] = self.Device.AppleAcct.account_owner_username
                else:
                    extra_attrs['apple_account'] = 'None'
                if self.Device.mobapp[DEVICE_TRACKER]:
                    extra_attrs['mobile_app'] = self.Device.mobapp[DEVICE_TRACKER]
                else:
                    extra_attrs['mobile_app'] = 'None'

            extra_attrs[NAME]                    = self._get_sensor_value(NAME)
            picture                              = self._get_sensor_value(PICTURE)
            if picture in ['', 'None', BLANK_SENSOR_FIELD]:
                extra_attrs['picture_file']      = 'None'
                extra_attrs.pop(PICTURE, None)
            else:
                extra_attrs[PICTURE]             = picture
                extra_attrs['picture_file']      = self._get_sensor_value(PICTURE)

            extra_attrs['icon_mdi:imagename']    = self._get_sensor_value(ICON)
            extra_attrs['track_from_zones']      = self.extra_attrs_track_from_zones
            extra_attrs['primary_home_zone']     = self.extra_attrs_primary_home_zone
            extra_attrs['away_time_zone_offset'] = self.extra_attrs_away_time_zone_offset

            extra_attrs[f"{'-'*5} LOCATION INFO {'-'*20}"] = self._get_sensor_value(LAST_UPDATE_DATETIME)
            extra_attrs[DEVICE_STATUS]  = self._get_sensor_value(DEVICE_STATUS)
            extra_attrs[LOCATION_SOURCE]= f"{self._get_sensor_value(LOCATION_SOURCE)}"
            extra_attrs[TRIGGER]        = self._get_sensor_value(TRIGGER)
            extra_attrs[ZONE]           = self._get_sensor_value(ZONE)
            extra_attrs[LAST_ZONE]      = self._get_sensor_value(LAST_ZONE)
            extra_attrs[FROM_ZONE]      = self._get_sensor_value(FROM_ZONE)
            extra_attrs[HOME_DISTANCE]  = self._get_sensor_value(HOME_DISTANCE)
            extra_attrs[ZONE_DISTANCE]  = self._get_sensor_value(ZONE_DISTANCE)
            extra_attrs[MAX_DISTANCE]   = self._get_sensor_value(MAX_DISTANCE)
            extra_attrs[CALC_DISTANCE]  = self._get_sensor_value(CALC_DISTANCE)
            extra_attrs[WAZE_DISTANCE]  = self._get_sensor_value(WAZE_DISTANCE)
            extra_attrs[DISTANCE_TO_DEVICES] = self._get_sensor_value(DISTANCE_TO_DEVICES)
            extra_attrs[ZONE_DATETIME]  = self._get_sensor_value(ZONE_DATETIME)
            extra_attrs[NEXT_UPDATE]    = self._get_sensor_value(NEXT_UPDATE_DATETIME)
            extra_attrs['last_timestamp']= f"{self._get_sensor_value(LAST_LOCATED_SECS)}"

            extra_attrs[f"{'-'*5} ICLOUD3 CONFIGURATION {'-'*19}"] = ''
            extra_attrs['icloud3_devices']   = ', '.join(Gb.Devices_by_devicename.keys())
            extra_attrs[f'{icloud3}_version']   = f"v{Gb.version}"
            extra_attrs['event_log_version'] = f"v{Gb.version_evlog}"
            extra_attrs[f'{icloud3}_directory'] = Gb.icloud3_directory

            return extra_attrs

        except Exception as err:
            log_exception(err)
            log_error_msg(f"►INTERNAL ERROR (Create device_tracker object-{err})")

#-------------------------------------------------------------------------------------------
    def _get_sensor_value(self, sensor, number=False):
        '''
        Get the sensor value from Device's sensor
        '''
        try:
            not_set_value = 0 if number else BLANK_SENSOR_FIELD

            if self.Device is None:
                return self._get_restore_or_default_value(sensor, not_set_value)

            sensor_value = self.Device.sensors.get(sensor, None)
            if self.Device.away_time_zone_offset != 0:
                sensor_value = adjust_time_hour_values(sensor_value, self.Device.away_time_zone_offset)

            if instr(sensor, DEVICE_TRACKER_STATE):
                return sensor_value

            if number and instr(sensor_value, ' '):
                sensor_value = float(sensor_value.split(' ')[0])

            number = is_number(sensor_value)
            if number is False and type(sensor_value) is str:
                if sensor_value is None or sensor_value.strip() == '' or sensor_value == NOT_SET:
                    sensor_value = BLANK_SENSOR_FIELD

        except Exception as err:
            log_error_msg(f"►INTERNAL ERROR (Create device_tracker object-{err})")
            sensor_value = not_set_value

        # Numeric fields are displayed in the attributes with 2-decimal places, Fix for gps
        # return str(sensor_value) if sensor in [LATITUDE, LONGITUDE] else sensor_value
        return sensor_value

#-------------------------------------------------------------------------------------------
    def _get_restore_or_default_value(self, sensor, not_set_value):
        '''
        Get a default value that is used when iCloud3 has not started or the Device for the
        sensor has not veen created.
        '''
        try:
            sensor_value = Gb.restore_state_devices[self.devicename]['sensors'][sensor]
        except:
            sensor_value = not_set_value

        return sensor_value

#-------------------------------------------------------------------------------------------
    def _get_attribute_value(self, attribute):
        '''
        Get the attribute value from Device's attributes
        '''
        try:
            if self.Device is None:
                return 0

            attr_value = self.Device.attrs.get(attribute, None)

            if attr_value is None or attr_value.strip() == '' or attr_value == NOT_SET:
                attr_value = 0

        except:
            attr_value = 0

        return attr_value

#-------------------------------------------------------------------------------------------
    def update_entity_attribute(self, new_fname=None, area_id=None, removing_device=False):
        """ Update entity definition attributes """

        ha_device_id = Gb.ha_device_id_by_devicename.get(self.devicename)
        if ha_device_id is None:
            return

        if removing_device:
            pass
        elif new_fname is None and area_id is None:
            return

        # try:
        #     area_id   = area_id or self.ha_area_id or Gb.area_id_personal_device
        #     area_reg  = ar.async_get(Gb.hass)
        #     area_name = area_reg.async_get_area(area_id).name
        # except:
        #     area_id = area_name = None

        self.device_fname = new_fname or self.device_fname
        # self.ha_area_id   = Gb.ha_area_id_by_devicename[self.devicename] = \
        #                         area_id

        log_debug_msg(f"Device Tracker entity changed: device_tracker.{self.devicename}, "
                        f"{self.device_fname}")
                        # f"({area_name})")

        kwargs = {}
        kwargs['original_name'] = self.device_fname
        kwargs['disabled_by']   = None

        entity_registry = er.async_get(Gb.hass)
        er_entry = entity_registry.async_update_entity(self.entity_id, **kwargs)

        """
            Typically used:
                original_name: str | None | UndefinedType = UNDEFINED,

            Not used:
                area_id: str | None | UndefinedType = UNDEFINED,
                capabilities: Mapping[str, Any] | None | UndefinedType = UNDEFINED,
                config_entry_id: str | None | UndefinedType = UNDEFINED,
                device_class: str | None | UndefinedType = UNDEFINED,
                device_id: str | None | UndefinedType = UNDEFINED,
                disabled_by: RegistryEntryDisabler | None | UndefinedType = UNDEFINED,
                entity_category: EntityCategory | None | UndefinedType = UNDEFINED,
                hidden_by: RegistryEntryHider | None | UndefinedType = UNDEFINED,
                icon: str | None | UndefinedType = UNDEFINED,
                name: str | None | UndefinedType = UNDEFINED,
                new_entity_id: str | UndefinedType = UNDEFINED,
                new_unique_id: str | UndefinedType = UNDEFINED,
                original_device_class: str | None | UndefinedType = UNDEFINED,
                original_icon: str | None | UndefinedType = UNDEFINED,
                supported_features: int | UndefinedType = UNDEFINED,
                unit_of_measurement: str | None | UndefinedType = UNDEFINED,
    """

        kwargs = {}
        kwargs['name']         = f"{self.device_fname} ({self.devicename})"
        kwargs['name_by_user'] = ""
        # kwargs['area_id']      = self.ha_area_id

        device_registry = dr.async_get(Gb.hass)
        dr_entry = device_registry.async_update_device(self.ha_device_id, **kwargs)

#-------------------------------------------------------------------------------------------
    def remove_device_tracker(self):

        try:
            Gb.hass.async_create_task(self.async_remove(force_remove=True))

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def after_removal_cleanup(self):
        """ Cleanup device_tracker after removal

        Passed in the `self._on_remove` parameter during initialization
        and called by HA after processing the async_remove request
        """

        self._remove_from_registries()
        self.entity_removed_flag = True

        if self.Device is None:
            return

        if self.Device.Sensors_from_zone and self.devicename in self.Device.Sensors_from_zone:
            self.Device.Sensors_from_zone.pop(self.devicename)

        if self.Device.Sensors and self.devicename in self.Device.Sensors:
            self.Device.Sensors.pop(self.devicename)

#-------------------------------------------------------------------------------------------
    def _remove_from_registries(self) -> None:
        """ Remove entity/device from registry """

        if not self.registry_entry:
            return

        device_registry = dr.async_get(Gb.hass)

        self.remove_device_flag = True

        # Remove from device registry.
        if device_id := self.registry_entry.device_id:
            device_registry = dr.async_get(Gb.hass)
            if device_id in device_registry.devices:
                device_registry.async_remove_device(device_id)

        # Remove from entity registry.
        if entity_id := self.registry_entry.entity_id:
            entity_registry = er.async_get(Gb.hass)
            if entity_id in entity_registry.entities:
                entity_registry.async_remove(entity_id)

#-------------------------------------------------------------------------------------------
    def remove_device_tracker_via_id(self):
        """Handle a deleted device."""
        try:
            dev_entry = dr.async_get_device(
                            identifiers={(DOMAIN, self.devicename)})

            if dev_entry is not None:
                dr.async_update_device(
                            dev_entry.id, remove_config_entry_id=self.ha_device_id)

        except Exception as err:
            log_exception(err)

        # https://github.com/gcobb321/homeassistant/blob/6c69b36b7b1e3dd0e1488489bd15117bc5eda889/homeassistant/components/smartthings/__init__.py#L226
        # def handle_deleted_device(device_id: str) -> None:
        # """Handle a deleted device."""
        # dev_entry = device_registry.async_get_device(
        #     identifiers={(DOMAIN, device_id)},
        # )
        # if dev_entry is not None:
        #     device_registry.async_update_device(
        #         dev_entry.id, remove_config_entry_id=entry.entry_id
        #     )

#-------------------------------------------------------------------------------------------
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        if self._unsub_dispatcher:
            self._unsub_dispatcher()

#-------------------------------------------------------------------------------------------
    def write_ha_device_tracker_state(self):
        """
        Update the entity's state.
        HA will determine if the device is in a zone based on the lat/long and set the device's
        state value to the zone or not_nome
        """
        try:
            # Pass gps data to the HA .see which handles zone triggers
            if self.Device and self.Device.sensors[LATITUDE] != 0:
                data = {LATITUDE: self.Device.sensors[LATITUDE],
                        LONGITUDE: self.Device.sensors[LONGITUDE],
                        GPS: (self.Device.sensors[LATITUDE], self.Device.sensors[LONGITUDE]),
                        GPS_ACCURACY: self.Device.sensors[GPS_ACCURACY],
                        BATTERY: self.Device.sensors[BATTERY],
                        ALTITUDE: self.Device.sensors[ALTITUDE],
                        VERT_ACCURACY: self.Device.sensors[VERT_ACCURACY]}
                self._data = data

        except Exception as err:
            log_exception(err)
            self._data = None

        # self.async_write_ha_state()
        try:
            if self.hass is None: self.hass = Gb.hass
            self.schedule_update_ha_state(force_refresh=True)

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def __repr__(self):
        return (f"<DeviceTracker: {self.devicename}/{self.device_type}>")
