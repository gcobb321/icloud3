

from .global_variables      import GlobalVariables as Gb
from .const                 import (DOMAIN, ICLOUD3, DATETIME_FORMAT, STORAGE_DIR,
                                    ICLOUD, MOBAPP, NO_MOBAPP, RARROW, NL_DOT, DOT, NL,
                                    TRACK, MONITOR, INACTIVE,
                                    CONF_VERSION, CONF_LOG_LEVEL,
                                    CONF_APPLE_ACCOUNTS,
                                    CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES,
                                    CONF_DATA_SOURCE,
                                    CONF_IC3_DEVICENAME, CONF_FNAME, CONF_TRACKING_MODE,
                                    CONF_PARAMETER_TIME_STR, CONF_PARAMETER_FLOAT,
                                    CF_APPLE_ACCOUNTS, CF_DEVICES,  CF_TRACKING, CF_GENERAL,
                                    DEFAULT_APPLE_ACCOUNT_CONF
                                    )

from .utils.utils           import (instr, is_number, is_empty, isnot_empty, list_to_str, str_to_list,
                                    is_running_in_event_loop, is_between, list_del, list_add,
                                    sort_dict_by_values, username_id,
                                    encode_password, decode_password, )
from .utils.messaging       import (log_exception, log_debug_msg, log_info_msg, add_log_file_filter,
                                    _log, _evlog, more_info, write_config_file_to_ic3log, close_ic3log_file,
                                    post_event, post_alert, post_monitor_msg, post_greenbar_msg,
                                    update_alert_sensor, )
from .utils.time_util       import (time_now_secs, )

from .                      import sensor as ic3_sensor
from .                      import device_tracker as ic3_device_tracker
from .startup               import start_ic3
from .startup               import config_file
from .support               import service_handler
from .utils                 import file_io

from .configure.screens     import form_config_flow     as forms
from .configure.screens     import form_apple_acct      as forms_aa
from .configure.screens     import form_icloud3_device  as forms_ic3_dev
from .configure.screens     import form_reauth          as forms_reauth
from .configure             import utils_cf
from .configure             import dashboard_builder as dbb

from .configure.const_form_lists      import *
from .configure.screens.step_apple_acct       import OptionsFlow_AppleAccount_Steps
from .configure.screens.step_reauth           import OptionsFlow_Reauth_Steps
from .configure.screens.step_icloud3_device   import OptionsFlow_iCloud3Device_Steps
from .configure.screens.step_sensors          import OptionsFlow_Sensors_Steps
from .configure.screens.step_tools            import OptionsFlow_Tools_Steps
from .configure.screens.step_dashboard_builder import OptionsFlow_DashboardBuilder_Steps
from .configure.screens.step_parameters       import OptionsFlow_Parameters_Steps


import logging
_CF_LOGGER = logging.getLogger("icloud3-cf")

#--------------------------------------------------------------------
from homeassistant                  import config_entries, data_entry_flow
from homeassistant.config_entries   import ConfigEntry as config_entry
from homeassistant.data_entry_flow  import FlowHandler, FlowResult
from homeassistant.core             import callback, HomeAssistant

import homeassistant.util.dt as dt_util
import voluptuous as vol

CONFIG_UPDATE_COMPLETE_MSG = 'iCloud3 Configuration Update Complete'

# #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                     ICLOUD3 CONFIG FLOW - INITIAL SETUP
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class iCloud3_ConfigFlow(config_entries.ConfigFlow, FlowHandler,
                            OptionsFlow_Reauth_Steps,
                            domain=DOMAIN):
    '''
    The config_flow_reauth orange button is activitated via a call to:
        Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)
    This is done in:
        > start_ic3.py if an apple acct needs to be authorized
        > step_reauth.py when the request_auth_code action is selected
    '''


    VERSION = 1
    def __init__(self):
        self.is_from_config_flow_handler    = True
        self.menu_item                      = 'config_flow_reauth'
        self.step_id                        = 'config_flow'     # step_id for the window displayed
        self.errors                         = {}     # Errors en.json error key
        self.errors_info_msg                = None   # dict that maps to a en.json msg for a 'description_placeholders' in the show_form stmt
        self.OptFlow                        = None
        self.data_source                    = ICLOUD

        # Items used in the REAUTH handler
        self.is_reauth_initialized          = False  # The reauth step has been initialized by _initialize_config_flow_reauth

        self.ha_initial_setup               = True
        self.username                       = ''
        self.AppleAcct                      = None
        # self.aa_reauth_username             = ''
        self.header_msg                     = ''
        self.conf_apple_acct                = {}
        self.aa_idx                         = 0
        self.apple_acct_items_by_username   = {}
        self.apple_acct_auth_items_by_username = {}
        self.is_reauth_needed            = False
        self.aa_auth_methods_by_auth_method = {}

        Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()


    def form_msg(self):
        return f"Form-{self.step_id}, Errors-{self.errors}"

#----------------------------------------------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        '''
        Create the options flow handler for iCloud3. This is called when the iCloud3 > Configure
        is selected on the Devices & Services screen, not when HA or iCloud3 is loaded
        '''
        if Gb.OptionsFlowHandler is None:
            Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()
        return Gb.OptionsFlowHandler

#----------------------------------------------------------------------
    @callback
    def async_remove(self) -> None:
        """HA calls this (sync @callback) when the user clicks 'X' to close the config flow."""
        self.flow_closed()

    def flow_closed(self) -> None:
        """Called when the user dismisses the config flow with 'X'."""
        # return self._reauth_goto_previous(exit_by_x_click=True)
        return self.ha_reconfigure_reauth_exit(exit_by_x_click=True)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            USER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_user(self, user_input=None):
        '''
        Invoked when a user initiates a '+ Add Integration' on the Integerations screen

        self.handler = 'icloud3' from domain name in manifest.json
        '''
        _OptFlow = Gb.OptionsFlowHandler
        disabled_by = added_datetime = None

        try:
            # Get the iCloud3 config_entry info. This will fail if it has not been installed.
            config_entries = self.hass.config_entries.async_entries(self.handler)
            config_entry   = config_entries[0]
            disabled_by    = config_entry.disabled_by
            added_datetime = config_entry.data.get('added')

        except Exception as err:
            pass

        errors = {}

        await self.async_set_unique_id(DOMAIN)

        if disabled_by:
            _CF_LOGGER.info(f"Aborting iCloud3 Integration, Already set up but Disabled")
            return self.async_abort(reason="disabled")

        if self.hass.data.get(DOMAIN):
            _CF_LOGGER.info(f"Aborting iCloud3 Integration, Already set up")
            return self.async_abort(reason="already_configured")

        # If Gb.hass is None, then the iCloud3 Integration is being added for the first itme and
        # __init__ has not run yet. Do the preliminary initialization and v2-v3 migration check
        # and migrate the data if needed from config_ic3.yaml.
        if Gb.hass is None:
            Gb.hass = self.hass

            start_ic3.initialize_directory_filenames()
            await config_file.async_load_icloud3_configuration_file()
            start_ic3.initialize_data_source_variables()

        await file_io.async_make_directory(Gb.icloud_session_directory)

        _CF_LOGGER.info(f"Config_Flow Added Integration-{Gb.ha_device_id_by_devicename=}")

        if user_input is not None:
            _CF_LOGGER.info(f"Added iCloud3 Integration")

            if user_input.get('reset_tracking', False):
                _CF_LOGGER.info(f"iCloud3 Reinstallation, Initialize Apple Accounts and Device Configuration")
                _OptFlow.reset_icloud3_config_file_tracking()
                await _OptFlow.delete_all_files_and_remove_directory(Gb.icloud_cookies_directory)

                Gb.config_parms_update_control = ['tracking', 'restart']
                await config_file.async_write_icloud3_configuration_file()

            data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}

            return self.async_create_entry(title=CONFIG_UPDATE_COMPLETE_MSG, data=data)

        return self.async_show_form(step_id="user",
                                    data_schema=forms.form_config_option_user(self),
                                    errors=errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH  --> SEE STEP_REAUTH
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def _initialize_config_flow_reauth(self):
        '''
        Initialize the self.reauth step for the config_flow.
        This is called from self.reauth
        '''
        self.step_id = 'Init Reauth-Config Flow'
        utils_cf.log_step_info(self, '', 'initialize')
        try:
            self.is_reauth_initialized = True
            self.data_source = Gb.conf_tracking.get(CONF_DATA_SOURCE, ICLOUD)
            AppleAcct, reauth_username = self.get_AppleAcct_reauth_needed()
            self.AppleAcct = AppleAcct

        except Exception as err:
            log_exception(err)
            reauth_username = ''
            AppleAcct = None

        utils_cf.log_step_info(self, None, 'optflow-init')

        return None

    #.........................................................................................
    # def _reauth_goto_previous(self, exit_by_x_click=False):
    def ha_reconfigure_reauth_exit(self, exit_by_x_click=False):
        self.is_reauth_initialized = False
        utils_cf.log_step_info(self, f'Xclick-{exit_by_x_click}', 'exit')

        if Gb.AppleAcct_reauth_needed is None:
            return self.async_abort(reason="auth_code_accepted")

        # self._display_ha_reauth_banner()
        return self.async_abort(reason="auth_code_cancelled")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#                        SUPPORT FUNCTIONS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def initialize_step(self, step_id, user_input=None, errors=None):
        user_input, action_item = Gb.OptionsFlowHandler.initialize_step(step_id, user_input, errors)

        return user_input, action_item

#-------------------------------------------------------------------------------------------
    def __repr__(self):
            return 'ConfigFlow'

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                 ICLOUD3 UPDATE CONFIGURATION / OPTIONS HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3_OptionsFlowHandler(config_entries.OptionsFlow,
                                    OptionsFlow_AppleAccount_Steps, OptionsFlow_Reauth_Steps,
                                    OptionsFlow_iCloud3Device_Steps, OptionsFlow_Sensors_Steps,
                                    OptionsFlow_Tools_Steps, OptionsFlow_DashboardBuilder_Steps,
                                    OptionsFlow_Parameters_Steps):



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   The screens/step handler are in separate files in the configure/config_flow_steps
#   directory. Below are the individual files and the configure screens they handle.
#
#   UPDATE APPLE ACCOUNT CONFIG FLOW STEPS (cfs_apple_account)
#       - async_step_apple_accounts
#       - async_step_update_apple_acct
#       - async_step_delete_apple_acct
#         - async_step_apple_accounts_parameters
#
#   REAUTH CONFIG FLOW STEPS  (cfs_reauth)
#       - async_step_reauth
#       - async_step_reauth_code_from_applecom_login
#       - async_step_reauth_change_auth_method
#
#   ICLOUD3 DEVICE CONFIG FLOW STEPS (cfs_icloud3_device)
#       - async_step_device_list
#       - async_step_add_device
#       - async_step_update_device
#       - async_step_update_other_device_parameters
#       - async_step_change_device_order
#
#   DASHBOARD BUILDER CONFIG FLOW STEPS (cfs_dashboard_builder)
#       - async_step_dashboard_builder
#
#   SENSORS CONFIG FLOW (cfs_sensors)
#       - async_step_sensors
#       - async_step_exclude_sensors
#
#   TOOLS CONFIG FLOW (cfs_tools)
#        - async_step_tools
#        - async_step_tools_entity_registry_cleanup
#        - async_step_exit_icloud3_configure
#
#   PARAMETERSFLOW STEPS (cfs_parameters)
#       - async_step_away_time_zone
#       - async_step_tracking_parameters
#       - async_step_format_settings
#       - async_step_inzone_intervals
#       - async_step_waze_main
#       - async_step_special_zones
#       - async_step_display_text_as
#       - async_step_display_text_as_update
#       - async_step_picture_dir_filter
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


    def __init__(self):
        self.is_from_config_flow_handler    = False
        self.is_initialize_options_required = True
        self.config_file_commit_updates     = False  # The config file has been updated and needs to be written

        self.initialize_options()

        self.step_id = 'Enter Configure Settings-OptionsFlow'
        utils_cf.log_step_info(self, '', 'initialize')

    def initialize_options(self):
        Gb.trace_prefix                     = 'CONFIG'
        self.is_initialize_options_required = False

        self.errors                         = {}    # Errors en.json error key
        self.multi_form_hdr                 = ''    # multi-form - text string displayed on the called form
        self.multi_form_user_input          = {}    # multi-form - user_input to be restored when returning to calling form
        self.errors_user_input              = {}    # user_input text for a value with an error
        self.errors_entered_value           = {}
        self.errors_info_msg                = None  # dict that maps to a en.json msg for a 'description_placeholders' in the show_form stmt
        self.step_id                        = ''    # step_id for the window displayed
        self.menu_item                      = ''
        self.menu_item_selected             = ['device_list', 'away_time_zone']
        self.menu_page_no                   = 0     # Menu currently displayed
        self.header_msg                     = None  # Message displayed on menu after update
        self.exit_msg                       = ''    # Summary of what was updated, displayed on the Exit screen

        self.action_item                    = ''
        self.actions_list                   = []    # Actions list at the bottom of the screen
        self.actions_list_default           = ''    # Default action_items to reassign on screen redisplay
        self.config_parms_update_control    = []    # Stores the type of parameters that were updated, used to reinitialize parms
        self.code_to_schema_pass_value      = None
        self.confirm_action                 = {
            'action_desc':          'Confirm Action',
            'yes_func':             None,
            'yes_func_async':       None,
            'return_to_func_async': self.async_step_tools,
            'return_to_next_yes_func_async': None}

        # Variables used for icloud_account update forms
        self.logging_into_icloud_flag      = False
        self.create_device_tracker_sensor_enities_on_exit = False

        # Variables used for device selection and update on the device_list and device_update forms
        self.rebuild_ic3db_dashboards       = False    # Set when a devices is added or deleted. Used to update the Dashboards
        self.device_items_by_devicename     = {}       # List of the devices in the Gb.conf_tracking[device] parameter
        self.device_items_displayed         = []       # List of the devices displayed on the device_list form
        self.dev_page_last_selected_devicename = ['', ''] # Device's devicename last displayed on each page
        self.dev_page_no                    = 0        # device List form page number, starting with 0
        self.display_rarely_updated_parms   = False    # Display the fixed interval & track from zone parameters

        self.ic3_devicename_being_updated   = ' '         # Devicename currently being updated
        self.conf_device                    = {}
        self.conf_device_idx                =   0
        self.update_device_ha_sensor_entity = {}          # Contains info regarding update_device and needed entity changes
        self.device_list_control_default    = 'select'    # Select the Return to main menu as the default
        self.add_device_flag                = False
        self.is_deleting_device             = False       # Deleting device via config_flow, used in  er_util.remove_dev_listener
        self.add_device_enter_devicename_form_part_flag = False  # Add device started, True = form top part only displayed

        self.device_trkr_by_entity_id_all   = {}         # other platform device_tracker used to validate the ic3 entity is not us
        # Option selection lists on the Update apple_accts screen
        self.apple_acct_items_list          = []       # List of the apple_accts in the Gb.conf_tracking[apple_accts] parameter
        self.apple_acct_items_displayed     = []       # List of the apple_accts displayed on the device_list form
        self.aa_page_item                   = ['', '', '', '', '']  # Apple acct username last displayed on each page
        self.aa_page_no                     = 0        # apple_accts List form page number, starting with 0
        self.conf_apple_acct                = {}       # apple acct item selected
        self.apple_acct_items_by_username   = {}       # Selection list for the apple accounts on data_sources screens
        self.apple_acct_auth_items_by_username = {}    # Selection list for the apple accounts reauth screens
        self.aa_idx                         = 0
        # self.aa_reauth_username             = ''
        self.add_apple_acct_flag            = False
        self.aa_auth_methods_by_auth_method = {}        # Authentication methods for an Aple acct
        self.imported_aa_ic3_conf_devices   = {}        # Used on aa_ic3_add_devices screen to add  all unknown aa devices
        self.imported_aadevices_sel_list    = {}        # Used on aa_ic3_add_devices screen to add  all unknown aa devices

        self.icloud_list_text_by_fname      = {}
        self.icloud_list_text_by_fname2     = {}
        self.mobapp_list_text_by_entity_id  = {}         # mobile_app device_tracker info used in devices form for mobapp selection
        self.mobapp_list_text_by_entity_id  = MOBAPP_DEVICE_NONE_OPTIONS.copy()
        self.picture_by_filename            = {}
        self.picture_by_filename_base       = PICTURE_NONE_KEY_TEXT.copy()
        self.zone_name_key_text             = {}
        self.opt_picture_file_name_list     = []

        self.mobapp_scan_for_for_devicename = 'None'
        self.inactive_devices_key_text      = {}
        self.log_level_devices_key_text     = {}

        self.is_reauth_needed            = False
        self.is_reauth_initialized          = False     # This is only used by config_flow_reauth

        # Variables used for the display_text_as update
        self.dta_selected_idx               = UNSELECTED # Current conf index being updated
        self.dta_selected_idx_page          = [0, 5]    # Selected idx to display on each page
        self.dta_page_no                    = 0         # Current page being displayed
        self.dta_working_copy               = {0: '', 1: '', 2: '', 3: '', 4: '', 5: '', 6: '', 7: '', 8: '', 9: '',}

        # EvLog Parameter screen, Change Device Order fields
        self.cdo_devicenames                = {}
        self.cdo_new_order_idx              = {}
        self.cdo_curr_idx                   = 0

        # Dashboard Builder
        self.db_templates                   = {}    # iCloud3 device templates from icloud3/dashboard folder
        self.db_templates_used              = []    # Templates used in master-dashboard template
        self.db_templates_used_by_device    = []    # Templates used in master-dashboard template to be built
                                                    # by device rather than by template. the names start with
                                                    # template-device
        self.master_dashboard               = {}    # Master Dashboard dictionary (json str --> dict)
        self.dashboards                     = []    # List of dashboards (lovelace.icloud3_xxx files) in conig./storage)
        self.icloud3_dashboards             = []    # List of iCloud3 dashboards created by the Dashboard Builder
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

        # Tools > Entity Registry Maintenance
        self.tools_cleanup_er_sensor_all = False
        self.tools_entity_reg_check_all = None    # Show action check all instead of check none

        # away_time_zone_adjustment
        self.away_time_zone_hours_key_text       = {}
        self.away_time_zone_devices_key_text     = {}

        # Variables used for the system_settings update
        self.www_directory_list                 = []

        # List of all sensors created by ic3 during startup by sensor.py that is used
        # in the exclude_sensors screen
        # Format: ('gary_iphone_zone_distance': 'Gary ZoneDistance (gary_iphone_zone_distance)')
        self.sensors_fname_list                 = []
        self.excluded_sensors                   = []
        self.excluded_sensors_removed           = []
        self.sensors_list_filter                = '?'
        self.devices_added_deleted_cnt          = 0
        self.sensors_added_deleted_cnt          = 0

        self.is_aborting_config_flow = ('version' not in Gb.conf_profile)
        if self.is_aborting_config_flow: return

        # AppleAcct object and variables. Using local variables rather than the Gb AppleAcct variables
        # in case the username/password is changed and another account is accessed. These will not
        # intefer with ones already in use by iC3. The Global Gb variables will be set to the local
        # variables if they were changes and a iC3 Restart was selected when finishing the config setup
        self._initialize_self_AppleAcct_fields_from_Gb()

#----------------------------------------------------------------------
    @callback
    def async_remove(self) -> None:
        """HA calls this (sync @callback) when the user clicks 'X' to close the options flow."""
        self.flow_closed()

    def flow_closed(self) -> None:
        """Called when the user dismisses the options flow with 'X'."""

        if isnot_empty(self.config_parms_update_control):
            Gb.hass.async_create_task(self.exit_configure_tasks(exit_by_x_click=True))


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            INIT
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_init(self, user_input=None):
        if self.is_initialize_options_required:
            self.initialize_options()

        self.errors = {}
        self.header_msg = None
        self.config_file_commit_updates = False
        if Gb.AppleAcct_reauth_needed:
            self.menu_item_selected[0] = 'reauth'

        # If the initial config file was just installed:
        #   - Add 'local.icloud3.event-log-card.js to the Lovelace Resources
        if (Gb.conf_profile[CONF_VERSION] <= 0
                and is_empty(self.master_dashboard)):
            await start_ic3.update_lovelace_resource_event_log_js_entry(silent=True)

            # Display update_apple_acct screen for username/password if no accts have
            # been set up
            #if Gb.conf_data_source_ICLOUD:
            if is_empty(Gb.conf_apple_accounts):
                self.add_apple_acct_flag = True
                self.menu_item = 'apple_accounts'
                self.conf_apple_acct = DEFAULT_APPLE_ACCOUNT_CONF.copy()
                return await self.async_step_update_apple_acct()

        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    def _initialize_self_AppleAcct_fields_from_Gb(self):
        conf_apple_acct, _idx = config_file.conf_apple_acct(0)
        self.username = conf_apple_acct[CONF_USERNAME]
        self.password = conf_apple_acct[CONF_PASSWORD]

        self.AppleAcct = Gb.AppleAcct_by_username.get(self.username)

        if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'famshr'):
            Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace('famshr', ICLOUD)
        if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'mobapp'):
            Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace('mobapp', MOBAPP)

        self.data_source = Gb.conf_tracking[CONF_DATA_SOURCE]
        if self.AppleAcct:
            self.apple_server_location = self.AppleAcct.apple_server_location
        else:
            self.apple_server_location = 'usa'

#-------------------------------------------------------------------------------------------
    @staticmethod
    def conf_fnames_by_devicename():
        return {conf_device[CONF_IC3_DEVICENAME]: conf_device[CONF_FNAME]
                    for conf_device in Gb.conf_devices
                    if conf_device[CONF_TRACKING_MODE] != INACTIVE}

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            MENU
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_menu_0(self, user_input=None, errors=None):
        return await self.async_step_menu(user_input, errors)

    async def async_step_menu_1(self, user_input=None, errors=None):
        return await self.async_step_menu(user_input, errors)

#...............................................................................
    async def async_step_menu(self, user_input=None, errors=None):
        self.step_id = 'menu'
        self.errors = errors or {}
        await self.async_write_icloud3_configuration_file()

        Gb.trace_prefix = 'CONFIG'
        Gb.is_config_flow_open = True

        if Gb.internet_error:
            self.header_msg = 'internet_error'

        elif Gb.conf_data_source_ICLOUD:
            if is_empty(Gb.conf_apple_accounts):
                # self.header_msg = 'apple_acct_not_set_up'
                pass
            elif self.is_reauth_needed:
                self.header_msg ='auth_code_needed'

        else:
            for AppleAcct in Gb.AppleAcct_by_username.values():
                if AppleAcct.terms_of_use_update_needed:
                    self.header_msg ='apple_acct_terms_of_use_update_needed'
                    break

        if user_input is None:
            self.set_inactive_devices_header_msg()
            utils_cf.set_header_msg(self)

            menu_form = f"menu_{self.menu_page_no}"
            return self.async_show_form(step_id=menu_form,
                                        data_schema=forms.form_menu(self),
                                        errors=self.errors,
                                        last_step=False)

        user_input, self.menu_item = utils_cf.menu_text_to_item(self, user_input, 'menu_items')

        if self.menu_item == 'menu':
            if self.menu_page_no == 0:
                self.menu_page_no = 1

            elif self.menu_page_no == 1:
                self.menu_page_no = 0

        elif self.menu_item == 'exit':
            return await self.exit_configure_tasks()

        else:
            self.menu_item_selected[self.menu_page_no] = self.menu_item

        utils_cf.log_step_info(self, '')

        if self.menu_item == '':
            pass
        elif self.menu_item == 'apple_accounts':
            return await self.async_step_apple_accounts()
        elif self.menu_item == 'reauth':
            return await self.async_step_reauth()
        elif self.menu_item == 'device_list':
            return await self.async_step_device_list()
        elif self.menu_item == 'sensors':
            return await self.async_step_sensors()
        elif self.menu_item == 'dashboard_builder':
            return await self.async_step_dashboard_builder()
        elif self.menu_item == 'tools':
            return await self.async_step_tools()
        elif self.menu_item == 'away_time_zone':
            return await self.async_step_away_time_zone()
        elif self.menu_item == 'format_settings':
            return await self.async_step_format_settings()
        elif self.menu_item == 'display_text_as':
            return await self.async_step_display_text_as()
        elif self.menu_item == 'tracking_parameters':
            return await self.async_step_tracking_parameters()
        elif self.menu_item == 'inzone_intervals':
            return await self.async_step_inzone_intervals()
        elif self.menu_item == 'waze':
            return await self.async_step_waze_main()
        elif self.menu_item == 'special_zones':
            return await self.async_step_special_zones()

        self.set_inactive_devices_header_msg()
        utils_cf.set_header_msg(self)

        menu_form = f"menu_{self.menu_page_no}"
        return self.async_show_form(step_id=menu_form,
                            data_schema=forms.form_menu(self),
                            errors=self.errors,
                            last_step=False)

#-------------------------------------------------------------------------------------------
    async def exit_configure_tasks(self, exit_by_x_click=False):
        '''
        Handle all Exit Configure cleanup and processing. This is the single entry point
        for exiting and is called when EXIT is selected on the menu or the 'X' is clicked.

        exit_by_x_click parameter:
            = False - EXIT was selected on the menu. Run the exit tasks, then display the
                    'exit_icloud3_configure_settings' screen summarizing what was updated.
            = True  - The 'X' was clicked. HA has already closed the Configure Settings
                    dialog so nothing can be displayed. Run the exit tasks and return.

        HA calls async_remove (--> flow_closed) whenever the flow is torn down, which
        happens on a normal EXIT as well as on an 'X' click. Gb.is_config_flow_open is
        reset by exit_configure_settings_final_tasks and keeps that second pass from
        running all of the exit tasks again.
        '''

        if Gb.is_config_flow_open is False:
            return None

        device_cnt, inactive_device_cnt, inactive_pct = config_file.device_cnts()

        # The Review Inactive Devices screen can not be displayed if the dialog is closed
        if exit_by_x_click is False and inactive_pct > .5:
            return await self.async_step_review_inactive_devices()

        return await self.exit_configure_settings_final_tasks(exit_by_x_click)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             EXIT ICLOUD3 CONFIGURE SETTINGS INACTIVE DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def exit_configure_settings_final_tasks(self, exit_by_x_click=False):
        self.step_id = 'Exit Configure Settings'
        Gb.is_config_flow_open = False
        self.is_initialize_options_required = False
        utils_cf.log_step_info(self, f'Xclick-{exit_by_x_click}, UpdateParms-{Gb.config_parms_update_control}', 'start')

        # If the initial config file was just installed, set it to 'has been reviewed'
        if Gb.conf_profile[CONF_VERSION] <= 0:
            Gb.conf_profile[CONF_VERSION] = 1
            list_add(self.config_parms_update_control, 'restart')
            user_input = {CONF_VERSION: 1}
            self.update_config_file_tracking(user_input, force_config_update=True)

        self.exit_msg = "### iCloud3 Configure Session is Ending"
        self.exit_msg += '\n'

        if self.create_device_tracker_sensor_enities_on_exit:
            self.create_device_tracker_sensor_enities_on_exit = False
            await config_file.async_build_conf_device_sensors_from_conf_sensors()
            await ic3_device_tracker.async_create_Device_Tracker_objects()
            await ic3_sensor.async_create_Sensor_objects()
            self.rebuild_ic3db_dashboards = True
            list_add(self.config_parms_update_control, 'restart')

        if isnot_empty(Gb.sensors_removed_by_devicename):
            for devicename in Gb.sensors_removed_by_devicename.keys():
                ic3_sensor.log_sensors_added_deleted('ADDED', devicename)
                ic3_sensor.log_sensors_added_deleted('REMOVED', devicename)

        if 'devices' in self.config_parms_update_control:
            self.exit_msg += "* Devices & Sensors have been updated\n"
        if 'general' in self.config_parms_update_control:
            self.exit_msg += "* The Parameters have been updated\n"

        # Update the *ic3db- dashboard views when devices have been added or deleted
        if self.rebuild_ic3db_dashboards:
            await dbb.update_ic3db_dashboards_new_deleted_devices(self)
            self.rebuild_ic3db_dashboards = False
            self.exit_msg += (  f"* The iCloud3 Dashboards have been updated "
                                f"({self.dbf_dashboard_icons_msg})\n")

        if 'restart' in self.config_parms_update_control:
            self.exit_msg += "* iCloud3 has been Restarted\n"

        Gb.config_parms_update_control = self.config_parms_update_control.copy()

        # If the polling loop has not been set up, set the restart flag to trigger a restart when
        # no devices are being updated will not run. There were probably no devices to track
        # when first loaded and a direct restart must be done.
        if Gb.polling_5_sec_loop_running is False:
            Gb.config_parms_update_control = []
            service_handler.reload_icloud3()

        utils_cf.log_step_info(self, '', 'end')

        # data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}

        if exit_by_x_click:
            return None

        return self.async_step_exit_icloud3_configure_settings()

#-------------------------------------------------------------------------------------------
    def async_step_exit_icloud3_configure_settings(self):
        '''
        Display the final screen containing the exit_msg summary of everything that was
        updated when the Configure Settings handler was exited.

        This is an 'abort' step rather than a form so it is the last screen displayed.
        Clicking CLOSE (or the 'X') ends the Configure Settings dialog immediately.
        Nothing needs to be saved in the config entry - all of the iCloud3 configuration
        parameters are stored in the iCloud3 configuration file.
        '''
        self.step_id = 'Exit Configure Settings'

        utils_cf.log_step_info(self, f'UpdateParms-{Gb.config_parms_update_control}', 'to ha')


        return self.async_abort(reason='config_update_complete',
                            description_placeholders={'exit_msg': self.exit_msg or ''})

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#                  DISPLAY AND HANDLE USER INPUT FORMS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def common_form_handler(self, user_input=None, action_item=None, errors=None):
        '''
        Handle the data verification, error handling and confguration update of
        normal parameter feenry forms, excluding those dealing with icloud and
        device updates.
        '''
        self.errors = errors or {}
        self.errors_user_input = {}

        if user_input is None:
            return False

        # Validate the user_input, update the config file with valid entries
        if action_item is None:
            user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        if action_item == 'cancel_goto_menu':
            return True
        elif self.step_id == 'apple_accounts':
            pass
        elif self.step_id == 'device_list':
            user_input = self._get_conf_device_selected(user_input)
        elif self.step_id == 'format_settings':
            user_input = self._validate_format_settings(user_input)
        elif self.step_id == 'away_time_zone':
            user_input = self._validate_away_time_zone(user_input)
        elif self.step_id == "display_text_as":
            pass
        elif self.step_id == 'tracking_parameters':
            user_input = self._validate_tracking_parameters(user_input)
        elif self.step_id == 'inzone_intervals':
            user_input = self._validate_inzone_intervals(user_input)
        elif self.step_id == "waze_main":
            user_input = self._validate_waze_main(user_input)
        elif self.step_id == "special_zones":
            user_input = self._validate_special_zones(user_input)

        utils_cf.log_step_info(self, user_input, action_item)

        post_event(f"Configuration Changed > Type-{self.step_id.replace('_', ' ').title()}")
        self._update_config_file_general(user_input)

        # Redisplay the menu if there were no errors
        if not self.errors:
            return True

        # Display the config data entry form, any errors will be redisplayed and highlighted
        return False

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             CONFIRM ACTION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_confirm_action(self, user_input=None, errors=None):
        '''
        Confirm an action - This will display a screen containing the action_items.

        Parametters:
            self.confirm_action = {
                    'action_desc': TOOL_LIST[acton_item],
                    'yes_func': self.confirm_test_yes,
                    'yes_func_async': self.async_confirm_test_yes,
                    'return_to_func_async': self.async_step_tools,
                    'return_to_next_yes_func_async': None}

        '''
        self.step_id = 'confirm_action'
        self.errors = {}
        self.errors_user_input = {}

        utils_cf.log_step_info(self, user_input)

        if user_input is None or 'action_items' not in user_input:
            try:
                return self.async_show_form(step_id='confirm_action',
                                        data_schema=forms.form_confirm_action(self),
                                        errors=self.errors)
            except Exception as err:
                log_exception(err)

        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'confirm_action_no':
            self.errors = {'base': 'action_cancelled'}
            return await self.confirm_action['return_to_func_async'](errors=self.errors)

        if action_item == 'confirm_action_yes':
            self.config_file_commit_updates = True
            list_add(self.config_parms_update_control, 'restart')

            if self.confirm_action['yes_func'] is not None:
                self.confirm_action['yes_func']()
                self.errors = {'base': 'action_completed'}
                self.confirm_action['yes_func'] = None

            elif self.confirm_action['yes_func_async'] is not None:
                await self.confirm_action['yes_func_async']()
                self.errors = {'base': 'action_completed'}
                self.confirm_action['yes_func_async'] = None

            if self.confirm_action['return_to_next_yes_func_async']:
                return await self.confirm_action['return_to_next_yes_func_async'](errors=self.errors)

        return await self.confirm_action['return_to_func_async'](errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  VALIDATE DATA AND UPDATE CONFIG FILE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_write_icloud3_configuration_file(self, force_write=False):
        '''
        Write the updated configuration file to .storage/icloud3/configuration
        The config file updates are done by setting the commit_updates flag in
        the update routines and adding a call to this fct on screen changes so they
        are done using async updates. The screen handlers are run in async mode
        while the update fcts are not.
        '''
        if self.config_file_commit_updates is False and force_write is False:
            return

        await config_file.async_write_icloud3_configuration_file()

        self.config_file_commit_updates = False
        if self.errors == {}:
            self.header_msg = 'conf_updated'
            self.errors['base'] = 'conf_updated'

        # Updating the config file will encode the password. Make sure the
        # password is deoded in the self.conf_apple_acct variable in case it
        # is mapped to the Gb.conf_ale_accounts variable
        if isnot_empty(self.conf_apple_acct):
            self.conf_apple_acct[CONF_PASSWORD] = \
                    decode_password(self.conf_apple_acct[CONF_PASSWORD])

#-------------------------------------------------------------------------------------------
    def update_config_file(self, parameter_type, user_input, action_item):
        utils_cf.log_step_info(self, user_input, action_item)

        post_event(f"Configuration Changed > Type-{self.step_id.replace('_', ' ').title()}")

        if parameter_type == CF_GENERAL:
            self._update_config_file_general(user_input)

        utils_cf.log_step_info(self, user_input, 'UPDATE-CONFIG-FILE')

#-------------------------------------------------------------------------------------------
    def _update_config_file_general(self, user_input, force_config_update=None):
        '''
        Update the configuration parameters and write to the icloud3.configuration file

        Parameters:
            force_config_update - The config_tracking, conf_devices or conf_apple_accounts
                has already been updated. Make sure the changes are saved.
        '''
        # The username/password may be in the user_input from the update_data_sources form
        # or it's subforms. If so, make sure it is set the the primary username/password
        force_config_update = False if force_config_update is None else True
        was_config_fle_changed = False

        if CONF_USERNAME in user_input:
            conf_apple_acct, _idx = config_file.conf_apple_acct(0)
            conf_username = conf_apple_acct[CONF_USERNAME]
            conf_password = conf_apple_acct[CONF_PASSWORD]
            user_input[CONF_USERNAME] = conf_username
            user_input[CONF_PASSWORD] = conf_password

        updated_parms = {''}
        for pname, pvalue in user_input.items():
            if type(pvalue) is str:
                pvalue = pvalue.strip()
                if pvalue == '.':
                    continue
            if (pname not in self.errors
                    and pname in CONF_PARAMETER_FLOAT):
                pvalue = float(pvalue)

            if pname in Gb.conf_tracking:
                if pname == CONF_PASSWORD:
                    pvalue = encode_password(pvalue)
                if Gb.conf_tracking[pname] != pvalue:
                    was_config_fle_changed = True
                    Gb.conf_tracking[pname] = pvalue
                    list_add(self.config_parms_update_control, ['tracking', 'restart'])

            if pname in Gb.conf_general:
                if Gb.conf_general[pname] != pvalue:
                    was_config_fle_changed = True
                    Gb.conf_general[pname] = pvalue
                    list_add(self.config_parms_update_control, 'general')
                    if 'special_zones' in self.step_id:
                        list_add(self.config_parms_update_control, 'special_zone')
                    if 'away_time_zone' in self.step_id:
                        list_add(self.config_parms_update_control, 'devices')
                    if 'waze' in self.step_id:
                        list_add(self.config_parms_update_control, 'waze')

                    if pname == CONF_LOG_LEVEL:
                        Gb.conf_general[CONF_LOG_LEVEL] = pvalue
                        start_ic3.set_log_level(pvalue)

            if pname in Gb.conf_sensors:
                if Gb.conf_sensors[pname] != pvalue:
                    was_config_fle_changed = True
                    Gb.conf_sensors[pname] = pvalue
                    self.create_device_tracker_sensor_enities_on_exit = True

            if pname in Gb.conf_profile:
                if Gb.conf_profile[pname] != pvalue:
                    was_config_fle_changed = True
                    Gb.conf_profile[pname] = pvalue
                    list_add(self.config_parms_update_control, ['profile', 'evlog'])

        # if self.config_parms_update_control or force_config_update:
        if was_config_fle_changed or force_config_update:
            if Gb.conf_profile[CONF_VERSION] <= 0:
                Gb.conf_profile[CONF_VERSION] = 1

            self.config_file_commit_updates = True

        return was_config_fle_changed

#-------------------------------------------------------------------------------------------
    def update_config_file_tracking(self, user_input=None, force_config_update=None):
        '''
        Update the configuration parameters and write to the icloud3.configuration file

        This is used for updating the devices, Apple account, and some profile items
        in the config file That requires an iCloud3 restart

        Parameters:
            force_config_update - The config_tracking, conf_devices or conf_apple_accounts
                has already been updated. Make sure the changes are saved.
        '''
        if user_input is None:
            user_input = {}

        # The username/password may be in the user_input from the update_data_sources form
        # or it's subforms. If so, make sure it is set the the primary username/password
        if CONF_USERNAME in user_input:
            conf_apple_acct, _idx = config_file.conf_apple_acct(0)
            conf_username_0 = conf_apple_acct[CONF_USERNAME]
            conf_password_0 = conf_apple_acct[CONF_PASSWORD]
            conf_password_0_encoded = encode_password(conf_password_0)

        updated_parms = {''}
        force_config_update = False if force_config_update is None else True

        for pname, pvalue in user_input.items():
            if pname not in Gb.conf_tracking:
                continue

            if type(pvalue) is str:
                pvalue = pvalue.strip()
                if pvalue == '.':
                    continue

            if (pname not in self.errors and pname in CONF_PARAMETER_FLOAT):
                pvalue = float(pvalue)

            elif Gb.conf_tracking[pname] != pvalue:
                Gb.conf_tracking[pname] = pvalue
                force_config_update = True

        if force_config_update:
            if Gb.conf_apple_accounts:
                Gb.conf_tracking[CONF_USERNAME] = Gb.conf_apple_accounts[0][CONF_USERNAME]
                Gb.conf_tracking[CONF_PASSWORD] = Gb.conf_apple_accounts[0][CONF_PASSWORD]
            Gb.conf_tracking[CONF_APPLE_ACCOUNTS] = Gb.conf_apple_accounts
            Gb.conf_tracking[CONF_DEVICES]        = Gb.conf_devices
            list_add(self.config_parms_update_control, ['tracking', 'restart'])
            self.config_file_commit_updates = True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#                        SUPPORT FUNCTIONS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def initialize_step(self, step_id, user_input=None, errors=None):
        '''
        Initialize the step variables:

        Return:
            - user_input
            - action_item
        '''

        self.step_id = step_id
        self.errors = errors or {}
        self.errors_user_input = {}

        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        utils_cf.log_step_info(self, user_input, action_item)

        return user_input, action_item

#-------------------------------------------------------------------------------------------
    def __repr__(self):
            return 'OptionsFlow'
