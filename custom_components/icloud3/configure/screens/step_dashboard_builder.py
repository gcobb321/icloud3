

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

    def initialize_dashboard_builder_variables(self):
        '''
        Initialize the variables used by the Dashboard Builder screen. Called from the
        flow handler's initialize_options (the mixin's __init__ would never be run).
        '''
        self.db_templates                   = {}    # iCloud3 device templates from icloud3/dashboard folder
        self.db_templates_used              = []    # Templates used in master-dashboard template
        self.master_dashboard               = {}    # Master Dashboard dictionary (json str --> dict)
        self.dashboards                     = []    # List of dashboards (lovelace.icloud3_xxx files) in conig./storage)
        self.ic3db_Dashboards_by_dbname     = {}    # HA Dashboard by dashboard name for Dashboards with Device-x available
        self.AllDashboards_by_dbname        = {}    # All HA Dashboard objects by dashboard name
        self.dbname                         = ''    # Dashboard  being created or updates
        self.Dashboard                      = None

        # These items are extracted from the main view when the dashboard is loaded. They are used to build to
        # selection list on the dashboard form
        self.main_view_extracted_dnames_by_dbname = {}  # Devicenames on the Main view of the dashboard
        self.main_view_extracted_fnames_by_dbname = {}  # Devices on the Main view of the dashboard

        # These items are set in config_flow dashboard form and passed to the dashboard functions when a dashboard
        # is recreated
        self.ui_main_view_style          = ''    #
        self.ui_selected_dbname          = ADD   # Dashboard currently selected on Dashboard Builder screen
        self.ui_main_view_dnames         = []    # Devices to be inserted into the dashboard layout
        self.dbf_dashboard_key_text      = {}    # db form device selection dictionary
        self.dbf_dashboard_icons_msg     = ''    # db form '<ha-icon..> title, ...' reference line

        # Main View Info from the main_view_info_str on the Events Log view
        # These items are loaded when the ic3db dashboards are loaded. They are used to set ui_xxx values when
        # a device is added or deleted and the dashboards are recreated
        self.main_view_info_style_by_dbname     = {}  # Devices on the Main view of the dashboard
        self.main_view_info_dnames_by_dbname    = {}  # Devices on the Main view of the dashboard
        self.main_view_dbfile_length_by_dbname  = {}  # Length of the main view str from the Lovelace db file
        self.main_view_created_length_by_dbname = {}  # Length of the main view str right now
        self.main_view_infomsg_length_by_dbname = {}  # Length of the main view str right now

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
                                        description_placeholders={'db_icons': self.dbf_dashboard_icons_msg},
                                        errors=self.errors)

        user_input = utils_cf.option_text_to_parm(user_input, 'selected_dashboard', self.dbf_dashboard_key_text)
        user_input = utils_cf.option_text_to_parm(user_input, 'main_view_style', DASHBOARD_MAIN_VIEW_STYLE_OPTIONS)

        utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        self.ui_selected_dbname = user_input.get('selected_dashboard', ADD)
        if self.ui_selected_dbname == ADD:
            action_item = 'create_dashboard'

        self.ui_main_view_style  = user_input['main_view_style']
        self.ui_main_view_dnames = [devicename
                                        for devicename in user_input['main_view_devices']
                                        if devicename.startswith('.') is False]
        self.errors = {}
        self._validate_dashboard_user_input(action_item, user_input)
        if utils_cf.any_errors(self):
            action_item = ''

        user_input['action_item'] = action_item

        if self.ui_selected_dbname == ADD:
            await dbb.create_dashboard(self)
        else:
            await dbb.update_dashboard(self)

        await dbb.build_existing_dashboards_selection_list(self)
        dbb.select_available_dashboard(self)

        return self.async_show_form(step_id= 'dashboard_builder',
                            data_schema=forms.form_dashboard_builder(self),
                            description_placeholders={'db_icons': self.dbf_dashboard_icons_msg},
                            errors=self.errors)

# #-------------------------------------------------------------------------------------------
    def _validate_dashboard_user_input(self, action_item, user_input):
        if is_empty(self.ui_main_view_dnames):
            self.ui_main_view_dnames = ['Display All']
