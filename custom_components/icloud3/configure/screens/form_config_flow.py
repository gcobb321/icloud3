

from ...global_variables    import GlobalVariables as Gb
from ...const               import (INACTIVE,
                                    CONF_VERSION,
                                    CONF_IC3_DEVICENAME, CONF_TRACKING_MODE,
                                    )

from ...utils.utils         import (list_to_str, list_add, list_del, isnot_empty,
                                    dict_value_to_list, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ...startup             import config_file
from ..                     import utils_cf
from ..const_form_lists     import *
from ...configure           import dashboard_builder as dbb

from homeassistant.helpers  import (selector,
                                    entity_registry as er,
                                    device_registry as dr,)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#     GENERAL CONFIG FLOW FORMS
#
#       - form_config_option_user
#       - form_menu
#       - form_confirm_action
#       - exit_icloud3_configure
#       - form_restart_ha
#       - form_restart_ha_reload_icloud3
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             USER - INITIAL ADD INTEGRATION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_config_option_user(self):


    if (Gb.conf_profile[CONF_VERSION] >=1
            and (isnot_empty(Gb.conf_apple_accounts)
                or isnot_empty(Gb.conf_devices))):
        schema = {
            vol.Required('reset_tracking', default=False): bool,
            # vol.Required('reset_general', default=False): bool,
        }
    else:
        schema = {}

    schema.update({
        vol.Required('continue', default=True): bool
    })

    return vol.Schema(schema)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             MENU
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_menu(self):
    menu_items =    MENU_KEY_TEXT_PAGE_0.copy() if self.menu_page_no == 0 else \
                    MENU_KEY_TEXT_PAGE_1.copy()

    if self.create_device_tracker_sensor_enities_on_exit:
        menu_items['exit'] = MENU_EXIT_ITEMS['exit_add_dev_trkrs_sensors']

    if self.rebuild_ic3db_dashboards:
        dbb.load_ic3db_dashboards_from_ha_data(self)

        if isnot_empty(self.ic3db_Dashboards_by_dbname):
            menu_items['exit'] = MENU_EXIT_ITEMS['exit_update_dashboards']

    if self.menu_page_no == 0:
        device_cnt, inactive_device_cnt, inactive_pct = config_file.device_cnts()
        if (self.username == '' or self.password == ''):
            self.menu_item_selected[0] = 'apple_accounts'
        elif (self.username and self.password
                and (device_cnt == 0 or device_cnt == inactive_device_cnt)):
            self.menu_item_selected[0] = 'device_list'

    return vol.Schema({
        vol.Required("menu_items",
                    default=menu_items[self.menu_item_selected[self.menu_page_no]]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(menu_items), mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             CONFIRM ACTION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_confirm_action(self):
    '''
    confirm_action form uses information in the self.confirm_action{}
    '''

    try:
        actions_list = CONFIRM_ACTIONS.copy()
        actions_list_default = 'confirm_action_no'
        action_desc = self.confirm_action.get('action_desc') or \
                    'Do you want to perform the selected action?'

        return vol.Schema({
            vol.Required('action_desc',
                    default=action_desc):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=[action_desc], mode='list')),
            vol.Required('action_items',
                    default=utils_cf.default_action_text(actions_list_default)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=actions_list, mode='list')),
            })
    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             EXIT ICLOUD3 CONFIGURE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_exit_icloud3_configure_settings(self):
    self.actions_list = EXIT_ICLOUD3_CONFIGURE_SETTINGS.copy()

    device_cnt, inactive_device_cnt, inactive_pct = config_file.device_cnts()
    if inactive_device_cnt == 0:
        self.actions_list['review_inactive_devices'].pop()
    else:
        inactive_devices = [conf_device[CONF_IC3_DEVICENAME]
                    for conf_device in Gb.conf_devices
                    if conf_device[CONF_TRACKING_MODE] == INACTIVE]

        # self.actions_list['review_inactive_devices'].replace(
        self.actions_list[0] = \
            self.actions_list[0].replace(
                    '^add-text^', list_to_str(inactive_devices))

    return vol.Schema({
        vol.Required('action_items',
                    default=utils_cf.default_action_text('exit')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })
