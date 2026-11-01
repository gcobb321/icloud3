

from ...global_variables    import GlobalVariables as Gb
from ...const_config        import (BATTERY, HOME_DISTANCE, ARRIVAL_TIME, TRAVEL_TIME, NEXT_UPDATE,
                                    CONF_SENSORS_TRACKING_TIME, CONF_SENSORS_TRACKING_DISTANCE,
                                    CONF_SENSORS_TRACK_FROM_ZONES, CONF_SENSORS_TRACKING_UPDATE,
                                    CONF_SENSORS_MONITORED_DEVICES, CONF_SENSORS_DEVICE,
                                    CONF_EXCLUDED_SENSORS, DEFAULT_SENSORS_CONF, )
from ...const_sensor        import (SENSOR_GROUPS )

from ...utils.utils         import (isnot_empty, list_add, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from .                      import form_sensors as forms
from ..                     import sensors_cf
from ..                     import utils_cf
from ..const_form_lists     import *


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SENSORS CONFIG FLOW
#       - async_step_sensors
#       - async_step_exclude_sensors
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OptionsFlow_Sensors_Steps:

    def initialize_sensors_variables(self):
        '''
        Initialize the variables used by the Sensors screens. Called from the
        flow handler's initialize_options (the mixin's __init__ would never be run).
        '''
        # List of all sensors created by ic3 during startup by sensor.py that is used
        # in the exclude_sensors screen
        # Format: ('gary_iphone_zone_distance': 'Gary ZoneDistance (gary_iphone_zone_distance)')
        self.sensors_fname_list             = []
        self.excluded_sensors               = []
        self.excluded_sensors_removed       = []
        self.sensors_list_filter            = ''

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #            SENSORS
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_sensors(self, user_input=None, errors=None):
        '''
        Select the sensors created for all devices. The Select the default sensors action
        redisplays the screen with the default sensors selected, they are saved with Save.
        '''
        self.step_id = 'sensors'
        self.errors = errors or {}
        await self.async_write_icloud3_configuration_file()
        user_input = utils_cf.flatten_sections(user_input)
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        user_input = self._add_always_created_sensors(user_input)

        utils_cf.log_step_info(self, user_input, action_item)

        if user_input is None:
            self._initialize_excluded_sensors()
            return self.async_show_form(step_id='sensors',
                                        data_schema=forms.form_sensors(self),
                                        errors=self.errors)

        if action_item == 'cancel_goto_menu':
            self.excluded_sensors = []
            return await self.async_step_menu()

        if action_item == 'select_default_sensors':
            return self.async_show_form(step_id='sensors',
                                        data_schema=forms.form_sensors(self,
                                            user_input=DEFAULT_SENSORS_CONF.copy()),
                                        errors=self.errors)

        self.set_default_sensors(user_input)
        user_input.setdefault(CONF_EXCLUDED_SENSORS, [])

        try:
            if action_item == 'save':
                self._save_sensors(user_input)
                return await self.async_step_menu()

        except Exception as err:
            log_exception(err)

        utils_cf.log_step_info(self, user_input, action_item)

        if utils_cf.any_errors(self):
            self.errors['base'] = 'update_aborted'

        return self.async_show_form(step_id='sensors',
                            data_schema=forms.form_sensors(self),
                            errors=self.errors)

#......................................................
    def _initialize_excluded_sensors(self):
        '''
        The excluded sensors being changed. Older versions saved a 'None' placeholder item
        when there were none, it is not an excluded sensor.
        '''
        # Startup excludes the (devicename_sensor) of an item. Items saved with only the
        # sensor fname are changed to the 'Gary-iPhone Battery (gary_iphone_battery)' format.
        excluded_by_fname = {Sensor.sensor_fname: self._sensor_list_item(Sensor)
                                    for Sensor in self._device_Sensors()}
        self.excluded_sensors = [excluded_by_fname.get(sensor, sensor)
                                    for sensor in Gb.conf_sensors[CONF_EXCLUDED_SENSORS]
                                    if sensor != 'None']

#......................................................
    @staticmethod
    def _device_Sensors():
        return [Sensor  for devicename in Gb.Devices_by_devicename.keys()
                        for Sensor in Gb.Sensors_by_devicename.get(devicename, {}).values()]

    @staticmethod
    def _sensor_list_item(Sensor):
        '''
        The Exclude sensors list item and the saved excluded sensor (config_file
        get_excluded_sensor_devicename_sensor): 'Gary-iPhone Battery (gary_iphone_battery)'
        '''
        return f"{Sensor.sensor_fname} ({Sensor.entity_name})"

#......................................................
    def _save_sensors(self, user_input):
        '''
        Save the sensors and excluded sensors, add and remove the sensor entities
        '''
        # TfZ Sensors are not configured via config_flow but built in
        # config_flow from the distance, time & zone sensors
        tfz_sensors_base = ['zone_info']
        tfz_sensors_base.extend(user_input[CONF_SENSORS_TRACKING_TIME])
        tfz_sensors_base.extend(user_input[CONF_SENSORS_TRACKING_DISTANCE])
        tfz_sensors = []
        for sensor in tfz_sensors_base:
            if sensor in SENSOR_GROUPS['track_from_zone']:
                tfz_sensors.append(f"tfz_{sensor}")
        user_input[CONF_SENSORS_TRACK_FROM_ZONES] = tfz_sensors

        (sensors_to_add, sensors_to_remove,
        sensors_to_exclude, sensors_to_not_exclude) = \
                    sensors_cf.identify_new_and_removed_sensors(self, user_input)

        self._update_config_file_general(user_input)

        self.create_device_tracker_sensor_enities_on_exit = isnot_empty(sensors_to_add)
        sensors_cf.remove_sensor_entities(sensors_to_remove)
        sensors_cf.remove_sensors_from_excluded_sensors_list(sensors_to_exclude)
        self.excluded_sensors = []

#......................................................
    @staticmethod
    def _add_always_created_sensors(user_input):
        '''
        The sensors that are always created are not on the Sensors screen. Add them at their
        position in the configuration.
        '''
        if user_input is None:
            return None

        for sensor_group, always_created in ALWAYS_CREATED_SENSORS.items():
            if sensor_group not in user_input:
                continue
            selected = user_input[sensor_group]
            conf_sensors = Gb.conf_sensors.get(sensor_group, [])
            user_input[sensor_group] = (
                    [sensor for sensor in conf_sensors if sensor in selected or sensor in always_created]
                    + [sensor for sensor in selected if sensor not in conf_sensors])

        return user_input

#......................................................
    @staticmethod
    def set_default_sensors(user_input):
        '''
        Always check default sensors
        '''
        if 'md_badge' not in user_input[CONF_SENSORS_MONITORED_DEVICES]:
            user_input[CONF_SENSORS_MONITORED_DEVICES].append('md_badge')
        if 'md_battery' not in user_input[CONF_SENSORS_MONITORED_DEVICES]:
            user_input[CONF_SENSORS_MONITORED_DEVICES].append('md_battery')

        if 'badge' not in user_input[CONF_SENSORS_DEVICE]:
            user_input[CONF_SENSORS_DEVICE].append('badge')
        if BATTERY not in user_input[CONF_SENSORS_DEVICE]:
            user_input[CONF_SENSORS_DEVICE].append(BATTERY)

        if ARRIVAL_TIME not in user_input[CONF_SENSORS_TRACKING_TIME]:
            user_input[CONF_SENSORS_TRACKING_TIME].append(ARRIVAL_TIME)
        if TRAVEL_TIME not in user_input[CONF_SENSORS_TRACKING_TIME]:
            user_input[CONF_SENSORS_TRACKING_TIME].append(TRAVEL_TIME)
        if HOME_DISTANCE not in user_input[CONF_SENSORS_TRACKING_DISTANCE]:
            user_input[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)

        if NEXT_UPDATE not in user_input[CONF_SENSORS_TRACKING_UPDATE]:
            user_input[CONF_SENSORS_TRACKING_UPDATE].append(NEXT_UPDATE)

        return user_input

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #            EXCLUDE SENSORS
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_exclude_sensors(self, user_input=None, errors=None):
        '''
        Select the sensors that are not created. Apply the filter moves the checked sensors
        to the Excluded sensors and lists the sensors containing the filter, Save saves the
        Excluded sensors and returns to the menu, Back discards the changes.
        '''
        self.step_id = 'exclude_sensors'
        self.errors = errors or {}
        await self.async_write_icloud3_configuration_file()
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        if user_input is None:
            self.sensors_list_filter = ''
            self._initialize_excluded_sensors()

        if self.sensors_fname_list == []:
                self.sensors_fname_list = sorted(self._sensor_list_item(Sensor)
                                                    for Sensor in self._device_Sensors())

        if user_input is None:
            return self._show_exclude_sensors_form()

        utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'cancel_goto_menu':
            self.excluded_sensors = []
            return await self.async_step_menu()

        self._update_excluded_sensors(user_input)

        if action_item == 'save_excluded_sensors':
            if self.excluded_sensors != [sensor for sensor in Gb.conf_sensors[CONF_EXCLUDED_SENSORS]
                                                if sensor != 'None']:
                sensors_user_input = {sensor_group: (sensors.copy() if isinstance(sensors, list) else sensors)
                                        for sensor_group, sensors in Gb.conf_sensors.items()}
                sensors_user_input[CONF_EXCLUDED_SENSORS] = self.excluded_sensors.copy()
                self._save_sensors(sensors_user_input)
                list_add(self.config_parms_update_control, ['restart'])
            self.excluded_sensors = []
            return await self.async_step_menu()

        self.sensors_list_filter = user_input.get('filter', '').lower().strip()
        return self._show_exclude_sensors_form()

#-------------------------------------------------------------------------------------------
    def _show_exclude_sensors_form(self):
        data_schema, placeholders = forms.form_exclude_sensors(self)
        return self.async_show_form(step_id='exclude_sensors',
                            data_schema=data_schema,
                            description_placeholders=placeholders,
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _update_excluded_sensors(self, user_input):

        excluded_sensors = []
        excluded_sensors.extend(user_input.get(CONF_EXCLUDED_SENSORS, []))
        excluded_sensors.extend(user_input.get('filtered_sensors', []))
        self.excluded_sensors = [sensor for sensor in set(excluded_sensors) if sensor != 'None']
        self.excluded_sensors.sort()

        self.excluded_sensors_removed = [sensor_fname
                                        for sensor_fname in Gb.conf_sensors[CONF_EXCLUDED_SENSORS]
                                        if sensor_fname not in self.excluded_sensors]

        self.sensors_fname_list.extend(self.excluded_sensors)
        self.sensors_fname_list = list(set(self.sensors_fname_list))
        self.sensors_fname_list.sort()

