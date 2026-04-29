

from ...global_variables    import GlobalVariables as Gb
from ...utils.utils         import (dict_value_to_list, six_item_dict, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..                     import utils_cf
from ..                     import selection_lists as lists
from ..const_form_lists     import *

from homeassistant.helpers  import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#     DASHBOARD BUILDER FORMS
#
#       - form_dashboard_builder
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           DASHBOARD BUILDER FORM
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_dashboard_builder(self):
    dbname = self.ui_selected_dbname
    self.actions_list = []
    default_action = 'create_dashboard'
    self.actions_list.append(ACTION_LIST_OPTIONS['create_dashboard'])
    self.actions_list.append(ACTION_LIST_OPTIONS['cancel_goto_menu'])

    # Set default dashboard to current dashboard, the previous dashboard or 'add'
    default_dbname = self.dbf_dashboard_key_text[dbname]

    default_main_view_style = DASHBOARD_MAIN_VIEW_STYLE_OPTIONS[RESULT_SUMMARY]

    self.dbf_main_view_devices_key_text = {}
    self.dbf_main_view_devices_key_text.update(DASHBOARD_MAIN_VIEW_DEVICES_BASE)
    self.dbf_main_view_devices_key_text.update(lists.devices_selection_list())

    self.ui_main_view_dnames = [ALL_DEVICES]

    return vol.Schema({
        vol.Required('selected_dashboard',
                    default=default_dbname):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.dbf_dashboard_key_text), mode='list')),
        vol.Required('main_view_style',
                    default=default_main_view_style):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(DASHBOARD_MAIN_VIEW_STYLE_OPTIONS), mode='dropdown')),
        vol.Required('main_view_devices',
                    default=self.ui_main_view_dnames):
                    cv.multi_select(six_item_dict(self.dbf_main_view_devices_key_text)),

        vol.Required('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(options=self.actions_list, mode='list')),
        })
