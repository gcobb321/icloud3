

from ...global_variables    import GlobalVariables as Gb
from ...utils.utils         import (is_empty, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from .                      import form_dashboard_builder as forms
from ..                     import utils_cf
from ..                     import dashboard_builder as dbb
from ..const_form_lists     import *


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           DASHBOARD BUILDER CONFIG FLOW STEPS
#
#           - async_step_dashboard_builder
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OptionsFlow_DashboardBuilder_Steps:



    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #            DASHBOARD BUILDER
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_dashboard_builder(self, user_input=None, errors=None):
        self.step_id = 'dashboard_builder'
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)


        await dbb.build_existing_dashboards_selection_list(self)
        dbb.select_available_dashboard(self)
        utils_cf.log_step_info(self, user_input, action_item)

        if user_input is None:
            return self.async_show_form(step_id='dashboard_builder',
                                        data_schema=forms.form_dashboard_builder(self),
                                        errors=self.errors)

        user_input = utils_cf.option_text_to_parm(user_input, 'selected_dashboard', self.dbf_dashboard_key_text)
        user_input = utils_cf.option_text_to_parm(user_input, 'main_view_style', DASHBOARD_MAIN_VIEW_STYLE_OPTIONS)

        utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        self.ui_selected_dbname = user_input.get('selected_dashboard', 'add')
        if self.ui_selected_dbname == 'add':
            action_item == 'create_dashboard'

        self.ui_main_view_style  = user_input['main_view_style']
        self.ui_main_view_dnames = [devicename
                                        for devicename in user_input['main_view_devices']
                                        if devicename.startswith('.') is False]
        self.errors = {}
        self._validate_dashboard_user_input(action_item, user_input)
        if utils_cf.any_errors(self):
            action_item = ''

        user_input['action_item'] = action_item

        await dbb.update_or_create_dashboard(self)
        await dbb.build_existing_dashboards_selection_list(self)
        dbb.select_available_dashboard(self)

        return self.async_show_form(step_id= 'dashboard_builder',
                            data_schema=forms.form_dashboard_builder(self),
                            errors=self.errors)

# #-------------------------------------------------------------------------------------------
    def _validate_dashboard_user_input(self, action_item, user_input):
        if is_empty(self.ui_main_view_dnames):
            self.ui_main_view_dnames = ['Display All']
