

from ...global_variables    import GlobalVariables as Gb
from ...const               import (HOME_DISTANCE,
                                    CONF_SENSORS_MONITORED_DEVICES,
                                    CONF_SENSORS_DEVICE,
                                    CONF_SENSORS_TRACKING_UPDATE, CONF_SENSORS_TRACKING_TIME, CONF_SENSORS_TRACKING_DISTANCE,
                                    CONF_SENSORS_TRACKING_OTHER, CONF_SENSORS_ZONE,
                                    CONF_SENSORS_OTHER, CONF_EXCLUDED_SENSORS,
                                    )

from ...utils.utils         import (instr, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..                     import utils_cf
from ..const_form_lists     import *

from homeassistant.helpers  import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#     SENSOR FORMS
#
#       - form_sensors
#       - form_exclude_sensors
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SENSORS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_sensors(self, user_input=None):
    self.actions_list = SENSORS_ACTIONS.copy()


    self.set_default_sensors(Gb.conf_sensors)
    sensors = user_input if user_input is not None else Gb.conf_sensors.copy()
    sensors[CONF_EXCLUDED_SENSORS] = self.excluded_sensors

    if HOME_DISTANCE not in Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE]:
        Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)

    return vol.Schema({
        vol.Required(CONF_SENSORS_DEVICE,
                    default=sensors[CONF_SENSORS_DEVICE]):
                    cv.multi_select(CONF_SENSORS_DEVICE_KEY_TEXT),
        vol.Required(CONF_SENSORS_TRACKING_UPDATE,
                    default=sensors[CONF_SENSORS_TRACKING_UPDATE]):
                    cv.multi_select(CONF_SENSORS_TRACKING_UPDATE_KEY_TEXT),
        vol.Required(CONF_SENSORS_TRACKING_TIME,
                    default=sensors[CONF_SENSORS_TRACKING_TIME]):
                    cv.multi_select(CONF_SENSORS_TRACKING_TIME_KEY_TEXT),
        vol.Required(CONF_SENSORS_TRACKING_DISTANCE,
                    default=sensors[CONF_SENSORS_TRACKING_DISTANCE]):
                    cv.multi_select(CONF_SENSORS_TRACKING_DISTANCE_KEY_TEXT),
        vol.Required(CONF_SENSORS_ZONE,
                    default=sensors[CONF_SENSORS_ZONE]):
                    cv.multi_select(CONF_SENSORS_ZONE_KEY_TEXT),
        vol.Required(CONF_SENSORS_OTHER,
                    default=sensors[CONF_SENSORS_OTHER]):
                    cv.multi_select(CONF_SENSORS_OTHER_KEY_TEXT),
        # vol.Required(CONF_SENSORS_TRACK_FROM_ZONES,
        #             default=sensors[CONF_SENSORS_TRACK_FROM_ZONES]):
        #             cv.multi_select(CONF_SENSORS_TRACK_FROM_ZONES_KEY_TEXT),
        vol.Required(CONF_SENSORS_MONITORED_DEVICES,
                    default=sensors[CONF_SENSORS_MONITORED_DEVICES]):
                    cv.multi_select(CONF_SENSORS_MONITORED_DEVICES_KEY_TEXT),
        vol.Required(CONF_SENSORS_TRACKING_OTHER,
                    default=sensors[CONF_SENSORS_TRACKING_OTHER]):
                    cv.multi_select(CONF_SENSORS_TRACKING_OTHER_KEY_TEXT),
        vol.Optional(CONF_EXCLUDED_SENSORS,
                    default=self.excluded_sensors):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.excluded_sensors,
                        mode='list', multiple=True)),

        vol.Required('action_items',
                    default=utils_cf.default_action_text('save_stay')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            EXCLUDE SENSORS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_exclude_sensors(self):
    self.actions_list = SENSORS_EXCLUDE_ACTIONS_.copy()

    if self.sensors_list_filter == '?':
        default_action_item = 'filter_sensors'
        filtered_sensors_fname_list = [f"None Displayed - Enter a Filter or `all` \
                        to display all sensors ({len(self.sensors_fname_list)} Sensors)"]
        filtered_sensors_list_default = []
    else:
        default_action_item = 'update_sensor_list'
        self.sensors_list_filter.replace('?', '')
        if self.sensors_list_filter.lower() == 'all':
            filtered_sensors_fname_list = [sensor_fname
                            for sensor_fname in self.sensors_fname_list
                            if sensor_fname not in self.excluded_sensors]
        else:
            filtered_sensors_fname_list = list(set([sensor_fname
                            for sensor_fname in self.sensors_fname_list
                            if ((instr(sensor_fname.lower(), self.sensors_list_filter)
                                and sensor_fname not in self.excluded_sensors))]))

        filtered_sensors_list_default = list(set([sensor_fname
                            for sensor_fname in filtered_sensors_fname_list
                            if sensor_fname in self.excluded_sensors]))

        filtered_sensors_fname_list.sort()
        if filtered_sensors_fname_list == []:
            default_action_item = 'filter_sensors'
            filtered_sensors_fname_list = [f"No Sensors found containing \
                                                '{self.sensors_list_filter}'"]

    return vol.Schema({
        vol.Optional(CONF_EXCLUDED_SENSORS,
                    default=self.excluded_sensors):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.excluded_sensors, mode='list', multiple=True)),
        vol.Optional('filter',
                    default=self.sensors_list_filter):
                    selector.TextSelector(),
        vol.Optional('filtered_sensors',
                    default=filtered_sensors_list_default):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=filtered_sensors_fname_list, mode='list', multiple=True)),

        vol.Required('action_items',
                    default=utils_cf.default_action_text(default_action_item)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })
