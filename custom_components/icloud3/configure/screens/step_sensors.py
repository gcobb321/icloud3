

from ...global_variables    import GlobalVariables as Gb
from ...const               import (BATTERY, HOME_DISTANCE,
                                    ARRIVAL_TIME, TRAVEL_TIME, NEXT_UPDATE,
                                    CONF_SENSORS_TRACKING_TIME, CONF_SENSORS_TRACKING_DISTANCE,
                                    CONF_SENSORS_TRACK_FROM_ZONES, CONF_SENSORS_TRACKING_UPDATE,
                                    CONF_SENSORS_MONITORED_DEVICES, CONF_SENSORS_DEVICE,
                                    CONF_EXCLUDED_SENSORS,
                                    DEFAULT_SENSORS_CONF,
                                    )
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



    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #            SENSORS
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_sensors(self, user_input=None, errors=None):

        self.step_id = 'sensors'
        self.errors = errors or {}
        await self.async_write_icloud3_configuration_file()
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        utils_cf.log_step_info(self, user_input, action_item)

        if Gb.conf_sensors[CONF_EXCLUDED_SENSORS] == []:
            Gb.conf_sensors[CONF_EXCLUDED_SENSORS] = ['None']
        if self.excluded_sensors == []:
            self.excluded_sensors = Gb.conf_sensors[CONF_EXCLUDED_SENSORS].copy()

        if user_input is None:
            return self.async_show_form(step_id='sensors',
                                        data_schema=forms.form_sensors(self),
                                        errors=self.errors)

        if action_item == 'goto_menu':
            return await self.async_step_menu()

        self.set_default_sensors(user_input)

        if action_item == 'set_to_default_sensors':
            user_input = DEFAULT_SENSORS_CONF.copy()
            utils_cf.log_step_info(self, user_input, action_item)

            return self.async_show_form(step_id='sensors',
                                        data_schema=forms.form_sensors(self, user_input=user_input),
                                        errors=self.errors)

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

        if action_item == 'exclude_sensors':
            self.sensors_list_filter = '?'
            self.excluded_sensors = user_input[CONF_EXCLUDED_SENSORS]
            return await self.async_step_exclude_sensors()

        if action_item == 'save_stay':
            (sensors_to_add, sensors_to_remove,
            sensors_to_exclude, sensors_to_not_exclude) = \
                        sensors_cf.identify_new_and_removed_sensors(self, user_input)

            self._update_config_file_general(user_input)

            self.create_device_tracker_sensor_enities_on_exit = isnot_empty(sensors_to_add)
            sensors_cf.remove_sensor_entities(sensors_to_remove)
            sensors_cf.remove_sensors_from_excluded_sensors_list(sensors_to_exclude)
            self.excluded_sensors = []

            return await self.async_step_sensors()

        utils_cf.log_step_info(self, user_input, action_item)

        if utils_cf.any_errors(self):
            self.errors['base'] = 'update_aborted'

        return self.async_show_form(step_id='sensors',
                            data_schema=forms.form_sensors(self),
                            errors=self.errors)

#......................................................
    @staticmethod
    def set_default_sensors(user_input):
        '''
        Always check default sensors
        '''
        if BATTERY not in user_input[CONF_SENSORS_DEVICE]:
            user_input[CONF_SENSORS_DEVICE].append(BATTERY)
        if 'md_battery' not in user_input[CONF_SENSORS_MONITORED_DEVICES]:
            user_input[CONF_SENSORS_MONITORED_DEVICES].append('md_battery')
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

        self.step_id = 'exclude_sensors'
        self.errors = errors or {}
        await self.async_write_icloud3_configuration_file()
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        if self.excluded_sensors == []:
            self.excluded_sensors = ['None']

        if self.sensors_fname_list == []:
                Sensors = []
                for devicename in Gb.Devices_by_devicename.keys():
                    devicename_Sensors = [Sensor for Sensor in Gb.Sensors_by_devicename[devicename].values()]
                    Sensors.extend(devicename_Sensors)

                self.sensors_fname_list = [Sensor.fname_entity_name for Sensor in Sensors]
                self.sensors_fname_list.sort()

        if user_input is None:
            return self.async_show_form(step_id='exclude_sensors',
                                        data_schema=forms.form_exclude_sensors(self),
                                        errors=self.errors)

        utils_cf.log_step_info(self, user_input, action_item)
        sensors_list_filter = user_input['filter'].lower().replace('?', '').strip()

        if (self.sensors_list_filter == sensors_list_filter
                and len(self.excluded_sensors) == len(user_input[CONF_EXCLUDED_SENSORS])
                and user_input['filtered_sensors'] == []):
            self.sensors_list_filter = '?'
        else:
            self.sensors_list_filter = sensors_list_filter or '?'

        if (user_input[CONF_EXCLUDED_SENSORS] != self.excluded_sensors
                or user_input['filtered_sensors'] != []):
            self._update_excluded_sensors(user_input)
            self.sensors_list_filter = '?'

            self.errors['excluded_sensors'] = 'excluded_sensors_ha_restart'
            list_add(self.config_parms_update_control, ['restart'])

        if action_item == 'return_to_sensor_screen':
            # return True
            return await self.async_step_sensors()

        if action_item == 'update_sensor_list':
            return await self.async_step_exclude_sensors()

        return self.async_show_form(step_id='exclude_sensors',
                            data_schema=forms.form_exclude_sensors(self),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _update_excluded_sensors(self, user_input):

        excluded_sensors = []
        excluded_sensors.extend(user_input[CONF_EXCLUDED_SENSORS])
        excluded_sensors.extend(user_input['filtered_sensors'])
        self.excluded_sensors = list(set(excluded_sensors))
        self.excluded_sensors.sort()

        self.excluded_sensors_removed = [sensor_fname
                                        for sensor_fname in Gb.conf_sensors[CONF_EXCLUDED_SENSORS]
                                        if sensor_fname not in self.excluded_sensors]

        self.sensors_fname_list.extend(self.excluded_sensors)
        self.sensors_fname_list = list(set(self.sensors_fname_list))
        self.sensors_fname_list.sort()

        if self.excluded_sensors == []:
            self.excluded_sensors = ['None']
        elif len(self.excluded_sensors) > 1 and 'None' in self.excluded_sensors:
            self.excluded_sensors.remove('None')

        # Add filtered sensors just selected/unselected
        # user_input[CONF_EXCLUDED_SENSORS] = self.excluded_sensors.copy()

        return #user_input
