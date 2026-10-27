

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
        self.is_initialize_options_required = True

        self.initialize_options()

        self.step_id = 'Enter Configure Settings-OptionsFlow'
        utils_cf.log_step_info(self, '', 'initialize')

    def initialize_options(self):
        Gb.trace_prefix                     = 'CONFIG'
        self.is_initialize_options_required = False

        # Variables shared by all of the step_... modules (step_common)
        self.initialize_common_variables()

        # OptionsFlow Menu and Exit screens
        self.menu_item_selected             = ['device_list', 'tracking_parameters']
        self.menu_page_no                   = 0     # Menu currently displayed
        self.exit_msg                       = ''    # Summary of what was updated, displayed on the Exit screen

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
            for AppleAcct in Gb.AppleAcct_by_apple_id.values():
                if AppleAcct.terms_of_use_update_needed:
                    self.header_msg ='apple_acct_terms_of_use_update_needed'
                    break

        self.set_inactive_devices_header_msg()
        self.set_analytics_menu_msg()
        utils_cf.set_header_msg(self)

        if user_input is None:
            menu_form = f"menu_{self.menu_page_no}"
            return self.async_show_form(step_id=menu_form,
                                        data_schema=forms.form_menu(self),
                                        errors=self.errors,
                                        last_step=False)

        menu_title     = user_input.get('menu_items', '').split(' →')[0]
        self.menu_item = MENU_KEYS_BY_TITLE[menu_title]
        action_title   = user_input.get('action_items', '').split(' →')[0]
        action_item    = MENU_KEYS_BY_TITLE.get(action_title)

        match action_item:
            case  '' | None:
                action_item = None
            case 'menu_0':
                self.menu_item_selected[1] = self.menu_item
                self.menu_page_no = 0
            case 'menu_1':
                self.menu_item_selected[0] = self.menu_item
                self.menu_page_no = 1
            case 'analytics':
                return await self.async_step_analytics()
            case 'exit':
                return await self.exit_configure_tasks()

        utils_cf.log_step_info(self, '')

        if action_item is not None:
            pass
        elif self.menu_item == '':
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
        elif self.menu_item == 'analytics':
            if Gb.analytics_enabled:
                return await self.async_step_analytics_reports()
            else:
                return await self.async_step_analytics()

        self.set_inactive_devices_header_msg()
        utils_cf.set_header_msg(self)

        menu_form = f"menu_{self.menu_page_no}"
        return self.async_show_form(step_id=menu_form,
                            data_schema=forms.form_menu(self),
                            errors=self.errors,
                            last_step=False)

#-------------------------------------------------------------------------------------------
    def set_analytics_menu_msg(self):

        if Gb.analytics_enabled is None:
            self.errors['action_items'] = 'analytics_enable_needed'

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            EXIT
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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
        # The handler is the Gb.OptionsFlowHandler singleton, reinitialize it when the
        # next Configure session starts (async_step_init)
        self.is_initialize_options_required = True
        utils_cf.log_step_info(self, f'XClick-{exit_by_x_click}, UpdateParms-{Gb.config_parms_update_control}', 'start')

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
            self.exit_msg += f"* Devices have been added ({Gb.device_trackers_cnt})\n"
            await ic3_sensor.async_create_Sensor_objects()
            self.exit_msg += f"* Sensors have been added ({Gb.sensors_cnt})\n"
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

#-------------------------------------------------------------------------------------------
    def __repr__(self):
            return 'OptionsFlow'
