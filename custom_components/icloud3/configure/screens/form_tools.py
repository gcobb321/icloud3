

from ...global_variables    import GlobalVariables as Gb
from ...const               import (INACTIVE, )
from ...const_config        import (CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES, CONF_IC3_DEVICENAME,
                                    CONF_TRACKING_MODE, )
from ...const_char          import (DOTS, )

from ...utils.utils         import (list_to_str, list_add, list_del,
                                    is_empty, six_item_dict, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..const_form_lists     import *
from ...utils               import entity_reg_util as er_util

from ..                     import utils_cf
from ..                     import selection_lists as lists

from homeassistant.helpers  import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#     TOOLS FORMS
#
#       - form_cleanup_entity_registry
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           LOG LEVEL
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_log_level(self):
    lists.build_log_level_devices_list(self)
    if Gb.conf_general[CONF_LOG_LEVEL_DEVICES] != 'all':
        Gb.conf_general[CONF_LOG_LEVEL_DEVICES] = [
                                    devicename for devicename in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]
                                    if devicename in Gb.Devices_by_devicename]
    if is_empty(Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
        Gb.conf_general[CONF_LOG_LEVEL_DEVICES] = ['all']

    return vol.Schema({
        vol.Optional(CONF_LOG_LEVEL,
                    default=utils_cf.option_parm_key(self, CONF_LOG_LEVEL, LOG_LEVEL_OPTIONS)):
                    utils_cf.select(LOG_LEVEL_OPTIONS, translation_key='log_level', mode='dropdown'),
        vol.Required(CONF_LOG_LEVEL_DEVICES,
                    default=Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
                    cv.multi_select(six_item_dict(self.log_level_devices_key_text)),

        **utils_cf.submit_back_field(self, 'save_menu', 'cancel_goto_menu', 'tools'),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           CLEANUP E#NTITY REGISTRY
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_cleanup_entity_registry(self, user_input=None):
    if user_input is None:
        er_util.scan_entity_reg_for_icloud3_items()

    # Build the base form_entities that will be displaed on the form
    #   - form_entoties['deleted'] = keys to each device
    selected_devicename_by_status = {}     # Divice display lines for each error type
    checked_device_sensors        = {}     # Checked devices for each error type
    for status, devicename_sensors in Gb.entity_reg_items_by_status.items():
        checked_device_sensors[status] = []     # Checked devices for each error type
        selected_devicename_by_status[status] = []
        if is_empty(devicename_sensors):
            continue

        for devicename, device_sensors in devicename_sensors.items():
            sensors = [sensor for sensor in device_sensors.keys()]
            sensors_str = list_to_str(sensors)
            if self.tools_cleanup_er_sensor_all:
                hdr_bar = f"{'_'*100}"
            else:
                hdr_bar = ''
                if len(sensors_str) > 130-len(devicename):
                    sensors_str = f"{sensors_str[0:(130-len(devicename))]}, {DOTS}"

            if self.tools_entity_reg_check_all:
                list_add(checked_device_sensors[status], devicename)


            if (sensors_str.startswith('.dr:')
                    and len(device_sensors) == 1):
                device_or_sensor = utils_cf.tr('er_device')
            else:
                device_or_sensor = utils_cf.tr('er_sensors')

            devicename_msg =  ( f"{hdr_bar} {devicename} · "
                                f"{len(device_sensors)} {device_or_sensor} ({sensors_str})")

            item = {'value': devicename, 'label': devicename_msg}
            selected_devicename_by_status[status].append(item)

    self.tools_entity_reg_check_all = None

    # ENTITY_STATUS_TYPES = ['active', 'inactive', 'other', 'disabled', 'orphaned',
    #                           'suffix_error', 'deleted_devices', 'deleted_sensors']
    schema = {}
    for status in er_util.ENTITY_STATUS_TYPES:
        if status not in selected_devicename_by_status:
            continue

        schema.update({
            vol.Required(status,
                    default=checked_device_sensors[status]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=selected_devicename_by_status[status],
                        multiple=True,
                        mode='list'))})

    # Select all and Show the sensor lists redisplay the screen
    other_actions = {
            'select_all': utils_cf.tr('action_select_all'),
            'toggle_sensor_lists': utils_cf.tr('action_show_short_sensor_lists'
                                                if self.tools_cleanup_er_sensor_all else
                                            'action_show_full_sensor_lists')}
    schema.update({
        **utils_cf.submit_back_field(self, 'delete_device_sensors', 'goto_previous', 'tools',
                                        other_actions=other_actions),})

    return vol.Schema(schema)
