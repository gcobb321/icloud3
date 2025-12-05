

from .global_variables  import GlobalVariables as Gb
from .const             import (DOMAIN, ICLOUD3, DATETIME_FORMAT, STORAGE_DIR,
                                NBSP, RARROW, PHDOT, CRLF_DOT, DOT, HDOT, PHDOT, CIRCLE_STAR, RED_X,
                                YELLOW_ALERT, RED_ALERT, EVLOG_NOTICE, EVLOG_ALERT, EVLOG_ERROR, LINK, LLINK, RLINK,
                                ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                IPHONE_FNAME, IPHONE, IPAD, WATCH, MAC, AIRPODS, ICLOUD, OTHER, HOME, FAMSHR,
                                DEVICE_TYPES, DEVICE_TYPE_FNAME, DEVICE_TYPE_FNAMES, DEVICE_TRACKER_DOT,
                                MOBAPP, NO_MOBAPP,
                                TRACK_DEVICE, MONITOR_DEVICE, INACTIVE_DEVICE,
                                NAME,  FRIENDLY_NAME, FNAME, TITLE, BATTERY,
                                ZONE, HOME_DISTANCE, DEVICE_TRACKER,
                                ARRIVAL_TIME, TRAVEL_TIME, NEXT_UPDATE,
                                CONF_PICTURE_WWW_DIRS,
                                CONF_VERSION, CONF_EVLOG_CARD_DIRECTORY,
                                CONF_EVLOG_BTNCONFIG_URL,
                                CONF_APPLE_ACCOUNTS, CONF_APPLE_ACCOUNT, CONF_TOTP_KEY,
                                CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES, CONF_SETUP_ICLOUD_SESSION_EARLY,
                                CONF_DATA_SOURCE, CONF_VERIFICATION_CODE, CONF_LOCATE_ALL,
                                CONF_SERVER_LOCATION, CONF_SERVER_LOCATION_NEEDED,
                                CONF_TRACK_FROM_ZONES, CONF_PASSWORD_SRP_ENABLED,
                                CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                                CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX, CONF_LOG_ZONES,
                                CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVALS,
                                CONF_RAW_MODEL, CONF_MODEL, CONF_MODEL_DISPLAY_NAME, CONF_FAMSHR_DEVICE_ID,
                                CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT,
                                CONF_TRAVEL_TIME_FACTOR,
                                CONF_PASSTHRU_ZONE_TIME, CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES,
                                CONF_DISPLAY_ZONE_FORMAT, CONF_DEVICE_TRACKER_STATE_SOURCE, CONF_DISPLAY_GPS_LAT_LONG,
                                CONF_WAZE_USED, CONF_WAZE_SERVER,
                                CONF_WAZE_REALTIME, CONF_WAZE_HISTORY_DATABASE_USED,
                                CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                CONF_STAT_ZONE_FNAME, CONF_STAT_ZONE_STILL_TIME, CONF_DISPLAY_TEXT_AS,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE, CONF_FMF_EMAIL,CONF_FMF_DEVICE_ID,
                                CONF_TRACKING_MODE, CONF_INZONE_INTERVAL, CONF_FIXED_INTERVAL,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                CONF_SENSORS_TRACKING_TIME, CONF_SENSORS_TRACKING_DISTANCE,
                                CONF_SENSORS_TRACK_FROM_ZONES, CONF_SENSORS_TRACKING_UPDATE,
                                CONF_SENSORS_MONITORED_DEVICES, CONF_SENSORS_DEVICE,
                                CONF_SENSORS_OTHER, CONF_EXCLUDED_SENSORS,
                                CONF_PARAMETER_TIME_STR, CONF_PARAMETER_FLOAT,
                                CF_PROFILE, CF_TRACKING, CF_GENERAL, CF_DATA, CF_SENSORS,
                                DEFAULT_DEVICE_CONF, DEFAULT_GENERAL_CONF, DEFAULT_APPLE_ACCOUNT_CONF, DEFAULT_DATA_CONF,
                                DEFAULT_DEVICE_APPLE_ACCT_DATA_SOURCE, DEFAULT_DEVICE_MOBAPP_DATA_SOURCE,
                                DEFAULT_TRACKING_CONF, DEFAULT_SENSORS_CONF,
                                )
from .const_sensor      import (SENSOR_GROUPS )

from .utils.utils       import (instr, is_number, is_empty, isnot_empty, list_to_str, str_to_list,
                                is_running_in_event_loop, isbetween, list_del, list_add,
                                sort_dict_by_values, username_id,
                                encode_password, decode_password, )
from .utils.messaging   import (log_exception, log_debug_msg, log_info_msg, add_log_file_filter,
                                _log, _evlog, more_info, write_config_file_to_ic3log, close_ic3log_file,
                                post_event, post_alert, post_monitor_msg, post_greenbar_msg,
                                update_alert_sensor, )

from .configure         import forms
from .configure         import selection_lists as lists
from .configure         import sensors as config_sensors
from .configure         import utils_configure as utils
from .configure         import dashboard_builder as dbb
from .configure.const_form_lists import *

from .apple_acct        import apple_acct_support_cf as aascf
from .apple_acct        import apple_acct_support as aas
from .apple_acct.apple_acct_upw import ValidateAppleAcctUPW
from .                  import sensor as ic3_sensor
from .                  import device_tracker as ic3_device_tracker
from .startup           import start_ic3
from .startup           import config_file
from .utils             import entity_io
from .utils             import file_io

import logging
_CF_LOGGER = logging.getLogger("icloud3-cf")
DEVICE_NON_TRACKING_FIELDS =   [CONF_FNAME, CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                                CONF_FIXED_INTERVAL, CONF_LOG_ZONES,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES]

#--------------------------------------------------------------------
from homeassistant                  import config_entries, data_entry_flow
from homeassistant.config_entries   import ConfigEntry as config_entry
from homeassistant.data_entry_flow  import FlowHandler, FlowResult
from homeassistant.core             import callback, HomeAssistant
from homeassistant.util             import slugify
# from homeassistant.helpers          import (selector, collection,
#                                             entity_registry as er,
#                                             device_registry as dr,
#                                             area_registry as ar,)

import homeassistant.util.dt as dt_util
import voluptuous as vol
# import pyotp


# #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                     ICLOUD3 CONFIG FLOW - INITIAL SETUP
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class iCloud3_ConfigFlow(config_entries.ConfigFlow, FlowHandler, domain=DOMAIN):
    '''iCloud3 config flow Handler'''

    VERSION = 1
    def __init__(self):
        self.step_id = ''           # step_id for the window displayed
        self.errors  = {}           # Errors en.json error key
        self.OptFlow = None
        self.data_source = ICLOUD

        # Items used in the REAUTH handler
        self.username = ''
        self.AppleAcct = None
        self.apple_acct_reauth_username = ''
        self.header_msg = ''
        self.conf_apple_acct = {}
        self.aa_idx = 0
        self.apple_acct_items_by_username = {}
        self.is_verification_code_needed  = False
        self.reauth_form_fido2_key_names_list = {}        # Fido2 key names for REAUTH form


    def form_msg(self):
        return f"Form-{self.step_id}, Errors-{self.errors}"

    def _logui(self, user_input):
        _log(f"{user_input=} {self.errors=} ")

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

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            USER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_user(self, user_input=None):
        '''
        Invoked when a user initiates a '+ Add Integration' on the Integerations screen

        self.handler = 'icloud3' from domain name in manifest.json
        '''
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

        # Convert the .storage/icloud3.configuration file if it is at a default
        # state or has never been updated via config_flow using 'HA Integrations > iCloud3'
        # if Gb.conf_profile[CONF_VERSION] == -1:
        #     await self.async_migrate_v2_config_to_v3()

        _CF_LOGGER.info(f"Config_Flow Added Integration-{Gb.ha_device_id_by_devicename=}")

        if user_input is not None:
            _CF_LOGGER.info(f"Added iCloud3 Integration")

            if user_input.get('reset_tracking', False):
                if Gb.OptionsFlowHandler is None:
                    Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()
                _OptFlow = Gb.OptionsFlowHandler

                _CF_LOGGER.info(f"iCloud3 Reinstallation, Initialize Apple Accounts and Device Configuration")
                _OptFlow.reset_icloud3_config_file_tracking()
                await _OptFlow.delete_all_files_and_remove_directory(Gb.icloud_cookie_directory)

                Gb.config_parms_update_control = ['tracking', 'restart']
                await config_file.async_write_icloud3_configuration_file()

            if Gb.restart_ha_flag:
                return await self.async_step_restart_ha()

            data = {}
            data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
            return self.async_create_entry(title="iCloud3", data=data)

        return self.async_show_form(step_id="user",
                                    data_schema=forms.form_config_option_user(self),
                                    errors=errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_reauth(self, user_input=None, errors=None,
                                return_to_step_id=None):
        '''
        Ask for the verification code from the user.

        The iCloud account needs to be verified. Show the code entry form, get the
        code from the user, send the code back to Apple ID iCloud via pyicloud and get
        a valid code indicator or invalid code error.

        If the code is valid, either:
            - return to the return_to_step_id (icloud_account form) if in the config_flow configuration routine or,
            - issue a 'create_entry' indicating a successful verification. This will return
            to the function it wass called from. This will be when a validation request was
            needed during the normal tracking.

        If invalid, display an error message and ask for the code again.

        Input:
            - return_to_step_id
                    = the step_id in the config_glow if the icloud3 configuration
                        is being updated
                    = None if the rquest is from another regular function during the normal
                        tracking operation.
        '''
        # Config_flow is only set up on the initial add. This reauth uses some of the OptionsFlowHandler
        # functions so we need to set up that link when a reauth is needed
        if Gb.OptionsFlowHandler is None:
            Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()
        _OptFlow = Gb.OptionsFlowHandler
        self.data_source = Gb.conf_tracking.get(CONF_DATA_SOURCE, ICLOUD)

        if user_input and 'account_selected' in user_input:
            user_input = utils.option_text_to_parm(user_input,
                                                    'account_selected',
                                                    self.apple_acct_items_by_username)
            ui_username = user_input['account_selected']
            conf_apple_acct, aa_idx = config_file.conf_apple_acct(ui_username)
            username  = conf_apple_acct[CONF_USERNAME]
            password  = conf_apple_acct[CONF_PASSWORD]
        else:
            # When iCloud3 creates the AppleAcct object for the Apple account during startup,
            # a 2fa needed check is made. If it is needed, a reauthentication is needed executive
            # job is run that tells HA to issue a notification.  The AppleAcct object is saved
            # to be used here
            user_input = None
            username   = Gb.AppleAcct_needing_reauth_via_ha.get(CONF_USERNAME, '')
            password   = Gb.AppleAcct_needing_reauth_via_ha.get(CONF_PASSWORD, '')
            acct_owner = Gb.AppleAcct_needing_reauth_via_ha.get('account_owner', '')

        self.AppleAcct = Gb.AppleAcct_by_username.get(username, None)
        self.apple_acct_reauth_username = reauth_username = self.username = username

        log_debug_msg(  f"⭐ REAUTH (From={return_to_step_id}, "
                            f"{username=} > UserInput-{user_input},  Errors-{errors}")

        action_item, reauth_username, user_input, errors = \
            await aascf.async_reauthenticate_apple_account(self,
                                            user_input=user_input, errors=errors,
                                            return_to_step_id='reauth',
                                            reauth_username=reauth_username)


        if action_item == 'goto_previous':
            return self.async_abort(reason="verification_code_cancelled")

        else:
            log_debug_msg(  f"⭐ REAUTH (From={return_to_step_id}, "
                            f"{action_item}) > UserInput-{user_input}, Errors-{errors}")
            return self.async_show_form(step_id='reauth',
                                        data_schema=forms.form_reauth(self,
                                                reauth_username=reauth_username),
                                        errors=self.errors)

#........................................................................................
    def _is_apple_acct_setup(self):
        if self.username:
            return True
        elif is_empty(Gb.conf_apple_accounts):
            return False
        elif Gb.conf_apple_accounts[0].get(CONF_USERNAME, '') == '':
            return False

        return True



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             RESTART HA
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_restart_ha(self, user_input=None, errors=None):
        '''
        A restart is required if there were devicenames in known_devices.yaml
        '''
        if Gb.OptionsFlowHandler is None:
            Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()
        _OptFlow = Gb.OptionsFlowHandler

        self.step_id = 'restart_ha'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = _OptFlow.action_text_to_item(_OptFlow, user_input)

        if user_input is not None or action_item is not None:
            if action_item.startswith('restart_ha'):
                await Gb.hass.services.async_call("homeassistant", "restart")

            data = {}
            data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
            return self.async_create_entry(title="iCloud3", data=data)

        return self.async_show_form(step_id='restart_ha',
                        data_schema=forms.form_restart_ha(self),
                        errors=self.errors,
                        last_step=False)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                 ICLOUD3 UPDATE CONFIGURATION / OPTIONS HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3_OptionsFlowHandler(config_entries.OptionsFlow):
    '''Handles options flow for the component.'''

    def __init__(self):
    # def __init__(self, settings=False):
        self.initialize_options_required_flag = True
        self.step_id        = ''       # step_id for the window displayed
        self.errors         = {}       # Errors en.json error key
        self.errors_entered_value = {}
        self.config_file_commit_updates = False  # The config file has been updated and needs to be written

        self.initialize_options()
        # if settings:
        #     Gb.hass.async_create_task(self.async_step_menu())

    def initialize_options(self):
        Gb.trace_prefix = 'CONFIG'
        # self._set_initial_icloud3_device_tracker_area_id()
        self.initialize_options_required_flag = False
        # self.v2v3_migrated_flag               = False  # Set to True when the conf_profile[VERSION] = -1 when first loaded

        self.errors                = {}     # Errors en.json error key
        self.multi_form_hdr        = ''     # multi-form - text string displayed on the called form
        self.multi_form_user_input = {}     # multi-form - user_input to be restored when returning to calling form
        self.errors_user_input     = {}     # user_input text for a value with an error
        self.step_id               = ''     # step_id for the window displayed
        self.menu_item_selected    = [  MENU_KEY_TEXT_PAGE_0[MENU_PAGE_0_INITIAL_ITEM],
                                        MENU_KEY_TEXT_PAGE_1[MENU_PAGE_1_INITIAL_ITEM]]
        self.menu_page_no          = 0      # Menu currently displayed
        self.header_msg            = None   # Message displayed on menu after update
        self.return_to_step_id_1   = ''     # Form/Fct to return to when verifying the icloud auth code
        self.return_to_step_id_2   = ''     # Form/Fct to return to when verifying the icloud auth code

        self.actions_list              = []     # Actions list at the bottom of the screen
        self.actions_list_default      = ''     # Default action_items to reassign on screen redisplay
        self.config_parms_update_control = []   # Stores the type of parameters that were updated, used to reinitialize parms
        self.code_to_schema_pass_value = None
        self.confirm_action = {
                'yes_fct': None,
                'yes_fct_async': None,
                'action_desc': 'Confirm Action',
                'return_to_fct': None,
                'return_to_async_step_fct': self.async_step_tools}

        # Variables used for icloud_account update forms
        self.logging_into_icloud_flag = False

        # Variables used for device selection and update on the device_list and device_update forms
        self.rebuild_ic3db_dashboards    = False    # Set when a devices is added or deleted. Used to update the Dashboards
        self.device_items_by_devicename    = {}       # List of the apple_accts in the Gb.conf_tracking[apple_accts] parameter
        self.device_items_displayed        = []       # List of the apple_accts displayed on the device_list form
        self.dev_page_item                 = ['', '', '', '', ''] # Device's devicename last displayed on each page
        self.dev_page_no                   = 0        # apple_accts List form page number, starting with 0
        self.display_rarely_updated_parms     = False    # Display the fixed interval & track from zone parameters

        self.ic3_devicename_being_updated  = ''         # Devicename currently being updated
        self.conf_device                   = {}
        self.conf_device_idx               = 0
        self.update_device_ha_sensor_entity   = {}          # Contains info regarding update_device and needed entity changes
        self.device_list_control_default   = 'select'    # Select the Return to main menu as the default
        self.add_device_flag               = False
        self.add_device_enter_devicename_form_part_flag = False  # Add device started, True = form top part only displayed

        self.device_trkr_by_entity_id_all  = {}         # other platform device_tracker used to validate the ic3 entity is not used

        # Option selection lists on the Update apple_accts screen
        self.apple_acct_items_list          = []       # List of the apple_accts in the Gb.conf_tracking[apple_accts] parameter
        self.apple_acct_items_displayed     = []       # List of the apple_accts displayed on the device_list form
        self.aa_page_item                   = ['', '', '', '', '']  # Apple acct username last displayed on each page
        self.aa_page_no                     = 0        # apple_accts List form page number, starting with 0
        self.conf_apple_acct                = {}       # apple acct item selected
        self.apple_acct_items_by_username   = {}       # Selection list for the apple accounts on data_sources and reauth screens
        self.aa_idx                         = 0
        self.apple_acct_reauth_username     = ''
        self.add_apple_acct_flag            = False
        # self.scanned_for_fido2_key_names    = False
        self.reauth_form_fido2_key_names_list = {}        # Fido2 key names for REAUTH form

        self.icloud_list_text_by_fname      = {}
        self.icloud_list_text_by_fname2     = {}
        self.mobapp_list_text_by_entity_id  = {}         # mobile_app device_tracker info used in devices form for mobapp selection
        self.mobapp_list_text_by_entity_id  = MOBAPP_DEVICE_NONE_OPTIONS.copy()
        self.picture_by_filename            = {}
        self.picture_by_filename_base       = PICTURE_NONE_KEY_TEXT.copy()
        self.zone_name_key_text             = {}
        self.opt_picture_file_name_list     = []

        self.mobapp_scan_for_for_devicename = 'None'
        self.inactive_devices_key_text    = {}
        self.log_level_devices_key_text   = {}

        self.is_verification_code_needed  = False

        # Variables used for the display_text_as update
        self.dta_selected_idx      = UNSELECTED # Current conf index being updated
        self.dta_selected_idx_page = [0, 5]    # Selected idx to display on each page
        self.dta_page_no           = 0         # Current page being displayed
        self.dta_working_copy      = {0: '', 1: '', 2: '', 3: '', 4: '', 5: '', 6: '', 7: '', 8: '', 9: '',}

        # EvLog Parameter screen, Change Device Order fields
        self.cdo_devicenames   = {}
        self.cdo_new_order_idx = {}
        self.cdo_curr_idx      = 0

        # Dashboard Builder
        self.db_templates                = {}    # iCloud3 device templates from icloud3/dashboard folder
        self.db_templates_used           = []    # Templates used in master-dashboard template
        self.db_templates_used_by_device = []    # Templates used in master-dashboard template to be built
                                                    # by device rather than by template. the names start with
                                                    # template-device
        self.master_dashboard            = {}    # Master Dashboard dictionary (json str --> dict)
        self.dashboards                  = []    # List of dashboards (lovelace.icloud3_xxx files) in conig./storage)
        self.icloud3_dashboards          = []    # List of iCloud3 dashboards created by the Dashboard Builder
        self.ic3db_Dashboards_by_dbname  = {}    # HA Dashboard by dashboard name for Dashboards with Device-x available
        self.AllDashboards_by_dbname  = {}    # All HA Dashboard objects by dashboard name
        self.dbname                      = ''    # Dashboard  being created or updates
        self.Dashboard                   = None

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

        # Main View Info from the main_view_info_str on the Events Log view
        # These items are loaded when the ic3db dashboards are loaded. They are used to set ui_xxx values when
        # a device is added or deleted and the dashboards are recreated
        self.main_view_info_style_by_dbname          = {}  # Devices on the Main view of the dashboard
        self.main_view_info_dnames_by_dbname         = {}  # Devices on the Main view of the dashboard
        self.main_view_dbfile_length_by_dbname  = {}  # Length of the main view str from the Lovelace db file
        self.main_view_created_length_by_dbname = {}  # Length of the main view str right now
        self.main_view_infomsg_length_by_dbname = {}  # Length of the main view str right now


        # away_time_zone_adjustment
        self.away_time_zone_hours_key_text   = {}
        self.away_time_zone_devices_key_text = {}

        # Variables used for the system_settings s update
        self.www_directory_list = []

        # List of all sensors created by ic3 during startup by sensor.py that is used
        # in the exclude_sensors screen
        # Format: ('gary_iphone_zone_distance': 'Gary ZoneDistance (gary_iphone_zone_distance)')
        self.sensors_fname_list     = []
        self.excluded_sensors       = ['None']
        self.excluded_sensors_removed = []
        self.sensors_list_filter    = '?'

        self.abort_flag = ('version' not in Gb.conf_profile)
        if self.abort_flag: return

        # AppleAcct object and variables. Using local variables rather than the Gb AppleAcct variables
        # in case the username/password is changed and another account is accessed. These will not
        # intefer with ones already in use by iC3. The Global Gb variables will be set to the local
        # variables if they were changes and a iC3 Restart was selected when finishing the config setup
        self._initialize_self_AppleAcct_fields_from_Gb()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            INIT
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_init(self, user_input=None):
        if self.initialize_options_required_flag:
            self.initialize_options()

        self.errors = {}
        self.header_msg = ''

        if self.abort_flag:
            return await self.async_step_restart_ha()

        return await self.async_step_menu_0()

#-------------------------------------------------------------------------------------------
    def _logui(self, user_input):
        _log(f"{user_input=} {self.errors=} ")

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
                    if conf_device[CONF_TRACKING_MODE] != INACTIVE_DEVICE}

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            MENU
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_menu_0(self, user_input=None, errors=None):

        # If the initial config file was just installed:
        #   - Check master_dashboard to only do this once
        #   - Add 'local.icloud3.event-log-card.js to the Lovelace Resources
        #   - Build and add the lovelace.ic3db-icloud3 dashboard panel to the Lovelace dashboards
        if (Gb.conf_profile[CONF_VERSION] <= 0
                and is_empty(self.master_dashboard)):
            await start_ic3.update_lovelace_resource_event_log_js_entry(silent=True)

            icloud3_dashboard_status = await dbb.build_initial_icloud3_dashboard(self)
            if icloud3_dashboard_status:
                self.header_msg = 'dashboard_created_initial'

        self.menu_page_no = 0
        return await self.async_step_menu(user_input, errors)

    async def async_step_menu_1(self, user_input=None, errors=None):
        self.menu_page_no = 1
        return await self.async_step_menu(user_input, errors)

    async def async_step_menu(self, user_input=None, errors=None):
        self.step_id = f"menu_{self.menu_page_no}"
        self.return_to_step_id_1 = self.return_to_step_id_2 = ''
        self.errors = errors or {}
        await self._async_write_icloud3_configuration_file()

        Gb.trace_prefix = 'CONFIG'
        Gb.config_flow_flag = True

        if Gb.internet_error:
            self.header_msg = 'internet_error'
        elif self.AppleAcct is None and self.username:
            self.header_msg = 'apple_acct_not_logged_into'
        elif self.is_verification_code_needed:
            self.header_msg ='verification_code_needed'
        else:
            for AppleAcct in Gb.AppleAcct_by_username.values():
                if AppleAcct.terms_of_use_update_needed:
                    self.header_msg ='apple_acct_terms_of_use_update_needed'
                    break

        if user_input is None:
            self._set_inactive_devices_header_msg()
            utils.set_header_msg(self)

            return self.async_show_form(step_id=self.step_id,
                                        data_schema=forms.form_menu(self),
                                        errors=self.errors,
                                        last_step=False)

        self.menu_item_selected[self.menu_page_no] = user_input['menu_items']
        user_input, menu_item = utils.menu_text_to_item(self, user_input, 'menu_items')
        user_input, menu_action_item = utils.menu_text_to_item(self, user_input, 'action_items')

        if menu_action_item.startswith('exit'):
            await self.exit_configure_tasks()

            if ('restart' in self.config_parms_update_control
                    or self._set_inactive_devices_header_msg() in ['all', 'most']):
                return await self.async_step_restart_icloud3()

            else:
                Gb.config_parms_update_control   = self.config_parms_update_control.copy()
                self.config_parms_update_control = []
                log_debug_msg(  f"⭐ Exit Configure Settings, UpdateParms-"
                                f"{list_to_str(Gb.config_parms_update_control)}")

                data = {'updated': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
                return self.async_create_entry(title="iCloud3", data={})

        elif menu_action_item == 'next_page_0':
            self.menu_page_no = 0
            self.step_id = 'menu_0'
        elif menu_action_item == 'next_page_1':
            self.menu_page_no = 1
            self.step_id = 'menu_1'

        elif 'menu_item' == '':
            pass
        elif menu_item == 'data_source':
            return await self.async_step_data_source()
        elif menu_item == 'verification_code':
            return await self.async_step_reauth()
        elif menu_item == 'device_list':
            return await self.async_step_device_list()
        elif menu_item == 'sensors':
            return await self.async_step_sensors()
        elif menu_item == 'dashboard_builder':
            return await self.async_step_dashboard_builder()
        elif menu_item == 'tools':
            return await self.async_step_tools()
        elif menu_item == 'away_time_zone':
            return await self.async_step_away_time_zone()
        elif menu_item == 'format_settings':
            return await self.async_step_format_settings()
        elif menu_item == 'display_text_as':
            return await self.async_step_display_text_as()
        elif menu_item == 'tracking_parameters':
            return await self.async_step_tracking_parameters()
        elif menu_item == 'inzone_intervals':
            return await self.async_step_inzone_intervals()
        elif menu_item == 'waze':
            return await self.async_step_waze_main()
        elif menu_item == 'special_zones':
            return await self.async_step_special_zones()

        self._set_inactive_devices_header_msg()
        utils.set_header_msg(self)

        return self.async_show_form(step_id=self.step_id,
                            data_schema=forms.form_menu(self),
                            errors=self.errors,
                            last_step=False)

#-------------------------------------------------------------------------------------------
    async def exit_configure_tasks(self):
        Gb.config_flow_flag = False
        self.initialize_options_required_flag = False

        # If the initial config file was just installed, set it to 'has been reviewed'
        if Gb.conf_profile[CONF_VERSION] <= 0:
            Gb.conf_profile[CONF_VERSION] = 1
            list_add(self.config_parms_update_control, 'restart')
            user_input = {CONF_VERSION: 1}
            self._update_config_file_tracking(user_input, update_config_flag=True)

        # Update the *ic3db- dashboard views when devices have been added or deleted
        if self.rebuild_ic3db_dashboards:
            dbb.load_ic3db_dashboards_from_ha_data(self)

            if isnot_empty(self.ic3db_Dashboards_by_dbname):
                await dbb.update_ic3db_dashboards_new_deleted_devices(self)
                self.rebuild_ic3db_dashboards = False

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             RESTART ICLOUD3
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_restart_icloud3(self, user_input=None, errors=None):
        '''
        A restart is required due to tracking, devices or sensors changes. Ask if this
        should be done now or later.
        '''

        self.step_id = 'restart_icloud3'
        self.errors = errors or {}
        self.errors_user_input = {}
        await config_sensors.update_configure_file_device_sensors()
        await self._async_write_icloud3_configuration_file()

        for devicename in Gb.sensors_removed_by_devicename.keys():
            ic3_sensor.log_sensors_added_deleted('ADDED', devicename)
            ic3_sensor.log_sensors_added_deleted('REMOVED', devicename)

        user_input, action_item = utils.action_text_to_item(self, user_input)
        utils.log_step_info(self, user_input, action_item)

        if user_input is not None or action_item is not None:
            if action_item == 'goto_menu':
                return await self.async_step_menu_0()

            elif action_item.startswith('restart_ha'):
                await Gb.hass.services.async_call("homeassistant", "restart")
                return self.async_abort(reason="ha_restarting")

            elif action_item == 'review_inactive_devices':
                self.return_to_step_id_1 = 'restart_icloud3'
                return await self.async_step_review_inactive_devices()

            if action_item == 'restart_ic3_now':
                Gb.config_parms_update_control = self.config_parms_update_control.copy()

            elif action_item == 'restart_ic3_later':
                if 'restart' in self.config_parms_update_control:
                    list_del(self.config_parms_update_control, 'restart')
                Gb.config_parms_update_control = self.config_parms_update_control.copy()
                self.config_parms_update_control = []

            # Update the *ic3db- dashboard views when devices have been added or deleted
            if self.rebuild_ic3db_dashboards:
                await dbb.update_ic3db_dashboards_new_deleted_devices(self)
                self.rebuild_ic3db_dashboards = False

            data = {}
            data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
            log_debug_msg(f"⭐ Exit Configure Settings, UpdateParms-{Gb.config_parms_update_control}")

            # If the polling loop has been set up, set the restart flag to trigger a restart when
            # no devices are being updated. Otherwise, there were probably no devices to track
            # when first loaded and a direct restart must be done.
            return self.async_create_entry(title="iCloud3", data={})

        self._set_inactive_devices_header_msg()
        utils.set_header_msg(self)

        return self.async_show_form(step_id='restart_icloud3',
                        data_schema=forms.form_restart_icloud3(self),
                        errors=self.errors,
                        last_step=False)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REVIEW INACTIVE DEVICES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_review_inactive_devices(self, user_input=None, errors=None):
        '''
        There are inactive devices. Display the list of devices and confirm they should
        remain active.
        ACTION_LIST_OPTIONS['inactive_to_track'],
        ACTION_LIST_OPTIONS['inactive_keep_inactive']]
        '''
        self.step_id = 'review_inactive_devices'
        self.errors = errors or {}
        self.errors_user_input = {}

        user_input, action_item = utils.action_text_to_item(self, user_input)
        utils.log_step_info(self, user_input, action_item)

        if user_input is None and action_item is None:
            return self.async_show_form(step_id='review_inactive_devices',
                        data_schema=forms.form_review_inactive_devices(self),
                        errors=self.errors,
                        last_step=False)

        if action_item == 'next_page_devices':
            return self.async_show_form(step_id='review_inactive_devices',
                    data_schema=forms.form_review_inactive_devices(self, start_cnt=5),
                    errors=self.errors,
                    last_step=False)

        if action_item == 'inactive_to_track':
            devicename_list = [self.inactive_devices_key_text.values()] \
                                if   user_input['inactive_devices'] == [] \
                                else user_input['inactive_devices']

            for conf_device in Gb.conf_devices:
                devicename = conf_device[CONF_IC3_DEVICENAME]
                if devicename in devicename_list:
                    conf_device[CONF_TRACKING_MODE] = TRACK_DEVICE

                if devicename not in Gb.DeviceTrackers_by_devicename:
                    config_sensors.create_device_tracker_and_sensor_entities(self, devicename, conf_device)

            self.header_msg = 'action_completed'
            list_add(self.config_parms_update_control, 'restart')
            self._update_config_file_tracking(update_config_flag=True)
            action_item = 'goto_previous'


        if action_item == 'goto_previous':
            if self.return_to_step_id_1 == 'restart_icloud3':
                return await self.async_step_restart_icloud3()

        return await self.async_step_menu()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  DISPLAY AND HANDLE USER INPUT FORMS
#
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
            user_input, action_item = utils.action_text_to_item(self, user_input)

        if action_item == 'cancel_goto_menu':
            return True
        elif self.step_id == 'data_source':
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
        elif self.step_id == "sensors":
            config_sensors.remove_and_create_sensors(self, user_input)

        utils.log_step_info(self, user_input, action_item)

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
                    'yes_fct': self.confirm_test_yes,
                    'yes_fct_async': self.async_confirm_test_yes,
                    'action_desc': TOOL_LIST[acton_item],
                    'return_to_fct': None,
                    'return_to_async_step_fct': self.async_step_tools}

        '''
        self.step_id = 'confirm_action'
        self.errors = {}
        self.errors_user_input = {}

        if user_input is None or 'action_items' not in user_input:
            return self.async_show_form(step_id='confirm_action',
                                        data_schema=forms.form_confirm_action(
                                            self, action_desc=self.confirm_action['action_desc']),
                                        errors=self.errors)

        user_input, action_item = utils.action_text_to_item(self, user_input)
        utils.log_step_info(self, user_input, action_item)

        if action_item == 'confirm_action_yes':
            self.config_file_commit_updates = True
            list_add(self.config_parms_update_control, 'restart')

            if self.confirm_action['yes_fct'] is not None:
                self.confirm_action['yes_fct']()
                self.errors = {'base': 'action_completed'}
                self.confirm_action['yes_fct'] = None

            elif self.confirm_action['yes_fct_async'] is not None:
                await self.confirm_action['yes_fct_async']()

                self.errors = {'base': 'action_completed'}
                self.confirm_action['yes_fct_async'] = None

        if self.confirm_action['return_to_fct']:
            return self.confirm_action['return_to_fct'](errors=self.errors)

        return await self.confirm_action['return_to_async_step_fct'](errors=self.errors)


#-------------------------------------------------------------------------------------------
    def _set_example_zone_name(self):
        '''
        This is used in config_flow_forms

        'fname': 'HA Zone Friendly Name used by zone automation triggers (TheShores)',
        'zone': 'HA Zone entity_id (the_shores)',
        'name': 'iCloud3 reformated Zone entity_id (zone.the_shores → TheShores)',
        'title': 'iCloud3 reformated Zone entity_id (zone.the_shores → The Shores)'
        '''
        DISPLAY_ZONE_FORMAT_OPTIONS.update(DISPLAY_ZONE_FORMAT_OPTIONS_BASE)

        Zone = [Zone    for zone, Zone in Gb.HAZones_by_zone.items()
                        if instr(Zone.zone, '_')]
        if Zone == []:
            Zone = [Zone    for zone, Zone in Gb.HAZones_by_zone.items()
                            if  zone != 'home']
        if Zone != []:
            exZone = Zone[0]
            self._dzf_set_example_zone_name_text(ZONE, 'the_shores', exZone.zone)
            self._dzf_set_example_zone_name_text(FNAME, 'The Shores', exZone.fname)
            self._dzf_set_example_zone_name_text(FNAME, 'TheShores', exZone.fname)
            self._dzf_set_example_zone_name_text('fname/Home', 'TheShores', exZone.fname)
            self._dzf_set_example_zone_name_text(NAME, 'the_shores', exZone.zone)
            self._dzf_set_example_zone_name_text(NAME, 'TheShores', exZone.name)
            self._dzf_set_example_zone_name_text(TITLE, 'the_shores', exZone.zone)
            self._dzf_set_example_zone_name_text(TITLE, 'The Shores', exZone.title)

    def _dzf_set_example_zone_name_text(self, key, example_text, real_text):
        if key in DISPLAY_ZONE_FORMAT_OPTIONS:
            DISPLAY_ZONE_FORMAT_OPTIONS[key] = \
                DISPLAY_ZONE_FORMAT_OPTIONS[key].replace(example_text, real_text)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            TRACKING PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_tracking_parameters(self, user_input=None, errors=None):
        self.step_id = 'tracking_parameters'
        user_input, action_item = utils.action_text_to_item(self, user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()


        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='tracking_parameters',
                            data_schema=forms.form_tracking_parameters(self),
                            errors=self.errors)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              FORMAT SETTINGS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_format_settings(self, user_input=None, errors=None):
        self.step_id = 'format_settings'
        user_input, action_item = utils.action_text_to_item(self, user_input)

        if self.www_directory_list == []:
            start_dir = 'www'
            self.www_directory_list = await Gb.hass.async_add_executor_job(
                                                            file_io.get_directory_list,
                                                            start_dir)

        if self.common_form_handler(user_input, action_item, errors):
            if action_item == 'save':
                Gb.picture_www_dirs = Gb.conf_profile[CONF_PICTURE_WWW_DIRS].copy()
                self.picture_by_filename = {}
                await lists.build_picture_filename_selection_list(self)

            return await self.async_step_menu()

        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='format_settings',
                            data_schema=forms.form_format_settings(self),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _format_device_text_hdr(conf_device):
        device_text = ( f"{conf_device[CONF_FNAME]} "
                        f"({conf_device[CONF_IC3_DEVICENAME]})")
        if conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
            device_text += ", 🅜 MONITOR"
        elif conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
            device_text += ", ✪ INACTIVE"

        return device_text


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            INZONE INTERVALS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_inzone_intervals(self, user_input=None, errors=None):
        self.step_id = 'inzone_intervals'
        user_input, action_item = utils.action_text_to_item(self, user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if utils.any_errors(self):
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='inzone_intervals',
                            data_schema=forms.form_inzone_intervals(self),
                            errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            WAZE MAIN
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_waze_main(self, user_input=None, errors=None):
        self.step_id = 'waze_main'
        user_input, action_item = utils.action_text_to_item(self, user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='waze_main',
                            data_schema=forms.form_waze_main(self),
                            errors=self.errors,
                            last_step=True)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SPECIAL ZONES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_special_zones(self, user_input=None, errors=None):
        self.step_id = 'special_zones'
        user_input, action_item = utils.action_text_to_item(self, user_input)
        await lists.build_zone_selection_list(self)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='special_zones',
                            data_schema=forms.form_special_zones(self),
                            errors=self.errors)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SENSORS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_sensors(self, user_input=None, errors=None):

        self.step_id = 'sensors'
        self.errors = errors or {}
        await self._async_write_icloud3_configuration_file()
        user_input, action_item = utils.action_text_to_item(self, user_input)
        utils.log_step_info(self, user_input, action_item)

        if Gb.conf_sensors[CONF_EXCLUDED_SENSORS] == []:
            Gb.conf_sensors[CONF_EXCLUDED_SENSORS] = ['None']

        if user_input is None:
            return self.async_show_form(step_id='sensors',
                                        data_schema=forms.form_sensors(self),
                                        errors=self.errors)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        self.set_default_sensors(user_input)

        if action_item == 'set_to_default_sensors':
            user_input = DEFAULT_SENSORS_CONF.copy()
            utils.log_step_info(self, user_input, action_item)
            return self.async_show_form(step_id='sensors',
                                        data_schema=forms.form_sensors(self, user_input=user_input),
                                        errors=self.errors)

        # TfZ Sensors are not configured via config_flow but built in
        # config_flow from the distance, time & zone sensors
        tfz_sensors_base = ['zone_info']
        tfz_sensors_base.extend(user_input[CONF_SENSORS_TRACKING_TIME])
        tfz_sensors_base.extend(user_input[CONF_SENSORS_TRACKING_DISTANCE])
        tfz_sensors = []
        for sensor in tfz_sensors_base:
            if sensor in SENSOR_GROUPS['track_from_zone']:
                tfz_sensors.append(f"tfz_{sensor}")
        user_input[CONF_SENSORS_TRACK_FROM_ZONES] = tfz_sensors

        if action_item == 'exclude_sensors':
            self.excluded_sensors = Gb.conf_sensors[CONF_EXCLUDED_SENSORS].copy()
            self.sensors_list_filter = '?'
            return await self.async_step_exclude_sensors()

        if (action_item == 'save'
                and self.common_form_handler(user_input, action_item, errors)):
            Gb.sensor_names_by_devicename = {}

            return await self.async_step_menu()

        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='sensors',
                            data_schema=forms.form_sensors(self),
                            errors=self.errors)

#................................................................................
    @staticmethod
    def set_default_sensors(user_input):
        '''
        Always check default sensors
        '''
        if BATTERY not in user_input[CONF_SENSORS_DEVICE]:
            user_input[CONF_SENSORS_DEVICE].append(BATTERY)
        if 'md_battery' not in user_input[CONF_SENSORS_MONITORED_DEVICES]:
            user_input[CONF_SENSORS_MONITORED_DEVICES].append('md_battery')
        if ARRIVAL_TIME not in user_input[CONF_SENSORS_TRACKING_TIME]:
            user_input[CONF_SENSORS_TRACKING_TIME].append(ARRIVAL_TIME)
        if TRAVEL_TIME not in user_input[CONF_SENSORS_TRACKING_TIME]:
            user_input[CONF_SENSORS_TRACKING_TIME].append(TRAVEL_TIME)
        if HOME_DISTANCE not in user_input[CONF_SENSORS_TRACKING_DISTANCE]:
            user_input[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)
        if NEXT_UPDATE not in user_input[CONF_SENSORS_TRACKING_UPDATE]:
            user_input[CONF_SENSORS_TRACKING_UPDATE].append(NEXT_UPDATE)

        return user_input

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            EXCLUDE SENSORS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_exclude_sensors(self, user_input=None, errors=None):

        self.step_id = 'exclude_sensors'
        self.errors = errors or {}
        await self._async_write_icloud3_configuration_file()
        user_input, action_item = utils.action_text_to_item(self, user_input)

        if self.excluded_sensors == []:
            self.excluded_sensors = ['None']

        if self.sensors_fname_list == []:
                Sensors = []
                for devicename in Gb.Devices_by_devicename.keys():
                    devicename_Sensors = [Sensor for Sensor in Gb.Sensors_by_devicename[devicename].values()]
                    Sensors.extend(devicename_Sensors)

                self.sensors_fname_list = [Sensor.fname_entity_name for Sensor in Sensors]
                self.sensors_fname_list.sort()

        if user_input is None:
            return self.async_show_form(step_id='exclude_sensors',
                                        data_schema=forms.form_exclude_sensors(self),
                                        errors=self.errors)

        utils.log_step_info(self, user_input, action_item)
        sensors_list_filter = user_input['filter'].lower().replace('?', '').strip()

        if (self.sensors_list_filter == sensors_list_filter
                and len(self.excluded_sensors) == len(user_input[CONF_EXCLUDED_SENSORS])
                and user_input['filtered_sensors'] == []):
            self.sensors_list_filter = '?'
        else:
            self.sensors_list_filter = sensors_list_filter or '?'

        if action_item == 'cancel_goto_previous':
            return await self.async_step_sensors()

        if (action_item == 'save_stay'
                or user_input[CONF_EXCLUDED_SENSORS] != self.excluded_sensors
                or user_input['filtered_sensors'] != []):
            user_input = self._update_excluded_sensors(user_input)

            if Gb.conf_sensors[CONF_EXCLUDED_SENSORS] != self.excluded_sensors:
                Gb.conf_sensors[CONF_EXCLUDED_SENSORS] = self.excluded_sensors.copy()
                Gb.sensor_names_by_devicename = {}
                self._update_config_file_general(user_input, update_config_flag=True)

                self.errors['excluded_sensors'] = 'excluded_sensors_ha_restart'
                list_add(self.config_parms_update_control, ['restart_ha', 'restart'])

        return self.async_show_form(step_id='exclude_sensors',
                            data_schema=forms.form_exclude_sensors(self),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _update_excluded_sensors(self, user_input):

        excluded_sensors = []
        excluded_sensors.extend(user_input[CONF_EXCLUDED_SENSORS])
        excluded_sensors.extend(user_input['filtered_sensors'])
        self.excluded_sensors = list(set(excluded_sensors))
        self.excluded_sensors.sort()

        self.excluded_sensors_removed = [sensor_fname
                                        for sensor_fname in Gb.conf_sensors[CONF_EXCLUDED_SENSORS]
                                        if sensor_fname not in self.excluded_sensors]
        self.sensors_fname_list.extend(self.excluded_sensors)
        self.sensors_fname_list = list(set(self.sensors_fname_list))
        self.sensors_fname_list.sort()

        if self.excluded_sensors == []:
            self.excluded_sensors = ['None']
        elif len(self.excluded_sensors) > 1 and 'None' in self.excluded_sensors:
            self.excluded_sensors.remove('None')

        # Add filtered sensors just selected/unselected
        user_input[CONF_EXCLUDED_SENSORS] = self.excluded_sensors.copy()
        return user_input


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISPLAY TEXT AS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_display_text_as(self, user_input=None, errors=None):
        self.step_id = 'display_text_as'
        user_input, action_item = utils.action_text_to_item(self, user_input)

        if user_input is None:
            if (self.dta_selected_idx == UNSELECTED):
                self.dta_selected_idx = 0
                self.dta_selected_idx_page = [0, 5]
                self.dta_page_no = 0
                idx = UNSELECTED
                for dta_text in Gb.conf_general[CONF_DISPLAY_TEXT_AS]:
                    idx += 1
                    self.dta_working_copy[idx] = dta_text
            return self.async_show_form(step_id='display_text_as',
                                        data_schema=forms.form_display_text_as(self),
                                        errors=self.errors)

        user_input = utils.option_text_to_parm(user_input,
                                CONF_DISPLAY_TEXT_AS, self.dta_working_copy)
        self.dta_selected_idx = int(user_input[CONF_DISPLAY_TEXT_AS])
        self.dta_selected_idx_page[self.dta_page_no] = self.dta_selected_idx
        utils.log_step_info(self, user_input, action_item)

        if action_item == 'next_page_items':
            self.dta_page_no = 1 if self.dta_page_no == 0 else 0
            return await self.async_step_display_text_as()

        elif action_item == 'select_text_as':
            return await self.async_step_display_text_as_update(user_input)

        elif action_item == 'cancel_goto_menu':
            self.dta_selected_idx = UNSELECTED
            return await self.async_step_menu()

        elif action_item == 'save':
            idx = self.dta_selected_idx = UNSELECTED
            dta_working_copy_list = DEFAULT_GENERAL_CONF[CONF_DISPLAY_TEXT_AS].copy()
            for temp_dta_text in self.dta_working_copy.values():
                if instr(temp_dta_text,'>'):
                    idx += 1
                    dta_working_copy_list[idx] = temp_dta_text

            user_input[CONF_DISPLAY_TEXT_AS] = dta_working_copy_list

            self._update_config_file_general(user_input)

            return await self.async_step_menu()

        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='display_text_as',
                        data_schema=forms.form_display_text_as(self),
                        errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISPLAY TEXT AS UPDATE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_display_text_as_update(self, user_input=None, errors=None):
        self.step_id = 'display_text_as_update'
        user_input, action_item = utils.action_text_to_item(self, user_input)
        utils.log_step_info(self, user_input, action_item)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_display_text_as()

        if action_item == 'save':
            text_from = user_input['text_from'].strip()
            text_to   = user_input['text_to'].strip()
            if  text_from and text_to:
                self.dta_working_copy[self.dta_selected_idx] = f"{text_from} > {text_to}"
            else:
                self.dta_working_copy[self.dta_selected_idx] = f"#{self.dta_selected_idx + 1}"

            return await self.async_step_display_text_as()

        if action_item == 'clear_text_as':
            self.dta_working_copy[self.dta_selected_idx] = f"#{self.dta_selected_idx + 1}"

            return await self.async_step_display_text_as()

        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='display_text_as_update',
                        data_schema=forms.form_display_text_as_update(self),
                        errors=self.errors)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              PICTURE DIRECTORY FILTER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_picture_dir_filter(self, user_input=None, errors=None):
        self.step_id = 'picture_dir_filter'
        user_input, action_item = utils.action_text_to_item(self, user_input)
        utils.log_step_info(self, user_input, action_item)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_update_device()

        if self.www_directory_list == []:
            self.www_directory_list = \
                await Gb.hass.async_add_executor_job(file_io.get_directory_list, 'www')

        if action_item == 'save':
            Gb.picture_www_dirs = []
            for group_no in ['1', '2', '3', '4', '5']:
                ui_group_name = f"www_group_{group_no}"
                if ui_group_name in user_input:
                    for dir in user_input[ui_group_name]:
                        list_add(Gb.picture_www_dirs, dir)

            Gb.conf_profile[CONF_PICTURE_WWW_DIRS] = Gb.picture_www_dirs
            self.picture_by_filename = {}
            await lists.build_picture_filename_selection_list(self)
            self._update_config_file_general(user_input)
            return await self.async_step_update_device()

        return self.async_show_form(step_id='picture_dir_filter',
                            data_schema=forms.form_picture_dir_filter(self),
                            errors=self.errors)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           TOOLS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_tools(self, user_input=None, errors=None):
        '''
        1. Delete the device from the tracking devices list and adjust the device index
        2. Delete all devices
        3. Clear the iCloud, Mobile App and track_from_zone fields from all devices
        '''
        self.step_id = 'tools'
        self.errors = errors or {}
        self.errors_user_input = {}



        await self._async_write_icloud3_configuration_file()

        if user_input is None or 'confrm_action_item' in user_input:
            return self.async_show_form(step_id='tools',
                                        data_schema=forms.form_tools(self),
                                        errors=self.errors)

        action_item = TOOL_LIST_ITEMS_KEY_BY_TEXT.get(user_input['action_items'], '')
        user_input['action_items'] = action_item
        user_input = utils.option_text_to_parm(user_input,
                                CONF_LOG_LEVEL, LOG_LEVEL_OPTIONS)

        utils.log_step_info(self, user_input, action_item)

        # Log Level was changed
        if (user_input[CONF_LOG_LEVEL] != Gb.conf_general[CONF_LOG_LEVEL]
                or user_input[CONF_LOG_LEVEL_DEVICES] != Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
            if (user_input[CONF_LOG_LEVEL_DEVICES] == []
                    or len(user_input[CONF_LOG_LEVEL_DEVICES]) >= len(Gb.Devices)):
                user_input[CONF_LOG_LEVEL_DEVICES] = ['all']
            elif len(user_input[CONF_LOG_LEVEL_DEVICES]) > 1:
                list_del(user_input[CONF_LOG_LEVEL_DEVICES], 'all')

            if is_empty(user_input[CONF_LOG_LEVEL_DEVICES]):
                user_input[CONF_LOG_LEVEL_DEVICES] = ['all']
            Gb.log_level_devices = user_input[CONF_LOG_LEVEL_DEVICES].copy()

            self._update_config_file_general(user_input)
            # return await self.async_step_tools()
            action_item = 'goto_menu'

        if action_item == 'goto_menu':
            return await self.async_step_menu()

        self.confirm_action = {
                'yes_fct': None,
                'yes_fct_async': None,
                'action_desc': TOOL_LIST[action_item],
                'return_to_fct': None,
                'return_to_async_step_fct': self.async_step_tools}

        if action_item == 'reset_data_source':
            self.confirm_action['yes_fct'] = self._reset_all_devices_data_source_fields

        elif action_item == 'reset_tracking':
            self.confirm_action['yes_fct'] = self.reset_icloud3_config_file_tracking

        elif action_item == 'reset_general':
            self.confirm_action['yes_fct'] = self.reset_icloud3_config_file_general

        elif action_item == 'reset_config':
            self.confirm_action['yes_fct'] = self.reset_icloud3_config_file_tracking_general

        elif action_item == 'del_apple_acct_cookies':
            self.confirm_action['return_to_async_step_fct'] = self.async_step_restart_ha
            self.confirm_action['yes_fct_async'] = self.async_delete_all_apple_cookie_files

        elif action_item == 'del_icloud3_config_files':
            self.confirm_action['return_to_async_step_fct'] = self.async_step_restart_ha
            self.confirm_action['yes_fct_async'] = self.async_delete_all_ic3_configuration_files

        elif action_item == 'fix_entity_name_error':
            if ic3_sensor.correct_sensor_entity_ids_with_2_extension(verify=True):
                ic3_sensor.correct_sensor_entity_ids_with_2_extension()
                self.base='fix_entity_name_complete'
            else:
                self.base='fix_entity_name_not_needed'

        if (self.confirm_action['yes_fct']
                or self.confirm_action['yes_fct_async']):
            return await self.async_step_confirm_action()

        elif action_item == 'restart_ha_reload_icloud3':
            return await self.async_step_restart_ha_reload_icloud3()

        list_add(self.config_parms_update_control, ['tracking', 'restart'])

        return await self.async_step_tools(errors=self.errors)

#................................................................................
    def reset_icloud3_config_file_tracking(self):

        self._delete_all_devices()
        Gb.conf_apple_accounts = []
        Gb.conf_devices        = []
        Gb.conf_tracking       = DEFAULT_TRACKING_CONF.copy()

#................................................................................
    def reset_icloud3_config_file_general(self):

        Gb.conf_general = DEFAULT_GENERAL_CONF.copy()
        Gb.log_level    = Gb.conf_general[CONF_LOG_LEVEL]

#................................................................................u
    def reset_icloud3_config_file_tracking_general(self):

        self.reset_icloud3_config_file_tracking()
        self.reset_icloud3_config_file_general()

#................................................................................
    async def async_delete_all_apple_cookie_files(self):
        '''
        Delete all files in the .storage/icloud3 directory
        '''

        post_alert(f"All iCloud3 Configuration files are being deleted")
        list_add(self.config_parms_update_control, ['restart_ha'])

        return await self.delete_all_files_and_remove_directory(Gb.icloud_cookie_directory)

#................................................................................
    async def async_delete_all_ic3_configuration_files(self):
        '''
        Delete all files in the .storage/icloud3 directory
        '''

        post_alert(f"All iCloud3 Configuration files are being deleted")

        return await self.delete_all_files_and_remove_directory(Gb.ha_storage_icloud3)

#................................................................................
    async def delete_all_files_and_remove_directory(self, start_dir):
        for Device in Gb.Devices:
            Device.pause_tracking()

        # start_dir = Gb.ha_storage_icloud3
        file_filter = []
        files = await Gb.hass.async_add_executor_job(
                                            file_io.get_filename_list,
                                            start_dir,
                                            file_filter)

        try:
            for file in files:
                await file_io.async_delete_file(f"{ start_dir}/{file}")

            if isnot_empty(files):
                await file_io.async_delete_directory( start_dir)

                list_add(self.config_parms_update_control, 'restart_ha')

        except Exception as err:
            log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            RESTART HA
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_restart_ha(self, user_input=None, errors=None):
        '''
        A restart HA or reload iCloud3
        '''
        self.step_id = 'restart_ha'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = utils.action_text_to_item(self, user_input)

        if user_input is None or action_item is None:
            return self.async_show_form(step_id='restart_ha',
                                    data_schema=forms.form_restart_ha(self),
                                    errors=self.errors)

        if action_item == 'restart_ha':
            await Gb.hass.services.async_call("homeassistant", "restart")
            return self.async_abort(reason="ha_restarting")

        elif action_item == 'restart_icloud3':
            list_add(self.config_parms_update_control, 'restart')

        elif action_item.startswith('exit'):
            return self.async_create_entry(title="iCloud3", data={})

        return await self.async_step_menu()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            RESTART HA, RELOAD ICLOUD3
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_restart_ha_reload_icloud3(self, user_input=None, errors=None):
        '''
        A restart HA or reload iCloud3
        '''
        self.step_id = 'restart_ha_reload_icloud3'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = utils.action_text_to_item(self, user_input)

        if user_input is None or action_item is None:
            return self.async_show_form(step_id='restart_ha_reload_icloud3',
                                    data_schema=forms.form_restart_ha_reload_icloud3(self),
                                    errors=self.errors)

        if action_item == 'restart_ha':
            await Gb.hass.services.async_call("homeassistant", "restart")
            return self.async_abort(reason="ha_restarting")

        # elif action_item == 'reload_icloud3':
        #     post_event("RELOAD ICLOUD3")
        #     write_config_file_to_ic3log()
        #     await config_file.async_write_icloud3_configuration_file()
        #     close_ic3log_file()

        #     await Gb.hass.services.async_call(
        #             "homeassistant",
        #             "reload_config_entry",
        #             {'device_id': Gb.ha_device_id_by_devicename[DOMAIN]},)

        #     return self.async_abort(reason="ic3_reloading")

        return await self.async_step_menu()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  VALIDATE DATA AND UPDATE CONFIG FILE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def _async_write_icloud3_configuration_file(self, force_write=False):
        '''
        Write the updated configuration file to .storage/icloud3/configuration
        The config file updates are done by setting the commit_updates flag in
        the update routines and adding a call to this fct on screen changes so they
        are done using async updates. The screen handlers are run in async mode
        while the update fcts are not.
        '''
        if self.config_file_commit_updates or force_write is True:
            await config_file.async_write_icloud3_configuration_file()

            self.config_file_commit_updates = False
            self.header_msg = 'conf_updated'
            self.errors['base'] = 'conf_updated'

            # Updating the config file will encode the password. Make sure the
            # password is deoded in the self.conf_apple_acct variable in case it
            # is mapped to the Gb.conf_ale_accounts variable
            if isnot_empty(self.conf_apple_acct):
                self.conf_apple_acct[CONF_PASSWORD] = \
                        decode_password(self.conf_apple_acct[CONF_PASSWORD])


#-------------------------------------------------------------------------------------------
    def _update_config_file_general(self, user_input, update_config_flag=None):
        '''
        Update the configuration parameters and write to the icloud3.configuration file

        Parameters:
            update_config_flag - The config_tracking, conf_devices or conf_apple_accounts
                has already been updated. Make sure the changes are saved.
        '''
        # The username/password may be in the user_input from the update_data_sources form
        # or it's subforms. If so, make sure it is set the the primary username/password
        update_config_flag = False if update_config_flag is None else True

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
                    Gb.conf_tracking[pname] = pvalue
                    list_add(self.config_parms_update_control, ['tracking', 'restart'])

            if pname in Gb.conf_general:
                if Gb.conf_general[pname] != pvalue:
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
                    Gb.conf_sensors[pname] = pvalue
                    list_add(self.config_parms_update_control, 'sensors')

            if pname in Gb.conf_profile:
                if Gb.conf_profile[pname] != pvalue:
                    Gb.conf_profile[pname] = pvalue
                    list_add(self.config_parms_update_control, ['profile', 'evlog'])

        if self.config_parms_update_control or update_config_flag:
            # If default or converted file, update version so the
            # ic3 parameters are now handled by config_flow
            if Gb.conf_profile[CONF_VERSION] <= 0:
                Gb.conf_profile[CONF_VERSION] = 1

            self.config_file_commit_updates = True

        return

#-------------------------------------------------------------------------------------------
    def _update_config_file_tracking(self, user_input=None, update_config_flag=None):
        '''
        Update the configuration parameters and write to the icloud3.configuration file

        This is used for updating the devices, Apple account, and some profile items
        in the config file That requires an iCloud3 restart

        Parameters:
            update_config_flag - The config_tracking, conf_devices or conf_apple_accounts
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
        update_config_flag = False if update_config_flag is None else True

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
                update_config_flag = True

        if update_config_flag:
            if Gb.conf_apple_accounts:
                Gb.conf_tracking[CONF_USERNAME] = Gb.conf_apple_accounts[0][CONF_USERNAME]
                Gb.conf_tracking[CONF_PASSWORD] = Gb.conf_apple_accounts[0][CONF_PASSWORD]
            Gb.conf_tracking[CONF_APPLE_ACCOUNTS] = Gb.conf_apple_accounts
            Gb.conf_tracking[CONF_DEVICES]        = Gb.conf_devices
            list_add(self.config_parms_update_control, ['tracking', 'restart'])
            self.config_file_commit_updates = True

            Gb.sensor_names_by_devicename = {}

#-------------------------------------------------------------------------------------------
    def _validate_format_settings(self, user_input):
        '''
        The display_zone_format may contain '(Example: ...). If so, strip it off.
        '''
        user_input = utils.option_text_to_parm(user_input,
                                CONF_DISPLAY_ZONE_FORMAT, DISPLAY_ZONE_FORMAT_OPTIONS)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_DEVICE_TRACKER_STATE_SOURCE,  DEVICE_TRACKER_STATE_SOURCE_OPTIONS)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_UNIT_OF_MEASUREMENT, UNIT_OF_MEASUREMENT_OPTIONS)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_TIME_FORMAT, TIME_FORMAT_OPTIONS)
        user_input = utils.strip_spaces(user_input, [CONF_EVLOG_BTNCONFIG_URL])

        if (Gb.display_zone_format != user_input[CONF_DISPLAY_ZONE_FORMAT]):
            list_add(self.config_parms_update_control, 'special_zone')

        if Gb.conf_general[CONF_TIME_FORMAT] != user_input[CONF_TIME_FORMAT]:
            self.away_time_zone_hours_key_text = {}
            Gb.time_format_12_hour = user_input[CONF_TIME_FORMAT].startswith('12')
            Gb.time_format_24_hour = not Gb.time_format_12_hour


        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_away_time_zone(self, user_input):
        '''
        Validate and reinitialize the local zone parameters
        '''
        user_input = utils.option_text_to_parm(user_input,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, self.away_time_zone_hours_key_text)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, self.away_time_zone_hours_key_text)

        if (('none' in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] and 'none' not in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES])
                or user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] == []
                or user_input[CONF_AWAY_TIME_ZONE_1_OFFSET] == 0):
            user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] = ['none']
            user_input[CONF_AWAY_TIME_ZONE_1_OFFSET] = 0
        elif ('all' in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] and 'all' not in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]):
            user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] = ['all']
            user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] = ['none']
            user_input[CONF_AWAY_TIME_ZONE_2_OFFSET] = 0
        if len(user_input[CONF_AWAY_TIME_ZONE_1_DEVICES]) > 1:
            list_del(user_input[CONF_AWAY_TIME_ZONE_1_DEVICES], 'none')
            list_del(user_input[CONF_AWAY_TIME_ZONE_1_DEVICES], 'all')

        if (('none' in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] and 'none' not in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES])
                or user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] == []
                or user_input[CONF_AWAY_TIME_ZONE_2_OFFSET] == 0):
            user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] = ['none']
            user_input[CONF_AWAY_TIME_ZONE_2_OFFSET] = 0
        elif ('all' in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] and 'all' not in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]):
            user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] = ['all']
            user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] = ['none']
            user_input[CONF_AWAY_TIME_ZONE_1_OFFSET] = 0
        if len(user_input[CONF_AWAY_TIME_ZONE_2_DEVICES]) > 1:
            list_del(user_input[CONF_AWAY_TIME_ZONE_2_DEVICES], 'none')
            list_del(user_input[CONF_AWAY_TIME_ZONE_2_DEVICES], 'all')

        dup_devices = [devicename   for devicename in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES]
                                    if devicename in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] and devicename != 'none']
        if dup_devices != [] : self.errors[CONF_AWAY_TIME_ZONE_1_DEVICES] = 'away_time_zone_dup_devices_1'
        dup_devices = [devicename   for devicename in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES]
                                    if devicename in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] and devicename != 'none']
        if dup_devices != [] : self.errors[CONF_AWAY_TIME_ZONE_2_DEVICES] = 'away_time_zone_dup_devices_2'

        list_add(self.config_parms_update_control, user_input[CONF_AWAY_TIME_ZONE_1_DEVICES])
        list_add(self.config_parms_update_control, user_input[CONF_AWAY_TIME_ZONE_2_DEVICES])

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_tracking_parameters(self, user_input):
        '''
        Update the profile parameters
        '''
        user_input = utils.option_text_to_parm(user_input,
                                CONF_TRAVEL_TIME_FACTOR, TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT)

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_inzone_intervals(self, user_input):
        '''
        Cycle through the inzone_interval items, validate them and rebuild the inzone_interval
        list in the config file.

        Return = valid inzone_interval diction item as part of the user_input field

        user_input:
            {'iphone': {'hours': 3, 'minutes': 11, 'seconds': 0},
            'ipad': {'hours': 2, 'minutes': 55, 'seconds': 0},
            'watch': {'hours': 0, 'minutes': 44, 'seconds': 0},
            'airpods': {'hours': 0, 'minutes': 33, 'seconds': 0},
            'no_mobapp': {'hours': 0, 'minutes': 22, 'seconds': 0},
            'center_in_zone': True,
            'discard_poor_gps_inzone': True}
        '''

        user_input_copy = user_input.copy()
        config_inzone_interval = Gb.conf_general[CONF_INZONE_INTERVALS].copy()

        for pname, pvalue in user_input_copy.items():
            if (pname not in self.errors and pname in config_inzone_interval):
                config_inzone_interval[pname] = pvalue
                user_input.pop(pname, '')

        user_input[CONF_INZONE_INTERVALS] = config_inzone_interval

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_waze_main(self, user_input):
        '''
        Validate the Waze numeric fields
        '''
        user_input = utils.option_text_to_parm(user_input,
                                CONF_WAZE_SERVER, WAZE_SERVER_OPTIONS)
        user_input = utils.validate_numeric_field(self, user_input)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_WAZE_HISTORY_TRACK_DIRECTION, WAZE_HISTORY_TRACK_DIRECTION_OPTIONS)
        user_input = utils.validate_numeric_field(self, user_input)

        user_input[CONF_WAZE_USED] = False if user_input[CONF_WAZE_USED] == [] else True
        user_input[CONF_WAZE_HISTORY_DATABASE_USED] = False if user_input[CONF_WAZE_HISTORY_DATABASE_USED] == [] else True

        # If Waze Used changes, also change the History DB used
        if user_input[CONF_WAZE_USED] != Gb.conf_general[CONF_WAZE_USED]:
            user_input[CONF_WAZE_HISTORY_DATABASE_USED] = user_input[CONF_WAZE_USED]

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_special_zones(self, user_input):
        """ Validate the stationary one fields

        user_input:
            {'stat_zone_fname': 'Stationary',
            'stat_zone_still_time': {'hours': 0, 'minutes': 10, 'seconds': 0},
            'stat_zone_inzone_interval': {'hours': 0, 'minutes': 30, 'seconds': 0},
            'stat_zone_base_latitude': '1',
            'stat_zone_base_longitude': '0'}
        """

        user_input = utils.validate_numeric_field(self, user_input)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text)
        user_input[CONF_TRACK_FROM_BASE_ZONE_USED] = (user_input[CONF_TRACK_FROM_BASE_ZONE_USED] != [])

        if 'passthru_zone_header' in user_input:
            if user_input['passthru_zone_header'] == []:
                user_input[CONF_PASSTHRU_ZONE_TIME] = 0
            elif (user_input['passthru_zone_header'] != []
                    and user_input[CONF_PASSTHRU_ZONE_TIME] == 0):
                user_input[CONF_PASSTHRU_ZONE_TIME] = DEFAULT_GENERAL_CONF[CONF_PASSTHRU_ZONE_TIME]

        if (user_input[CONF_TRACK_FROM_BASE_ZONE_USED] != Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE_USED]
                or user_input[CONF_TRACK_FROM_BASE_ZONE] != Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE]
                or user_input[CONF_TRACK_FROM_HOME_ZONE] != Gb.conf_general[CONF_TRACK_FROM_HOME_ZONE]):
            list_add(self.config_parms_update_control, 'restart')

        if 'stat_zone_header' in user_input:
            if user_input['stat_zone_header'] == []:
                user_input[CONF_STAT_ZONE_STILL_TIME] = 0
            elif (user_input['stat_zone_header'] != []
                    and user_input[CONF_STAT_ZONE_STILL_TIME] == 0):
                user_input[CONF_STAT_ZONE_STILL_TIME] = DEFAULT_GENERAL_CONF[CONF_STAT_ZONE_STILL_TIME]

        return user_input

#-------------------------------------------------------------------------------------------
    def _check_inactive_devices(self):

        inactive_list = [conf_device[CONF_IC3_DEVICENAME]
                            for conf_device in Gb.conf_devices
                            if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE]

        return inactive_list != [] or self.inactive_devices_key_text.get('keep_inactive', False)

#-------------------------------------------------------------------------------------------
    def _set_inactive_devices_header_msg(self):
        '''
        Display the All/Most/Some Devices are Inactive message by setting the header message key.

        Return none, few, some, most, all based on the number of inactive devices
        '''

        if instr(self.data_source, ICLOUD):
            if self._is_apple_acct_setup() is False:
                self.header_msg = 'apple_acct_not_set_up'

            if self.header_msg:
                errors = {'base': self.header_msg}
                return 'none'

        device_cnt = self._device_cnt()
        if device_cnt == 0:
            self.header_msg = 'inactive_no_devices'
            return 'none'

        inactive_device_cnt = self._inactive_device_cnt()
        if inactive_device_cnt == 0:
            return 'none'

        inactive_pct = inactive_device_cnt / device_cnt

        if device_cnt == inactive_device_cnt:
            self.header_msg = f'inactive_all_devices'
        return 'none'

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _inactive_device_cnt():
        '''
        Return the number of inactive Devices
        '''

        return len([conf_device[CONF_IC3_DEVICENAME]
                        for conf_device in Gb.conf_devices
                        if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE])

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _device_cnt():
        '''
        Return the number of Devices
        '''

        return len(Gb.conf_devices)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              DATA SOURCE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_data_source(   self, user_input=None, errors=None,
                                        return_to_step_id=None):
        '''
        Updata Data Sources form enables/disables finddev and mobile app datasources and
        adds/updates/removes an Apple account using the Update Username/Password screen
        '''
        self.step_id = 'data_source'
        self.errors = errors or {}
        self.errors_user_input = {}
        self.multi_form_user_input = {}
        self.add_apple_acct_flag = False
        self.actions_list_default = ''
        action_item = ''

        if Gb.internet_error:
            self.errors['base'] = 'internet_error'

        await self._async_write_icloud3_configuration_file()
        user_input, action_item = utils.action_text_to_item(self, user_input)
        if self._is_apple_acct_setup() is False:
            self.errors['apple_accts'] = 'apple_acct_not_set_up'
        elif (isnot_empty(Gb.conf_apple_accounts)
                and instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD) is False):
            self.errors['apple_accts'] = 'apple_acct_data_source_warning'

        if user_input is None:
            self.actions_list_default = 'update_apple_acct'
            return self.async_show_form(step_id='data_source',
                                        data_schema=forms.form_data_source(self),
                                        errors=self.errors)

        user_input = self._update_data_source(user_input)
        utils.log_step_info(self, user_input, action_item)

        if action_item == 'cancel_goto_menu':
            self._initialize_self_AppleAcct_fields_from_Gb()
            return await self.async_step_menu()

        if action_item == 'data_source_parameters':
            return await self.async_step_data_source_parameters()

        # Set add or display next page now since they are not in apple_acct_items_by_idx
        if user_input['apple_accts'].startswith('➤ ADD'):
            self.add_apple_acct_flag = True
            action_item = 'update_apple_acct'
            self.conf_apple_acct = DEFAULT_APPLE_ACCOUNT_CONF.copy()
            return await self.async_step_update_apple_acct()

        if user_input['apple_accts'].startswith('➤ OTHER'):
            self.aa_page_no += 1
            if self.aa_page_no > int(len(self.apple_acct_items_list)/5):
                self.aa_page_no = 0
            return await self.async_step_data_source()

        # Display the Confirm Actions form which will execute the remove_apple... function
        user_input = utils.option_text_to_parm(user_input,
                                'apple_accts', self.apple_acct_items_by_username)

        ui_username = user_input['apple_accts']
        self.conf_apple_acct, self.aa_idx = config_file.conf_apple_acct(ui_username)

        utils.log_step_info(self, user_input, action_item)

        if action_item == 'delete_apple_acct':
            # Drop the tracked/untracked part from the current heading (user_input['account_selected'])
            # Ex: account_selected = 'GaryCobb (gcobb321) -> 4 of 7 iCloud Devices Tracked, Tracked-(Gary-iPad ...'
            confirm_action_form_hdr = ( f"Delete Apple Account - {user_input['apple_accts']}")
            if self.AppleAcct:
                confirm_action_form_hdr += f", Devices-{list_to_str(self.AppleAcct.icloud_dnames)}"
            self.multi_form_user_input = user_input.copy()

            return await self.async_step_delete_apple_acct(user_input=user_input)

        if self.aa_idx < 0:
            conf_apple_acct_usernames = [apple_acct[CONF_USERNAME]
                                        for apple_acct in Gb.conf_apple_accounts]
            log_info_msg(   f"Error > {ui_username}, Username not found in Apple accts device list, "
                            f"Valid Accts-{list_to_str(conf_apple_acct_usernames)}")


        if (self.username != user_input.get('apple_accts', self.username)
                and action_item == 'save'):
            action_item = 'update_apple_acct'

        self.username = self.conf_apple_acct[CONF_USERNAME]
        self.password = self.conf_apple_acct[CONF_PASSWORD]
        self.AppleAcct = Gb.AppleAcct_by_username.get(self.username)

        if Gb.log_debug_flag:
            log_user_input = user_input.copy()
            log_debug_msg(  f"⭐ {self.step_id.upper()} ({action_item}) > "
                            f"UserInput-{log_user_input}, Errors-{errors}")

        if action_item == 'update_apple_acct':
            self.aa_page_item[self.aa_page_no] = self.conf_apple_acct[CONF_USERNAME]
            return await self.async_step_update_apple_acct()

        if action_item == 'verification_code':
            self.apple_acct_reauth_username = self.username
            return await self.async_step_reauth(return_to_step_id='data_source')

        if user_input[CONF_DATA_SOURCE] == '':
            self.errors['base'] = 'apple_acct_no_data_source'

        if self.errors == {}:
            if action_item == 'add_change_apple_acct':
                action_item == 'save'

            if action_item == 'save':
                if self.data_source != Gb.conf_tracking[CONF_DATA_SOURCE]:
                    self._update_config_file_tracking(user_input)

                return await self.async_step_menu()

        self.step_id = 'data_source'
        return self.async_show_form(step_id='data_source',
                            data_schema=forms.form_data_source(self),
                            errors=self.errors)

#........................................................................................
    def _update_data_source(self, user_input):

        self.data_source = []
        ds_apple_acct = user_input.pop('data_source_apple_acct', [])
        ds_mobapp     = user_input.pop('data_source_mobapp', [])

        data_source = []
        if isnot_empty(ds_apple_acct):
            list_add(data_source, ICLOUD)
        if isnot_empty(ds_mobapp):
            list_add(data_source, MOBAPP)

        self.data_source = list_to_str(data_source, ',')
        user_input[CONF_DATA_SOURCE] = self.data_source

        if self.data_source != Gb.conf_tracking[CONF_DATA_SOURCE]:
            self._update_config_file_tracking(user_input)

        return user_input

#........................................................................................
    def _is_apple_acct_setup(self):
        if self.username:
            return True
        elif is_empty(Gb.conf_apple_accounts):
            return False
        elif Gb.conf_apple_accounts[0].get(CONF_USERNAME, '') == '':
            return False

        return True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            APPLE USERNAME PASSWORD
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_update_apple_acct(self, user_input=None, errors=None):
        self.step_id = 'update_apple_acct'
        self.errors = errors or {}
        self.multi_form_user_input = {}
        self.errors_user_input = user_input or {}
        self.actions_list_default = ''
        action_item = ''
        await self._async_write_icloud3_configuration_file()

        user_input, action_item = utils.action_text_to_item(self, user_input)

        if action_item == 'cancel_goto_previous':
            self.username = self.conf_apple_acct[CONF_USERNAME]
            self.password = decode_password(self.conf_apple_acct[CONF_PASSWORD])
            self.AppleAcct = Gb.AppleAcct_by_username.get(self.username)
            return await self.async_step_data_source(user_input=None)

        elif action_item == 'stop_login_retry':
            AppleAcct = Gb.AppleAcct_by_username.get(self.username)
            if AppleAcct:
                AppleAcct.error_retry_cnt = 0
                AppleAcct.error_next_retry_secs = 0
            user_input = None
            post_alert(f"Apple Acct > {AppleAcct.username_id}, Retry Login Canceled")
            self.errors['base'] = 'conf_updated'
            return await self.async_step_update_apple_acct(
                                            user_input=user_input, errors=self.errors)

        if (user_input is None
                or instr(self.errors.get(CONF_USERNAME, ''), 'invalid')
                or instr(self.errors.get(CONF_USERNAME, ''), 'error')):
            return self.async_show_form(step_id='update_apple_acct',
                        data_schema=forms.form_update_apple_acct(self),
                        errors=self.errors)

        user_input = utils.option_text_to_parm(user_input,
                                'account_selected', self.apple_acct_items_by_username)
        user_input = utils.strip_spaces(user_input, [CONF_USERNAME, CONF_PASSWORD, CONF_TOTP_KEY])
        if CONF_SERVER_LOCATION in user_input:
            user_input = utils.option_text_to_parm(user_input,
                                    CONF_SERVER_LOCATION, APPLE_SERVER_LOCATION_OPTIONS)
        else:
            user_input[CONF_SERVER_LOCATION] = 'usa'

        if (user_input[CONF_LOCATE_ALL] is False
                and self._can_disable_locate_all(user_input) is False):
            self.errors[CONF_LOCATE_ALL] = 'apple_acct_locate_all_reqd'
            user_input[CONF_LOCATE_ALL] = True
            action_item = ''
            return await self.async_step_update_apple_acct(
                                    user_input=user_input,
                                    errors=self.errors)

        if (Gb.internet_error and action_item == 'save_log_into_apple_acct'):
            self.errors['base'] = 'internet_error_no_change'
            user_input = None
            return await self.async_step_update_apple_acct(
                                            user_input=user_input, errors=self.errors)

        if action_item == 'cancel_goto_previous':
            self.username = self.conf_apple_acct[CONF_USERNAME]
            self.password = decode_password(self.conf_apple_acct[CONF_PASSWORD])
            self.AppleAcct = Gb.AppleAcct_by_username.get(self.username)
            return await self.async_step_data_source(user_input=None)

        user_input[CONF_USERNAME] = user_input[CONF_USERNAME].lower()
        user_input[CONF_TOTP_KEY] = ''      #user_input[CONF_TOTP_KEY].upper()
        ui_username = user_input[CONF_USERNAME]
        ui_password = user_input[CONF_PASSWORD]

        # Make an apple acct dict to compare to the current one
        ui_apple_acct = DEFAULT_APPLE_ACCOUNT_CONF.copy()
        ui_apple_acct[CONF_USERNAME]   = ui_username
        ui_apple_acct[CONF_PASSWORD]   = ui_password
        ui_apple_acct[CONF_TOTP_KEY]   = user_input[CONF_TOTP_KEY]
        ui_apple_acct[CONF_LOCATE_ALL] = user_input[CONF_LOCATE_ALL]
        ui_apple_acct[CONF_SERVER_LOCATION] = user_input[CONF_SERVER_LOCATION]

        conf_username   = self.conf_apple_acct[CONF_USERNAME]
        conf_password   = decode_password(self.conf_apple_acct[CONF_PASSWORD])
        conf_locate_all = self.conf_apple_acct[CONF_LOCATE_ALL]

        add_log_file_filter(ui_username, f"**{self.aa_idx}**")
        add_log_file_filter(ui_username.upper(), f"**{self.aa_idx}**")
        add_log_file_filter(ui_password)

        if Gb.log_debug_flag:
            log_user_input = user_input.copy()
            log_debug_msg(f"⭐ {self.step_id.upper()} ({action_item}) > UserInput-{log_user_input}, Errors-{errors}")


        if action_item == 'save_log_into_apple_acct':
            if ui_username == '':
                self.errors[CONF_USERNAME] = 'required_field'
                action_item = ''

            # Adding an Apple Account but it already exists
            elif (self.add_apple_acct_flag
                    and ui_username in Gb.AppleAcct_by_username):
                self.errors[CONF_USERNAME] = 'apple_acct_dup_username_error'
                action_item = ''

            if ui_password == '':
                self.errors[CONF_PASSWORD] = 'required_field'
                action_item = ''

        # Changing a username and the old one is being used and no devices are
        # using the old one, it's ok to change the name
        elif (ui_username != conf_username
                and ui_username in Gb.AppleAcct_by_username
                and instr(self.apple_acct_items_by_username[ui_username], ' 0 of ') is False):
            user_input[CONF_USERNAME] = conf_username
            user_input[CONF_PASSWORD] = conf_password
            self.errors[CONF_USERNAME] = 'apple_acct_username_inuse_error'
            action_item = ''

        # Saving an existing account with no changes, nothing to do
        if (action_item == 'save_log_into_apple_acct'
                and ui_apple_acct == self.conf_apple_acct
                # and user_input[CONF_SERVER_LOCATION] == self.conf_apple_acct[CONF_SERVER_LOCATION]
                and user_input[CONF_LOCATE_ALL] != conf_locate_all
                and Gb.AppleAcct_by_username.get(ui_username) is not None):
            self.header_msg = 'apple_acct_logged_into'
            action_item = ''

        if action_item == '':
            return await self.async_step_update_apple_acct(user_input=user_input, errors=self.errors)

        # Display the Confirm Actions form which will execute the remove_apple... function
        if action_item == 'delete_apple_acct':
            # Drop the tracked/untracked part from the current heading (user_input['account_selected'])
            # Ex: account_selected = 'GaryCobb (gcobb321) -> 4 of 7 iCloud Devices Tracked, Tracked-(Gary-iPad ...'
            confirm_action_form_hdr = ( f"Delete Apple Account - {user_input['account_selected']}")
            if self.AppleAcct:
                confirm_action_form_hdr += f", Devices-{list_to_str(self.AppleAcct.icloud_dnames)}"
            self.multi_form_user_input = user_input.copy()

            return await self.async_step_delete_apple_acct(user_input=user_input)

        valid_upw = False
        aa_login_info_changed   = False
        other_flds_changed      = False
        username_items_text = self.apple_acct_items_by_username.get(ui_username, NOT_LOGGED_IN)
        aa_not_logged_into = instr(username_items_text, NOT_LOGGED_IN)

        if action_item == 'save_log_into_apple_acct':
            # Apple acct login info changed, validate it without logging in
            if (conf_username != user_input[CONF_USERNAME]
                    or conf_password != user_input[CONF_PASSWORD]
                    or user_input[CONF_SERVER_LOCATION] != self.conf_apple_acct[CONF_SERVER_LOCATION]
                    or ui_username not in Gb.AppleAcct_by_username
                    or Gb.AppleAcct_by_username.get(ui_username) is None):
                aa_login_info_changed = True

            if (user_input[CONF_LOCATE_ALL] != self.conf_apple_acct[CONF_LOCATE_ALL]
                    or user_input[CONF_TOTP_KEY] != self.conf_apple_acct[CONF_TOTP_KEY]):
                other_flds_changed = True

            # if valid_upw:
            #     if aa_login_info_changed or other_flds_changed:
            #         self._update_conf_apple_accounts(self.aa_idx, user_input)
            #         await self._async_write_icloud3_configuration_file()
            #         self.add_apple_acct_flag = False


            # Update the Apple config even if it is not validated. If the un/pw has been tried
            # multiple times and it  was wrong, Apple will still refuse it even if it correct.
            # A 401 is returned from validate_upw and 403 from PasswordSRP. If it is not saved,
            # It will still be invalid on a restart because a failed valid one will not have
            # been saved
            if aa_login_info_changed or other_flds_changed:
                self._update_conf_apple_accounts(self.aa_idx, user_input)
                await self._async_write_icloud3_configuration_file()
                self.add_apple_acct_flag = False

            if aascf.is_asp_password(ui_password):
                pass

            elif valid_upw is False or aa_login_info_changed:
                if Gb.ValidateAppleAcctUPW is None:
                    Gb.ValidateAppleAcctUPW = ValidateAppleAcctUPW()
                valid_upw = await Gb.ValidateAppleAcctUPW.async_validate_username_password(
                                        ui_username, ui_password)
                Gb.valid_upw_by_username[ui_username] = valid_upw

                if valid_upw is False:
                    self.actions_list_default = 'add_change_apple_acct'
                    self.errors['base'] = ''
                    self.errors[CONF_USERNAME] = 'apple_acct_invalid_upw'

                    # App Specific Password (ASP) format: uqvf-gguc-tzpd-knor
                    if aascf.is_asp_password(ui_password):
                        self.errors[CONF_PASSWORD] = 'password_asp_invalid'
                    return await self.async_step_update_apple_acct(
                                        user_input=user_input,
                                        errors=self.errors)

        # A new config, Log into the account
        if (aa_login_info_changed
                or aa_not_logged_into
                or ui_username not in Gb.AppleAcct_by_username
                or Gb.AppleAcct_by_username.get(ui_username) is None):

            successful_login = await aascf.async_log_into_apple_account(self,
                                                user_input, return_to_step_id='update_apple_acct')

            # Update the Apple config even if it is not validated. If the un/pw has been tried
            # multiple times and it  was wrong, Apple will still refuse it even if it correct.
            # A 401 is returned from validate_upw and 403 from PasswordSRP. If it is not saved,
            # It will still be invalid on a restart because a failed valid one will not have
            # been saved

            if successful_login:
                self.errors[CONF_USERNAME] = ''

            if successful_login is False:
                self.add_apple_acct_flag = False
                self.errors[CONF_USERNAME] = aascf.login_err_msg(AppleAcct, ui_username)

                return await self.async_step_update_apple_acct(
                                    user_input=user_input,
                                    errors=self.errors)

            if instr(self.data_source, ICLOUD) is False:
                self._update_data_source({CONF_DATA_SOURCE: [ICLOUD, self.data_source]})

            AppleAcct = self.AppleAcct = Gb.AppleAcct_by_username[ui_username]
            Gb.AppleAcct_password_by_username[ui_username] = user_input[CONF_PASSWORD]

            if (aa_login_info_changed and
                    ui_username in Gb.AppleAcct_error_by_username):
                self.errors['base'] = 'apple_acct_updated_not_logged_into'

            if AppleAcct.auth_2fa_code_needed:
                action_item = 'verification_code'
            else:
                return await self.async_step_data_source(user_input=None)

        if action_item == 'verification_code':
            self.apple_acct_reauth_username = ui_username
            return await self.async_step_reauth(return_to_step_id='data_source')

        return self.async_show_form(step_id='update_apple_acct',
                        data_schema=forms.form_update_apple_acct(self),
                        errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _set_data_source(self, user_input):

        # No Apple Accounts set up, don't use it as a data source
        if len(Gb.conf_apple_accounts) == 1:
            conf_username = self.conf_apple_acct[CONF_USERNAME]
            conf_password = self.conf_apple_acct[CONF_PASSWORD]
            if conf_username == '' and conf_password == '':
                user_input['data_source_icloud'] = []

        data_source = [ user_input['data_source_icloud'],
                        user_input['data_source_mobapp']]
        user_input[CONF_DATA_SOURCE] = self.data_source = list_to_str(data_source, ',')

        return user_input

#-------------------------------------------------------------------------------------------
    def _update_conf_apple_accounts(self, aa_idx, user_input, remove_acct_flag=False):
        '''
        Update the apple accounts config entry with the new values.

        Input (user_input):
            - username = Updated username
            - password = Updated password
            - apple_account =
                - #  = Index number of the username being updated in the conf_apple_accounts list
                - -1 = Add this username/password to the conf_apple_accounts list

        If the apple_account is the index ('#') and the username & password are empty, that item
        is deleted if it is not the primary account (1st entry).

        '''
        # Updating the account
        if remove_acct_flag is False:
            self.conf_apple_acct[CONF_USERNAME]   = user_input[CONF_USERNAME]
            self.conf_apple_acct[CONF_PASSWORD]   = encode_password(user_input[CONF_PASSWORD])
            self.conf_apple_acct[CONF_TOTP_KEY]   = user_input[CONF_TOTP_KEY]
            self.conf_apple_acct[CONF_LOCATE_ALL] = user_input[CONF_LOCATE_ALL]
            self.conf_apple_acct[CONF_SERVER_LOCATION] = user_input[CONF_SERVER_LOCATION]

        # Delete an existing account
        if remove_acct_flag:
            Gb.conf_apple_accounts.pop(aa_idx)
            if Gb.conf_tracking[CONF_USERNAME] == self.conf_apple_acct[CONF_USERNAME]:
                Gb.conf_tracking[CONF_USERNAME] = ''
                Gb.conf_tracking[CONF_PASSWORD] = ''
            self.conf_apple_acct = DEFAULT_APPLE_ACCOUNT_CONF.copy()
            self.aa_idx = aa_idx - 1
            if self.aa_idx < 0: self.aa_idx = 0
            self.aa_page_item[self.aa_page_no] = ''

        # Add a new account
        elif self.add_apple_acct_flag:
            Gb.conf_apple_accounts.append(self.conf_apple_acct)
            self.aa_idx = len(Gb.conf_apple_accounts) - 1
            self.aa_page_no = int(self.aa_idx / 5)
            self.aa_page_item[self.aa_page_no] = self.conf_apple_acct[CONF_USERNAME]

        # Set the account being updated to the new value
        else:
            Gb.conf_apple_accounts[aa_idx] = self.conf_apple_acct
            self.aa_idx = aa_idx
            self.aa_page_no = int(self.aa_idx / 5)
            self.aa_page_item[self.aa_page_no] = self.conf_apple_acct[CONF_USERNAME]

        max_aa_idx = len(Gb.conf_apple_accounts) - 1
        if self.aa_idx > max_aa_idx:
            self.aa_idx = max_aa_idx
        elif self.aa_idx < 0:
            self.aa_idx = 0

        user_input['account_selected'] = self.aa_idx
        self._update_config_file_tracking(update_config_flag=True)
        lists.build_apple_accounts_list(self)
        lists.build_devices_list(self)
        config_file.build_log_file_filters()

#-------------------------------------------------------------------------------------------
    def _can_disable_locate_all(self, user_input):
        famshr_Devices = [Device    for Device in Gb.Devices
                                    if Device.family_share_device
                                        and Device.conf_apple_acct_username == user_input[CONF_USERNAME]]

        return is_empty(famshr_Devices)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           DELETE APPLE ACCOUNT
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_delete_apple_acct(self, user_input=None, errors=None):
        '''
        1. Delete the device from the tracking devices list and adjust the device index
        2. Delete all devices
        3. Clear the iCloud, Mobile App and track_from_zone fields from all devices
        '''
        self.step_id = 'delete_apple_acct'
        self.errors = errors or {}
        self.errors_user_input = {}

        user_input, action_item = utils.action_text_to_item(self, user_input)
        user_input = utils.option_text_to_parm(user_input,
                                'device_action', DELETE_APPLE_ACCT_DEVICE_ACTION_OPTIONS)
        utils.log_step_info(self, user_input, action_item)

        if user_input is None or action_item is None:
            return self.async_show_form(step_id='delete_apple_acct',
                                        data_schema=forms.form_delete_apple_acct(self),
                                        errors=self.errors)

        if action_item == 'cancel_goto_previous':
            return await self.async_step_update_apple_acct()

        device_action = user_input['device_action']
        self._delete_apple_acct(user_input)

        list_add(self.config_parms_update_control, ['tracking', 'restart'])
        self.header_msg = 'action_completed'

        return await self.async_step_data_source()

#------------------------------------------------------------------------------------------
    def _delete_apple_acct(self, user_input):
        '''
        Remove Apple Account from the Apple Accounts config list
        and from all devices using it.
        '''

        # Cycle through the devices and see if it is assigned to the acct being removed.
        # If it is, see if the device is in the primary (1st) username Apple acct.
        # If it is, reassign the device to that Apple acct. Otherwise, remove it

        primary_username = Gb.conf_apple_accounts[0][CONF_USERNAME]
        device_action = user_input['device_action']
        conf_username = self.conf_apple_acct[CONF_USERNAME]

        # Cycle thru config and get the username being deleted. Delete or update it
        updated_conf_devices = []
        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]
            if conf_device[CONF_APPLE_ACCOUNT] != conf_username:
                updated_conf_devices.append(conf_device)

            elif device_action == 'delete_devices':
                config_sensors.remove_device_tracker_entity(self, devicename)

            elif device_action == 'set_devices_inactive':
                conf_device[CONF_APPLE_ACCOUNT] = ''
                conf_device[CONF_FAMSHR_DEVICENAME] ='None'
                conf_device[CONF_TRACKING_MODE] = INACTIVE_DEVICE
                updated_conf_devices.append(conf_device)

            elif device_action == 'reassign_devices':
                icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
                other_apple_acct = [AppleAcct.username
                                        for username, AppleAcct in Gb.AppleAcct_by_username.items()
                                        if icloud_dname in AppleAcct.device_id_by_icloud_dname]
                if other_apple_acct == []:
                    conf_device[CONF_APPLE_ACCOUNT] = ''
                    conf_device[CONF_TRACKING_MODE] = INACTIVE_DEVICE
                else:
                    conf_device[CONF_APPLE_ACCOUNT] = other_apple_acct[0]
                updated_conf_devices.append(conf_device)

        Gb.conf_devices = updated_conf_devices
        self._update_config_file_tracking(user_input={}, update_config_flag=True)

        aas.delete_AppleAcct_Gb_variables_username(conf_username)
        self._update_conf_apple_accounts(self.aa_idx, user_input, remove_acct_flag=True)

        return user_input

#------------------------------------------------------------------------------------------
    def _delete_all_apple_accts(self):
        Gb.conf_apple_accounts = []
        Gb.conf_tracking[CONF_USERNAME] = ''
        Gb.conf_tracking[CONF_PASSWORD] = ''
        self.aa_idx = 0
        self.aa_page_item[self.aa_page_no] = ''

        self.reset_all_devices_data_source_fields(reset_mobapp=False)
        self._update_config_file_tracking(user_input={}, update_config_flag=True)
        lists.build_apple_accounts_list(self)
        lists.build_devices_list(self)
        config_file.build_log_file_filters()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE DATA SOURCE (APPLE) PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_data_source_parameters(self, user_input=None, errors=None):
        self.step_id = 'data_source_parameters'
        user_input, action_item = utils.action_text_to_item(self, user_input)
        utils.log_step_info(self, user_input, action_item)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_data_source()

        if action_item == 'save':
            self._update_config_file_tracking(user_input)
            # Gb.password_srp_enabled = user_input[CONF_PASSWORD_SRP_ENABLED]
            return await self.async_step_data_source()

        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='data_source_parameters',
                        data_schema=forms.form_data_source_parameters(self),
                        errors=self.errors)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_reauth(self, user_input=None, errors=None,
                                        return_to_step_id=None, reauth_username=None):

        self.step_id = 'reauth'
        self.errors = errors or {}
        self.errors_user_input = {}
        self.return_to_step_id_1 = return_to_step_id or self.return_to_step_id_1 or 'menu_0'

        action_item, reauth_username, user_input, errors = \
            await aascf.async_reauthenticate_apple_account(self, user_input=user_input, errors=errors,
                                            return_to_step_id=return_to_step_id, reauth_username=reauth_username)


        if action_item == 'goto_previous':
            return self.async_show_form(step_id=self.return_to_step_id_1,
                                            data_schema=self.form_schema(self.return_to_step_id_1),
                                            errors=self.errors)

        else:
            log_debug_msg(  f"⭐ REAUTH (From={return_to_step_id}, "
                            f"{action_item}) > UserInput-{user_input}, Errors-{errors}")
            if user_input and 'account_selected' in user_input:
                reauth_username = user_input['account_selected']
            return self.async_show_form(step_id='reauth',
                                        data_schema=forms.form_reauth(self, reauth_username=reauth_username),
                                        errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DEVICE LIST
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_device_list(self, user_input=None, errors=None):
        '''
        Display the list of devices form and the function to be performed
        (add, update, delete) on the selected device.
        '''
        self.step_id = 'device_list'
        self.errors = errors or {}
        self.errors_user_input = {}
        self.add_device_flag = self.display_rarely_updated_parms = False
        await self._async_write_icloud3_configuration_file()

        if Gb.internet_error:
            self.errors['base'] = 'internet_error'

        if user_input is None:
            await lists.build_icloud_device_selection_list(self)
            await lists.build_mobapp_entity_selection_list(self)
            self._set_inactive_devices_header_msg()
            utils.set_header_msg(self)
            lists.build_devices_list(self)
            self.update_device_ha_sensor_entity = {}

            return self.async_show_form(step_id='device_list',
                        data_schema=forms.form_device_list(self),
                        errors=self.errors,
                        last_step=False)


        user_input, action_item = utils.action_text_to_item(self, user_input)
        utils.log_step_info(self, user_input, action_item)

        if action_item == 'goto_menu':
            self.update_device_ha_sensor_entity = {}
            return await self.async_step_menu()

        if instr(self.data_source, ICLOUD):
            if self._is_apple_acct_setup() is False:
                self.header_msg = 'apple_acct_not_set_up'

            if self.header_msg:
                errors = {'base': self.header_msg}

        device_cnt = len(Gb.conf_devices)

        if (action_item in ['update_device', 'delete_device']
                and CONF_DEVICES not in user_input):
            action_item = ''

        if action_item == 'goto_menu':
            self.update_device_ha_sensor_entity = {}
            return await self.async_step_menu()

        if action_item == 'change_device_order':
            self.cdo_devicenames = [self._format_device_text_hdr(conf_device)
                                        for conf_device in Gb.conf_devices]
            self.cdo_new_order_idx = [x for x in range(0, len(Gb.conf_devices))]
            self.actions_list_default = 'move_down'
            return await self.async_step_change_device_order()

        if user_input['devices'].startswith('➤ OTHER'):
            if action_item == 'delete_device':
                action_item = 'update_device'
            self.dev_page_no += 1
            if self.dev_page_no > int(len(self.device_items_list)/5):
                self.dev_page_no = 0
            return await self.async_step_device_list()

        if user_input['devices'].startswith('➤ ADD'):
            self.update_device_ha_sensor_entity['add_device'] = True
            self.conf_device = DEFAULT_DEVICE_CONF.copy()
            return await self.async_step_add_device()

        user_input = utils.option_text_to_parm(user_input,
                                'devices', self.device_items_by_devicename)
        user_input[CONF_IC3_DEVICENAME] = user_input['devices']

        utils.log_step_info(self, user_input, action_item)
        self._get_conf_device_selected(user_input)

        if action_item == 'update_device':
            self.update_device_ha_sensor_entity['update_device'] = True
            return await self.async_step_update_device()

        if action_item == 'delete_device':
            action_desc = ( f"Delete Device > {self.conf_device[CONF_FNAME]} "
                            f"({self.conf_device[CONF_IC3_DEVICENAME]})")
            self.confirm_action = {
                'yes_fct': self._delete_device,
                'action_desc': action_desc,
                'return_to_fct': None,
                'return_to_async_step_fct': self.async_step_device_list}

            return await self.async_step_confirm_action()

        await lists.build_icloud_device_selection_list(self)
        await lists.build_mobapp_entity_selection_list(self)
        self._set_inactive_devices_header_msg()
        utils.set_header_msg(self)

        lists.build_devices_list(self)
        self.update_device_ha_sensor_entity = {}

        return self.async_show_form(step_id='device_list',
                        data_schema=forms.form_device_list(self),
                        errors=self.errors,
                        last_step=False)

#..........................................................................................-
    def _get_conf_device_selected(self, user_input):
        '''
        Cycle through the devices listed on the device_list screen. If one was selected,
        get it's device name and position in the Gb.config_tracking[DEVICES] parameter.
        If Found, tThe position was saved in conf_device_idx
        Returns:
            - True = The devicename was found.
            - False = The devicename was not found.
        '''
        idx = -1
        for conf_device in Gb.conf_devices:
            idx += 1
            if conf_device[CONF_IC3_DEVICENAME] == user_input[CONF_IC3_DEVICENAME]:
                self.conf_device     = conf_device
                self.conf_device_idx = idx
                break

        return (idx >= 0)

#-------------------------------------------------------------------------------------------
    def _delete_device(self):
        '''
        Delete the device_tracker entity and associated ic3 configuration
        '''

        try:
            devicename = self.conf_device[CONF_IC3_DEVICENAME]
            event_msg = (f"Configuration Changed > DeleteDevice-{devicename}, "
                        f"{self.conf_device[CONF_FNAME]}/"
                        f"{DEVICE_TYPE_FNAME(self.conf_device[CONF_DEVICE_TYPE])}")
            post_event(event_msg)

            # if deleting last device, use _delete all to simplifying table resetting
            if len(Gb.conf_devices) <= 1:
                return self._delete_all_devices()

            config_sensors.remove_device_tracker_entity(self, devicename)

            self.dev_page_item[self.dev_page_no] = ''
            Gb.conf_devices.pop(self.conf_device_idx)
            self._update_config_file_tracking(update_config_flag=True)

            if devicename in Gb.log_level_devices:
                list_del(Gb.log_level_devices, devicename)
                if is_empty(Gb.log_level_devices):
                    Gb.log_level_devices = ['all']
                self._update_config_file_general(user_input={CONF_LOG_LEVEL_DEVICES: Gb.log_level_devices})

            # The lists may have not been built if deleting a device when deleting an Apple acct
            if devicename in self.device_items_by_devicename:
                del self.device_items_by_devicename[devicename]

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def _delete_all_devices(self):
        """
        Erase all ic3 devices,
        Delete the device_tracker entity and associated ic3 configuration
        """

        try:
            for conf_device in Gb.conf_devices:
                devicename = conf_device[CONF_IC3_DEVICENAME]
                config_sensors.remove_device_tracker_entity(self, devicename)

            Gb.conf_devices = []
            self.device_items_by_devicename    = {}       # List of the apple_accts in the Gb.conf_tracking[apple_accts] parameter
            self.device_items_displayed        = []       # List of the apple_accts displayed on the device_list form
            self.dev_page_item                 = ['', '', '', '', ''] # Device's devicename last displayed on each page
            self.dev_page_no                   = 0        # apple_accts List form page number, starting with 0

            self._update_config_file_tracking(update_config_flag=True)

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def reset_all_devices_data_source_fields(self, reset_mobapp=None):
        """
        Reset the iCloud & Mobile App fields to their initiial values.
        Keep the devicename, friendly name, picture and other fields
        """

        reset_mobapp = True if reset_mobapp is None else False
        for conf_device in Gb.conf_devices:
            conf_device.update(DEFAULT_DEVICE_APPLE_ACCT_DATA_SOURCE)
            if reset_mobapp:
                conf_device.update(DEFAULT_DEVICE_MOBAPP_DATA_SOURCE)

        self._update_config_file_tracking(update_config_flag=True)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            ADD DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_add_device(self, user_input=None, errors=None):
        '''
        Display the device form. Validate and update the device parameters
        '''
        self.step_id = 'add_device'
        self.errors = errors or {}
        self.errors_user_input = {}
        self.multi_form_user_input = {}
        self.add_device_flag = self.display_rarely_updated_parms = True

        await lists.build_update_device_selection_lists(self, self.conf_device[CONF_IC3_DEVICENAME])

        if Gb.internet_error:
            self.errors['base'] = 'internet_error'

        if user_input is None or isnot_empty(self.errors):
            return self.async_show_form(step_id='add_device',
                                        data_schema=forms.form_add_device(self),
                                        errors=self.errors,
                                        last_step=False)

        user_input, action_item = utils.action_text_to_item(self, user_input)

        if (action_item == 'cancel_goto_menu'
                or user_input[CONF_IC3_DEVICENAME] == ''):
            return await self.async_step_device_list()

        user_input = utils.strip_special_text_from_user_input(user_input, CONF_IC3_DEVICENAME)
        user_input = utils.strip_special_text_from_user_input(user_input, CONF_FNAME)
        user_input = utils.strip_special_text_from_user_input(user_input, CONF_MOBILE_APP_DEVICE)

        user_input = utils.option_text_to_parm(user_input,
                                CONF_MOBILE_APP_DEVICE, self.mobapp_list_text_by_entity_id)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_PICTURE, self.picture_by_filename)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)

        utils.log_step_info(self, user_input, action_item)
        user_input = self._validate_ic3_devicename(user_input)

        user_input = self._resolve_selection_list_items(user_input)
        user_input = self._validate_data_source_selections(user_input)
        ui_devicename = user_input[CONF_IC3_DEVICENAME]

        utils.log_step_info(self, user_input, action_item)

        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'
            self.multi_form_user_input = user_input

            return self.async_show_form(step_id='add_device',
                        data_schema=forms.form_add_device(self),
                        errors=self.errors,
                        last_step=False)

        user_input = self._set_other_device_field_values(user_input)

        self.conf_device.update(user_input)
        Gb.conf_devices.append(self.conf_device)

        # This is the first device being added,
        # we need to set up the device_tracker platform, which will add it
        ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)
        if Gb.async_add_entities_device_tracker is None:
            await Gb.hass.config_entries.async_forward_entry_setups(Gb.config_entry, ['device_tracker'])

            sensors_list = config_sensors.build_all_sensors_list()
            config_sensors.create_sensor_entity(ui_devicename, self.conf_device, sensors_list)

        else:
            config_sensors.create_device_tracker_and_sensor_entities(self, ui_devicename, self.conf_device)
            ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)

        # Add the new device to the device_list form and and set it's position index
        self.conf_device_idx = len(Gb.conf_devices) - 1
        self.dev_page_no = int(self.conf_device_idx / 5)
        ui_devicename = user_input[CONF_IC3_DEVICENAME]
        self.device_items_by_devicename[ui_devicename] = \
                    lists.format_device_list_item(self, self.conf_device)

        return await self.async_step_update_other_device_parameters()

#...............................................................................
    def _set_other_device_field_values(self, user_input):
        '''
        Set the device type and inZone interval fields
        '''

        # Get device_type from iCloud device info
        device_type = ''
        model       = IPHONE
        if user_input[CONF_FAMSHR_DEVICENAME] != 'None':
            icloud_dname = user_input[CONF_FAMSHR_DEVICENAME]
            username = user_input[CONF_APPLE_ACCOUNT]
            if username in Gb.AppleAcct_by_username:
                AppleAcct = Gb.AppleAcct_by_username[username]
                raw_model, model, model_display_name = \
                                AppleAcct.device_model_info_by_fname[icloud_dname]
                model = model.lower()
                if model in DEVICE_TYPE_FNAMES:
                    device_type = model

        # Get device_type from mobapp info
        if (device_type == ''
                and user_input[CONF_MOBILE_APP_DEVICE] != 'None'):
            mobapp_dname = user_input[CONF_MOBILE_APP_DEVICE]
            if mobapp_dname in Gb.device_info_by_mobapp_dname:
                device_type = Gb.device_info_by_mobapp_dname[mobapp_dname][2].lower()
                if device_type in DEVICE_TYPE_FNAMES:
                    device_type = DEVICE_TYPE_FNAMES[device_type].lower()

        # Get device_type from ic3_devicename
        if device_type == '':
            ic3_devicename = user_input[CONF_IC3_DEVICENAME].lower()
            ic3_fname = user_input[CONF_FNAME].lower()
            for device_type, device_type_fname in DEVICE_TYPE_FNAMES.items():
                if device_type == MAC:
                    continue
                if instr(ic3_devicename, device_type) or instr(ic3_fname.lower(), device_type):
                    break

        if device_type == '':
            device_type = IPHONE

        user_input[CONF_DEVICE_TYPE] = device_type
        inzone_interval_item = NO_MOBAPP if user_input[CONF_MOBILE_APP_DEVICE] == 'None' else device_type
        user_input[CONF_INZONE_INTERVAL] = DEFAULT_GENERAL_CONF[CONF_INZONE_INTERVALS][inzone_interval_item]
        return user_input

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_update_device(self, user_input=None, errors=None):
        '''
        Display the device form. Validate and update the device parameters
        '''
        self.step_id = 'update_device'
        self.errors = errors or {}
        self.errors_user_input = {}

        await lists.build_update_device_selection_lists(self, self.conf_device[CONF_IC3_DEVICENAME])
        log_debug_msg(f"⭐ {self.step_id.upper()} ( > UserInput-{user_input}, Errors-{errors}")

        if Gb.internet_error:
            self.errors['base'] = 'internet_error'

        if user_input is None:
            return self.async_show_form(step_id='update_device',
                                        data_schema=forms.form_update_device(self),
                                        errors=self.errors)

        user_input, action_item = utils.action_text_to_item(self, user_input)
        utils.log_step_info(self, user_input, action_item)

        if self.add_device_flag is False:
            self.dev_page_item[self.dev_page_no] = self.conf_device[CONF_IC3_DEVICENAME]

        if action_item == 'cancel_goto_select_device':
            return await self.async_step_device_list()
        elif action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        utils.log_step_info(self, user_input, action_item)

        user_input = utils.strip_special_text_from_user_input(user_input, CONF_IC3_DEVICENAME)
        user_input = utils.strip_special_text_from_user_input(user_input, CONF_FNAME)
        user_input = utils.strip_special_text_from_user_input(user_input, CONF_MOBILE_APP_DEVICE)

        user_input = utils.option_text_to_parm(user_input,
                                CONF_MOBILE_APP_DEVICE, self.mobapp_list_text_by_entity_id)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_PICTURE, self.picture_by_filename)

        user_input = utils.option_text_to_parm(user_input,
                                CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)
        utils.log_step_info(self, user_input, action_item)

        user_input = self._validate_ic3_devicename(user_input)

        if (CONF_IC3_DEVICENAME not in self.errors
                and CONF_FNAME not in self.errors):
            user_input = self._resolve_selection_list_items(user_input)
            user_input = self._validate_data_source_selections(user_input)
            user_input = self._update_device_fields(user_input)
            change_flag = self._was_device_data_changed(user_input)

        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'
            self.multi_form_user_input  = user_input

            return self.async_show_form(step_id='update_device',
                            data_schema=forms.form_update_device(self),
                            errors=self.errors)

        if user_input[CONF_PICTURE] == 'setup_dir_filter':
            self.multi_form_user_input = user_input
            self.multi_form_user_input[CONF_PICTURE] = self.conf_device[CONF_PICTURE]
            return await self.async_step_picture_dir_filter()

        if change_flag is False:
            if action_item == 'update_other_device_parameters':
                return await self.async_step_update_other_device_parameters()

            return await self.async_step_device_list()

        # Device fname was changed --> change name on all of it's sensors
        if user_input[CONF_FNAME] != self.conf_device[CONF_FNAME]:
            self.update_device_ha_sensor_entity[CONF_FNAME] = user_input[CONF_FNAME]

        # Picture was changed to None, display Icon mdi: selector later on
        picture_changed_to_none = (user_input[CONF_PICTURE] == 'None' \
                                        and self.conf_device[CONF_PICTURE] != 'None')

        ui_devicename = user_input[CONF_IC3_DEVICENAME]

        only_non_tracked_field_updated = self._is_only_non_tracked_field_updated(user_input)
        self.conf_device.update(user_input)
        Gb.conf_devices[self.conf_device_idx] = self.conf_device

        # Update the configuration file
        add_change_msg = 'Add' if self.add_device_flag else 'Change'
        post_event( f"Configuration Changed > {add_change_msg}Device-{ui_devicename}, "
                    f"{self.conf_device[CONF_FNAME]}/"
                    f"{DEVICE_TYPE_FNAME(self.conf_device[CONF_DEVICE_TYPE])}")

        self.dev_page_item[self.dev_page_no] = ui_devicename
        self._update_config_file_tracking(update_config_flag=True)

        # Rebuild this list in case anything changed
        Gb.devicenames_by_icloud_dname = {}
        Gb.icloud_dnames_by_devicename = {}
        for conf_device in Gb.conf_devices:
            devicename   = conf_device.get(CONF_IC3_DEVICENAME)
            icloud_dname = conf_device.get(CONF_FAMSHR_DEVICENAME)
            Gb.devicenames_by_icloud_dname[icloud_dname] = devicename
            Gb.icloud_dnames_by_devicename[devicename]   = icloud_dname

        await lists.build_icloud_device_selection_list(self)

        self.header_msg = 'conf_updated'
        if only_non_tracked_field_updated:
            list_add(self.config_parms_update_control, ['devices', devicename])
        else:
            list_add(self.config_parms_update_control, ['tracking', 'restart'])

        # Update the device_tracker & sensor entities now that the configuration has been updated
        if self.add_device_flag is False:
            self._update_changed_sensor_entities()

        if action_item == 'update_other_device_parameters':
            return await self.async_step_update_other_device_parameters()

        # Picture was changed to None, display Icon mdi: selector
        if picture_changed_to_none:
            return await self.async_step_update_device()

        return await self.async_step_device_list()

#-------------------------------------------------------------------------------------------
    def _resolve_selection_list_items(self, user_input):
        '''
        Extract the apple_acct and icloud_dname (conf_famshr_devicename) from the
        user_input icloud_dname-LINK-apple_acct value

        Note: The value in self.icloud_list_text_by_fname ends with a '.' when the item
        is in an apple acts list but without the '.' whe it has been selected and is 'this' device
        This Device:
            'Gary-AirPods Pro⟢gcobb321@gmail.com': 'Gary-AirPods Pro⟢GaryCobb, AirPods Pro 2nd gen'
        To be selected (in an accts list):
            'Gary-AirPods Pro⟢gcobb321@gmail.com': 'Gary-AirPods Pro⟢GaryCobb, AirPods Pro 2nd gen.'

        From: 'famshr_devicename': 'Gary-AirPods Pro⟢GaryCobb, AirPods Pro 2nd gen.'
        To:   'apple_account': 'gcobb321@gmail.com', 'famshr_devicename': 'Gary-AirPods Pro',
        '''

        # Get the dname_apple_acct key from the value description of FAMSHR_DEVICENAME field
        _icloud_dname_apple_acct = [icloud_dname_apple_acct
                            for icloud_dname_apple_acct, v in self.icloud_list_text_by_fname.items()
                            if (v == user_input[CONF_FAMSHR_DEVICENAME])]

        if is_empty(_icloud_dname_apple_acct):
            _icloud_dname_apple_acct = 'None'
        else:
            _icloud_dname_apple_acct = _icloud_dname_apple_acct[0]

        # Get the dname_apple_acct key from the value description of FAMSHR_DEVICENAME field
        if (_icloud_dname_apple_acct.startswith('.')
                or _icloud_dname_apple_acct.startswith('ⓧ')):
            user_input[CONF_APPLE_ACCOUNT]     = self.conf_device[CONF_APPLE_ACCOUNT]
            user_input[CONF_FAMSHR_DEVICENAME] = self.conf_device[CONF_FAMSHR_DEVICENAME]
            self.errors[CONF_FAMSHR_DEVICENAME] = 'invalid_selection'

        elif _icloud_dname_apple_acct == 'None':
            user_input[CONF_APPLE_ACCOUNT]     = ''
            user_input[CONF_FAMSHR_DEVICENAME] = 'None'

        elif instr(_icloud_dname_apple_acct, LINK):
            icloud_dname_part, username_part  = _icloud_dname_apple_acct.split(LINK)
            user_input[CONF_APPLE_ACCOUNT]     = username_part
            user_input[CONF_FAMSHR_DEVICENAME] = icloud_dname_part
        else:
            user_input[CONF_APPLE_ACCOUNT]     = self.conf_device[CONF_APPLE_ACCOUNT]
            user_input[CONF_FAMSHR_DEVICENAME] = self.conf_device[CONF_FAMSHR_DEVICENAME]

        if CONF_FMF_EMAIL in user_input:
            user_input[CONF_FMF_EMAIL] = 'None'
            user_input[CONF_FMF_DEVICE_ID] = ''

        # Check the MobApp for an invalid selection
        if (user_input[CONF_MOBILE_APP_DEVICE].startswith('.')
                or user_input[CONF_MOBILE_APP_DEVICE].startswith('ⓧ')):
            user_input[CONF_MOBILE_APP_DEVICE] = self.conf_device[CONF_MOBILE_APP_DEVICE]
            self.errors[CONF_MOBILE_APP_DEVICE] = 'invalid_selection'

        # Check the MobApp for an invalid selection
        if user_input[CONF_PICTURE].startswith('.'):
            user_input[CONF_PICTURE] = self.conf_device[CONF_PICTURE]
            self.errors[CONF_PICTURE] = 'invalid_selection'

        return user_input

#-------------------------------------------------------------------------------------------
    def _is_only_non_tracked_field_updated(self, user_input):
        '''
        Cycle through the fields in the working fields dictionary for the device and see if
        only non-tracked fields were updated.

        Update the device's fields if only non-tracked fields were updated
        Restart iCloud3 if a tracked field was updated
        '''

        try:
            if Gb.conf_devices == []:
                return False

            for pname, pvalue in user_input.items():
                if (Gb.conf_devices[self.conf_device_idx][pname] != pvalue
                        and pname not in DEVICE_NON_TRACKING_FIELDS):
                    return False
        except:
            return False

        return True

#-------------------------------------------------------------------------------------------
    def _validate_ic3_devicename(self, user_input):
        '''
        Validate the add device parameters
        '''

        ui_devicename = user_input[CONF_IC3_DEVICENAME] = slugify(user_input[CONF_IC3_DEVICENAME]).strip()
        ui_fname      = user_input[CONF_FNAME]          = user_input[CONF_FNAME].strip()

        if ui_devicename == '':
            self.errors[CONF_IC3_DEVICENAME] = 'required_field'
            return user_input

        if ui_fname == '':
            self.errors[CONF_FNAME] = 'required_field'
            return user_input

        # ic3 devicename was changed or adding a new device
        if ui_devicename != self.conf_device[CONF_IC3_DEVICENAME]:
            # Already used if the new ic3_devicename is in the ic3 devicename list
            if ui_devicename in self.device_items_by_devicename:
                self.errors[CONF_IC3_DEVICENAME] = 'duplicate_ic3_devicename'
                self.errors_user_input[CONF_IC3_DEVICENAME] = ( f"{ui_devicename}{DATA_ENTRY_ALERT}"
                                                                f"Assigned to another iCloud3 device")

            # Already used if the new ic3_devicename is in the ha device_tracker entity list
            device_tracker_entities, device_tracker_entity_data = \
                    entity_io.get_entity_registry_data(domain=DEVICE_TRACKER)
            dt_devicename = f"{DEVICE_TRACKER}.{ui_devicename}"

            if (dt_devicename in device_tracker_entities
                    and device_tracker_entity_data[dt_devicename]['platform'] != DOMAIN):
                self.errors[CONF_IC3_DEVICENAME] = 'duplicate_other_devicename'
                self.errors_user_input[CONF_IC3_DEVICENAME] = (
                                    f"{ui_devicename}{DATA_ENTRY_ALERT}Used by Integration > "
                                    f"{device_tracker_entity_data[dt_devicename]['platform']}")
        if ui_fname != self.conf_device[CONF_FNAME]:
            # Get any devicenames with the same ui_fname to see if it is already used by another
            # ic3 device. Exclude the self.conf_device instead of ui_devicename in case he ic3
            # devicename is being changed
            used_by_devicename = [conf_device[CONF_IC3_DEVICENAME]
                                    for conf_device in Gb.conf_devices
                                    if (conf_device[CONF_IC3_DEVICENAME] != self.conf_device[CONF_IC3_DEVICENAME]
                                        and conf_device[CONF_FNAME] == ui_fname)]

            if isnot_empty(used_by_devicename):
                self.errors[CONF_FNAME] = 'duplicate_ic3_devicename'
                self.errors_user_input[CONF_FNAME] = (  f"{ui_fname}{DATA_ENTRY_ALERT}Used by iCloud3 device > "
                                                        f"{used_by_devicename[0]}")

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_data_source_selections(self, user_input):
        '''
        Check the devicenames in device's configuration for any errors in the iCloud and
        Mobile App fields.

        Parameters:
            - user_input - the conf_device or user_input item for the device

        Return:
            - self.errors[xxx] will be set if any errors are found
            - user_input
        '''
        if user_input[CONF_FAMSHR_DEVICENAME].strip() == '':
            user_input[CONF_FAMSHR_DEVICENAME] = 'None'
            user_input[CONF_APPLE_ACCOUNT]     = ''

        if (user_input[CONF_MOBILE_APP_DEVICE].strip() == ''
                or user_input[CONF_MOBILE_APP_DEVICE] == 'scan_hdr'):
            user_input[CONF_MOBILE_APP_DEVICE] = 'None'

        ui_apple_acct      = user_input[CONF_APPLE_ACCOUNT]
        ui_icloud_dname    = user_input[CONF_FAMSHR_DEVICENAME]
        ui_mobile_app_name = user_input[CONF_MOBILE_APP_DEVICE]
        icloud_dname_apple_acct = f"{ui_icloud_dname}{LINK}{ui_apple_acct}"

        if (ui_apple_acct  == ''
                and ui_icloud_dname != 'None'):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'unknown_apple_acct'

        elif (ui_icloud_dname != 'None'
                and icloud_dname_apple_acct not in self.icloud_list_text_by_fname
                and instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD)):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'unknown_icloud'

        elif (ui_icloud_dname == 'None'
                and ui_mobile_app_name == 'None'
                and user_input.get(CONF_TRACKING_MODE, TRACK_DEVICE) != INACTIVE_DEVICE):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'no_data_source'
            self.errors[CONF_TRACKING_MODE] = 'no_data_source_set_inactive'

        if (ui_mobile_app_name != 'None'
                and ui_mobile_app_name not in self.mobapp_list_text_by_entity_id
                and instr(Gb.conf_tracking[CONF_DATA_SOURCE], MOBAPP)):
            self.errors[CONF_MOBILE_APP_DEVICE] = 'unknown_mobapp'

        return user_input

#-------------------------------------------------------------------------------------------
    def _update_device_fields(self, user_input):
        """ Validate the device parameters

            Sets:
                self.error[] for fields that are in error
            Returns:
                user_input
                change_flag: True if a field was changed
                change_fname_flag: True if the fname was changed and the device_tracker entity needs to be updated
                change_tfz_flag: True if the track_fm_zones zone was changed and the sensors need to be updated
        """

        if self.AppleAcct:
            _AppleDev = self.AppleAcct.AADevices
            conf_icloud_dname = user_input[CONF_FAMSHR_DEVICENAME]
            device_id = self.AppleAcct.device_id_by_icloud_dname.get(conf_icloud_dname, '')
            raw_model, model, model_display_name = self.AppleAcct.device_model_info_by_fname.get(conf_icloud_dname, ['', '', ''])
            user_input[CONF_FAMSHR_DEVICE_ID]   = device_id
            user_input[CONF_RAW_MODEL]          = raw_model
            user_input[CONF_MODEL]              = model
            user_input[CONF_MODEL_DISPLAY_NAME] = model_display_name

        return user_input

#-------------------------------------------------------------------------------------------
    def _was_device_data_changed(self, user_input):
        """ Cycle thru old and new data and identify changed fields

            Returns:
                True if anything was changed
            Updates:
                sensor_entity_attrs_changed based on changes detected
        """

        if utils.any_errors(self):
            return False

        change_flag = False
        if CONF_IC3_DEVICENAME in user_input:
            self.update_device_ha_sensor_entity[CONF_IC3_DEVICENAME]  = self.conf_device[CONF_IC3_DEVICENAME]
            self.update_device_ha_sensor_entity['new_ic3_devicename'] = user_input[CONF_IC3_DEVICENAME]
        if CONF_TRACKING_MODE in user_input:
            self.update_device_ha_sensor_entity[CONF_TRACKING_MODE]   = self.conf_device[CONF_TRACKING_MODE]
            self.update_device_ha_sensor_entity['new_tracking_mode']  = user_input[CONF_TRACKING_MODE]

        for pname, pvalue in self.conf_device.items():
            if pname not in user_input:
                continue

            if user_input[pname] != pvalue:
                change_flag = True

        return change_flag

#-------------------------------------------------------------------------------------------
    def _update_changed_sensor_entities(self):
        """ Update the device_tracker sensors if needed"""

        # Use the current ic3_devicename since that is how the Device & DeviceTracker objects with the
        # device_tracker and sensor entities are stored. If the devicename was also changed, the
        # device_tracker and sensor entity names will be changed later

        devicename        = self.update_device_ha_sensor_entity[CONF_IC3_DEVICENAME]
        new_devicename    = self.update_device_ha_sensor_entity['new_ic3_devicename']
        tracking_mode     = self.update_device_ha_sensor_entity[CONF_TRACKING_MODE]
        new_tracking_mode = self.update_device_ha_sensor_entity['new_tracking_mode']

        # fname was changed - change the fname of device_tracker and all sensors to the new fname
        # Inactive devices were not created so they are not in Gb.DeviceTrackers_by_devicename
        if (devicename == new_devicename
                and CONF_FNAME in self.update_device_ha_sensor_entity
                and devicename in Gb.DeviceTrackers_by_devicename):
            DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
            DeviceTracker.update_entity_attribute(new_fname=self.conf_device[CONF_FNAME])

            for sensor, Sensor in Gb.Sensors_by_devicename[devicename].items():
                try:
                    Sensor.update_entity_attribute(new_fname=self.conf_device[CONF_FNAME])
                except  Exception as err:
                    # log_exception(err)
                    pass

        # devicename was changed - delete device_tracker and all sensors for
        # devicename and add them for new_devicename
        if devicename != new_devicename:
            self._update_config_file_tracking()
            config_sensors.create_device_tracker_and_sensor_entities(self, new_devicename, self.conf_device)
            config_sensors.remove_device_tracker_entity(self, devicename)

        # If the device was 'inactive' it's entity may not exist since they are not created for
        # inactive devices. If so, create it now if it is no longer 'inactive'.
        elif (tracking_mode == INACTIVE_DEVICE
                and new_tracking_mode != INACTIVE_DEVICE
                and new_devicename not in Gb.DeviceTrackers_by_devicename):
            config_sensors.create_device_tracker_and_sensor_entities(self, new_devicename, self.conf_device)

        # If the device was 'monitored' and is now tracked, create the tracked sensors
        elif (tracking_mode == MONITOR_DEVICE
                and new_tracking_mode == TRACK_DEVICE):
            sensors_list = config_sensors.build_all_sensors_list()
            config_sensors.create_sensor_entity(devicename, self.conf_device, sensors_list)
            # self.devices_added_deleted_flag = True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE OTHER DEVICE PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_update_other_device_parameters(self, user_input=None, errors=None):
        self.step_id = 'update_other_device_parameters'
        user_input, action_item = utils.action_text_to_item(self, user_input)

        if user_input is None:
            return self.async_show_form(step_id='update_other_device_parameters',
                                        data_schema=forms.form_update_other_device_parameters(self),
                                        errors=self.errors)

        utils.log_step_info(self, user_input, action_item)

        if action_item == 'cancel_goto_previous':
            if self.add_device_flag:
                return await self.async_step_device_list()
            else:
                return await self.async_step_update_device()

        user_input = utils.option_text_to_parm(user_input,
                                CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_DEVICE_TYPE, DEVICE_TYPE_FNAMES)
        user_input = utils.option_text_to_parm(user_input,
                                CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text)

        user_input = self._finalize_other_parameters_selections(user_input)
        change_flag = self.add_device_flag or self._was_device_data_changed(user_input)


        if utils.any_errors(self):
            self.errors['action_items'] = 'update_aborted'
            return self.async_show_form(step_id='async_step_update_other_device_parameters',
                            data_schema=forms.form_update_other_device_parameters(self),
                            errors=self.errors)

        elif change_flag and action_item == 'save':
            list_add(self.config_parms_update_control, ['devices', self.conf_device[CONF_IC3_DEVICENAME]])
            tfz_changed = (user_input[CONF_TRACK_FROM_ZONES] != self.conf_device[CONF_TRACK_FROM_ZONES])

            self.conf_device.update(user_input)
            self._update_config_file_tracking(update_config_flag=True)

            if tfz_changed:
                config_sensors.update_track_from_zones_sensors(self, user_input)

        if self.add_device_flag:
            return await self.async_step_device_list()

        return await self.async_step_update_device()

#-------------------------------------------------------------------------------------------
    def _finalize_other_parameters_selections(self, user_input):
        '''
        Check the devicenames in device's configuration for any errors in the iCloud and
        Mobile App fields.

        Parameters:
            - user_input - the conf_device or user_input item for the device

        Return:
            - self.errors[xxx] will be set if any errors are found
            - user_input
        '''
        # Build 'log_zones' list
        if ('none' in user_input[CONF_LOG_ZONES]
                and 'none' not in self.conf_device[CONF_LOG_ZONES]):
            log_zones = []
        else:
            log_zones = [zone   for zone in self.zone_name_key_text.keys()
                                if zone in user_input[CONF_LOG_ZONES] and zone != '.' ]
        if log_zones == []:
            log_zones = ['none']
        else:
            user_input[CONF_LOG_ZONES].append('name-zone')
            log_zones.append([item  for item in user_input[CONF_LOG_ZONES]
                                    if item.startswith('name')][0])
        user_input[CONF_LOG_ZONES] = log_zones

        # See if there are any track_from_zone changes that will be processed after the
        # device is updated
        new_tfz_zones_list, remove_tfz_zones_list = \
                    config_sensors.devices_form_identify_new_and_removed_tfz_zones(self, user_input)

        self.update_device_ha_sensor_entity['new_tfz_zones']    = new_tfz_zones_list
        self.update_device_ha_sensor_entity['remove_tfz_zones'] = remove_tfz_zones_list

        # Build 'track_from_zones' list
        track_from_zones = [zone    for zone in self.zone_name_key_text.keys()
                                    if (zone in user_input[CONF_TRACK_FROM_ZONES]
                                        and zone not in ['.',
                                            self.conf_device[CONF_TRACK_FROM_BASE_ZONE]])]

        track_from_zones.append(self.conf_device[CONF_TRACK_FROM_BASE_ZONE])
        list_add(track_from_zones, user_input[CONF_TRACK_FROM_BASE_ZONE])
        user_input[CONF_TRACK_FROM_ZONES] = track_from_zones

        if isbetween(user_input[CONF_FIXED_INTERVAL], 1, 2):
            user_input[CONF_FIXED_INTERVAL] = 3
            self.errors[CONF_FIXED_INTERVAL] = 'fixed_interval_invalid_range'

        return user_input


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           CHANGE DEVICE ORDER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_change_device_order(self, user_input=None, errors=None):
        self.step_id = 'change_device_order'
        user_input, action_item = utils.action_text_to_item(self, user_input)

        if user_input is None:
            utils.log_step_info(self, user_input, action_item)
            self.cdo_devicenames = [self._format_device_text_hdr(conf_device)
                                        for conf_device in Gb.conf_devices]
            self.cdo_new_order_idx = [x for x in range(0, len(Gb.conf_devices))]
            self.actions_list_default = 'move_down'
            return self.async_show_form(step_id='change_device_order',
                                        data_schema=forms.form_change_device_order(self),
                                        errors=self.errors)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_device_list()

        if action_item == 'save':
            new_conf_devices = []
            for idx in self.cdo_new_order_idx:
                new_conf_devices.append(Gb.conf_devices[idx])

            Gb.conf_devices = new_conf_devices
            config_file.set_conf_devices_index_by_devicename()
            self._update_config_file_tracking(update_config_flag=True)
            lists.build_devices_list(self)
            list_add(self.config_parms_update_control, ['restart', 'profile'])
            self.errors['base'] = 'conf_updated'
            return await self.async_step_device_list()

        self.cdo_curr_idx = self.cdo_devicenames.index(user_input['device_desc'])
        new_idx = self.cdo_curr_idx

        if action_item == 'move_up':
            if new_idx > 0:
                new_idx = new_idx - 1

        elif action_item == 'move_down':
            if new_idx < len(self.cdo_devicenames) - 1:
                new_idx = new_idx + 1
        self.actions_list_default = action_item

        if new_idx != self.cdo_curr_idx:
            self.cdo_devicenames[self.cdo_curr_idx], self.cdo_devicenames[new_idx] = \
                    self.cdo_devicenames[new_idx], self.cdo_devicenames[self.cdo_curr_idx]
            self.cdo_new_order_idx[self.cdo_curr_idx], self.cdo_new_order_idx[new_idx] = \
                    self.cdo_new_order_idx[new_idx], self.cdo_new_order_idx[self.cdo_curr_idx]

            self.cdo_curr_idx = new_idx

        return self.async_show_form(step_id='change_device_order',
                            data_schema=forms.form_change_device_order(self),
                            errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DASHBOARD BUILDER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_dashboard_builder(self, user_input=None, errors=None):
        self.step_id = 'dashboard_builder'
        user_input, action_item = utils.action_text_to_item(self, user_input)


        await dbb.build_existing_dashboards_selection_list(self)
        dbb.select_available_dashboard(self)
        utils.log_step_info(self, user_input, action_item)

        if user_input is None:
            return self.async_show_form(step_id='dashboard_builder',
                                        data_schema=forms.form_dashboard_builder(self),
                                        errors=self.errors)

        user_input = utils.option_text_to_parm(user_input, 'selected_dashboard', self.dbf_dashboard_key_text)
        user_input = utils.option_text_to_parm(user_input, 'main_view_style', DASHBOARD_MAIN_VIEW_STYLE_OPTIONS)

        utils.log_step_info(self, user_input, action_item)

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
        if utils.any_errors(self):
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



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            AWAY TIME ZONE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_away_time_zone(self, user_input=None, errors=None):
        self.step_id = 'away_time_zone'
        user_input, action_item = utils.action_text_to_item(self, user_input)

        lists.build_away_time_zone_devices_list(self)
        lists.build_away_time_zone_hours_list(self)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if utils.any_errors(self):
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id= 'away_time_zone',
                            data_schema=forms.form_away_time_zone(self),
                            errors=self.errors)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                        FORM SCHEMA DEFINITIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def form_schema(self, step_id, actions_list=None, actions_list_default=None):
        '''
        Return the step_id form schema for the data entry forms
        '''
        log_debug_msg(f"⭐ Show Form-{step_id}, Errors-{self.errors}")
        schema = {}
        self.actions_list = actions_list or ACTION_LIST_ITEMS_BASE.copy()

        if step_id in ['menu', 'menu_0', 'menu_1']:
            return forms.form_menu(self)
        elif step_id == 'data_source':
            return forms.form_data_source(self)
        elif step_id == 'update_apple_acct':
            return forms.form_update_apple_acct(self)
        elif step_id == 'reauth':
            return forms.form_reauth(self)
        else:
            return {}