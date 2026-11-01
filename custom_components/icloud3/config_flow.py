

from .global_variables      import GlobalVariables as Gb
from .const                 import (DOMAIN, ICLOUD3, DATETIME_FORMAT, STORAGE_DIR,
                                    ICLOUD, MOBAPP, NO_MOBAPP,
                                    TRACK, MONITOR, INACTIVE, )
from .const_config          import (CONF_VERSION, CONF_LOG_LEVEL, CONF_APPLE_ACCOUNTS,
                                    CONF_APPLE_ACCT, CONF_PASSWORD, CONF_DEVICES, CONF_DATA_SOURCE,
                                    CONF_IC3_DEVICENAME, CONF_FNAME, CONF_TRACKING_MODE,
                                    CONF_PARAMETER_TIME_STR, CONF_PARAMETER_FLOAT,
                                    CF_APPLE_ACCOUNTS, CF_DEVICES, CF_TRACKING, CF_GENERAL,
                                    DEFAULT_APPLE_ACCOUNT_CONF, CONF_ANALYTICS_ENABLED, )
from .const_char            import (RARROW, NL_DOT, DOT, NL, )

from .utils.utils           import (instr, is_number, is_empty, isnot_empty, list_to_str, str_to_list,
                                    is_running_in_event_loop, is_between, list_del, list_add,
                                    dict_sort_values, apple_user,
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
from .configure             import selection_lists as lists

from .configure.const_form_lists      import *
from .configure.screens.step_common           import OptionsFlow_Common_Steps
from .configure.screens.step_apple_acct      import OptionsFlow_AppleAccount_Steps
from .configure.screens.step_reauth           import OptionsFlow_Reauth_Steps
from .configure.screens.step_icloud3_device   import OptionsFlow_iCloud3Device_Steps
from .configure.screens.step_sensors          import OptionsFlow_Sensors_Steps
from .configure.screens.step_tools            import OptionsFlow_Tools_Steps
from .configure.screens.step_dashboard_builder import OptionsFlow_DashboardBuilder_Steps
from .configure.screens.step_parameters       import OptionsFlow_Parameters_Steps
from .configure.screens.step_analytics       import OptionsFlow_Analytics_Steps


import logging
_CF_LOGGER = logging.getLogger("icloud3-cf")

#--------------------------------------------------------------------
from homeassistant                  import config_entries, data_entry_flow
from homeassistant.config_entries   import ConfigEntry as config_entry
from homeassistant.data_entry_flow  import FlowHandler, FlowResult
from homeassistant.core             import callback, HomeAssistant

import homeassistant.util.dt as dt_util
import voluptuous as vol
from .apple_acct            import apple_acct_support_cf as aascf

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
        self.data_source                    = ICLOUD

        self.apple_id                      = ''
        self.AppleAcct                      = None
        # self.aa_reauth_apple_id             = ''
        self.header_msg                     = ''
        self.conf_apple_acct                = {}
        self.aa_idx                         = 0
        self.is_reauth_needed            = False

        lists.initialize_lists(self)
        self.initialize_reauth_variables()

        # Used for the OptionsFlow support functions. It is not the handler of an
        # iCloud3 Configure window, that one is created by async_get_options_flow.
        self.OptFlow = iCloud3_OptionsFlowHandler()

    @callback
    def async_show_form(self, **kwargs):
        kwargs['description_placeholders'] = utils_cf.show_form_placeholders(
                                                self, kwargs.get('description_placeholders'))
        return super().async_show_form(**kwargs)


    # UNUSED (10/31/2026) - not called anywhere. Commented out, delete after v3.8.0
    # def form_msg(self):
    #     return f"Form-{self.step_id}, Errors-{self.errors}"

#----------------------------------------------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        '''
        Create the options flow handler for iCloud3. This is called when the iCloud3 > Configure
        is selected on the Devices & Services screen, not when HA or iCloud3 is loaded

        A new handler is created for each Configure window. HA stores the window's flow_id,
        context and current screen on the handler so two open windows can not share one.
        Gb.OptionsFlowHandler is the last one opened, Gb.OptionsFlowHandlers_open has the
        handlers of all open windows (used by the entity registry listeners).
        '''
        Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()
        return Gb.OptionsFlowHandler

#----------------------------------------------------------------------
    @callback
    def async_remove(self) -> None:
        """HA calls this (sync @callback) when the user clicks 'X' to close the config flow."""
        self.flow_closed()

    def flow_closed(self) -> None:
        """Called when the user dismisses the config flow with 'X'."""
        return self.ha_reconfigure_reauth_exit(exit_by_x_click=True)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            USER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_user(self, user_input=None):
        '''
        Invoked when a user initiates a '+ Add Integration' on the Integerations screen

        self.handler = 'icloud3' from domain name in manifest.json
        '''
        _OptFlow = self.OptFlow
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

        _CF_LOGGER.info(f"Config_Flow Added Integration-{Gb.ha_device_id_x_devicename=}")

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
            AppleAcct, reauth_apple_id = self.get_AppleAcct_reauth_needed()
            self.AppleAcct = AppleAcct

        except Exception as err:
            log_exception(err)
            reauth_apple_id = ''
            AppleAcct = None

        utils_cf.log_step_info(self, None, 'optflow-init')

        return None

    #.........................................................................................
    def ha_reconfigure_reauth_exit(self, exit_by_x_click=False):
        self.is_reauth_initialized = False
        utils_cf.log_step_info(self, f'XClick-{exit_by_x_click}', 'exit')

        if Gb.AppleAcct_reauth_needed is None:
            return self.async_abort(reason="auth_code_accepted")

        # self._display_ha_reauth_banner()
        return self.async_abort(reason="auth_code_cancelled")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#                        SUPPORT FUNCTIONS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def initialize_step(self, step_id, user_input=None, errors=None):
        user_input, action_item = self.OptFlow.initialize_step(step_id, user_input, errors)

        return user_input, action_item

    def update_config_file_tracking(self, user_input=None, force_config_update=None):
        self.OptFlow.update_config_file_tracking(user_input, force_config_update)

#-------------------------------------------------------------------------------------------
    def __repr__(self):
            return 'ConfigFlow'

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                 ICLOUD3 UPDATE CONFIGURATION / OPTIONS HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3_OptionsFlowHandler(config_entries.OptionsFlow, OptionsFlow_Common_Steps,
                                    OptionsFlow_AppleAccount_Steps, OptionsFlow_Reauth_Steps,
                                    OptionsFlow_iCloud3Device_Steps, OptionsFlow_Sensors_Steps,
                                    OptionsFlow_Tools_Steps, OptionsFlow_DashboardBuilder_Steps,
                                    OptionsFlow_Parameters_Steps, OptionsFlow_Analytics_Steps):



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

        self.initialize_options()

        self.step_id = 'Enter Configure Settings-OptionsFlow'
        utils_cf.log_step_info(self, '', 'initialize')

    def initialize_options(self):
        Gb.trace_prefix                     = 'CONFIG'
        # Gb.is_config_flow_open for this Configure window only, the Gb one stays set
        # until the last open window is closed (set_config_flow_open)
        self.is_config_flow_open            = False

        # Variables shared by all of the step_... modules (step_common)
        self.initialize_common_variables()

        # OptionsFlow Menu and Exit screens
        self.menu_id                        = MAIN_MENU # Menu the configure screens return to
        self.needs_attention                = []    # Needs attention items of the main menu
        self.needs_attention_placeholders   = {}
        self.needs_attention_terms_apple_id = ''    # Apple Acct opened by the Terms of Use item
        self.needs_attention_reauth_apple_id = ''   # Apple Acct opened by the Reauth item
        self.needs_attention_devicename     = ''    # Device opened by the No data source item

        # Selection lists and the variables used by only one step_... module. Each
        # step class initializes its own so it can be used outside this handler.
        lists.initialize_lists(self)
        self.initialize_apple_acct_variables()
        self.initialize_reauth_variables()
        self.initialize_icloud3_device_variables()
        self.initialize_sensors_variables()
        self.initialize_tools_variables()
        self.initialize_dashboard_builder_variables()
        self.initialize_parameters_variables()
        self.initialize_analytics_variables()

        self.is_aborting_config_flow = ('version' not in Gb.conf_profile)
        if self.is_aborting_config_flow: return

        # AppleAcct object and variables. Using local variables rather than the Gb AppleAcct variables
        # in case the apple_id/password is changed and another account is accessed. These will not
        # intefer with ones already in use by iC3. The Global Gb variables will be set to the local
        # variables if they were changes and a iC3 Restart was selected when finishing the config setup
        self._initialize_self_AppleAcct_fields_from_Gb()

#----------------------------------------------------------------------
    @callback
    def async_remove(self) -> None:
        """HA calls this (sync @callback) when the user clicks 'X' to close the options flow."""
        self.flow_closed()

    @callback
    def async_show_form(self, **kwargs):
        kwargs['description_placeholders'] = utils_cf.show_form_placeholders(
                                                self, kwargs.get('description_placeholders'))
        return super().async_show_form(**kwargs)

    def flow_closed(self) -> None:
        """
        Called when the user closes the options flow with 'X'. This ends the Configure session.
        The exit tasks save the changes and restart or reload iCloud3, they are only run when
        something was changed.
        """
        if (isnot_empty(self.config_parms_update_control)
                or self.create_device_tracker_sensor_enities_on_exit
                or self.rebuild_ic3db_dashboards
                or Gb.conf_profile.get(CONF_VERSION, 1) <= 0):
            Gb.hass.async_create_task(self.exit_configure_tasks())
        else:
            self.set_config_flow_open(False)
            self.apply_config_updates_on_last_close()

    def set_config_flow_open(self, is_open):
        '''
        Gb.is_config_flow_open is True while any Configure window is open. Closing one
        window does not reset it for the other ones.
        '''
        self.is_config_flow_open = is_open
        if is_open:
            Gb.OptionsFlowHandlers_open.add(self)
        else:
            Gb.OptionsFlowHandlers_open.discard(self)
        Gb.is_config_flow_open = len(Gb.OptionsFlowHandlers_open) > 0

    def apply_config_updates_on_last_close(self):
        '''
        The changes saved in the Configure windows are applied (iCloud3 is restarted or
        reloaded) when the last open window is closed, not under another open window.
        '''
        if Gb.is_config_flow_open or is_empty(Gb.config_parms_update_control_pending):
            return

        list_add(Gb.config_parms_update_control, Gb.config_parms_update_control_pending)
        Gb.config_parms_update_control_pending = []

        # If the polling loop has not been set up, set the restart flag to trigger a restart when
        # no devices are being updated will not run. There were probably no devices to track
        # when first loaded and a direct restart must be done.
        if Gb.polling_5_sec_loop_running is False:
            Gb.config_parms_update_control = []
            service_handler.reload_icloud3()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            INIT
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_init(self, user_input=None):
        await utils_cf.async_load_texts()

        self.errors = {}
        self.header_msg = None
        self.config_file_commit_updates = False
        self.menu_id = MAIN_MENU
        self.set_config_flow_open(True)

        # If the initial config file was just installed:
        #   - Add 'local.icloud3.event-log-card.js to the Lovelace Resources
        if (Gb.conf_profile[CONF_VERSION] <= 0
                and is_empty(self.master_dashboard)):
            await start_ic3.update_lovelace_resource_event_log_js_entry(silent=True)

            # Display update_apple_acct screen for apple_id/password if no accts have
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
        self.apple_id = conf_apple_acct[CONF_APPLE_ACCT]
        self.password = conf_apple_acct[CONF_PASSWORD]

        self.AppleAcct = Gb.AppleAcct_by_apple_id.get(self.apple_id)

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

#...............................................................................
    async def async_step_menu(self, user_input=None, errors=None):
        '''
        Display the menu the configure screen was opened from. The step_... screens
        return here when they are done.
        '''
        return await self.async_show_configure_menu(self.menu_id, errors)

    async def async_step_main_menu(self, user_input=None, errors=None):
        return await self.async_show_configure_menu(MAIN_MENU, errors)

    async def async_step_menu_tracking(self, user_input=None, errors=None):
        return await self.async_show_configure_menu('menu_tracking', errors)

    async def async_step_menu_display(self, user_input=None, errors=None):
        return await self.async_show_configure_menu('menu_display', errors)

    async def async_step_menu_sensors(self, user_input=None, errors=None):
        return await self.async_show_configure_menu('menu_sensors', errors)

    async def async_step_menu_system(self, user_input=None, errors=None):
        return await self.async_show_configure_menu('menu_system', errors)

#...............................................................................
    async def async_show_configure_menu(self, menu_id, errors=None):
        self.step_id   = menu_id
        self.menu_id   = menu_id
        self.menu_item = ''
        self.errors    = errors or {}
        await self.async_write_icloud3_configuration_file()

        Gb.trace_prefix = 'CONFIG'
        self.set_config_flow_open(True)

        utils_cf.log_step_info(self, '')

        placeholders = {'header_msg': await self.async_menu_header_msg()}
        if menu_id == MAIN_MENU:
            forms.build_needs_attention(self)
            placeholders['status_line'] = forms.menu_status_line(self)
            placeholders.update(self.needs_attention_placeholders)
            if self.config_parms_update_control and placeholders['header_msg'] == '':
                placeholders['header_msg'] = utils_cf.tr('changes_pending')

        return self.async_show_menu(step_id=menu_id,
                            menu_options=forms.menu_options(self, menu_id),
                            description_placeholders=placeholders)

#...............................................................................
    async def async_menu_header_msg(self):
        '''
        The messages displayed at the top of the menu. Menus can not display errors so the
        update results and alerts are displayed in the menu description.
        '''
        msg_keys = []
        if self.errors.get('base'):
            msg_keys.append(self.errors['base'])

        if Gb.internet_error:
            msg_keys.append('internet_error')

        self.header_msg = None
        msgs = await utils_cf.async_header_msgs(self, list(dict.fromkeys(msg_keys)))

        return '\n\n'.join(msgs)

#...............................................................................
    async def open_menu_item(self, menu_item):
        '''
        Open the configure screen of the menu item selected on a menu. The screens use
        self.menu_item to determine the screen to return to.
        '''
        self.menu_item = menu_item
        utils_cf.log_step_info(self, '')

        match menu_item:
            case 'apple_accounts':
                return await self.async_step_apple_accounts()
            case 'device_list':
                return await self.async_step_device_list()
            case 'inzone_intervals':
                return await self.async_step_inzone_intervals()
            case 'tracking_parameters':
                return await self.async_step_tracking_parameters()
            case 'special_zones':
                return await self.async_step_special_zones()
            case 'waze':
                return await self.async_step_waze_main()
            case 'format_settings':
                return await self.async_step_format_settings()
            case 'display_text_as':
                return await self.async_step_display_text_as()
            case 'away_time_zone':
                return await self.async_step_away_time_zone()
            case 'sensors':
                return await self.async_step_sensors()
            case 'exclude_sensors':
                return await self.async_step_exclude_sensors()
            case 'dashboard_builder':
                return await self.async_step_dashboard_builder()
            case 'tools':
                return await self.async_step_tools()
            case 'analytics':
                return await self.async_step_analytics()
            case 'analytics_reports':
                # Refresh the report list when the screen is opened to pick up
                # reports that have been added, renamed or reordered.
                self.analytic_reports_by_name = {}
                return await self.async_step_analytics_reports()

            # Needs attention items at the top of the main menu
            case 'action_terms_of_use':
                self.menu_item = 'reauth'
                return await self.async_step_reauth(reauth_apple_id=self.needs_attention_terms_apple_id)
            case 'action_reauth':
                self.menu_item = 'reauth'
                return await self.async_step_reauth(
                            reauth_apple_id=self.needs_attention_reauth_apple_id or aascf.reauth_needed_apple_id())
            case 'action_no_data_source':
                self.menu_item = 'device_list'
                if self._get_conf_device_selected(
                        {CONF_IC3_DEVICENAME: self.needs_attention_devicename}):
                    return await self.async_open_update_device_screen(self.needs_attention_devicename)
                return await self.async_step_device_list()
            case 'action_login_failed':
                self.menu_item = 'apple_accounts'
                return await self.async_step_apple_accounts()
            case 'action_add_apple_acct':
                self.menu_item = 'apple_accounts'
                self.add_apple_acct_flag = True
                self.conf_apple_acct = DEFAULT_APPLE_ACCOUNT_CONF.copy()
                return await self.async_step_update_apple_acct()
            case 'action_add_devices':
                # Import the Apple Account devices, add one if there are none to import
                self.menu_item = 'device_list'
                if Gb.use_data_source_ICLOUD and isnot_empty(Gb.AppleAcct_by_apple_id):
                    return await self.async_step_import_apple_devices()
                return await self.async_step_device_list_add()
            case 'action_review_inactive' | 'action_review_inactive_some':
                self.menu_item = 'device_list'
                return await self.async_step_review_inactive_devices()
            case 'action_analytics':
                self.menu_item = 'analytics'
                return await self.async_step_analytics()

        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            EXIT
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def exit_configure_tasks(self):
        '''
        Handle all Exit Configure cleanup and processing. The Configure session ends when
        the 'X' is clicked. HA has already closed the dialog so nothing can be displayed.

        HA calls async_remove (--> flow_closed) whenever the flow is torn down.
        self.is_config_flow_open is reset by exit_configure_settings_final_tasks and keeps a
        second pass from running all of the exit tasks again. It is not Gb.is_config_flow_open
        so closing another Configure window does not skip this window's exit tasks.
        '''
        if self.is_config_flow_open is False:
            return None

        return await self.exit_configure_settings_final_tasks()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             EXIT ICLOUD3 CONFIGURE SETTINGS INACTIVE DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def exit_configure_settings_final_tasks(self):
        self.step_id = 'Exit Configure Settings'
        self.set_config_flow_open(False)
        utils_cf.log_step_info(self, f'UpdateParms-{Gb.config_parms_update_control}', 'start')

        # If the initial config file was just installed, set it to 'has been reviewed'
        if Gb.conf_profile[CONF_VERSION] <= 0:
            Gb.conf_profile[CONF_VERSION] = 1
            list_add(self.config_parms_update_control, 'restart')
            user_input = {CONF_VERSION: 1}
            self.update_config_file_tracking(user_input, force_config_update=True)

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

        # Update the *ic3db- dashboard views when devices have been added or deleted
        if self.rebuild_ic3db_dashboards:
            await dbb.update_ic3db_dashboards_new_deleted_devices(self)
            self.rebuild_ic3db_dashboards = False

        list_add(Gb.config_parms_update_control_pending, self.config_parms_update_control)
        self.apply_config_updates_on_last_close()

        utils_cf.log_step_info(self, '', 'end')

#-------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------------
    def __repr__(self):
            return 'OptionsFlow'


#-------------------------------------------------------------------------------------------
#   HA runs the async_step_[option] step when a menu option is selected. Add the
#   async_step_open_[menu item] steps that open the configure screens.
def _open_menu_item_step(menu_item):
    async def async_step_open_menu_item(self, user_input=None):
        return await self.open_menu_item(menu_item)

    return async_step_open_menu_item

for _menu_item in MENU_ITEMS + MENU_ACTION_NEEDED_ITEMS:
    setattr(iCloud3_OptionsFlowHandler, f"async_step_open_{_menu_item}",
            _open_menu_item_step(_menu_item))
