

from ...global_variables    import GlobalVariables as Gb
from ...const_config        import (CF_GENERAL, CONF_ANALYTICS_ENABLED, CONF_ANALYTICS_SENT_DATE,
                                    CONF_ANALYTICS_COMMENT, )

from ...utils.utils         import (list_to_str, list_add, list_del,
                                    is_empty, dict_value_to_list, six_item_dict, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..const_form_lists     import *
from ...utils               import entity_reg_util as er_util

from ...support             import analytics
from ..                     import utils_cf
from ..                     import selection_lists as lists

from homeassistant.helpers  import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#     ANALYTICS FORMS
#       - form_analytics
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           ANALYTICS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_analytics(self, user_input):
    self.actions_list = ANALYTICS_ACTIONS.copy()
    self.actions_list.extend(ACTION_LIST_ITEMS_SAVE_MENU)
    default_action = 'save'

    ah_default = [ANALYTICS_ENABLED_HDR] if Gb.analytics_enabled else []
    comment    = ' ' if Gb.conf_general[CONF_ANALYTICS_COMMENT].strip() == '' else \
                    Gb.conf_general[CONF_ANALYTICS_COMMENT]

    return vol.Schema({
        vol.Optional(CONF_ANALYTICS_ENABLED,
                    default=ah_default):
                    cv.multi_select([ANALYTICS_ENABLED_HDR]),
        vol.Optional(CONF_ANALYTICS_COMMENT,
                    default=comment):
                    selector.TextSelector(),

        vol.Required('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           ANALYTICS REPORTS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_analytics_reports(self, user_input):
    self.actions_list = ANALYTICS_REPORTS_ACTIONS.copy()
    default_action = 'run_report'

    analytics.build_analytics_report_names_list(self)

    report_names = dict_value_to_list(self.analytic_reports_by_name)
    if is_empty(self.analytic_reports_by_name):
        default_report = 'none'
    elif self.report_selected in self.analytic_reports_by_name:
        default_report = self.report_selected
    else:
        default_report = list(self.analytic_reports_by_name.keys())[0]

    return vol.Schema({
        vol.Optional('report_selected',
                    default=self.analytic_reports_by_name[default_report]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=report_names,
                        mode='dropdown')),

        vol.Required('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })
