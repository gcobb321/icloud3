

from ...global_variables    import GlobalVariables as Gb
from ...const_config        import (HOME_DISTANCE, CONF_SENSORS_MONITORED_DEVICES,
                                    CONF_SENSORS_DEVICE, CONF_SENSORS_TRACKING_UPDATE,
                                    CONF_SENSORS_TRACKING_TIME, CONF_SENSORS_TRACKING_DISTANCE,
                                    CONF_SENSORS_TRACKING_OTHER, CONF_SENSORS_ZONE,
                                    CONF_SENSORS_OTHER, CONF_EXCLUDED_SENSORS, )

from ...utils.utils         import (instr, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..                     import utils_cf
from ..const_form_lists     import *

from homeassistant.helpers  import selector
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
    self.set_default_sensors(Gb.conf_sensors)
    sensors = user_input if user_input is not None else Gb.conf_sensors.copy()

    if HOME_DISTANCE not in Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE]:
        Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)

    schema = {
        vol.Required(CONF_SENSORS_DEVICE,
                    default=_selectable_sensors(CONF_SENSORS_DEVICE, sensors[CONF_SENSORS_DEVICE])):
                    utils_cf.select(_selectable_sensors(CONF_SENSORS_DEVICE, CONF_SENSORS_DEVICE_KEY_TEXT), translation_key='sensor', mode='list', multiple=True),
        vol.Required(CONF_SENSORS_TRACKING_UPDATE,
                    default=_selectable_sensors(CONF_SENSORS_TRACKING_UPDATE, sensors[CONF_SENSORS_TRACKING_UPDATE])):
                    utils_cf.select(_selectable_sensors(CONF_SENSORS_TRACKING_UPDATE, CONF_SENSORS_TRACKING_UPDATE_KEY_TEXT), translation_key='sensor', mode='list', multiple=True),
        vol.Required(CONF_SENSORS_TRACKING_TIME,
                    default=_selectable_sensors(CONF_SENSORS_TRACKING_TIME, sensors[CONF_SENSORS_TRACKING_TIME])):
                    utils_cf.select(_selectable_sensors(CONF_SENSORS_TRACKING_TIME, CONF_SENSORS_TRACKING_TIME_KEY_TEXT), translation_key='sensor', mode='list', multiple=True),
        vol.Required(CONF_SENSORS_TRACKING_DISTANCE,
                    default=_selectable_sensors(CONF_SENSORS_TRACKING_DISTANCE, sensors[CONF_SENSORS_TRACKING_DISTANCE])):
                    utils_cf.select(_selectable_sensors(CONF_SENSORS_TRACKING_DISTANCE, CONF_SENSORS_TRACKING_DISTANCE_KEY_TEXT), translation_key='sensor', mode='list', multiple=True),
        vol.Required(CONF_SENSORS_ZONE,
                    default=sensors[CONF_SENSORS_ZONE]):
                    utils_cf.select(CONF_SENSORS_ZONE_KEY_TEXT, translation_key='sensor', mode='list', multiple=True),
        vol.Required(CONF_SENSORS_OTHER,
                    default=sensors[CONF_SENSORS_OTHER]):
                    utils_cf.select(CONF_SENSORS_OTHER_KEY_TEXT, translation_key='sensor', mode='list', multiple=True),
        # vol.Required(CONF_SENSORS_TRACK_FROM_ZONES,
        #             default=sensors[CONF_SENSORS_TRACK_FROM_ZONES]):
        #             utils_cf.select(CONF_SENSORS_TRACK_FROM_ZONES_KEY_TEXT, translation_key='sensor', mode='list', multiple=True),
        vol.Required(CONF_SENSORS_MONITORED_DEVICES,
                    default=_selectable_sensors(CONF_SENSORS_MONITORED_DEVICES, sensors[CONF_SENSORS_MONITORED_DEVICES])):
                    utils_cf.select(_selectable_sensors(CONF_SENSORS_MONITORED_DEVICES, CONF_SENSORS_MONITORED_DEVICES_KEY_TEXT), translation_key='sensor', mode='list', multiple=True),
        vol.Required(CONF_SENSORS_TRACKING_OTHER,
                    default=sensors[CONF_SENSORS_TRACKING_OTHER]):
                    utils_cf.select(CONF_SENSORS_TRACKING_OTHER_KEY_TEXT, translation_key='sensor', mode='list', multiple=True),
        }
    if self.excluded_sensors:
        schema[vol.Optional(CONF_EXCLUDED_SENSORS, default=self.excluded_sensors)] = \
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.excluded_sensors, mode='list', multiple=True))

    return utils_cf.sectioned_schema(self, schema, [
            ('device_section', [CONF_SENSORS_DEVICE], True),
            ('location_update_section', [CONF_SENSORS_TRACKING_UPDATE], False),
            ('time_section', [CONF_SENSORS_TRACKING_TIME], False),
            ('distance_section', [CONF_SENSORS_TRACKING_DISTANCE], False),
            ('zone_section', [CONF_SENSORS_ZONE], False),
            ('monitored_devices_section', [CONF_SENSORS_MONITORED_DEVICES], False),
            ('other_section', [CONF_SENSORS_OTHER, CONF_SENSORS_TRACKING_OTHER, CONF_EXCLUDED_SENSORS], False),
            ],
            utils_cf.submit_back_field(self, 'save', 'cancel_goto_menu', utils_cf.menu_name(self),
                    other_actions={'select_default_sensors': utils_cf.tr('select_default_sensors')}))

def _selectable_sensors(sensor_group, sensors):
    '''
    The sensors (list or {sensor: text}) without the ones that are always created. They
    are added when the sensors are saved (set_default_sensors).
    '''
    always_created = ALWAYS_CREATED_SENSORS.get(sensor_group, [])
    if isinstance(sensors, dict):
        return {sensor: text for sensor, text in sensors.items() if sensor not in always_created}
    return [sensor for sensor in sensors if sensor not in always_created]

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            EXCLUDE SENSORS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_exclude_sensors(self):
    '''
    The Excluded sensors and Sensors fields are only on the form when they have sensors,
    the description says why they are not.

    Return:
        The form schema and the description placeholders
    '''
    sensors_filter = self.sensors_list_filter
    if sensors_filter == '':
        filtered_sensors_fname_list = []
        filter_msg = utils_cf.tr('exclude_sensors_enter_filter', count=len(self.sensors_fname_list))
    else:
        filtered_sensors_fname_list = sorted({sensor_fname
                            for sensor_fname in self.sensors_fname_list
                            if ((sensors_filter == 'all' or instr(sensor_fname.lower(), sensors_filter))
                                and sensor_fname not in self.excluded_sensors)})
        filter_msg = ('' if filtered_sensors_fname_list else
                        utils_cf.tr('exclude_sensors_none_found', filter=sensors_filter))

    excluded_msg = '' if self.excluded_sensors else utils_cf.tr('exclude_sensors_none_excluded')

    schema = {}
    if self.excluded_sensors:
        schema[vol.Optional(CONF_EXCLUDED_SENSORS, default=self.excluded_sensors)] = \
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.excluded_sensors, mode='list', multiple=True))
    schema[vol.Optional('filter', default=sensors_filter)] = selector.TextSelector()
    if filtered_sensors_fname_list:
        schema[vol.Optional('filtered_sensors', default=[])] = \
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=filtered_sensors_fname_list, mode='list', multiple=True))
    schema.update(utils_cf.submit_back_field(self, 'update_sensor_list', 'cancel_goto_menu',
                    utils_cf.menu_name(self),
                    other_actions={'save_excluded_sensors':
                        utils_cf.tr('action_save_excluded_sensors',
                            dest=utils_cf.destination_name(utils_cf.menu_name(self)))}))

    return vol.Schema(schema), {'excluded_msg': excluded_msg, 'filter_msg': filter_msg}
