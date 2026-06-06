

from ...global_variables    import GlobalVariables as Gb
from ...const               import (DOTS,
                                    CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES,
                                    )

from ...utils.utils         import (list_to_str, list_add, list_del,
                                    is_empty, dict_value_to_list, six_item_dict, )
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
#       - form_tools
#       - form_tools_entity_registry_cleanup
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           TOOLS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_tools(self):
    self.actions_list = TOOL_LIST_ITEMS.copy()
    default_action = 'goto_menu'

    lists.build_log_level_devices_list(self)
    if Gb.conf_general[CONF_LOG_LEVEL_DEVICES] != 'all':
        Gb.conf_general[CONF_LOG_LEVEL_DEVICES] = [
                                    devicename for devicename in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]
                                    if devicename in Gb.Devices_by_devicename]
    if is_empty(Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
        Gb.conf_general[CONF_LOG_LEVEL_DEVICES] = ['all']

    return vol.Schema({
        vol.Optional(CONF_LOG_LEVEL,
                    default=utils_cf.option_parm_to_text(self, CONF_LOG_LEVEL, LOG_LEVEL_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(LOG_LEVEL_OPTIONS), mode='dropdown')),
        vol.Required(CONF_LOG_LEVEL_DEVICES,
                    default=Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
                    cv.multi_select(six_item_dict(self.log_level_devices_key_text)),

        vol.Required('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           TOOLS ENTITY REGISTRY MAINTENANCE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_tools_entity_registry_cleanup(self, user_input=None):
    self.actions_list = ACTIONS_REPAIR_ENTITY_ERRORS.copy()
    self.actions_list_default = 'delete_device_sensors'
    if self.tools_entity_reg_check_all:
        list_del(self.actions_list, 'check_all')
    else:
        list_del(self.actions_list, 'check_none')
    if self.tools_entity_reg_show_sensor_names_all:
        list_del(self.actions_list, 'show_sensor_names_all')
    else:
        list_del(self.actions_list, 'show_sensor_names_some')

    if user_input is None:
        self.repair_entity_show_check_all = False
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
            if self.tools_entity_reg_show_sensor_names_all:
                hdr_bar = f"{'_'*100}"
            else:
                hdr_bar = ''
                if len(sensors_str) > 140-len(devicename):
                    sensors_str = f"{sensors_str[0:(140-len(devicename))]}, {DOTS}"

            if self.tools_entity_reg_check_all:
                list_add(checked_device_sensors[status], devicename)


            if (sensors_str.startswith('.dr:')
                    and len(device_sensors) == 1):
                device_or_sensor = 'Device'
            else:
                device_or_sensor = 'Sensors'

            devicename_msg =  ( f"{hdr_bar} {devicename.upper()} > "
                                f"{len(device_sensors)} {device_or_sensor} ({sensors_str})")

            item = {'value': devicename, 'label': devicename_msg}
            selected_devicename_by_status[status].append(item)

    self.tools_entity_reg_check_all = None

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

    schema.update({
        vol.Required('action_items',
                default=self.actions_list_default):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=utils_cf.actions_list(self), mode='list')),})

    return vol.Schema(schema)
