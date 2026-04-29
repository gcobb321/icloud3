

from ...global_variables    import GlobalVariables as Gb
from ...const               import (INACTIVE,
                                    CONF_VERSION,
                                    CONF_IC3_DEVICENAME, CONF_TRACKING_MODE,
                                    )

from ...utils.utils         import (list_to_str, list_add, list_del, isnot_empty, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

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
#       - form_restart_icloud3
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
    menu_title = MENU_PAGE_TITLE[self.menu_page_no]
    menu_action_items = MENU_ACTION_ITEMS.copy()
    if self.create_device_tracker_sensor_enities_on_exit:
        list_del(menu_action_items, MENU_KEY_TEXT['exit'])
        list_add(menu_action_items, MENU_KEY_TEXT['exit_add_dev_trkrs_sensors'])

    if self.rebuild_ic3db_dashboards:
        dbb.load_ic3db_dashboards_from_ha_data(self)

        if isnot_empty(self.ic3db_Dashboards_by_dbname):
            list_del(menu_action_items, MENU_KEY_TEXT['exit'])
            list_add(menu_action_items, MENU_KEY_TEXT['exit_update_dashboards'])

    if self.menu_page_no == 0:
        menu_key_text  = MENU_KEY_TEXT_PAGE_0
        menu_action_items[1] = MENU_KEY_TEXT['next_page_1']

        if (self.username == '' or self.password == ''):
            self.menu_item_selected[0] = MENU_KEY_TEXT['apple_accounts']
        elif (self.username and self.password
                and (self._device_cnt() == 0 or self._device_cnt() == self._inactive_device_cnt())):
            self.menu_item_selected[0] = MENU_KEY_TEXT['device_list']
    else:
        menu_key_text  = MENU_KEY_TEXT_PAGE_1
        menu_action_items[1] = MENU_KEY_TEXT['next_page_0']

    return vol.Schema({
        vol.Required("menu_items",
                    default=self.menu_item_selected[self.menu_page_no]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=menu_key_text, mode='list')),
        vol.Required("action_items",
                    default=menu_action_items[0]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=menu_action_items, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             CONFIRM ACTION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_confirm_action(self, action_desc=None):
    '''
    confirm_action form uses information in the self.confirm_action{}
    '''

    actions_list = CONFIRM_ACTIONS.copy()
    actions_list_default = 'confirm_action_no'
    action_desc = action_desc if action_desc is not None else\
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


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             RESTART ICLOUD3
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_restart_icloud3(self):
    self.actions_list = []
    restart_default='restart_ic3_now'

    if 'restart_ha' in self.config_parms_update_control:
        restart_default='restart_ha'
        self.actions_list.append(ACTION_LIST_OPTIONS['restart_ha'])
    else:
        restart_default='restart_ic3_now'
        self.actions_list.append(ACTION_LIST_OPTIONS['restart_ic3_now'])

    self.actions_list.append(ACTION_LIST_OPTIONS['restart_ic3_later'])

    actions_list_default = utils_cf.default_action_text(restart_default)
    if self._inactive_device_cnt() > 0:
        inactive_devices = [conf_device[CONF_IC3_DEVICENAME]
                    for conf_device in Gb.conf_devices
                    if conf_device[CONF_TRACKING_MODE] == INACTIVE]
        inactive_devices_list = \
            ACTION_LIST_OPTIONS['review_inactive_devices'].replace(
                    '^add-text^', list_to_str(inactive_devices))
        self.actions_list.append(inactive_devices_list)

    self.actions_list.append(ACTION_LIST_OPTIONS['goto_menu'])

    return vol.Schema({
        vol.Required('action_items',
                    default=actions_list_default):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            RESTART HA IC3
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_restart_ha(self):

    self.actions_list = []
    self.actions_list.append(ACTION_LIST_OPTIONS['restart_ha'])
    # self.actions_list.append(ACTION_LIST_OPTIONS['restart_icloud3'])
    self.actions_list.append(ACTION_LIST_OPTIONS['goto_menu'])
    if self.create_device_tracker_sensor_enities_on_exit:
        self.actions_list.append(ACTION_LIST_OPTIONS['exit_add_dev_trkrs_sensors'])
    elif self.rebuild_ic3db_dashboards:
        self.actions_list.append(ACTION_LIST_OPTIONS['exit_update_dashboards'])
    else:
        self.actions_list.append(ACTION_LIST_OPTIONS['exit'])

    actions_list_default = utils_cf.default_action_text('restart_ha')

    return vol.Schema({
        vol.Required('action_items',
                    default=actions_list_default):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            RESTART HA, RELOAD ICLOUD3
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_restart_ha_reload_icloud3(self):

    self.actions_list = []
    self.actions_list.append(ACTION_LIST_OPTIONS['reload_icloud3'])
    self.actions_list.append(ACTION_LIST_OPTIONS['restart_ha'])
    self.actions_list.append(ACTION_LIST_OPTIONS['exit'])

    actions_list_default = utils_cf.default_action_text('exit')

    return vol.Schema({
        vol.Required('action_items',
                    default=actions_list_default):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
                })
