
from homeassistant                  import config_entries, data_entry_flow
from homeassistant.config_entries   import ConfigEntry as config_entry
from homeassistant.data_entry_flow  import FlowHandler, FlowResult
from homeassistant.core             import callback, HomeAssistant
from homeassistant.util             import slugify
from homeassistant.helpers          import (selector, entity_registry as er, device_registry as dr,
                                            area_registry as ar,)

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from re                 import match
import time
from datetime           import datetime
import pyotp

from .global_variables  import GlobalVariables as Gb
from .const             import (DOMAIN, ICLOUD3, DATETIME_FORMAT, STORAGE_DIR,
                                NBSP, RARROW, PHDOT, CRLF_DOT, DOT, HDOT, PHDOT, CIRCLE_STAR, RED_X,
                                YELLOW_ALERT, RED_ALERT, EVLOG_NOTICE, EVLOG_ALERT, EVLOG_ERROR, LINK, LLINK, RLINK,
                                IPHONE_FNAME, IPHONE, IPAD, WATCH, AIRPODS, ICLOUD, OTHER, HOME, FAMSHR,
                                DEVICE_TYPES, DEVICE_TYPE_FNAME, DEVICE_TYPE_FNAMES, DEVICE_TRACKER_DOT,
                                MOBAPP, NO_MOBAPP,
                                TRACK_DEVICE, MONITOR_DEVICE, INACTIVE_DEVICE,
                                NAME,  FRIENDLY_NAME, FNAME, TITLE, BATTERY,
                                ZONE, HOME_DISTANCE,
                                CONF_PICTURE_WWW_DIRS,
                                CONF_VERSION, CONF_EVLOG_CARD_DIRECTORY,
                                CONF_EVLOG_BTNCONFIG_URL,
                                CONF_APPLE_ACCOUNTS, CONF_APPLE_ACCOUNT, CONF_TOTP_KEY,
                                CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES, CONF_SETUP_ICLOUD_SESSION_EARLY,
                                CONF_DATA_SOURCE, CONF_VERIFICATION_CODE, CONF_LOCATE_ALL,
                                CONF_TRACK_FROM_ZONES,
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
                                CONF_SENSORS_TRACK_FROM_ZONES,
                                CONF_SENSORS_OTHER, CONF_EXCLUDED_SENSORS,
                                CONF_PARAMETER_TIME_STR, CONF_PARAMETER_FLOAT,
                                CF_PROFILE, CF_TRACKING, CF_GENERAL,
                                DEFAULT_DEVICE_CONF, DEFAULT_GENERAL_CONF, DEFAULT_APPLE_ACCOUNTS_CONF,
                                DEFAULT_DEVICE_DATA_SOURCE,
                                )
from .const_sensor      import (SENSOR_GROUPS )
from .const_config_flow import *
from .config_flow_forms import *
from .helpers.common    import (instr, isnumber, is_empty, isnot_empty, list_to_str, str_to_list,
                                is_statzone, zone_dname, isbetween, list_del, list_add,
                                sort_dict_by_values,
                                encode_password, decode_password, )
from .helpers.messaging import (log_exception, log_debug_msg, log_info_msg,
                                _log, _evlog, more_info,
                                post_event, post_monitor_msg, )
from .helpers           import entity_io
from .helpers           import file_io
from .                  import sensor as ic3_sensor
from .                  import device_tracker as ic3_device_tracker
from .support           import start_ic3
from .support           import config_file
from .support           import service_handler
from .support           import pyicloud_ic3_interface
from .support.v2v3_config_migration import iCloud3_v2v3ConfigMigration
from .support.pyicloud_ic3  import (PyiCloudService, PyiCloudValidateAppleAcct,
                                    PyiCloudException, PyiCloudFailedLoginException,
                                    PyiCloudServiceNotActivatedException, PyiCloudNoDevicesException, )
import logging
_CF_LOGGER = logging.getLogger("icloud3-cf")
DATA_ENTRY_ALERT_CHAR = '⛔'
DATA_ENTRY_ALERT      = f"      {DATA_ENTRY_ALERT_CHAR} "
DEVICE_NON_TRACKING_FIELDS =   [CONF_FNAME, CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                                CONF_FIXED_INTERVAL, CONF_LOG_ZONES,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES]


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
        self.PyiCloud = None
        self.apple_acct_reauth_username = None

    def form_msg(self):
        return f"Form-{self.step_id}, Errors-{self.errors}"

    def _evlogui(self, user_input):
        _log(f"{user_input=} {self.errors=} ")

#----------------------------------------------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        '''
        Create the options flow handler for iCloud3. This is called when the iCloud3 > Configure
        is selected on the Devices & Services screen, not when HA or iCloud3 is loaded
        '''
        Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()

        return Gb.OptionsFlowHandler


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            USER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_user(self, user_input=None):
        '''
        Invoked when a user initiates a '+ Add Integration' on the Integerations screen
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
            await config_file.async_load_storage_icloud3_configuration_file()
            start_ic3.initialize_data_source_variables()

        await file_io.async_make_directory(Gb.icloud_session_directory)

        # Convert the .storage/icloud3.configuration file if it is at a default
        # state or has never been updated via config_flow using 'HA Integrations > iCloud3'
        if Gb.conf_profile[CONF_VERSION] == -1:
            await self.async_migrate_v2_config_to_v3()

        _CF_LOGGER.info(f"Config_Flow Added Integration-{Gb.ha_device_id_by_devicename=}")

        if user_input is not None:
            _CF_LOGGER.info(f"Added iCloud3 Integration")

            if Gb.restart_ha_flag:
                return await self.async_step_restart_ha()

            data = {}
            data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
            return self.async_create_entry(title="iCloud3", data=data)

        schema = vol.Schema({
            vol.Required('continue', default=True): bool})

        return self.async_show_form(step_id="user",
                                    data_schema=schema,
                                    errors=errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_reauth(self, user_input=None, errors=None, called_from_step_id=None):
        '''
        Ask for the verification code from the user.

        The iCloud account needs to be verified. Show the code entry form, get the
        code from the user, send the code back to Apple ID iCloud via pyicloud and get
        a valid code indicator or invalid code error.

        If the code is valid, either:
            - return to the called_from_step_id (icloud_account form) if in the config_flow configuration routine or,
            - issue a 'create_entry' indicating a successful verification. This will return
            to the function it wass called from. This will be when a validation request was
            needed during the normal tracking.

        If invalid, display an error message and ask for the code again.

        Input:
            - called_from_step_id
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

        self.step_id = 'reauth'
        self.errors = errors or {}
        self.errors_user_input = {}
        action_item = ''

        if user_input is None:
            return self.async_show_form(step_id='reauth',
                                        data_schema=form_reauth(_OptFlow),
                                        errors=self.errors)

        user_input, action_item = _OptFlow._action_text_to_item(user_input)
        user_input = _OptFlow._strip_spaces(user_input, [CONF_VERIFICATION_CODE])
        user_input = _OptFlow._option_text_to_parm(user_input, 'account_selected', _OptFlow.apple_acct_items_by_username)

        log_debug_msg(f"CF-{self.step_id.upper()} ({action_item}) > UserInput-{user_input}, Errors-{errors}")

        if 'account_selected' in user_input:
            _OptFlow._get_conf_apple_acct_selected(user_input['account_selected'])
            username  = _OptFlow.conf_apple_acct[CONF_USERNAME]
            password  = _OptFlow.conf_apple_acct[CONF_PASSWORD]
            _OptFlow.PyiCloud = Gb.PyiCloud_by_username.get(username)
        else:
            # When iCloud3 creates the PyiCloud object for the Apple account during startup,
            # a 2fa needed check is made. If it is needed, a reauthentication is needed executive
            # job is run that tells HA to issue a notification.  The PyiCloud object is saved
            # to be used here
            user_input = None
            username   = Gb.PyiCloud_needing_reauth_via_ha[CONF_USERNAME]
            password   = Gb.PyiCloud_needing_reauth_via_ha[CONF_PASSWORD]
            acct_owner = Gb.PyiCloud_needing_reauth_via_ha['account_owner']

        _OptFlow.apple_acct_reauth_username = username

        if _OptFlow.PyiCloud is None:
            self.errors['base'] = 'icloud_acct_not_logged_into'
            action_item = 'cancel_return'

        elif (action_item == 'send_verification_code'
                and user_input.get(CONF_VERIFICATION_CODE, '') == ''):
            action_item = 'cancel_return'

        if action_item == 'cancel_return':
            _OptFlow.clear_PyiCloud_2fa_flags()
            return self.async_abort(reason="verification_code_cancelled")

        if action_item == 'send_verification_code':
            valid_code = await _OptFlow.reauth_send_verification_code_handler(_OptFlow, user_input)

            if valid_code:
                self.errors['base'] = 'verification_code_accepted'
                if instr(str(_OptFlow.apple_acct_items_by_username), 'AUTHENTICATION'):
                    _OptFlow.conf_apple_acct = ''
                else:
                    _OptFlow.clear_PyiCloud_2fa_flags()
                    return self.async_abort(reason="verification_code_accepted")
            else:
                self.errors[CONF_VERIFICATION_CODE] = 'verification_code_invalid'

        elif action_item == 'request_verification_code':
            await _OptFlow.async_pyicloud_reset_session(username, password)

        return self.async_show_form(step_id='reauth',
                                    data_schema=form_reauth(_OptFlow),
                                    errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             RESTART HA
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_restart_ha(self, user_input=None, errors=None):
        '''
        A restart is required if there were devicenames in known_devices.yaml
        '''
        if Gb.OptionsFlowHandler is None:
            Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()

        self.step_id = 'restart_ha'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = Gb.OptionsFlowHandler._action_text_to_item(user_input)

        if user_input is not None or action_item is not None:
            if action_item.startswith('restart_ha'):
                await Gb.hass.services.async_call("homeassistant", "restart")

            data = {}
            data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
            return self.async_create_entry(title="iCloud3", data=data)

        return self.async_show_form(step_id='restart_ha',
                        data_schema=form_restart_ha_ic3(self),
                        errors=self.errors,
                        last_step=False)

#-------------------------------------------------------------------------------------------
    async def async_migrate_v2_config_to_v3(self):
        '''
        Migrate v2 to v3 if needed

        conf_version goes from:
            -1 --> 0 (default version installed) --> (v2 migrated to v3)
            0 --> 1 (configurator/config_flow opened and configuration file was accessed/updated).
        '''
        # if a platform: icloud3 statement or config_ic3.yaml, migrate the files
        if Gb.ha_config_platform_stmt:
            await Gb.hass.async_add_executor_job(config_file.load_icloud3_ha_config_yaml, Gb.config)

        elif file_io.file_exists(Gb.hass.config.path('config_ic3.yaml')):
            pass
        else:
            return

        v2v3_config_migration = iCloud3_v2v3ConfigMigration()
        v2v3_config_migration.convert_v2_config_files_to_v3()
        v2v3_config_migration.remove_ic3_devices_from_known_devices_yaml_file()

        config_file.async_load_storage_icloud3_configuration_file()
        Gb.v2v3_config_migrated = True

        if Gb.restart_ha_flag:
            pass


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                 ICLOUD3 UPDATE CONFIGURATION / OPTIONS HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3_OptionsFlowHandler(config_entries.OptionsFlow):
    '''Handles options flow for the component.'''

    def __init__(self, settings=False):
        self.initialize_options_required_flag = True
        self.step_id        = ''       # step_id for the window displayed
        self.errors         = {}       # Errors en.json error key
        self.errors_entered_value = {}
        self.config_file_commit_updates = False  # The config file has been updated and needs to be written

        self.initialize_options()
        if settings:
            Gb.hass.async_create_task(self.async_step_menu())

    def initialize_options(self):
        Gb.trace_prefix = 'CONFIG'
        self._set_initial_icloud3_device_tracker_area_id()
        self.initialize_options_required_flag = False
        self.v2v3_migrated_flag               = False  # Set to True when the conf_profile[VERSION] = -1 when first loaded

        self.errors                = {}     # Errors en.json error key
        self.multi_form_hdr        = ''     # multi-form - text string displayed on the called form
        self.multi_form_user_input = {}     # multi-form - user_input to be restored when returning to calling form
        self.errors_user_input     = {}     # user_input text for a value with an error
        self.step_id               = ''     # step_id for the window displayed
        self.menu_item_selected    = [  MENU_KEY_TEXT_PAGE_0[MENU_PAGE_0_INITIAL_ITEM],
                                        MENU_KEY_TEXT_PAGE_1[MENU_PAGE_1_INITIAL_ITEM]]
        self.menu_page_no          = 0      # Menu currently displayed
        self.header_msg            = None   # Message displayed on menu after update
        self.called_from_step_id_1 = ''     # Form/Fct to return to when verifying the icloud auth code
        self.called_from_step_id_2 = ''     # Form/Fct to return to when verifying the icloud auth code

        self.actions_list              = []     # Actions list at the bottom of the screen
        self.actions_list_default      = ''     # Default action_items to reassign on screen redisplay
        self.config_parms_update_control = []   # Stores the type of parameters that were updated, used to reinitialize parms
        self.code_to_schema_pass_value = None

        # Variables used for icloud_account update forms
        self.logging_into_icloud_flag = False

        # Variables used for device selection and update on the device_list and device_update forms
        self.device_items_by_devicename    = {}       # List of the apple_accts in the Gb.conf_tracking[apple_accts] parameter
        self.device_items_displayed        = []       # List of the apple_accts displayed on the device_list form
        self.dev_page_item                 = ['', '', '', '', ''] # Device's devicename last displayed on each page
        self.dev_page_no                   = 0        # apple_accts List form page number, starting with 0
        self.display_rarely_updated_parms     = False    # Display the fixed interval & track from zone parameters

        self.ic3_devicename_being_updated  = ''         # Devicename currently being updated
        self.conf_device                   = {}
        self.conf_device_idx               = 0
        self.conf_device_update_control   = {}          # Contains info regarding update_device and needed entity changes
        self.device_list_control_default   = 'select'    # Select the Return to main menu as the default
        self.add_device_flag               = False
        self.add_device_enter_devicename_form_part_flag = False  # Add device started, True = form top part only displayed

        self.device_trkr_by_entity_id_all  = {}         # other platform device_tracker used to validate the ic3 entity is not used

        # Option selection lists on the Update apple_accts screen
        self.apple_acct_items_list          = []       # List of the apple_accts in the Gb.conf_tracking[apple_accts] parameter
        self.apple_acct_items_displayed     = []       # List of the apple_accts displayed on the device_list form
        self.aa_page_item                   = ['', '', '', '', '']  # Apple acct username last displayed on each page
        self.aa_page_no                     = 0        # apple_accts List form page number, starting with 0
        self.conf_apple_acct                = ''        # apple acct item selected
        self.apple_acct_items_by_username   = {}        # Selection list for the apple accounts on data_sources and reauth screens
        self.aa_idx                 = 0
        self.apple_acct_reauth_username     = None
        self.add_apple_acct_flag            = False

        self.icloud_list_text_by_fname      = {}
        self.icloud_list_text_by_fname2     = {}
        self.icloud_list_text_by_fname_base = NONE_DICT_KEY_TEXT.copy()
        self.mobapp_list_text_by_entity_id  = {}         # mobile_app device_tracker info used in devices form for mobapp selection
        self.mobapp_list_text_by_entity_id  = MOBAPP_DEVICE_NONE_OPTIONS.copy()
        self.picture_by_filename            = {}
        self.picture_by_filename_base       = NONE_DICT_KEY_TEXT.copy()
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

        # PyiCloud object and variables. Using local variables rather than the Gb PyiCloud variables
        # in case the username/password is changed and another account is accessed. These will not
        # intefer with ones already in use by iC3. The Global Gb variables will be set to the local
        # variables if they were changes and a iC3 Restart was selected when finishing the config setup
        self._initialize_self_PyiCloud_fields_from_Gb()
        self._build_apple_accounts_list()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            INIT
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_init(self, user_input=None):
        if self.initialize_options_required_flag:
            self.initialize_options()
        self.errors = {}

        if self.abort_flag:
            return await self.async_step_restart_ha_ic3_load_error()

        return await self.async_step_menu_0()

#-------------------------------------------------------------------------------------------
    def _evlogui(self, user_input):
        _log(f"{user_input=} {self.errors=} ")

#-------------------------------------------------------------------------------------------
    def _initialize_self_PyiCloud_fields_from_Gb(self):
        conf_apple_acct, _idx = config_file.conf_apple_acct(0)
        self.username = conf_apple_acct[CONF_USERNAME]
        self.password = conf_apple_acct[CONF_PASSWORD]

        self.PyiCloud        = Gb.PyiCloud_by_username.get(self.username)
        self.data_source     = Gb.conf_tracking[CONF_DATA_SOURCE]
        self.endpoint_suffix = Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX] or \
                                        Gb.icloud_server_endpoint_suffix

#-------------------------------------------------------------------------------------------
    def _set_initial_icloud3_device_tracker_area_id(self):
        '''
        When the integration is first added, there are no devices (conf_devices == [] or all of the
        devices are set to inactive. If this is the case, no Device objects have been created and
        the ICLOUD3 Integration Device Tracker Entity has not been totaly initialized. Do it now.

        - Add the 'Personal Device' area to the iCloud3 device tracker
        '''
        if (ICLOUD3 not in Gb.ha_device_id_by_devicename
                or Gb.area_id_personal_device == None
                or Gb.ha_area_id_by_devicename[ICLOUD3] not in [None, 'unknown', '']):
            return

        inactive_devices_cnt = len([Device for Device in Gb.Devices if Device.is_inactive])
        if Gb.Devices == []:
            pass
        elif inactive_devices_cnt != len(Gb.Devices):
            return

        self.update_area_id_personal_device(ICLOUD3)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            MENU
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_menu_0(self, user_input=None, errors=None):
        self.menu_page_no = 0
        return await self.async_step_menu(user_input, errors)

    async def async_step_menu_1(self, user_input=None, errors=None):
        self.menu_page_no = 1
        return await self.async_step_menu(user_input, errors)

    async def async_step_menu(self, user_input=None, errors=None):
        self.step_id = f"menu_{self.menu_page_no}"
        self.called_from_step_id_1 = self.called_from_step_id_2 = ''
        self.errors = errors or {}
        await self._async_write_storage_icloud3_configuration_file()

        Gb.trace_prefix = 'CONFIG'
        Gb.config_flow_flag = True

        if (self.username != '' and self.password != ''
                and instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD) is False):
            self.header_msg = 'icloud_acct_data_source_warning'

        elif self.PyiCloud is None and self.username:
            self.header_msg = 'icloud_acct_not_logged_into'

        elif self.is_verification_code_needed:
            self.header_msg = 'verification_code_needed'


        if user_input is None:
            self._set_inactive_devices_header_msg()
            self._set_header_msg()

            return self.async_show_form(step_id=self.step_id,
                                        data_schema=form_menu(self),
                                        errors=self.errors)

        self.menu_item_selected[self.menu_page_no] = user_input['menu_items']
        user_input, menu_item = self._menu_text_to_item(user_input, 'menu_items')
        user_input, menu_action_item = self._menu_text_to_item(user_input, 'action_items')

        if menu_action_item == 'exit':
            Gb.config_flow_flag = False
            self.initialize_options_required_flag = False

            # conf_version goes from:
            #   -1 --> 0    default version installed --> v2 migrated to v3
            #   -1 --> 1    default version installed --> configurator/config_flow opened and updated, or
            #    0 --> 1    migrated config file  --> configurator/config_flow opened and updated
            # Set to 1 here indicating the config file was reviewed/updated after inital v3 install.
            if Gb.conf_profile[CONF_VERSION] <= 0:
                self.v2v3_migrated_flag = (Gb.conf_profile[CONF_VERSION] == 0)
                Gb.conf_profile[CONF_VERSION] = 1
                self._update_config_file_tracking(user_input)

            if ('restart' in self.config_parms_update_control
                    or self._set_inactive_devices_header_msg() in ['all', 'most']):
                return await self.async_step_restart_icloud3()

            else:
                Gb.config_parms_update_control   = self.config_parms_update_control.copy()
                self.config_parms_update_control = []
                log_debug_msg(f"Exit Configure Settings, UpdateParms-{list_to_str(Gb.config_parms_update_control)}")

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
        elif menu_item == 'sensors':
            return await self.async_step_sensors()
        elif menu_item == 'actions':
            return await self.async_step_actions()

        self._set_inactive_devices_header_msg()
        self._set_header_msg()

        return self.async_show_form(step_id=self.step_id,
                            data_schema=form_menu(self),
                            errors=self.errors,
                            last_step=False)


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
        await self._async_write_storage_icloud3_configuration_file()
        user_input, action_item = self._action_text_to_item(user_input)

        if user_input is not None or action_item is not None:
            if action_item == 'cancel':
                return await self.async_step_menu_0()

            elif action_item.startswith('restart_ha'):
                await Gb.hass.services.async_call("homeassistant", "restart")
                return self.async_abort(reason="ha_restarting")

            elif action_item == 'review_inactive_devices':
                self.called_from_step_id_1 = 'restart_icloud3'
                return await self.async_step_review_inactive_devices()

            if action_item == 'restart_ic3_now':
                Gb.config_parms_update_control = self.config_parms_update_control.copy()

            elif action_item == 'restart_ic3_later':
                if 'restart' in self.config_parms_update_control:
                    list_del(self.config_parms_update_control, 'restart')
                Gb.config_parms_update_control = self.config_parms_update_control.copy()
                self.config_parms_update_control = []

            data = {}
            data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
            log_debug_msg(f"Exit Configure Settings, UpdateParms-{Gb.config_parms_update_control}")

            # If the polling loop has been set up, set the restart flag to trigger a restart when
            # no devices are being updated. Otherwise, there were probably no devices to track
            # when first loaded and a direct restart must be done.
            return self.async_create_entry(title="iCloud3", data={})

        self._set_inactive_devices_header_msg()
        self._set_header_msg()

        return self.async_show_form(step_id='restart_icloud3',
                        data_schema=form_restart_icloud3(self),
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

        user_input, action_item = self._action_text_to_item(user_input)

        if user_input is not None or action_item is not None:
            if action_item == 'inactive_to_track':
                devicename_list = [self.inactive_devices_key_text.values()] \
                        if user_input['inactive_devices'] == [] \
                        else user_input['inactive_devices']

                for conf_device in Gb.conf_devices:
                    if conf_device[CONF_IC3_DEVICENAME] in devicename_list:
                        conf_device[CONF_TRACKING_MODE] = TRACK_DEVICE

                self._update_config_file_tracking(user_input)
                self.header_msg = 'action_completed'

            if self.called_from_step_id_1 == 'restart_icloud3':
                return await self.async_step_restart_icloud3()

            return await self.async_step_menu()

        return self.async_show_form(step_id='review_inactive_devices',
                        data_schema=form_review_inactive_devices(self),
                        errors=self.errors,
                        last_step=False)


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
            user_input, action_item = self._action_text_to_item(user_input)

        if action_item == 'cancel':
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
            self._remove_and_create_sensors(user_input)

        self.log_step_info(user_input, action_item)

        post_event(f"Configuration Changed > Type-{self.step_id.replace('_', ' ').title()}")
        self._update_config_file_general(user_input)

        # Redisplay the menu if there were no errors
        if not self.errors:
            return True

        # Display the config data entry form, any errors will be redisplayed and highlighted
        return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              FORMAT SETTINGS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_format_settings(self, user_input=None, errors=None):
        self.step_id = 'format_settings'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self.errors != {} and self.errors.get('base') != 'conf_updated':
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='format_settings',
                            data_schema=form_format_settings(self),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _format_device_text_hdr(conf_device):
        device_text = ( f"{conf_device[CONF_FNAME]} "
                        f"({conf_device[CONF_IC3_DEVICENAME]})")
        if conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
            device_text += ", MONITOR"
        elif conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
            device_text += ", ✪ INACTIVE"

        return device_text


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             CONFIRM ACTION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_confirm_action(self, user_input=None,
                                        extra_action_items=None,
                                        actions_list_default=None,
                                        confirm_action_form_hdr=None,
                                        called_from_step_id=None):
        '''
        Confirm an action - This will display a screen containing the action_items.

        Parameters:
            action_items - The action_item keys in the ACTION_LIST_OPTIONS dictionary.
                            The last key is the default item on the confirm actions screen.
            called_from_step_id - The name of the step to return to.
            self.multi_form_user_input['confirm_msg'] = Text message to be displayed on the
                            Confirm Actions screen

        Notes:
            Before calling this function, set the self.multi_form_user_input to the user_input.
                    This will have all parameter changes in the calling screen. They are
                    returned to the called from step on exit.
            Action item - The action_item selected on this screen is added to the
                    self.multi_form_user_input variable returned. It is resolved in the calling
                    step in the self._action_text_to_item function in the calling step.
            On Return - Set the function to return to for the called_from_step_id.
        '''
        self.step_id = 'confirm_action'
        self.errors = {}
        self.errors_user_input = {}
        self.called_from_step_id_1 = called_from_step_id or self.called_from_step_id_1 or 'menu_0'

        if user_input is None:
            return self.async_show_form(step_id='confirm_action',
                                        data_schema=form_confirm_action(self,
                                                    extra_action_items,
                                                    actions_list_default,
                                                    confirm_action_form_hdr),
                                        errors=self.errors)

        user_input, action_item = self._action_text_to_item(user_input)

        if action_item == 'confirm_action':
            if self.called_from_step_id_1 == 'data_source/remove_account':
                self._delete_apple_acct(self.multi_form_user_input)

        if self.called_from_step_id_1 == 'data_source/remove_account':
            return await self.async_step_data_source()

        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    def _set_example_zone_name(self):
        '''
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
        user_input, action_item = self._action_text_to_item(user_input)

        if self.www_directory_list == []:
            start_dir = 'www'
            self.www_directory_list = await Gb.hass.async_add_executor_job(
                                                            file_io.get_directory_list,
                                                            start_dir)

        if self.common_form_handler(user_input, action_item, errors):
            if action_item == 'save':
                Gb.picture_www_dirs = Gb.conf_profile[CONF_PICTURE_WWW_DIRS].copy()
                self.picture_by_filename = {}
            return await self.async_step_menu()


        if self._any_errors():
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='tracking_parameters',
                            data_schema=form_tracking_parameters(self),
                            errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            INZONE INTERVALS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_inzone_intervals(self, user_input=None, errors=None):
        self.step_id = 'inzone_intervals'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self._any_errors():
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='inzone_intervals',
                            data_schema=form_inzone_intervals(self),
                            errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            WAZE MAIN
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_waze_main(self, user_input=None, errors=None):
        self.step_id = 'waze_main'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self._any_errors():
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='waze_main',
                            data_schema=form_waze_main(self),
                            errors=self.errors,
                            last_step=True)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SPECIAL ZONES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_special_zones(self, user_input=None, errors=None):
        self.step_id = 'special_zones'
        user_input, action_item = self._action_text_to_item(user_input)
        await self._build_zone_selection_list()

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self._any_errors():
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='special_zones',
                            data_schema=form_special_zones(self),
                            errors=self.errors)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SENSORS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_sensors(self, user_input=None, errors=None):

        self.step_id = 'sensors'
        self.errors = errors or {}
        await self._async_write_storage_icloud3_configuration_file()
        user_input, action_item = self._action_text_to_item(user_input)

        if Gb.conf_sensors[CONF_EXCLUDED_SENSORS] == []:
            Gb.conf_sensors[CONF_EXCLUDED_SENSORS] = ['None']

        if user_input is None:
            return self.async_show_form(step_id='sensors',
                                        data_schema=form_sensors(self),
                                        errors=self.errors)

        if HOME_DISTANCE not in user_input[CONF_SENSORS_TRACKING_DISTANCE]:
            user_input[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)

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

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self._any_errors():
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='sensors',
                            data_schema=form_sensors(self),
                            errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            EXCLUDE SENSORS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_exclude_sensors(self, user_input=None, errors=None):

        self.step_id = 'exclude_sensors'
        self.errors = errors or {}
        await self._async_write_storage_icloud3_configuration_file()
        user_input, action_item = self._action_text_to_item(user_input)

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
                                        data_schema=form_exclude_sensors(self),
                                        errors=self.errors)

        self.log_step_info(user_input, action_item)
        sensors_list_filter = user_input['filter'].lower().replace('?', '').strip()

        if (self.sensors_list_filter == sensors_list_filter
                and len(self.excluded_sensors) == len(user_input[CONF_EXCLUDED_SENSORS])
                and user_input['filtered_sensors'] == []):
            self.sensors_list_filter = '?'
        else:
            self.sensors_list_filter = sensors_list_filter or '?'

        if action_item == 'cancel_return':
            return await self.async_step_sensors()

        if (action_item == 'save_stay'
                or user_input[CONF_EXCLUDED_SENSORS] != self.excluded_sensors
                or user_input['filtered_sensors'] != []):
            user_input = self._update_excluded_sensors(user_input)

            if Gb.conf_sensors[CONF_EXCLUDED_SENSORS] != self.excluded_sensors:
                Gb.conf_sensors[CONF_EXCLUDED_SENSORS] = self.excluded_sensors.copy()
                self._update_config_file_general(user_input, update_config_flag=True)

                self.errors['excluded_sensors'] = 'excluded_sensors_ha_restart'
                list_add(self.config_parms_update_control, ['restart_ha', 'restart'])

        return self.async_show_form(step_id='exclude_sensors',
                            data_schema=form_exclude_sensors(self),
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
        user_input, action_item = self._action_text_to_item(user_input)

        # Reinitialize everything
        if self.dta_selected_idx == UNSELECTED:
            self.dta_selected_idx = 0
            self.dta_selected_idx_page = [0, 5]
            self.dta_page_no = 0
            idx = UNSELECTED
            for dta_text in Gb.conf_general[CONF_DISPLAY_TEXT_AS]:
                idx += 1
                self.dta_working_copy[idx] = dta_text

        if user_input is None:
            return self.async_show_form(step_id='display_text_as',
                                        data_schema=form_display_text_as(self),
                                        errors=self.errors)

        user_input = self._option_text_to_parm(user_input, CONF_DISPLAY_TEXT_AS, self.dta_working_copy)
        self.dta_selected_idx = int(user_input[CONF_DISPLAY_TEXT_AS])
        self.dta_selected_idx_page[self.dta_page_no] = self.dta_selected_idx
        self.log_step_info(user_input, action_item)

        if action_item == 'next_page_items':
            self.dta_page_no = 1 if self.dta_page_no == 0 else 0

        elif action_item == 'select_text_as':
            return await self.async_step_display_text_as_update(user_input)

        elif action_item == 'cancel':
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

        if self._any_errors():
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='display_text_as',
                        data_schema=form_display_text_as(self),
                        errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISPLAY TEXT AS UPDATE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_display_text_as_update(self, user_input=None, errors=None):
        self.step_id = 'display_text_as_update'
        user_input, action_item = self._action_text_to_item(user_input)

        if action_item == 'cancel':
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

        if self._any_errors():
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id='display_text_as_update',
                        data_schema=form_display_text_as_update(self),
                        errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            ACTIONS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    '''
    "divider1": "━━━━━━━━━━ ICLOUD3 CONTROL ACTIONS ━━━━━━━━━━ ",
    "restart": "RESTART > Restart iCloud3",
    "pause": "PAUSE > Pause polling on all devices",
    "resume": "RESUME > Resume Polling on all devices, Refresh all locations",
    "divider2": "━━━━━━━━━━ ICLOUD ACCOUNT ACTIONS ━━━━━━━━━━ ",
    "debug": "START/STOP DEBUG LOGGING > Start or stop debug logging",
    "rawdata": "START/STOP DEBUG RAWDATA LOGGING > Start or stop debug rawdata logging",
    "commit": "COMMIT DEBUG LOG RECORDS > Verify all debug log file records are written",
    "divider3": "━━━━━━━━━━━━ OTHER COMMANDS ━━━━━━━━━━━━ ",
    "evlog_export": "EXPORT EVENT LOG > Export Event Log data",
    "wazehist_maint": "WAZE HIST DATABASE > Recalc time/distance data at midnight",
    "wazehist_track": "WAZE HIST MAP TRACK > Load route locations for map display",
    "divider4": "═══════════════════════════════════════════════ ",
    "return": "RETURN > Return to the Main Menu"
    '''

    async def async_step_actions(self, user_input=None, errors=None):
        '''
        Handle the Actions request menu
        '''
        self.step_id = 'actions'
        self.errors = errors or {}
        self.errors_user_input = {}

        if user_input is None:
            return self.async_show_form(step_id='actions',
                                        data_schema=form_actions(self),
                                        errors=self.errors)

        # Get key for item selected ("RESTART" --> "restart") and then
        # process the requested action
        if user_input['action_items']:
            action_item =user_input['action_items'][0]
        elif user_input['ic3_actions']:
            action_item = user_input['ic3_actions'][0]
        elif user_input['debug_actions']:
            action_item = user_input['debug_actions'][0]
        elif user_input['other_actions']:
            action_item = user_input['other_actions'][0]
        else:
            action_item = 'return'

        if action_item == 'return':
            return await self.async_step_menu()

        elif action_item in [   'restart', 'pause', 'resume',
                                'wazehist_maint', 'wazehist_track',
                                'evlog_export', ]:
            service_handler.update_service_handler(action_item)

        elif action_item.startswith('debug'):
            service_handler.handle_action_log_level('debug', change_conf_log_level=False)

        elif action_item.startswith('rawdata'):
            service_handler.handle_action_log_level('rawdata', change_conf_log_level=False)

        elif action_item == 'restart_ha':
            return await self.async_step_restart_ha_ic3()

        if self.header_msg is None:
            self.header_msg = 'action_completed'

        return await self.async_step_menu()

#--------------------------------------------------------------------------------
    async def _process_action_request(self, action_item):
        self.header_msg = None

        if action_item == 'return':
            return

        elif action_item in [   'restart', 'pause', 'resume',
                                'wazehist_maint', 'wazehist_track',
                                'evlog_export', ]:
            service_handler.update_service_handler(action_item)

        elif action_item.startswith('debug'):
            service_handler.handle_action_log_level('debug', change_conf_log_level=False)

        elif action_item.startswith('rawdata'):
            service_handler.handle_action_log_level('rawdata', change_conf_log_level=False)

        if self.header_msg is None:
            self.header_msg = 'action_completed'


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            RESTART HA IC3LOAD ERROR
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_restart_ha_ic3_load_error(self, user_input=None, errors=None):
        self.step_id = 'restart_ha_ic3_load_error'
        return await self.async_restart_ha_ic3(user_input, errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            RESTART HA IC3
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_restart_ha_ic3(self, user_input=None, errors=None):
        self.step_id = 'restart_ha_ic3'
        return await self.async_restart_ha_ic3(user_input, errors)
        # return await self.async_step_menu()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            RESTART HA IC3
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_restart_ha_ic3(self, user_input, errors):
        '''
        A restart HA or reload iCloud3
        '''
        self.step_id = 'restart_ha_ic3'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = self._action_text_to_item(user_input)

        if user_input is None or action_item is None:
            return self.async_show_form(step_id='restart_ha_ic3',
                                    data_schema=form_restart_ha_ic3(self),
                                    errors=self.errors)

        if action_item == 'restart_ha':
            await Gb.hass.services.async_call("homeassistant", "restart")
            return self.async_abort(reason="ha_restarting")

        elif action_item == 'restart_icloud3':
            # Gb.config_parms_update_control = ['restart']
            list_add(self.config_parms_update_control, 'restart')
            return self.async_abort(reason="ic3_restarting")

        return await self.async_step_menu()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  VALIDATE DATA AND UPDATE CONFIG FILE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def _async_write_storage_icloud3_configuration_file(self):
        '''
        Write the updated configuration file to .storage/icloud3/configuration
        The config file updates are done by setting the commit_updates flag in
        the update routines and adding a call to this fct on screen changes so they
        are done using async updates. The screen handlers are run in async made
        while the update fcts are not.
        '''
        if self.config_file_commit_updates:
            await config_file.async_write_storage_icloud3_configuration_file()
            self.config_file_commit_updates = False
            self.header_msg = 'conf_updated'
            self.errors['base'] = 'conf_updated'

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
        update_config_flag = update_config_flag or False

        if CONF_USERNAME in user_input:
            conf_apple_acct, _idx = config_file.conf_apple_acct(0)
            conf_username = conf_apple_acct[CONF_USERNAME]
            conf_password = conf_apple_acct[CONF_PASSWORD]
            user_input[CONF_USERNAME] = conf_username
            user_input[CONF_PASSWORD] = encode_password(conf_password)

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
        in the config file That requires a n iCloud3 restart

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
        update_config_flag = update_config_flag or False
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

#-------------------------------------------------------------------------------------------
    def _validate_format_settings(self, user_input):
        '''
        The display_zone_format may contain '(Example: ...). If so, strip it off.
        '''
        user_input = self._option_text_to_parm(user_input, CONF_DISPLAY_ZONE_FORMAT, DISPLAY_ZONE_FORMAT_OPTIONS)
        user_input = self._option_text_to_parm(user_input, CONF_DEVICE_TRACKER_STATE_SOURCE, DEVICE_TRACKER_STATE_SOURCE_OPTIONS)
        user_input = self._option_text_to_parm(user_input, CONF_UNIT_OF_MEASUREMENT, UNIT_OF_MEASUREMENT_OPTIONS)
        user_input = self._option_text_to_parm(user_input, CONF_TIME_FORMAT, TIME_FORMAT_OPTIONS)
        user_input = self._option_text_to_parm(user_input, CONF_LOG_LEVEL, LOG_LEVEL_OPTIONS)

        if (user_input[CONF_LOG_LEVEL_DEVICES] == []
                or len(user_input[CONF_LOG_LEVEL_DEVICES]) >= len(Gb.Devices)):
            user_input[CONF_LOG_LEVEL_DEVICES] = ['all']
        elif len(user_input[CONF_LOG_LEVEL_DEVICES]) > 1:
            list_del(user_input[CONF_LOG_LEVEL_DEVICES], 'all')

        if (Gb.display_zone_format != user_input[CONF_DISPLAY_ZONE_FORMAT]):
            list_add(self.config_parms_update_control, 'special_zone')

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_away_time_zone(self, user_input):
        '''
        Validate and reinitialize the local zone parameters
        '''
        user_input = self._option_text_to_parm(user_input, CONF_AWAY_TIME_ZONE_1_OFFSET, self.away_time_zone_hours_key_text)
        user_input = self._option_text_to_parm(user_input, CONF_AWAY_TIME_ZONE_2_OFFSET, self.away_time_zone_hours_key_text)

        if (('none' in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] and 'none' not in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES])
                or user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] == []
                or user_input[CONF_AWAY_TIME_ZONE_1_OFFSET] == 0):
            user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] = ['none']
            user_input[CONF_AWAY_TIME_ZONE_1_OFFSET] = 0
        elif 'none' in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] and len(user_input[CONF_AWAY_TIME_ZONE_1_DEVICES]) > 1:
            if 'none' in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES]:
                user_input[CONF_AWAY_TIME_ZONE_1_DEVICES].remove('none')

        if (('none' in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] and 'none' not in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES])
                or user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] == []
                or user_input[CONF_AWAY_TIME_ZONE_2_OFFSET] == 0):
            user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] = ['none']
            user_input[CONF_AWAY_TIME_ZONE_2_OFFSET] = 0
        elif 'none' in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] and len(user_input[CONF_AWAY_TIME_ZONE_2_DEVICES]) > 1:
            if 'none' in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES]:
                user_input[CONF_AWAY_TIME_ZONE_2_DEVICES].remove('none')

        dup_devices = [devicename   for devicename in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES]
                                    if devicename in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] and devicename != 'none']
        if dup_devices != [] : self.errors[CONF_AWAY_TIME_ZONE_1_DEVICES] = 'away_time_zone_dup_devices_1'
        dup_devices = [devicename   for devicename in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES]
                                    if devicename in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] and devicename != 'none']
        if dup_devices != [] : self.errors[CONF_AWAY_TIME_ZONE_2_DEVICES] = 'away_time_zone_dup_devices_2'

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_tracking_parameters(self, user_input):
        '''
        Update the profile parameters
        '''
        user_input = self._option_text_to_parm(user_input, CONF_TRAVEL_TIME_FACTOR, TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT)
        user_input[CONF_EVLOG_BTNCONFIG_URL] = user_input[CONF_EVLOG_BTNCONFIG_URL].strip()

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
                user_input.pop(pname)

        user_input[CONF_INZONE_INTERVALS] = config_inzone_interval

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_waze_main(self, user_input):
        '''
        Validate the Waze numeric fields
        '''
        user_input = self._option_text_to_parm(user_input, CONF_WAZE_SERVER, WAZE_SERVER_OPTIONS)
        user_input = self._validate_numeric_field(user_input)
        user_input = self._option_text_to_parm(user_input, CONF_WAZE_HISTORY_TRACK_DIRECTION, WAZE_HISTORY_TRACK_DIRECTION_OPTIONS)
        user_input = self._validate_numeric_field(user_input)

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

        user_input = self._validate_numeric_field(user_input)
        user_input = self._option_text_to_parm(user_input, CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text)
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
    def _strip_special_text_from_user_input(self, user_input, pname):
        '''
        The user_input options may contain a special message after the actual parameter
        value. If so, strip it off so the field can be updated in the configuration file.

        Special message types:
            - '(Example: exampletext)'
            - '>'

        Returns:
            user_input  - user_input without the example text
        '''
        if user_input is None: return

        if pname not in user_input or type(pname) is not str:
            return user_input

        pvalue = user_input[pname]
        try:
            if instr(pvalue, DATA_ENTRY_ALERT_CHAR):
                pvalue = pvalue.split(DATA_ENTRY_ALERT_CHAR)[0]
            elif instr(pvalue, '(Example:'):
                pvalue = pvalue.split('(Example:')[0]

        except Exception as err:
            log_exception(err)
            pass

        user_input[pname] = pvalue.strip()

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
            if (Gb.conf_apple_accounts == []
                    or Gb.conf_apple_accounts[0] == []
                    or Gb.conf_apple_accounts[0].get(CONF_USERNAME, '') == ''
                    or Gb.conf_apple_accounts[0].get(CONF_PASSWORD, '') == ''):
                self.header_msg = 'icloud_acct_not_set_up'
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
            inactive_msg = 'all'
        elif  inactive_pct > .66:
            inactive_msg =  'most'
        elif inactive_pct > .34:
            inactive_msg =  'some'
        else:
            return 'none'
            # inactive_msg = 'few'

        self.header_msg = f'inactive_{inactive_msg}_devices'

        return inactive_msg

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
                                        called_from_step_id=None):
        '''
        Updata Data Sources form enables/disables finddev and mobile app datasources and
        adds/updates/removes an Apple account using the Update Username/Password screen
        '''

        self.step_id = 'data_source'
        self.errors = errors or {}
        self.errors_user_input = {}
        self.add_apple_acct_flag = False
        self.actions_list_default = ''
        action_item = ''
        await self._async_write_storage_icloud3_configuration_file()
        user_input, action_item = self._action_text_to_item(user_input)
        self.called_from_step_id_2 = called_from_step_id or self.called_from_step_id_2 or 'menu_0'

        if user_input is None:
            self.actions_list_default = 'update_apple_acct'
            return self.async_show_form(step_id='data_source',
                                        data_schema=form_data_source(self),
                                        errors=self.errors)

        self.log_step_info(user_input, action_item)

        # Set add or display next page now since they are not in apple_acct_items_by_idx
        if user_input['apple_accts'].startswith('➤ OTHER'):
            self.aa_page_no += 1
            if self.aa_page_no > int(len(self.apple_acct_items_list)/5):
                self.aa_page_no = 0
            return await self.async_step_data_source()

        if action_item == 'cancel':
            self._initialize_self_PyiCloud_fields_from_Gb()
            return await self.async_step_menu()

        if user_input['apple_accts'].startswith('➤ ADD'):
            self.add_apple_acct_flag = True
            action_item = 'update_apple_acct'
            self.conf_apple_acct = DEFAULT_APPLE_ACCOUNTS_CONF.copy()
            self.username = self.password = ''
            self.PyiCloud = None
        else:
            user_input = self._option_text_to_parm(user_input, 'apple_accts', self.apple_acct_items_by_username)
            self._get_conf_apple_acct_selected(user_input['apple_accts'])

        self.log_step_info(user_input, action_item)

        if (self.username != user_input.get('apple_accts', self.username)
                and action_item == 'save'):
            action_item = 'update_apple_acct'

        self.username = self.conf_apple_acct[CONF_USERNAME]
        self.password = self.conf_apple_acct[CONF_PASSWORD]
        self.PyiCloud = Gb.PyiCloud_by_username.get(self.username)

        if Gb.log_debug_flag:
            log_user_input = user_input.copy()
            log_debug_msg(f"{self.step_id.upper()} ({action_item}) > UserInput-{log_user_input}, Errors-{errors}")

        if action_item == 'update_apple_acct':
            self.aa_page_item[self.aa_page_no] = self.conf_apple_acct[CONF_USERNAME]
            return await self.async_step_update_apple_acct()

        if action_item == 'verification_code':
            return await self.async_step_reauth(called_from_step_id='data_source')

        if user_input[CONF_DATA_SOURCE] == ',':
            self.errors['base'] = 'icloud_acct_no_data_source'

        if self.errors == {}:
            if action_item == 'add_change_apple_acct':
                action_item == 'save'
                user_input[CONF_DATA_SOURCE] = list_add(user_input[CONF_DATA_SOURCE], ICLOUD)

            if action_item == 'save':
                self.data_source = list_to_str(user_input[CONF_DATA_SOURCE], ',')
                user_input[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX] = self.endpoint_suffix
                user_input[CONF_DATA_SOURCE] = self.data_source
                self._update_config_file_general(user_input)

                return await self.async_step_menu()

        self.step_id = 'data_source'
        return self.async_show_form(step_id='data_source',
                            data_schema=form_data_source(self),
                            errors=self.errors)

#..........................................................................................-
    def _get_conf_apple_acct_selected(self, username):
        '''
        Cycle through the devices listed on the device_list screen. If one was selected,
        get it's device name and position in the Gb.config_tracking[DEVICES] parameter.
        If Found, tThe position was saved in conf_device_idx
        Returns:
            - True = The devicename was found.
            - False = The devicename was not found.
        '''
        self.conf_apple_acct, self.aa_idx = config_file.conf_apple_acct(username)
        return

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            APPLE USERNAME PASSWORD
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_update_apple_acct(self, user_input=None, errors=None):

        self.step_id = 'update_apple_acct'
        self.errors = errors or {}
        self.errors_user_input = user_input or {}
        self.actions_list_default = ''
        action_item = ''
        await self._async_write_storage_icloud3_configuration_file()
        user_input, action_item = self._action_text_to_item(user_input)

        if user_input is None or CONF_USERNAME in self.errors:
            return self.async_show_form(step_id='update_apple_acct',
                        data_schema=form_update_apple_acct(self),
                        errors=self.errors)

        user_input = self._option_text_to_parm(user_input, 'account_selected', self.apple_acct_items_by_username)
        user_input[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX] = 'cn' \
                    if user_input.get('url_suffix_china') is True else 'None'
        user_input = self._strip_spaces(user_input, [CONF_USERNAME, CONF_PASSWORD, CONF_TOTP_KEY])

        if (user_input[CONF_LOCATE_ALL] is False
                and self._can_disable_locate_all(user_input) is False):
            self.errors[CONF_LOCATE_ALL] = 'icloud_acct_locate_all_reqd'
            user_input[CONF_LOCATE_ALL] = True
            action_item = ''
            return await self.async_step_update_apple_acct(
                                    user_input=user_input,
                                    errors=self.errors)

        user_input[CONF_USERNAME] = user_input[CONF_USERNAME].lower()
        user_input[CONF_TOTP_KEY] = ''      #user_input[CONF_TOTP_KEY].upper()
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        ui_apple_acct ={CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_TOTP_KEY: user_input[CONF_TOTP_KEY],
                        CONF_LOCATE_ALL: user_input[CONF_LOCATE_ALL]}

        #conf_apple_acct, _idx = config_file.conf_apple_acct(self.aa_idx)
        conf_username   = self.conf_apple_acct[CONF_USERNAME]
        conf_password   = self.conf_apple_acct[CONF_PASSWORD]
        conf_locate_all = self.conf_apple_acct[CONF_LOCATE_ALL]

        if Gb.log_debug_flag:
            log_user_input = user_input.copy()
            log_debug_msg(f"{self.step_id.upper()} ({action_item}) > UserInput-{log_user_input}, Errors-{errors}")

        if action_item == 'cancel_return':
            self.username = self.conf_apple_acct[CONF_USERNAME]
            self.password = self.conf_apple_acct[CONF_PASSWORD]
            self.PyiCloud = Gb.PyiCloud_by_username.get(self.username)
            return await self.async_step_data_source(user_input=None)

        if username == '' or password == '':
            action_item = ''

        # Adding an Apple Account but it already exists
        if (self.add_apple_acct_flag
                and username in Gb.PyiCloud_by_username):
            self.errors[CONF_USERNAME] = 'icloud_acct_dup_username_error'
            action_item = ''

        # Changing a username and the old one is being used and no devices are
        # using the old one, it's ok to change the name
        elif (username != conf_username
                and username in Gb.PyiCloud_by_username
                and instr(self.apple_acct_items_by_username[username], ' 0 of ') is False):
            user_input[CONF_USERNAME] = conf_username
            user_input[CONF_PASSWORD] = conf_password
            self.errors[CONF_USERNAME] = 'icloud_acct_username_inuse_error'
            action_item = ''

        # Saving an existing account with same password, no change, nothing to do
        if (action_item == 'log_into_apple_acct'
                and ui_apple_acct == self.conf_apple_acct
                and user_input[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX] ==\
                                        Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX]
                and user_input[CONF_LOCATE_ALL] != conf_locate_all
                and Gb.PyiCloud_by_username.get(username) is not None):
            self.errors['base'] = 'icloud_acct_logged_into'
            action_item = ''

        # Display the Confirm Actions form which will execute the remove_apple... function
        if action_item == 'stop_using_apple_acct':
            # Drop the tracked/untracked part from the current heading (user_input['account_selected'])
            # Ex: account_selected = 'GaryCobb (gcobb321) -> 4 of 7 iCloud Devices Tracked, Tracked-(Gary-iPad ...'
            confirm_action_form_hdr = ( f"Remove Apple Account - "
                                        f"{user_input['account_selected']}")
            if self.PyiCloud:
                confirm_action_form_hdr += f", Devices-{list_to_str(self.PyiCloud.icloud_dnames)}"
            self.multi_form_user_input = user_input.copy()

            return await self.async_step_delete_apple_acct(user_input=user_input)

        username_password_valid =  True
        aa_login_info_changed   = False
        other_flds_changed      = False
        # self.errors = {}
        if action_item == 'log_into_apple_acct':
            # Apple acct login info changed, validate it without logging in
            if (conf_username != user_input[CONF_USERNAME]
                    or conf_password != user_input[CONF_PASSWORD]
                    or user_input[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX] \
                            != Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX]
                    or username not in Gb.PyiCloud_by_username
                    or Gb.PyiCloud_by_username.get(username) is None):
                aa_login_info_changed = True

            if (user_input[CONF_LOCATE_ALL] != self.conf_apple_acct[CONF_LOCATE_ALL]
                    or user_input[CONF_TOTP_KEY] != self.conf_apple_acct[CONF_TOTP_KEY]):
                other_flds_changed = True

            if aa_login_info_changed:
                username_password_valid = \
                    await self._async_validate_username_password(username, password)

            if username_password_valid is False:
                self.actions_list_default = 'add_change_apple_acct'
                self.errors['base'] = ''
                self.errors[CONF_USERNAME] = 'icloud_acct_username_password_error'
                return await self.async_step_update_apple_acct(
                                    user_input=user_input,
                                    errors=self.errors)

        if aa_login_info_changed or other_flds_changed:
            self._update_conf_apple_accounts(self.aa_idx, user_input)
            await self._async_write_storage_icloud3_configuration_file()

        # Log into the account
        if (username not in Gb.PyiCloud_by_username
                or Gb.PyiCloud_by_username.get(username) is None):
            successful_login = await self.log_into_icloud_account(
                                                user_input,
                                                called_from_step_id='update_apple_acct')

            if successful_login:
                Gb.PyiCloud_by_username[user_input[CONF_USERNAME]] = \
                                    self.PyiCloud or Gb.PyiCloudLoggingInto
                Gb.PyiCloud_password_by_username[user_input[CONF_USERNAME]] = \
                                    user_input[CONF_PASSWORD]

                if (aa_login_info_changed and
                        username in Gb.username_pyicloud_503_connection_error):
                    self.errors['base'] = 'icloud_acct_updated_not_logged_into'

                if self.PyiCloud.requires_2fa:
                    action_item = 'verification_code'
                else:
                    return await self.async_step_data_source(user_input=None)

        if action_item == 'verification_code':
            return await self.async_step_reauth(called_from_step_id='update_apple_acct')

        return self.async_show_form(step_id='update_apple_acct',
                        data_schema=form_update_apple_acct(self),
                        errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _set_data_source(self, user_input):

        # No Apple Accounts set up, don't use it as a data source
        if len(Gb.conf_apple_accounts) == 1:
            #conf_apple_acct, _idx = config_file.conf_apple_acct(0)
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

        # Delete an existing account
        if remove_acct_flag:
            Gb.conf_apple_accounts.pop(aa_idx)
            self.aa_idx = aa_idx - 1
            if self.aa_idx < 0: self.aa_idx = 0
            self.aa_page_item[self.aa_page_no] = ''

        # Add a new account
        elif self.add_apple_acct_flag:
            if len(Gb.conf_apple_accounts) < 1:
                Gb.conf_apple_accounts = [DEFAULT_APPLE_ACCOUNTS_CONF.copy()]

            if Gb.conf_apple_accounts[0][CONF_USERNAME] == '':
                Gb.conf_apple_accounts[0] = self.conf_apple_acct.copy()
                self.aa_idx = 0
            else:
                Gb.conf_apple_accounts.append(self.conf_apple_acct.copy())
                self.aa_idx = len(Gb.conf_apple_accounts) - 1

            self.aa_page_no = int(self.aa_idx / 5)
            self.aa_page_item[self.aa_page_no] = self.conf_apple_acct[CONF_USERNAME]

        # Set the account being updated to the new value
        else:
            Gb.conf_apple_accounts[aa_idx] = self.conf_apple_acct.copy()
            self.aa_idx = aa_idx
            self.aa_page_item[self.aa_page_no] = self.conf_apple_acct[CONF_USERNAME]

        max_aa_idx = len(Gb.conf_apple_accounts) - 1
        if self.aa_idx > max_aa_idx:
            self.aa_idx = max_aa_idx
        elif self.aa_idx < 0:
            self.aa_idx = 0

        user_input['account_selected'] = self.aa_idx
        self._update_config_file_tracking(update_config_flag=True)
        self._build_apple_accounts_list()
        self._build_devices_list()
        config_file.build_log_file_filters()

#-------------------------------------------------------------------------------------------
    def tracked_untracked_form_msg(self, username):
        '''
        This is used in the config_flow_forms to fill in the tracked and untracked devices
        on the username password form
        '''

        PyiCloud = Gb.PyiCloud_by_username.get(username)
        icloud_dnames = PyiCloud.icloud_dnames if PyiCloud else []

        devicenames_by_username, icloud_dnames_by_username = \
                    self.get_conf_device_names_by_username(username)
        tracked_devices = [icloud_dname
                                for icloud_dname in icloud_dnames
                                if icloud_dname in icloud_dnames_by_username]
        untracked_devices = [icloud_dname
                                for icloud_dname in icloud_dnames
                                if icloud_dname not in icloud_dnames_by_username]

        return (f"Tracked-({list_to_str(tracked_devices)}), "
                f"Untracked-({list_to_str(untracked_devices)})")

#--------------------------------------------------------------------
    def get_conf_device_names_by_username(self, username):
        '''
        Cycle through the conf_devices and build a list of device names by the
        apple account usernames

        Parameter:
            username
        Return:
            {devicenames_by_username}, {icloud_dnames_by_username}
        '''
        devicenames_by_username = [conf_device[CONF_IC3_DEVICENAME]
                            for conf_device in Gb.conf_devices
                            if conf_device[CONF_APPLE_ACCOUNT] == username]

        icloud_dnames_by_username = [conf_device[CONF_FAMSHR_DEVICENAME]
                            for conf_device in Gb.conf_devices
                            if conf_device[CONF_APPLE_ACCOUNT] == username]

        devicenames_by_username.sort()
        icloud_dnames_by_username.sort()

        return devicenames_by_username, icloud_dnames_by_username

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

        user_input, action_item = self._action_text_to_item(user_input)
        user_input = self._option_text_to_parm(user_input, 'device_action',
                                                DELETE_APPLE_ACCT_DEVICE_ACTION_OPTIONS)
        self.log_step_info(user_input, action_item)

        if user_input is None or action_item is None:
            return self.async_show_form(step_id='delete_apple_acct',
                                        data_schema=form_delete_apple_acct(self),
                                        errors=self.errors)

        if action_item == 'cancel_return':
            return await self.async_step_update_apple_acct()

        device_action = user_input['device_action']
        self._delete_apple_acct(user_input)

        list_add(self.config_parms_update_control, ['tracking', 'restart'])
        self.header_msg = 'action_completed'

        return await self.async_step_data_source()

#-------------------------------------------------------------------------------------------
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
        #conf_apple_acct, _idx = config_file.conf_apple_acct(self.aa_idx)
        conf_username = self.conf_apple_acct[CONF_USERNAME]

        # Cycle thru config and get the username being deleted. Delete or update it
        updated_conf_devices = []
        for conf_device in Gb.conf_devices:
            if conf_device[CONF_APPLE_ACCOUNT] != conf_username:
                updated_conf_devices.append(conf_device)

            elif device_action == 'delete_devices':
                devicename = conf_device[CONF_IC3_DEVICENAME]
                self._remove_device_tracker_entity(devicename)

            elif device_action == 'set_devices_inactive':
                conf_device[CONF_APPLE_ACCOUNT] = ''
                conf_device[CONF_TRACKING_MODE] = INACTIVE_DEVICE
                updated_conf_devices.append(conf_device)

            elif device_action == 'reassign_devices':
                icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
                other_apple_acct = [PyiCloud.username
                                        for username, PyiCloud in Gb.PyiCloud_by_username.items()
                                        if icloud_dname in PyiCloud.device_id_by_icloud_dname]
                if other_apple_acct == []:
                    conf_device[CONF_APPLE_ACCOUNT] = ''
                    conf_device[CONF_TRACKING_MODE] = INACTIVE_DEVICE
                else:
                    conf_device[CONF_APPLE_ACCOUNT] = other_apple_acct[0]
                updated_conf_devices.append(conf_device)

        Gb.conf_devices = updated_conf_devices
        self._update_config_file_tracking(user_input={}, update_config_flag=True)

        # Remove the apple acct from the PyiCloud dict and delete it's instance
        PyiCloud = Gb.PyiCloud_by_username.pop(conf_username, None)
        if PyiCloud: del PyiCloud

        self._update_conf_apple_accounts(self.aa_idx, user_input, remove_acct_flag=True)

        return user_input

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_reauth(self, user_input=None, errors=None,
                                        called_from_step_id=None, ha_reauth_username=None):
        '''
        Ask the verification code to the user.

        The iCloud account needs to be verified. Show the code entry form, get the
        code from the user, send the code back to Apple ID iCloud via pyicloud and get
        a valid code indicator or invalid code error.

        If the code is valid, either:
            - return to the called_from_step_id (icloud_account form) if in the config_flow configuration routine or,
            - issue a 'create_entry' indicating a successful verification. This will return
            to the function it wass called from. This will be when a validation request was
            needed during the normal tracking.

        If invalid, display an error message and ask for the code again.

        Input:
            - called_from_step_id
                    = the step_id in the config_glow if the icloud3 configuration
                        is being updated
                    = None if the rquest is from another regular function during the normal
                        tracking operation.
        '''
        self.step_id = 'reauth'
        self.errors = errors or {}
        self.errors_user_input = {}
        action_item = ''
        self.called_from_step_id_1 = called_from_step_id or self.called_from_step_id_1 or 'menu_0'

        log_debug_msg(  f"OF-{self.step_id.upper()} ({action_item}) > "
                        f"FromForm-{called_from_step_id}, UserInput-{user_input}, Errors-{errors}")

        if user_input is None:
            if self.PyiCloud and self.PyiCloud.requires_2fa:
                self.errors['base'] ='verification_code_needed'

            return self.async_show_form(step_id='reauth',
                                        data_schema=form_reauth(self),
                                        errors=self.errors)
        try:
            user_input, action_item = self._action_text_to_item(user_input)
            user_input = self._strip_spaces(user_input, [CONF_VERIFICATION_CODE])
            user_input = self._option_text_to_parm(user_input, 'account_selected', self.apple_acct_items_by_username)
            log_debug_msg(f"OF-{self.step_id.upper()} ({action_item}) > UserInput-{user_input}, Errors-{errors}")

            if user_input['account_selected']:
                self._get_conf_apple_acct_selected(user_input['account_selected'])
                username = self.conf_apple_acct[CONF_USERNAME]
                password = self.conf_apple_acct[CONF_PASSWORD]
            else:
                self.aa_idx = 0
                username = self.conf_apple_acct[CONF_USERNAME] = user_input[CONF_USERNAME]
                password = self.conf_apple_acct[CONF_PASSWORD] = user_input[CONF_PASSWORD]

            self.apple_acct_reauth_username = username
            self.PyiCloud = Gb.PyiCloud_by_username.get(username, self.PyiCloud)

            if action_item == 'log_into_apple_acct':
                await self.log_into_icloud_account(user_input, called_from_step_id='reauth')

            elif (action_item == 'send_verification_code'
                    and user_input.get(CONF_VERIFICATION_CODE, '') == ''):
                action_item = 'cancel_return'

            if action_item == 'cancel_return':
                self.clear_PyiCloud_2fa_flags()
                return self.async_show_form(step_id=self.called_from_step_id_1,
                                            data_schema=self.form_schema(self.called_from_step_id_1),
                                            errors=self.errors)

            if action_item == 'send_verification_code':
                # if self.conf_apple_acct[CONF_TOTP_KEY]:
                #     OTP = pyotp.TOTP(conf_apple_acct[CONF_TOTP_KEY].replace('-', ''))
                #     otp_code = OTP.now()
                #     user_input[CONF_VERIFICATION_CODE] = otp_code
                valid_code = await self.reauth_send_verification_code_handler(self, user_input)

                if valid_code:
                    if instr(str(self.apple_acct_items_by_username), 'AUTHENTICATION'):
                        self.conf_apple_acct = ''
                    else:
                        self.clear_PyiCloud_2fa_flags()
                        return self.async_show_form(step_id=self.called_from_step_id_1,
                                                data_schema=self.form_schema(self.called_from_step_id_1),
                                                errors=self.errors)

            elif action_item == 'request_verification_code':
                await self.async_pyicloud_reset_session(username, password)

            return self.async_show_form(step_id='reauth',
                                        data_schema=form_reauth(self),
                                        errors=self.errors)
        except Exception as err:
            log_exception(err)

#..............................................................................................
    def clear_PyiCloud_2fa_flags(self):
        for username, PyiCloud in Gb.PyiCloud_by_username.items():
            if PyiCloud.requires_2fa:
                PyiCloud.new_2fa_code_already_requested_flag = False

#..............................................................................................
    @staticmethod
    async def reauth_send_verification_code_handler(caller_self, user_input):
        '''
        Handle the send_verification_code action. This is called from the ConfigFlow and OptionFlow
        reauth steps in each Flow. This provides this function with the appropriate data and return objects.

        Parameters:
            - caller_self = 'self' for OptionFlow and the _OptFlow object when calling from ConfigFlow
                            OptionFlow --> valid_code = await self.reauth_send_verification_code_handler(
                                                                    self, user_input)
                            ConfigFlow --> valid_code = await _OptFlow.reauth_send_verification_code_handler(
                                                                    _OptFlow, user_input)
            - user_input = user_input dictionary
        '''
        try:
            valid_code = await Gb.hass.async_add_executor_job(
                                        caller_self.PyiCloud.validate_2fa_code,
                                        user_input[CONF_VERIFICATION_CODE])

            # Do not restart iC3 right now if the username/password was changed on the
            # iCloud setup screen. If it was changed, another account is being logged into
            # and it will be restarted when exiting the configurator.
            if valid_code:
                post_event( f"{EVLOG_NOTICE}Apple Acct > {caller_self.PyiCloud.account_owner}, "
                            f"Code accepted, Verification completed")

                await caller_self._build_icloud_device_selection_list()

                Gb.EvLog.clear_evlog_greenbar_msg()
                Gb.icloud_force_update_flag = True
                caller_self.PyiCloud.new_2fa_code_already_requested_flag = False
                caller_self._build_apple_accounts_list()

                caller_self.errors['base'] = caller_self.header_msg = 'verification_code_accepted'

            else:
                post_event( f"{EVLOG_NOTICE}The Apple Account Verification Code is invalid "
                            f"({user_input[CONF_VERIFICATION_CODE]})")
                caller_self.errors[CONF_VERIFICATION_CODE] = 'verification_code_invalid'

            return valid_code

        except Exception as err:
            log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            ICLOUD UTILITIES - LOG INTO ACCOUNT
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def log_into_icloud_account(self, user_input, called_from_step_id=None):
        '''
        Log into the icloud account and check to see if a verification code is needed.
        If so, show the verification form, get the code from the user, verify it and
        return to the 'called_from_step_id' (icloud_account).

        Input:
            user_input  = A dictionary with the username and password, or
                            {username: icloudAccountUsername, password: icloudAccountPassword}
                        = {} to use the username/password in the tracking configuration parameters
            called_from_step_id
                        = The step logging into the iCloud account. This step will be returned
                            to when the login is complete.

        Exception:
            The self.PyiCloud.requres_2fa must be checked after a login to see if the account
            access needs to be verified. If so, the verification code entry form must be displayed.

        Returns:
            self.Pyicloud object
            self.PyiCloud_DeviceSvc object
            self.PyiCloud_FindMyFriends object
            self.opt_icloud_dname_list & self.device_form_icloud_famf_list =
                    A dictionary with the devicename and identifiers
                    used in the tracking configuration devices icloud_device parameter
        '''
        self.errors = {}
        called_from_step_id = called_from_step_id or 'update_apple_acct'
        log_debug_msg(  f"Logging into Apple Acct > UserInput-{user_input}, "
                        f"Errors-{self.errors}, Step-{self.step_id}, CalledFrom-{called_from_step_id}")

        # The username may be changed to assign a new account, if so, log into the new one
        if CONF_USERNAME not in user_input or CONF_PASSWORD not in user_input:
            return

        username = user_input[CONF_USERNAME].lower()
        password = user_input[CONF_PASSWORD]
        list_add(Gb.log_file_filter, password)
        endpoint_suffix = user_input.get(CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX,
                                        Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX])

        # Already logged in and no changes
        PyiCloud = Gb.PyiCloud_by_username.get(username)
        if (PyiCloud
                and password == PyiCloud.password
                and endpoint_suffix == PyiCloud.endpoint_suffix):
            self.PyiCloud = PyiCloud
            self.username = username
            self.password = password
            self.errors['base'] = 'icloud_acct_logged_into'
            self.header_msg = 'icloud_acct_logged_into'

            return True

        # Validate the account before actually logging in
        username_password_valid = await self._async_validate_username_password(username, password)
        if username_password_valid is False:
            self.errors['base'] = 'icloud_acct_login_error_user_pw'

            return False

        event_msg =(f"{EVLOG_NOTICE}Configure Settings > Logging into Apple Account {username}")
        if endpoint_suffix != 'None': event_msg += f", AppleServerURLSuffix-{endpoint_suffix}"
        log_info_msg(event_msg)

        try:
            await file_io.async_make_directory(Gb.icloud_cookie_directory)

            PyiCloud = None
            PyiCloud = await Gb.hass.async_add_executor_job(
                                        self.create_PyiCloudService_config_flow,
                                        username,
                                        password,
                                        endpoint_suffix)

            # Successful login, set PyiCloud fields
            self.PyiCloud = PyiCloud
            self.username = username
            self.password = password
            self.endpoint_suffix = endpoint_suffix
            Gb.username_valid_by_username[username] = True

            #if PyiCloud.DeviceSvc:
                #PyiCloud.DeviceSvc.refresh_client()
            PyiCloud.refresh_icloud_data()
            start_ic3.dump_startup_lists_to_log()

            if PyiCloud.requires_2fa or called_from_step_id is None:
                return True

            self.errors['base'] = 'icloud_acct_logged_into'
            self.header_msg = 'icloud_acct_logged_into'

            if called_from_step_id is None:
                return True

            return self.async_show_form(step_id=called_from_step_id,
                        data_schema=self.form_schema(called_from_step_id),
                        errors=self.errors)

        except (PyiCloudFailedLoginException) as err:
            err = str(err)
            _CF_LOGGER.error(f"Error logging into Apple Acct: {err}")

            # if called_from_step_id == 'update_apple_acct':
            if True is True:
                response_code = Gb.PyiCloudLoggingInto.response_code
                if Gb.PyiCloudLoggingInto.response_code_pwsrp_err == 503:
                    list_add(Gb.username_pyicloud_503_connection_error, username)
                    error_msg = 'icloud_acct_login_error_503'
                elif response_code == 400:
                    error_msg = 'icloud_acct_login_error_user_pw'
                elif response_code == 401 and instr(err, 'Python SRP'):
                    error_msg = 'icloud_acct_login_error_srp_401'
                elif response_code == 401:
                    error_msg = 'icloud_acct_login_error_user_pw'
                else:
                    error_msg = 'icloud_acct_login_error_other'
            else:
                error_msg = 'icloud_acct_login_error_other'
            self.errors['base'] = error_msg

        except Exception as err:
            log_exception(err)
            _CF_LOGGER.error(f"Error logging into Apple Account: {err}")
            self.errors['base'] = 'icloud_acct_login_error_other'

        start_ic3.dump_startup_lists_to_log()
        return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            CREATE PYICLOUD SERVICE OBJECTS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    @staticmethod
    async def _async_validate_username_password(username, password):
        '''
        Verify the username and password are valid using the Apple Acct validate
        routine before logging into the Apple Acct. This uses one PyiCloud call to
        validate instead of logging in and having it fail later in the process.
        '''
        if Gb.PyiCloudValidateAppleAcct is None:
            Gb.PyiCloudValidateAppleAcct = PyiCloudValidateAppleAcct()

        valid_apple_acct = await Gb.hass.async_add_executor_job(
                                        Gb.PyiCloudValidateAppleAcct.validate_username_password,
                                        username,
                                        password)

        return valid_apple_acct

#--------------------------------------------------------------------
    @staticmethod
    def create_PyiCloudService_config_flow(username, password, endpoint_suffix):
        '''
        Create the PyiCloudService object without going through the error checking and
        authentication test routines. This is used by config_flow to open a second
        PyiCloud session
        '''
        PyiCloud = PyiCloudService( username,
                                    password,
                                    cookie_directory=Gb.icloud_cookie_directory,
                                    session_directory=Gb.icloud_session_directory,
                                    endpoint_suffix=endpoint_suffix,
                                    config_flow_login=True)

        log_debug_msg(  f"Apple Acct > {PyiCloud.account_owner}, Login Successful, "
                        f"Update Connfiguration")

        start_ic3.dump_startup_lists_to_log()
        return PyiCloud

#--------------------------------------------------------------------
    @staticmethod
    def create_DeviceSvc_config_flow(PyiCloud):

        _DeviceSvc = PyiCloud.create_DeviceSvc_object(config_flow_login=True)

        start_ic3.dump_startup_lists_to_log()
        return _DeviceSvc

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            RESET PYICLOUD SESSION, GENERATE VERIFICATION CODE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_pyicloud_reset_session(self, username, password):
        '''
        Reset the current session and authenticate to restart pyicloud_ic3
        and enter a new verification code

        The username & password are specified in case the Apple acct is not logged
        into because of an error
        '''
        try:
            PyiCloud = self.PyiCloud
            if PyiCloud:
                post_event(f"{EVLOG_NOTICE}Apple Acct > {PyiCloud.account_owner}, Authentication needed")

                await self.async_delete_pyicloud_cookies_session_files(PyiCloud.username)

                if PyiCloud.authentication_alert_displayed_flag is False:
                    PyiCloud.authentication_alert_displayed_flag = True

                await Gb.hass.async_add_executor_job(PyiCloud.__init__,
                                                    PyiCloud.username,
                                                    PyiCloud.password,
                                                    Gb.icloud_cookie_directory,
                                                    Gb.icloud_session_directory)

                # Initialize PyiCloud object to force a new one that will trigger the 2fa process
                PyiCloud.verification_code = None

            # The Apple acct is not logged into. There may have been some type Of error.
            # Delete the session files four the username selected on the request form and
            # try to login
            elif username and password:
                post_event(f"{EVLOG_NOTICE}Apple Acct > {username}, Authentication needed")

                await self.async_delete_pyicloud_cookies_session_files(username)

                user_input = {}
                user_input[CONF_USERNAME] = username
                user_input[CONF_PASSWORD] = password

                await self.log_into_icloud_account(user_input)

                PyiCloud = self.PyiCloud

            if PyiCloud:
                post_event( f"{EVLOG_NOTICE}Apple Acct > {PyiCloud.account_owner}, "
                            f"Waiting for 6-digit Verification Code to be entered")
                return

        except PyiCloudFailedLoginException as err:
            login_err = str(err)
            login_err + ", Will retry logging into the Apple Account later"

        except Exception as err:
            login_err = str(err)
            log_exception(err)

        if instr(login_err, '-200') is False:
            PyiCloudSession = Gb.PyiCloudSession_by_username.get(username)
            if PyiCloudSession and PyiCloudSession.response_code == 503:
                list_add(Gb.username_pyicloud_503_connection_error, username)
                self.errors['base'] = 'icloud_acct_login_error_503'

            if PyiCloudSession.response_code == 503:
                post_event( f"{EVLOG_ERROR}Apple Acct > {username}, "
                            f"Apple is delaying displaying a new Verification code to "
                            f"prevent Suspicious Activity, probably due to too many requests. "
                            f"It should be displayed in about 20-30 minutes. "
                            f"{CRLF_DOT}The Apple Acct login will be retried within 15-mins. "
                            f"The Verification Code will be displayed then if successful")
            else:
                post_event( f"{EVLOG_ERROR}Apple Acct > {username}, "
                            f"An Error was encountered requesting the 6-digit Verification Code, "
                            f"{login_err}")


#--------------------------------------------------------------------
    async def async_delete_pyicloud_cookies_session_files(self, username=None):
        '''
        Delete the cookies and session files as part of the reset_session and request_verification_code
        This is called from config_flow/setp_reauth and pyicloud_reset_session

        '''
        post_event(f"{EVLOG_NOTICE}Apple Acct > Resetting Cookie/Session Files")

        if username is None: username = self.username
        cookie_directory  = Gb.icloud_cookie_directory
        cookie_filename   = "".join([c for c in username if match(r"\w", c)])

        delete_msg =  f"Apple Acct > Deleting Session Files > ({cookie_directory})"

        delete_msg += f"{CRLF_DOT}Session ({cookie_filename}.session)"
        await file_io.async_delete_file_with_msg(
                        'Apple Acct Session', cookie_directory, f"{cookie_filename}.session", delete_old_sv_file=True)
        delete_msg += f"{CRLF_DOT}Token Password ({cookie_filename}.tpw)"
        await file_io.async_delete_file_with_msg(
                        'Apple Acct Tokenpw', cookie_directory, f"{cookie_filename}.tpw")
        post_monitor_msg(delete_msg)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            TRUSTED DEVICES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_trusted_device(self, user_input=None, errors=None):
        """We need a trusted device."""
        return {}

        if errors is None:
            errors = {}

        trusted_devices_key_text = await self._build_trusted_devices_list()
        trusted_devices = await(Gb.hass.async_add_executor_job(
                                        self.PyiCloud.trusted_devices)
        )
        trusted_devices_for_form = {}
        for i, device in enumerate(trusted_devices):
            trusted_devices_for_form[i] = device.get(
                "deviceName", f"SMS to {device.get('phoneNumber')}"
            )

        # if user_input is None:
        #     return await self._show_trusted_device_form(
        #         trusted_devices_for_form, user_input, errors
        #     )

        # self._trusted_device = trusted_devices[int(user_input[CONF_TRUSTED_DEVICE])]

        # if not await self.hass.async_add_executor_job(
        #     self.api.send_verification_code, self._trusted_device
        # ):
        #     _LOGGER.error("Failed to send verification code")
        #     self._trusted_device = None
        #     errors[CONF_TRUSTED_DEVICE] = "send_verification_code"

        #     return await self._show_trusted_device_form(
        #         trusted_devices_for_form, user_input, errors
        #     )

        # return await self.async_step_verification_code()

    # async def _show_trusted_device_form(
    #     self, trusted_devices, user_input=None, errors=None
    # ):
    #     """Show the trusted_device form to the user."""

    #     return self.async_show_form(
    #         step_id=CONF_TRUSTED_DEVICE,
    #         data_schema=vol.Schema(
    #             {
    #                 vol.Required(CONF_TRUSTED_DEVICE): vol.All(
    #                     vol.Coerce(int), vol.In(trusted_devices)
    #                 )
    #             }
    #         ),
    #         errors=errors or {},
    #     )

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
        await self._async_write_storage_icloud3_configuration_file()

        if user_input is None:
            await self._build_icloud_device_selection_list()
            await self._build_mobapp_entity_selection_list()
            self._set_inactive_devices_header_msg()
            self._set_header_msg()
            self._build_devices_list()
            self.conf_device_update_control = {}

            return self.async_show_form(step_id='device_list',
                        data_schema=form_device_list(self),
                        errors=self.errors)

        user_input, action_item = self._action_text_to_item(user_input)
        self.log_step_info(user_input, action_item)

        if action_item == 'return':
            self.conf_device_update_control = {}
            return await self.async_step_menu()

        if instr(self.data_source, ICLOUD):
            if (Gb.conf_apple_accounts == []
                    or Gb.conf_apple_accounts[0] == []
                    or Gb.conf_apple_accounts[0].get(CONF_USERNAME, '') == ''
                    or Gb.conf_apple_accounts[0].get(CONF_PASSWORD, '') == ''):
                self.header_msg = 'icloud_acct_not_set_up'
                errors = {'base': 'icloud_acct_not_set_up'}

        device_cnt = len(Gb.conf_devices)

        if (action_item in ['update_device', 'delete_device']
                and CONF_DEVICES not in user_input):
            action_item = ''

        if action_item == 'return':
            self.conf_device_update_control = {}
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
            self.conf_device_update_control['add_device'] = True
            self.conf_device = DEFAULT_DEVICE_CONF.copy()
            return await self.async_step_add_device()

        user_input = self._option_text_to_parm(user_input, 'devices', self.device_items_by_devicename)
        user_input[CONF_IC3_DEVICENAME] = user_input['devices']
        self.log_step_info(user_input, action_item)
        self._get_conf_device_selected(user_input)

        if action_item == 'update_device':
            self.conf_device_update_control['update_device'] = True
            return await self.async_step_update_device()

        if action_item == 'delete_device':
            self.conf_device_update_control['delete_device'] = True
            return await self.async_step_delete_device()

        await self._build_icloud_device_selection_list()
        await self._build_mobapp_entity_selection_list()
        self._set_inactive_devices_header_msg()
        self._set_header_msg()

        self._build_devices_list()
        self.conf_device_update_control = {}

        return self.async_show_form(step_id='device_list',
                        data_schema=form_device_list(self),
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

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           DELETE DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_delete_device(self, user_input=None, errors=None):
        '''
        1. Delete the device from the tracking devices list and adjust the device index
        2. Delete all devices
        3. Clear the iCloud, Mobile App and track_from_zone fields from all devices
        '''
        self.step_id = 'delete_device'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = self._action_text_to_item(user_input)

        # The delete_this_device item was modified to add the devicename/fname so it will
        # return a field value without a match, reset it here
        if action_item and action_item.startswith('delete_this_device'):
            action_item = 'delete_this_device'

        self.log_step_info(user_input, action_item)

        if user_input is None or action_item is None:
            return self.async_show_form(step_id='delete_device',
                                        data_schema=form_delete_device(self),
                                        errors=self.errors)

        # if user_input is not None or action_item is not None:
        if action_item == 'delete_device_cancel':
            pass

        elif action_item == 'delete_this_device':
            self._delete_this_device()

        elif action_item == 'delete_all_devices':
            self._delete_all_devices()

        elif action_item == 'reset_this_device_data_source':
            self._reset_this_device_data_source_fields()

        elif action_item == 'reset_all_devices_data_source':
            self._reset_all_devices_data_source_fields()

        if action_item != 'delete_device_cancel':
            list_add(self.config_parms_update_control, ['tracking', 'restart'])
            self.header_msg = 'action_completed'

        return await self.async_step_device_list()

#-------------------------------------------------------------------------------------------
    def _delete_this_device(self, conf_device=None):
        """ Delete the device_tracker entity and associated ic3 configuration """

        try:
            if conf_device:
                devicename = conf_device[CONF_IC3_DEVICENAME]
                self.conf_device = conf_device
                self.conf_device_idx = Gb.conf_devices_idx_by_devicename[devicename]
            else:
                devicename = self.conf_device[CONF_IC3_DEVICENAME]

            event_msg = (f"Configuration Changed > DeleteDevice-{devicename}, "
                        f"{self.conf_device[CONF_FNAME]}/"
                        f"{DEVICE_TYPE_FNAME(self.conf_device[CONF_DEVICE_TYPE])}")
            post_event(event_msg)

            # if deleting last  device, use _delete all to simplifying table resetting
            if len(Gb.conf_devices) <= 1:
                return self._delete_all_devices()

            self._remove_device_tracker_entity(devicename)

            self.dev_page_item[self.dev_page_no] = ''
            Gb.conf_devices.pop(self.conf_device_idx)
            self._update_config_file_tracking(update_config_flag=True)

            # The lists may have not been built if deleting a device when deleting an Apple acct
            if devicename in self.device_items_by_devicename:
                del self.device_items_by_devicename[devicename]
            # if self.device_items_by_devicename == {}:
            #     return

            # del self.device_items_by_devicename[devicename]
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
                self._remove_device_tracker_entity(devicename)

            Gb.conf_devices = []
            self.device_items_by_devicename    = {}       # List of the apple_accts in the Gb.conf_tracking[apple_accts] parameter
            self.device_items_displayed        = []       # List of the apple_accts displayed on the device_list form
            self.dev_page_item                 = ['', '', '', '', ''] # Device's devicename last displayed on each page
            self.dev_page_no                   = 0        # apple_accts List form page number, starting with 0

            self._update_config_file_tracking(update_config_flag=True)
        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def _reset_this_device_data_source_fields(self):
        """
        Reset the iCloud & Mobile App to their initiial values.
        Keep the devicename, friendly name, picture and other fields
        """

        self.conf_device.update(DEFAULT_DEVICE_DATA_SOURCE)

        self._update_config_file_tracking(update_config_flag=True)

#-------------------------------------------------------------------------------------------
    def _reset_all_devices_data_source_fields(self):
        """
        Reset the iCloud & Mobile App fields to their initiial values.
        Keep the devicename, friendly name, picture and other fields
        """

        for conf_device in Gb.conf_devices:
            conf_device.update(DEFAULT_DEVICE_DATA_SOURCE)

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
        await self._build_update_device_selection_lists(self.conf_device[CONF_IC3_DEVICENAME])

        if user_input is None:
            return self.async_show_form(step_id='add_device',
                                        data_schema=form_add_device(self),
                                        errors=self.errors)

        user_input, action_item = self._action_text_to_item(user_input)
        user_input = self._strip_special_text_from_user_input(user_input, CONF_IC3_DEVICENAME)
        user_input = self._strip_special_text_from_user_input(user_input, CONF_FNAME)
        user_input = self._strip_special_text_from_user_input(user_input, CONF_MOBILE_APP_DEVICE)
        user_input = self._option_text_to_parm(user_input, CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)
        user_input = self._option_text_to_parm(user_input, CONF_DEVICE_TYPE, DEVICE_TYPE_FNAMES)
        self.log_step_info(user_input, action_item)

        if (action_item == 'cancel'
                or user_input[CONF_IC3_DEVICENAME].strip() == ''):
            return await self.async_step_device_list()

        self.add_device_flag = self.display_rarely_updated_parms = True
        self._validate_devicename(user_input)

        if not self.errors:
            self.conf_device.update(user_input)

            if user_input['mobapp'] is False:
                self.conf_device[CONF_INZONE_INTERVAL] = DEFAULT_GENERAL_CONF[CONF_INZONE_INTERVALS][NO_MOBAPP]
            else:
                device_type = user_input[CONF_DEVICE_TYPE]
                self.conf_device[CONF_INZONE_INTERVAL] = DEFAULT_GENERAL_CONF[CONF_INZONE_INTERVALS][device_type]

            self.conf_device.pop('mobapp')

        if self._any_errors():
            self.errors['action_items'] = 'update_aborted'
            self.conf_device.update(user_input)

        return self.async_show_form(step_id='update_device',
                        data_schema=form_update_device(self),
                        errors=self.errors,
                        last_step=False)


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

        await self._build_update_device_selection_lists(self.conf_device[CONF_IC3_DEVICENAME])
        log_debug_msg(f"{self.step_id.upper()} ( > UserInput-{user_input}, Errors-{errors}")

        if user_input is None:
            return self.async_show_form(step_id='update_device',
                                        data_schema=form_update_device(self),
                                        errors=self.errors)

        user_input, action_item = self._action_text_to_item(user_input)
        self.log_step_info(user_input, action_item)

        # Add rarely used parameters to user input from their current values since they
        # If rarely used parms is not in user_input (it is True and not displayed) or is True
        # display the fields, otherwise do not display them and fill in there values
        if (RARELY_UPDATED_PARMS not in user_input
                or isnot_empty(user_input[RARELY_UPDATED_PARMS])):
            ui_rarely_updated_parms = True
        else:
            ui_rarely_updated_parms = False
        user_input.pop(RARELY_UPDATED_PARMS, None)

        if self.display_rarely_updated_parms is False:
            user_input[CONF_DEVICE_TYPE]          = self.conf_device[CONF_DEVICE_TYPE]
            user_input[CONF_INZONE_INTERVAL]      = self.conf_device[CONF_INZONE_INTERVAL]
            user_input[CONF_FIXED_INTERVAL]       = self.conf_device[CONF_FIXED_INTERVAL]
            user_input[CONF_LOG_ZONES]            = self.conf_device[CONF_LOG_ZONES]
            user_input[CONF_TRACK_FROM_ZONES]     = self.conf_device[CONF_TRACK_FROM_ZONES]
            user_input[CONF_TRACK_FROM_BASE_ZONE] = self.conf_device[CONF_TRACK_FROM_BASE_ZONE]
        ui_rarely_used_parms_changed = (ui_rarely_updated_parms != self.display_rarely_updated_parms)
        self.display_rarely_updated_parms = ui_rarely_updated_parms

        if 'add_device' not in self.conf_device_update_control:
            self.dev_page_item[self.dev_page_no] = self.conf_device[CONF_IC3_DEVICENAME]

        if action_item == 'cancel_device_selection':
            return await self.async_step_device_list()
        elif action_item == 'cancel':
            return await self.async_step_menu()

        # Get the dname_username key from the value description of FAMSHR_DEVICENAME field
        _icloud_dname_username = [icloud_dname_username
                                    for icloud_dname_username, v in self.icloud_list_text_by_fname.items()
                                    if (v == user_input[CONF_FAMSHR_DEVICENAME])]

        _icloud_dname_username = _icloud_dname_username[0] if isnot_empty(_icloud_dname_username) else 'None'

        # Reset if non-devicename entry selected (one that starts with a '.')
        if _icloud_dname_username.startswith('.'):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'unknown_icloud'
            user_input[CONF_FAMSHR_DEVICENAME] = (  f"{self.conf_device[CONF_FAMSHR_DEVICENAME]}"
                                                    f"{LINK}{self.conf_device[CONF_APPLE_ACCOUNT]}")

        self.log_step_info(user_input, action_item)

        if _icloud_dname_username == 'None':
            user_input[CONF_APPLE_ACCOUNT]     = ''
            user_input[CONF_FAMSHR_DEVICENAME] = 'None'
        elif instr( _icloud_dname_username, LINK):
            icloud_dname_part, username_part  = _icloud_dname_username.split(LINK)
            user_input[CONF_APPLE_ACCOUNT]     = username_part
            user_input[CONF_FAMSHR_DEVICENAME] = icloud_dname_part
        else:
            user_input[CONF_APPLE_ACCOUNT]     = self.conf_device[CONF_APPLE_ACCOUNT]
            user_input[CONF_FAMSHR_DEVICENAME] = self.conf_device[CONF_FAMSHR_DEVICENAME]
        if CONF_FMF_EMAIL in user_input:
            user_input[CONF_FMF_EMAIL] = 'None'
            user_input[CONF_FMF_DEVICE_ID] = ''

        user_input = self._option_text_to_parm(user_input, CONF_MOBILE_APP_DEVICE, self.mobapp_list_text_by_entity_id)
        user_input = self._option_text_to_parm(user_input, CONF_PICTURE, self.picture_by_filename)
        user_input = self._option_text_to_parm(user_input, CONF_DEVICE_TYPE, DEVICE_TYPE_FNAMES)
        user_input = self._option_text_to_parm(user_input, CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text)
        user_input = self._strip_special_text_from_user_input(user_input, CONF_IC3_DEVICENAME)
        self.log_step_info(user_input, action_item)

        user_input['old_devicename'] = self.conf_device[CONF_IC3_DEVICENAME]
        user_input  = self._validate_devicename(user_input)
        user_input  = self._validate_update_device(user_input)
        change_flag = self._was_device_data_changed(user_input)
        user_input.pop('old_devicename', None)

        if self.errors:
            self.errors['action_items'] = 'update_aborted'

            return self.async_show_form(step_id='update_device',
                            data_schema=form_update_device(self),
                            errors=self.errors,
                            last_step=True)

        if change_flag is False:
            if ui_rarely_used_parms_changed and self.display_rarely_updated_parms:
                return await self.async_step_update_device()

            return await self.async_step_device_list()

        ui_devicename = user_input[CONF_IC3_DEVICENAME]

        only_non_tracked_field_updated = self._is_only_non_tracked_field_updated(user_input)
        self.conf_device.update(user_input)

        # Update the configuration file
        if 'add_device' in self.conf_device_update_control:
            Gb.conf_devices.append(self.conf_device)
            self.conf_device_idx = len(Gb.conf_devices) - 1
            self.dev_page_no = int(self.conf_device_idx / 5)

            # Add the new device to the device_list form and and set it's position index
            self.device_items_by_devicename[ui_devicename] = self._format_device_list_item(self.conf_device)

            post_event( f"Configuration Changed > AddDevice-{ui_devicename}, "
                        f"{self.conf_device[CONF_FNAME]}/"
                        f"{DEVICE_TYPE_FNAME(self.conf_device[CONF_DEVICE_TYPE])}")
        else:
            Gb.conf_devices[self.conf_device_idx] = self.conf_device

            post_event (f"Configuration Changed > ChangeDevice-{ui_devicename}, "
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

        await self._build_icloud_device_selection_list()

        self.header_msg = 'conf_updated'
        if only_non_tracked_field_updated:
            list_add(self.config_parms_update_control, 'devices')
        else:
            list_add(self.config_parms_update_control, ['tracking', 'restart'])

        # Update the device_tracker & sensor entities now that the configuration has been updated
        if 'add_device' in self.conf_device_update_control:
            # This is the first device being added,
            # we need to set up the device_tracker platform, which will add it
            ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)
            if Gb.async_add_entities_device_tracker is None:
                await Gb.hass.config_entries.async_forward_entry_setups(Gb.config_entry, ['device_tracker'])

                sensors_list = self._build_all_sensors_list()
                self._create_sensor_entity(devicename, conf_device, sensors_list)

            else:
                self._create_device_tracker_and_sensor_entities(ui_devicename, self.conf_device)
                ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)

        else:
            self._update_changed_sensor_entities()

            if ui_rarely_used_parms_changed:
                return await self.async_step_update_device()

        return await self.async_step_device_list()



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
    def _validate_devicename(self, user_input):
        '''
        Validate the add device parameters
        '''
        user_input = self._option_text_to_parm(user_input, CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)

        ui_devicename     = user_input[CONF_IC3_DEVICENAME] = slugify(user_input[CONF_IC3_DEVICENAME]).strip()
        ui_fname          = user_input[CONF_FNAME]          = user_input[CONF_FNAME].strip()
        old_devicename    = user_input.get('old_devicename', ui_fname)
        ui_old_devicename = [ui_devicename, old_devicename]

        if ui_devicename == '':
            self.errors[CONF_IC3_DEVICENAME] = 'required_field'
            return user_input

        if ui_fname == '':
            self.errors[CONF_FNAME] = 'required_field'
            return user_input

        # Already used if the new ic3_devicename is in the devicename list
        if (ui_devicename in self.device_items_by_devicename
                and ui_devicename != self.conf_device[CONF_IC3_DEVICENAME]):
            self.errors[CONF_IC3_DEVICENAME] = 'duplicate_ic3_devicename'
            self.errors_user_input[CONF_IC3_DEVICENAME] = ui_devicename
            self.errors_user_input[CONF_IC3_DEVICENAME] = f"{ui_devicename}{DATA_ENTRY_ALERT}Assigned to another iCloud3 device"

        # Already used if the new ic3_devicename is in the ha device_tracker entity list
        if (ui_devicename in self.device_trkr_by_entity_id_all
                and self.device_trkr_by_entity_id_all[ui_devicename] != DOMAIN):
            self.errors[CONF_IC3_DEVICENAME] = 'duplicate_other_devicename'
            self.errors_user_input[CONF_IC3_DEVICENAME] = ( f"{ui_devicename}{DATA_ENTRY_ALERT}Used by Integration > "
                                                            f"{self.device_trkr_by_entity_id_all[ui_devicename]}")

        for conf_device in Gb.conf_devices:
            if ui_devicename == conf_device[CONF_IC3_DEVICENAME]:
                continue
            if ui_fname == conf_device[CONF_FNAME]:
                self.errors[CONF_FNAME] = 'duplicate_ic3_devicename'
                self.errors_user_input[CONF_FNAME] = (  f"{ui_fname}{DATA_ENTRY_ALERT}Used by iCloud3 device > "
                                                        f"{conf_device[CONF_IC3_DEVICENAME]}")
                break

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_data_source_names(self, conf_device):
        '''
        Check the devicenames in device's configuration for any errors in the iCloud and
        Mobile App fields.

        Parameters:
            - conf_device - the conf_device or user_input item for the device

        Return:
            - self.errors[xxx] will be set if any errors are found
            - True/False - if errors are found/not found
        '''
        if self.add_device_flag:
            return False

        _conf_apple_acct      = conf_device[CONF_APPLE_ACCOUNT]
        _conf_icloud_dname    = conf_device[CONF_FAMSHR_DEVICENAME]
        _conf_mobile_app_name = conf_device[CONF_MOBILE_APP_DEVICE]
        icloud_dname_username = f"{_conf_icloud_dname}{LINK}{_conf_apple_acct}"

        if (_conf_apple_acct  == ''
                and _conf_icloud_dname != 'None'):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'unknown_apple_acct'

        elif (_conf_icloud_dname != 'None'
                and icloud_dname_username not in self.icloud_list_text_by_fname
                and instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD)):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'unknown_icloud'

        elif (conf_device[CONF_TRACKING_MODE] != INACTIVE_DEVICE
                and _conf_icloud_dname == 'None'
                and _conf_mobile_app_name == 'None'):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'no_device_selected'
            self.errors[CONF_MOBILE_APP_DEVICE] = 'no_device_selected'

        if (_conf_mobile_app_name != 'None'
                and _conf_mobile_app_name not in self.mobapp_list_text_by_entity_id
                and instr(Gb.conf_tracking[CONF_DATA_SOURCE], MOBAPP)):
            self.errors[CONF_MOBILE_APP_DEVICE] = 'unknown_mobapp'

        return (CONF_FAMSHR_DEVICENAME in self.errors
                or CONF_MOBILE_APP_DEVICE in self.errors)

#-------------------------------------------------------------------------------------------
    def _validate_update_device(self, user_input):
        """ Validate the device parameters

            Sets:
                self.error[] for fields that are in error
            Returns:
                user_input
                change_flag: True if a field was changed
                change_fname_flag: True if the fname was changed and the device_tracker entity needs to be updated
                change_tfz_flag: True if the track_fm_zones zone was changed and the sensors need to be updated
        """

        ui_devicename  = user_input[CONF_IC3_DEVICENAME]
        old_devicename = user_input.get('old_devicename', ui_devicename)
        ui_old_devicename = [ui_devicename, old_devicename]

        self.ic3_devicename_being_updated = ui_devicename

        user_input[CONF_FNAME] = user_input[CONF_FNAME].strip()
        if user_input[CONF_FNAME] == '':
            self.errors[CONF_FNAME] = 'required_field'

        # Check to make sure either the iCloud Device or MobApp device was entered
        # You must have one of them to enable tracking
        if user_input[CONF_FAMSHR_DEVICENAME].strip() == '':
            user_input[CONF_FAMSHR_DEVICENAME] = 'None'

        if CONF_FMF_EMAIL in user_input:
            user_input[CONF_FMF_EMAIL] = 'None'
            user_input[CONF_FMF_DEVICE_ID] = ''

        if (user_input[CONF_MOBILE_APP_DEVICE].strip() == ''
                or user_input[CONF_MOBILE_APP_DEVICE] == 'scan_hdr'):
            user_input[CONF_MOBILE_APP_DEVICE] = 'None'

        self._validate_data_source_names(user_input)

        if self.PyiCloud:
            _AppleDev = self.PyiCloud.DeviceSvc
            conf_icloud_dname = user_input[CONF_FAMSHR_DEVICENAME]
            device_id = self.PyiCloud.device_id_by_icloud_dname.get(conf_icloud_dname, '')
            raw_model, model, model_display_name = self.PyiCloud.device_model_info_by_fname.get(conf_icloud_dname, ['', '', ''])
            user_input[CONF_FAMSHR_DEVICE_ID]   = device_id
            user_input[CONF_RAW_MODEL]          = raw_model
            user_input[CONF_MODEL]              = model
            user_input[CONF_MODEL_DISPLAY_NAME] = model_display_name

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

        # Build 'track_from_zones' list
        track_from_zones = [zone    for zone in self.zone_name_key_text.keys()
                                    if (zone in user_input[CONF_TRACK_FROM_ZONES]
                                        and zone not in ['.',
                                            self.conf_device[CONF_TRACK_FROM_BASE_ZONE]])]
        # track_from_zones.append(self.conf_device[CONF_TRACK_FROM_BASE_ZONE])
        list_add(track_from_zones, user_input[CONF_TRACK_FROM_BASE_ZONE])
        user_input[CONF_TRACK_FROM_ZONES] = track_from_zones

        if isbetween(user_input[CONF_FIXED_INTERVAL], 1, 2):
            user_input[CONF_FIXED_INTERVAL] = 3
            self.errors[CONF_FIXED_INTERVAL] = 'fixed_interval_invalid_range'

        return user_input

#-------------------------------------------------------------------------------------------
    def _was_device_data_changed(self, user_input):
        """ Cycle thru old and new data and identify changed fields

            Returns:
                True if anything was changed
            Updates:
                sensor_entity_attrs_changed based on changes detected
        """

        if self.errors:
            return False

        change_flag = False
        self.conf_device_update_control[CONF_IC3_DEVICENAME]  = self.conf_device[CONF_IC3_DEVICENAME]
        self.conf_device_update_control['new_ic3_devicename'] = user_input[CONF_IC3_DEVICENAME]
        self.conf_device_update_control[CONF_TRACKING_MODE]   = self.conf_device[CONF_TRACKING_MODE]
        self.conf_device_update_control['new_tracking_mode']  = user_input[CONF_TRACKING_MODE]

        for pname, pvalue in self.conf_device.items():
            if pname in ['evlog_display_order', 'unique_id', 'fmf_device_id']:
                continue

            if pname not in user_input or user_input[pname] != pvalue:
                change_flag = True

            if pname == CONF_FNAME and user_input[CONF_FNAME] != pvalue:
                self.conf_device_update_control[CONF_FNAME] = user_input[CONF_FNAME]

            if pname == CONF_TRACK_FROM_ZONES and user_input[CONF_TRACK_FROM_ZONES] != pvalue:
                new_tfz_zones_list, remove_tfz_zones_list = \
                            self._devices_form_identify_new_and_removed_tfz_zones(user_input)

                self.conf_device_update_control['new_tfz_zones']    = new_tfz_zones_list
                self.conf_device_update_control['remove_tfz_zones'] = remove_tfz_zones_list

        return change_flag

#-------------------------------------------------------------------------------------------
    def _update_changed_sensor_entities(self):
        """ Update the track_fm_zone and device_tracker sensors if needed"""

        # Use the current ic3_devicename since that is how the Device & DeviceTracker objects with the
        # device_tracker and sensor entities are stored. If the devicename was also changed, the
        # device_tracker and sensor entity names will be changed later

        devicename        = self.conf_device_update_control[CONF_IC3_DEVICENAME]
        new_devicename    = self.conf_device_update_control['new_ic3_devicename']
        tracking_mode     = self.conf_device_update_control[CONF_TRACKING_MODE]
        new_tracking_mode = self.conf_device_update_control['new_tracking_mode']

        # Remove the new track_fm_zone sensors just unchecked
        if 'remove_tfz_zones' in self.conf_device_update_control:
            remove_tfz_zones_list = self.conf_device_update_control['remove_tfz_zones']
            self.remove_track_fm_zone_sensor_entity(devicename, remove_tfz_zones_list)

        # Create the new track_fm_zone sensors just checked
        if 'new_tfz_zones' in self.conf_device_update_control:
            new_tfz_zones_list = self.conf_device_update_control['new_tfz_zones']
            self._create_track_fm_zone_sensor_entity(devicename, new_tfz_zones_list)

        # fname was changed - change the fname of device_tracker and all sensors to the new fname
        # Inactive devices were not created so they are not in Gb.DeviceTrackers_by_devicename
        if (devicename == new_devicename
                and CONF_FNAME in self.conf_device_update_control
                and devicename in Gb.DeviceTrackers_by_devicename):
            DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
            DeviceTracker.update_entity_attribute(new_fname=self.conf_device[CONF_FNAME])

            try:
                for sensor, Sensor in Gb.Sensors_by_devicename[devicename].items():
                    Sensor.update_entity_attribute(new_fname=self.conf_device[CONF_FNAME])
            except:
                pass

            # check to see if device has tfz sensors
            try:
                for sensor, Sensor in Gb.Sensors_by_devicename_from_zone[devicename].items():
                    Sensor.update_entity_attribute(new_fname=self.conf_device[CONF_FNAME])
            except:
                pass

        # devicename was changed - delete device_tracker and all sensors for devicename and add them for new_devicename
        if devicename != new_devicename:
            self._update_config_file_tracking()
            self._create_device_tracker_and_sensor_entities(new_devicename, self.conf_device)
            self._remove_device_tracker_entity(devicename)

        # If the device was 'inactive' it's entity may not exist since they are not created for
        # inactive devices. If so, create it now if it is no longer 'inactive'.
        elif (tracking_mode == INACTIVE_DEVICE
                and new_tracking_mode != INACTIVE_DEVICE
                and new_devicename not in Gb.DeviceTrackers_by_devicename):
            self._create_device_tracker_and_sensor_entities(new_devicename, self.conf_device)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           CHANGE DEVICE ORDER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_change_device_order(self, user_input=None, errors=None):
        self.step_id = 'change_device_order'
        user_input, action_item = self._action_text_to_item(user_input)

        if user_input is None:
            self.log_step_info(user_input, action_item)
            self.cdo_devicenames = [self._format_device_text_hdr(conf_device)
                                        for conf_device in Gb.conf_devices]
            self.cdo_new_order_idx = [x for x in range(0, len(Gb.conf_devices))]
            self.actions_list_default = 'move_down'
            return self.async_show_form(step_id='change_device_order',
                                        data_schema=form_change_device_order(self),
                                        errors=self.errors)

        if action_item == 'cancel':
            return await self.async_step_device_list()

        if action_item == 'save':
            new_conf_devices = []
            for idx in self.cdo_new_order_idx:
                new_conf_devices.append(Gb.conf_devices[idx])

            Gb.conf_devices = new_conf_devices
            config_file.set_conf_devices_index_by_devicename()
            self._update_config_file_tracking(update_config_flag=True)
            self._build_devices_list()
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
                            data_schema=form_change_device_order(self),
                            errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            AWAY TIME ZONE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_away_time_zone(self, user_input=None, errors=None):
        self.step_id = 'away_time_zone'
        user_input, action_item = self._action_text_to_item(user_input)

        self._build_away_time_zone_devices_list()
        self._build_away_time_zone_hours_list()

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self._any_errors():
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id= 'away_time_zone',
                            data_schema=form_away_time_zone(self),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _build_away_time_zone_hours_list(self):
        if self.away_time_zone_hours_key_text != {}:
            return

        ha_time = int(Gb.this_update_time[0:2])
        for hh in range(ha_time-12, ha_time+13):
            away_hh = hh + 24 if hh < 0 else hh

            if   away_hh == 0: ap_hh = 12; ap = 'a'
            elif away_hh < 12:  ap_hh = away_hh; ap = 'a'
            elif away_hh == 12: ap_hh = 12; ap = 'p'
            else: ap_hh = away_hh - 12; ap = 'p'

            if away_hh >= 24:
                away_hh -= 24
                if   ap_hh == 12: ap = 'a'
                elif ap_hh >= 13: ap_hh -= 12; ap = 'a'

            if Gb.time_format_12_hour:
                time_str = f"{ap_hh:}{Gb.this_update_time[2:]}{ap}"
            else:
                time_str = f"{away_hh:02}{Gb.this_update_time[2:]}"

            if away_hh == ha_time:
                time_str = f"Home Time Zone"
            elif hh < ha_time:
                time_str += f" (-{abs(hh-ha_time):} hours)"
            else:
                time_str += f" (+{abs(ha_time-hh):} hours)"
            self.away_time_zone_hours_key_text[hh-ha_time] = time_str

#-------------------------------------------------------------------------------------------
    def _build_away_time_zone_devices_list(self):

        self.away_time_zone_devices_key_text = {'none': 'None - All devices are at Home'}
        self.away_time_zone_devices_key_text.update(self._devices_selection_list())

#-------------------------------------------------------------------------------------------
    def _build_log_level_devices_list(self):

        self.log_level_devices_key_text = {'all': 'All Devices - Add RawData for all devices to the `icloud-0.log` file'}
        self.log_level_devices_key_text.update(self._devices_selection_list())

#-------------------------------------------------------------------------------------------
    def _devices_selection_list(self):
        return {conf_device[CONF_IC3_DEVICENAME]: conf_device[CONF_FNAME]
                                for conf_device in Gb.conf_devices
                                if conf_device[CONF_TRACKING_MODE] != INACTIVE_DEVICE}


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            DEVICES LIST FORM, DEVICE UPDATE FORM SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _build_apple_accounts_list(self):
        '''
        Build a list of the Apple Accounts that is used in the data source,
        username/password and reauthentication screens to s select the
        Apple Account or add a new one.

        Parameters:
            include_icloud_dnames:
                True - Add a list of the devices in the Apple Account and add a
                        new account option
        '''

        self.apple_acct_items_by_username = {}
        self.is_verification_code_needed = False

        aa_idx = -1
        for apple_account in Gb.conf_apple_accounts:
            aa_idx += 1
            username = apple_account[CONF_USERNAME]
            devicenames_by_username, icloud_dnames_by_username = \
                        self.get_conf_device_names_by_username(username)
            devices_assigned_cnt = len(devicenames_by_username)

            if aa_idx == 0 and username == '':
                break
            elif username == '':
                continue
            else:
                PyiCloud = Gb.PyiCloud_by_username.get(username)
                if PyiCloud:
                    aa_text = f"{PyiCloud.account_owner.split('@')[0]}{RARROW}"
                    if PyiCloud.requires_2fa:
                        self.is_verification_code_needed = True
                        aa_text += f"{RED_ALERT} AUTHENTICATION NEEDED, "

                    aa_text += (f"{devices_assigned_cnt} of "
                                f"{len(PyiCloud.icloud_dnames)} iCloud Devices Tracked")

                else:
                    aa_text = f"{username}{RARROW}{RED_ALERT} Not logged into this Apple Account"

            self.apple_acct_items_by_username[username] = aa_text

#-------------------------------------------------------------------------------------------
    def _build_devices_list(self):
        '''
        Rebuild the device list for displaying on the devices list form. This is necessary
        since the parameters displayed may have been changed. Update the default values for
        each page for the device selected on each page.
        '''
        self.device_items_by_devicename = {}

        # Format all the device info to be listed on the form
        for conf_device in Gb.conf_devices:
            conf_device[CONF_IC3_DEVICENAME] = conf_device[CONF_IC3_DEVICENAME].replace(' ', '_')
            self.device_items_by_devicename[conf_device[CONF_IC3_DEVICENAME]] = \
                    self._format_device_list_item(conf_device)

        # No devices in config, reset to initial conditions
        if self.device_items_by_devicename == {}:
            self.conf_device_idx  = 0
            return

#-------------------------------------------------------------------------------------------
    def _format_device_list_item(self, conf_device):
        '''
        Format the text that is displayed for the device on the device_list screen
        '''
        device_text  = (f"{conf_device[CONF_FNAME]}"
                        f" ({conf_device[CONF_IC3_DEVICENAME]}){RARROW}")

        if conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
            device_text += "MONITOR, "
        elif conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
            device_text += "✪ INACTIVE, "

        if conf_device[CONF_FAMSHR_DEVICENAME] != 'None':
            icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
            apple_acct   = conf_device[CONF_APPLE_ACCOUNT]
            device_text += "iCloud > "
            if PyiCloud := Gb.PyiCloud_by_username.get(apple_acct):
                if icloud_dname in PyiCloud.device_id_by_icloud_dname:
                    device_text += f"{icloud_dname}{PyiCloud.account_owner_link}, "
                else:
                    device_text += f"{RED_X}{icloud_dname}{PyiCloud.account_owner_link}"
                    device_text += " (DEVICE NOT IN APPLE ACCT), "
                if PyiCloud.requires_2fa:
                    device_text += f" {YELLOW_ALERT}AUTH NEEDED, "
            elif apple_acct in ['', 'None']:
                device_text += f"{icloud_dname}{LINK}{RED_X}UNKNOWN{RLINK}, "
                #device_text += " (NO APPLE ACCT), "
            else:
                device_text += f"{icloud_dname}{LINK}{RED_X}UNKNOWN-{apple_acct}{RLINK}, "
                #device_text += " (UNKNOWN APPLE ACCT), "

        if conf_device[CONF_MOBILE_APP_DEVICE] != 'None':
            mobapp_dname = conf_device[CONF_MOBILE_APP_DEVICE]
            device_text += "MobApp > "
            if mobapp_dname in Gb.device_info_by_mobapp_dname:
                device_text += f"{Gb.device_info_by_mobapp_dname[mobapp_dname][0]}, "
            else:
                device_text += f"{RED_X}UNKNOWN-{mobapp_dname}, "

        if conf_device[CONF_TRACK_FROM_BASE_ZONE] != HOME:
            tfhbz = conf_device[CONF_TRACK_FROM_BASE_ZONE]
            device_text +=  f"PrimaryHomeZone > {zone_dname(tfhbz)}, "

        if conf_device[CONF_TRACK_FROM_ZONES] != [HOME]:
            tfz_fnames = [zone_dname(z) for z in conf_device[CONF_TRACK_FROM_ZONES]]
            device_text +=  f"TrackFromZones > {list_to_str(tfz_fnames)}, "

        device_text = device_text.replace(' , ', ' ')

        return device_text[:-2]

#----------------------------------------------------------------------
    async def _build_update_device_selection_lists(self, selected_devicename=None):
        '''
        Setup the option lists used to select device parameters

        Parameter:
            selected_device - The iC3 devicename being added or updated on the Update
                Devices screen. This is used to highlight the selected device and
                place it at the top of the finddev device list
        '''

        try:
            await self._build_icloud_device_selection_list(selected_devicename)
            await self._build_mobapp_entity_selection_list(selected_devicename)
            await self._build_picture_filename_selection_list()
            await self._build_zone_selection_list()

            # _xtraceha(f"{self.icloud_list_text_by_fname=}")
            # _xtraceha(f"{self.mobapp_list_text_by_entity_id=}")
            # _xtraceha(f"{self.conf_device=}")
            # _xtraceha(f"{self.zone_name_key_text=}")

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------
    async def _build_icloud_device_selection_list(self, selected_devicename=None):
        '''
        Create the iCloud object if it does not exist. This will create the icloud_info_by_icloud_dname
        that contains the fname and device info dictionary. Then sort this by the lower case fname values
        so the uppercase items (Watch) are not listed before the lower case ones (iPhone).

        This creates the list of devices used on the update devices screen
        '''
        self.icloud_list_text_by_fname_base = NONE_DICT_KEY_TEXT.copy()
        self.icloud_list_text_by_fname2 = NONE_FAMSHR_DICT_KEY_TEXT.copy()
        all_devices_available = {}
        all_devices_used = {}
        all_devices_this_device = {}
        all_devices_unknown_device = {}
        username_hdr_available = {}
        selected_device_icloud_dname = 'None' if is_empty(Gb.conf_devices) else ''

        # Get the list of devices with unknown apple accts
        for conf_device in Gb.conf_devices:
            if conf_device[CONF_FAMSHR_DEVICENAME] == 'None':
                continue

            if Gb.username_valid_by_username.get(conf_device[CONF_APPLE_ACCOUNT], False) is False:
                icloud_dname_username = f".{conf_device[CONF_IC3_DEVICENAME]}{LINK}UNKNOWN"
                self.icloud_list_text_by_fname2[icloud_dname_username] = (
                        f"{RED_X}{conf_device[CONF_FNAME]} ({conf_device[CONF_IC3_DEVICENAME]})"
                        f"{LINK}{conf_device[CONF_APPLE_ACCOUNT]}{RLINK}"
                        f"{RARROW}UNKNOWN APPLE ACCOUNT")

            # Save the FamShr config parameter in case it is not found
            if conf_device[CONF_IC3_DEVICENAME] == selected_devicename:
                selected_device_icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]

        # Get the list of devices with valid apple accounts
        aa_idx = 0
        for apple_acct in Gb.conf_apple_accounts:
            username = apple_acct[CONF_USERNAME]
            aa_idx += 1

            if Gb.username_valid_by_username.get(username, False) is False:
                continue

            PyiCloud = Gb.PyiCloud_by_username.get(username)
            if PyiCloud is None:
                continue

            if PyiCloud.DeviceSvc is None or PyiCloud.is_DeviceSvc_setup_complete is False:
                _AppleDev = await Gb.hass.async_add_executor_job(
                                        self.create_DeviceSvc_config_flow,
                                        PyiCloud)

            if PyiCloud:
                self._check_finish_v2v3conversion_for_icloud_dname()

                devices_available, devices_used, this_device = \
                        self._get_icloud_devices_list_avail_used_this(aa_idx,
                                                            PyiCloud, PyiCloud.account_owner,
                                                            selected_devicename)
                # Available devices
                devices_cnt  = len(devices_used) + len(devices_available) + len(this_device)
                assigned_cnt = len(devices_used) + len(this_device)

                aa_idx_dots = '.'*aa_idx
                username_hdr_available = {f"{aa_idx_dots}hdr":
                    f"🍎 ~~~~ {PyiCloud.account_owner}, "
                    f"Apple Account #{aa_idx} of {len(Gb.conf_apple_accounts)} ~~~~ "
                    f"{assigned_cnt} of {devices_cnt} Tracked ~~~~"}
                if devices_available == {}:
                    devices_available = {f"{aa_idx_dots}nodev":
                    f"⊗ All Apple account devices are assigned"}

                all_devices_available.update(username_hdr_available)
                all_devices_available.update(devices_available)
                all_devices_used.update(devices_used)
                all_devices_this_device.update(this_device)

        if (is_empty(all_devices_this_device)
                and selected_device_icloud_dname != 'None'):
            this_device = {f".{conf_device[CONF_IC3_DEVICENAME]}{LINK}UNKNOWN":
                    f"{RED_X}{conf_device[CONF_FNAME]} ({conf_device[CONF_IC3_DEVICENAME]})"
                    f"{LINK}{conf_device[CONF_APPLE_ACCOUNT]}{RLINK}"
                    f"{RARROW}UNKNOWN APPLE ACCOUNT"}

        self.icloud_list_text_by_fname2.update(all_devices_this_device)
        self.icloud_list_text_by_fname2.update(all_devices_available)
        self.icloud_list_text_by_fname2.update({f".assigned": f"⛔ ~~~~ ASSIGNED TO ICLOUD3 DEVICES ~~~~"})
        self.icloud_list_text_by_fname2.update(sort_dict_by_values(all_devices_used))

        self.icloud_list_text_by_fname = self.icloud_list_text_by_fname2.copy()

#----------------------------------------------------------------------
    def _get_icloud_devices_list_avail_used_this( self, aa_idx, PyiCloud, apple_acct_owner,
                                        selected_devicename=None):
        '''
        Build the dictionary with the Apple Account devices

        Return:
            [devices_available, devices_used, devices_this_device]
        '''
        this_device = {}
        devices_available = {}
        devices_used = {}
        unknown_devices = {}
        famshr_available = {}
        owner_available = {}
        aa_idx_msg  = f"#{aa_idx} - "
        aa_idx_dots = '.'*aa_idx

        devices_assigned = {}
        selected_device_icloud_dname = ''
        for _conf_device in Gb.conf_devices:
            icloud_dname = _conf_device[CONF_FAMSHR_DEVICENAME]
            username     = _conf_device[CONF_APPLE_ACCOUNT]
            if (icloud_dname == 'None'
                    or PyiCloud.username != username):
                continue

            devices_assigned[icloud_dname] = _conf_device[CONF_IC3_DEVICENAME]
            devices_assigned[_conf_device[CONF_IC3_DEVICENAME]] = icloud_dname

            if icloud_dname not in PyiCloud.device_id_by_icloud_dname:
                icloud_dname_username = f"{icloud_dname}{LINK}{username}"
                icloud_dname_owner    = f"{icloud_dname}{LINK}{username}{RLINK}"
                unknown_devices[icloud_dname_username] = (
                                        f"{RED_X}{icloud_dname_owner} >"
                                        f"{RARROW}UNKNOWN DEVICE")

        try:
            for icloud_dname, device_model in PyiCloud.device_model_name_by_icloud_dname.items():
                device_id = PyiCloud.device_id_by_icloud_dname[icloud_dname]
                _RawData  = PyiCloud.RawData_by_device_id[device_id]
                conf_apple_acct, conf_aa_idx = config_file.conf_apple_acct(PyiCloud.username)
                locate_all_sym = '' if conf_apple_acct[CONF_LOCATE_ALL] else 'ⓧ '
                famshr_device = ' (FamShr)' if _RawData.family_share_device else ''
                if famshr_device  and locate_all_sym:
                    famshr_device = ' (FamShr - NOT LOCATING DEVICE)'

                icloud_dname_username = f"{icloud_dname}{LINK}{PyiCloud.username}"
                icloud_dname_owner    = f"{icloud_dname}{LINK}{PyiCloud.account_owner}{RLINK}"
                icloud_dname_owner_model = f"{icloud_dname} > {device_model}{famshr_device}"

                # If not assigned to an ic3 device
                if icloud_dname not in devices_assigned:
                    if famshr_device:
                        famshr_available[icloud_dname_username] = (
                                        f"{locate_all_sym}"
                                        f"{icloud_dname_owner_model}"
                                        f"{aa_idx_dots}")
                    else:
                        owner_available[icloud_dname_username] = (
                                        f"{icloud_dname_owner_model}"
                                        f"{aa_idx_dots}")
                    continue

                # Is the icloud device name assigned to the current device being updated
                devicename = devices_assigned[icloud_dname]
                if devicename == selected_devicename:
                    err = RED_X if instr(icloud_dname_owner_model, 'NOT LOCATING') else ''
                    this_device[icloud_dname_username] = (
                                f"{err}{icloud_dname_owner} > "
                                f"{device_model}{famshr_device}")
                    continue

                # Assigned to another device
                _assigned_to_fname = self._icloud_device_assigned_to(PyiCloud, icloud_dname)
                err = RED_X if instr(icloud_dname_owner_model, 'NOT LOCATING') else ''
                devices_used[icloud_dname_username] = (
                                f"{err}{icloud_dname_owner_model}{RARROW}"
                                f"{_assigned_to_fname}")

        except Exception as err:
            log_exception(err)

        devices_available.update(sort_dict_by_values(unknown_devices))
        devices_available.update(sort_dict_by_values(owner_available))
        devices_available.update(sort_dict_by_values(famshr_available))

        return devices_available, devices_used, this_device

#----------------------------------------------------------------------
    def _icloud_device_assigned_to(self, PyiCloud, icloud_dname):
        _assigned_to_fname = [f"{PyiCloud.account_owner_username})"
                for conf_device in Gb.conf_devices
                if (PyiCloud.username == conf_device[CONF_APPLE_ACCOUNT]
                        and icloud_dname == conf_device[CONF_FAMSHR_DEVICENAME])]

        if _assigned_to_fname:
            return _assigned_to_fname[0]
        else:
            return ''

#----------------------------------------------------------------------
    async def _build_mobapp_entity_selection_list(self, selected_devicename=None):
        '''
        Cycle through the /config/.storage/core.entity_registry file and return
        the entities for platform ('mobile_app', etc)

        Gb.devicenames_by_mobapp_dname={'gary_iphone_app': 'gary_iphone', 'Gary-iPhone-MobApp': 'gary_iphone'}
        Gb.device_info_by_mobapp_dname={'gary_iphone_app': ['Gary-iPhone-MobApp', 'iPhone17,2', 'iPhone', 'iPhone 16 Pro Max'], ...
        mobapp_devices={'gary_iphone_app': 'Gary-iPhone-MobApp (iPhone17,2); device_tracker.gary_iphone_app'}
        '''

        devices_this_device = {}
        devices_available = {}
        devices_used = {}
        scan_for_mobapp_devices = {}
        self.mobapp_list_text_by_entity_id = MOBAPP_DEVICE_NONE_OPTIONS.copy()

        Gb.devicenames_by_mobapp_dname = {}
        Gb.mobapp_dnames_by_devicename = {}
        for _conf_device in Gb.conf_devices:
            if _conf_device[CONF_MOBILE_APP_DEVICE] != 'None':
                Gb.devicenames_by_mobapp_dname[_conf_device[CONF_MOBILE_APP_DEVICE]] =\
                                _conf_device[CONF_IC3_DEVICENAME]
                Gb.mobapp_dnames_by_devicename[_conf_device[CONF_IC3_DEVICENAME]] =\
                                _conf_device[CONF_MOBILE_APP_DEVICE]

        mobapp_devices ={mobapp_dname:(
                            f"{mobapp_info[0]} "
                            f"(device_tracker.{mobapp_dname}) > "
                            f"{mobapp_info[3]}")
                            for mobapp_dname, mobapp_info in Gb.device_info_by_mobapp_dname.items()}

        for mobapp_dname, mobapp_info in mobapp_devices.items():
            if mobapp_dname not in Gb.devicenames_by_mobapp_dname:
                devices_available[mobapp_dname] = mobapp_info
                continue

            if (selected_devicename
                    and mobapp_dname == self.conf_device[CONF_MOBILE_APP_DEVICE]):
                devices_this_device[mobapp_dname] = mobapp_info
                continue

            else:
                devicename = Gb.devicenames_by_mobapp_dname[mobapp_dname]
                Device = Gb.Devices_by_devicename.get(devicename)
                if Device:
                    fname_devicename = Device.fname_devicename
                else:
                    fname_devicename = f"{CIRCLE_STAR}{devicename} (UNKNOWN)"
                
                devices_used[mobapp_dname] = (
                            f"{mobapp_info.split(';')[0]}{RARROW}"
                            f"ASSIGNED TO-{fname_devicename}")

        try:
            scan_for_mobapp_devices = {
                        f"ScanFor: {_conf_device[CONF_IC3_DEVICENAME]}": (
                        f"Starting with > "
                        f"{_conf_device[CONF_IC3_DEVICENAME]} "
                        f"({_conf_device[CONF_FNAME]})")
                            for _conf_device in Gb.conf_devices}

        except:
            scan_for_mobapp_devices = {}

        if (selected_devicename
                and is_empty(devices_this_device)
                and self.conf_device[CONF_MOBILE_APP_DEVICE] != 'None'):
            devices_this_device = {'.unknown':
                    f"{RED_X}{self.conf_device[CONF_MOBILE_APP_DEVICE]}{RARROW}UNKNOWN MOBILE APP DEVICE"}

        self.mobapp_list_text_by_entity_id.update(devices_this_device)
        self.mobapp_list_text_by_entity_id.update({'.available': f"✅ ~~~~ AVAILABLE MOBILE APP DEVICES ~~~~"})
        self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(devices_available))
        self.mobapp_list_text_by_entity_id.update({'.assigned': f"⛔ ~~~~ ASSIGNED MOBILE APP DEVICES ~~~~"})
        self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(devices_used))
        self.mobapp_list_text_by_entity_id.update({'.scanfor': f"🔄 ~~~~ SCAN FOR DEVICE TRACKER ENTITY ~~~~"})
        self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(scan_for_mobapp_devices))

        return

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _mobapp_fname(entity_attrs):
        return entity_attrs['name'] or entity_attrs['original_name']

#-------------------------------------------------------------------------------------------
    async def _build_picture_filename_selection_list(self):

        try:
            if self.picture_by_filename != {}:
                return

            start_dir = 'www'
            file_filter = ['png', 'jpg', 'jpeg']
            image_filenames = await Gb.hass.async_add_executor_job(
                                                    file_io.get_directory_filename_list,
                                                    start_dir,
                                                    file_filter)

            sorted_image_filenames = []
            over_25_warning_msgs = []
            for image_filename in image_filenames:
                if image_filename.startswith('⛔'):
                    over_25_warning_msgs.append(image_filename)
                else:
                    sorted_image_filenames.append(f"{image_filename.rsplit('/', 1)[1]}:{image_filename}")
            sorted_image_filenames.sort()
            self.picture_by_filename = {}
            self.picture_by_filename['www_dirs'] = "Source Directories:"
            www_dir_idx = 0

            if Gb.picture_www_dirs:
                while www_dir_idx < len(Gb.picture_www_dirs):
                    self.picture_by_filename[f"www_dirs{www_dir_idx}"] = \
                                f"{DOT}{list_to_str(Gb.picture_www_dirs[www_dir_idx:www_dir_idx+3])}"
                    www_dir_idx += 3
            else:
                self.picture_by_filename["www_dirs0"] = f"{DOT}All `www/*` directories are scaned"

            for over_25_warning_msg in over_25_warning_msgs:
                www_dir_idx += 1
                self.picture_by_filename[f"www_dirs{www_dir_idx}"] = over_25_warning_msg

            self.picture_by_filename['www_dirs998'] = "Set filter on `Tracking and Other Parameters` screen"
            self.picture_by_filename['www_dirs999'] = f"{'-'*85}"
            self.picture_by_filename.update(self.picture_by_filename_base)

            for sorted_image_filename in sorted_image_filenames:
                image_filename, image_filename_path = sorted_image_filename.split(':')
                self.picture_by_filename[image_filename_path] = \
                            f"{image_filename}{RARROW}{image_filename_path.replace(image_filename, '')}"

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    async def _build_zone_selection_list(self):

        if self.zone_name_key_text != {}:
            return

        fname_zones = []
        for zone, Zone in Gb.HAZones_by_zone.items():
            if is_statzone(zone):
                continue

            passive_msg = ' (Passive)' if Zone.passive else ''
            fname_zones.append(f"{Zone.dname}{passive_msg}|{zone}")

        fname_zones.sort()

        self.zone_name_key_text = {'home': 'Home'}

        for fname_zone in fname_zones:
            fname, zone = fname_zone.split('|')
            self.zone_name_key_text[zone] = fname

#----------------------------------------------------------------------
    async def _build_trusted_devices_list(self):
        '''
        Build a list of the trusted devices for the Apple account
        '''
        try:
            return {}
            _log(f"BUILD BEF TRUSTED DEVICES")
            trusted_devices = await self.hass.async_add_executor_job(
                            getattr, self.PyiCloud, "trusted_devices")
            # trusted_devices = trusted_devices_json.json()
            _log(f"BUILD AFT TRUSTED DEVICES")
            _log(f"{trusted_devices=}")

            trusted_devices_key_text = {}
            for i, device in enumerate(trusted_devices):
                trusted_devices_key_text[i] = self.PyiCloud.device.get(
                    "deviceName", f"SMS to {device.get('phoneNumber')}")

            _log(f"{trusted_devices_key_text=}")

            return trusted_devices_key_text

        except Exception as err:
            log_exception(err)

        return {}

#----------------------------------------------------------------------
    def _check_finish_v2v3conversion_for_icloud_dname(self):
        '''
        This will be done if the v2 files were just converted to the v3 configuration.
        Finish setting up the device by determining the actual iCloud devicename and the
        raw_model, model, model_display_name and device_id fields.
        '''

        if (Gb.conf_profile[CONF_VERSION] == 1
                or self.PyiCloud is None
                or self.PyiCloud.DeviceSvc is None):
            return

        icloud_dnames = [conf_device[CONF_FAMSHR_DEVICENAME]
                                            for conf_device in Gb.conf_devices
                                            if (conf_device[CONF_FAMSHR_DEVICENAME] == \
                                                        conf_device[CONF_IC3_DEVICENAME]
                                                and conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE)]

        if icloud_dnames == []:
            return

        # Build a dictionary of the iCloud fnames to compare to the ic3_devicename {gary_iphone: Gary-iPhone}
        icloud_dname_by_ic3_devicename = {slugify(fname).strip(): fname
                    for fname in self.PyiCloud.device_model_info_by_fname.keys()}

        # Cycle thru conf_devices and see if there are any ic3_devicename = icloud_dname entries.
        # If so, they were just converted and the real icloud_dname needs to be reset to the actual
        # value from the PyiCloud RawData fields
        update_conf_file_flag = False
        for conf_device in Gb.conf_devices:
            icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
            ic3_devicename    = conf_device[CONF_IC3_DEVICENAME]

            if (icloud_dname != ic3_devicename
                    or ic3_devicename not in icloud_dname_by_ic3_devicename):
                continue

            icloud_dname = icloud_dname_by_ic3_devicename[ic3_devicename]

            conf_device[CONF_APPLE_ACCOUNT]     = self.username
            conf_device[CONF_FAMSHR_DEVICENAME] = icloud_dname

            raw_model, model, model_display_name = \
                                self.PyiCloud.device_model_info_by_fname[icloud_dname]

            device_id = self.PyiCloud.device_id_by_icloud_dname[icloud_dname]

            conf_device[CONF_FAMSHR_DEVICE_ID] = device_id
            conf_device[CONF_MODEL] = model
            conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name
            conf_device[CONF_RAW_MODEL] = raw_model
            update_conf_file_flag = True

        if update_conf_file_flag:
            self._update_config_file_tracking()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#      ROUTINES THAT SUPPORT ADD & REMOVE SENSOR AND DEVICE_TRACKER ENTITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _any_errors(self):
        return self.errors != {} and self.errors.get('base') != 'conf_updated'

    def _remove_and_create_sensors(self, user_input):
        """ Remove unchecked sensor entities and create newly checked sensor entities """

        new_sensors_list, remove_sensors_list = \
                self._sensor_form_identify_new_and_removed_sensors(user_input)
        self._remove_sensor_entity(remove_sensors_list)

        for conf_device in Gb.conf_devices:
            devicename  = conf_device[CONF_IC3_DEVICENAME]
            self._create_sensor_entity(devicename, conf_device, new_sensors_list)

#-------------------------------------------------------------------------------------------
    def _create_device_tracker_and_sensor_entities(self, devicename, conf_device):
        """ Create a device and all of it's sensors in the ha entity registry

            Create device_tracker.[devicename] and all sensor.[devicename]_[sensor_name]
            associated with the device.
        """

        if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
            return

        NewDeviceTrackers = []
        DeviceTracker     = None
        ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)
        if devicename in Gb.DeviceTrackers_by_devicename:
            DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
        else:
            DeviceTracker = ic3_device_tracker.iCloud3_DeviceTracker(devicename, conf_device)
            self.update_area_id_personal_device(devicename)

        if DeviceTracker is None:
            return

        ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)
        Gb.DeviceTrackers_by_devicename[devicename] = DeviceTracker
        NewDeviceTrackers.append(DeviceTracker)

        # if devicename not in Gb.ha_device_id_by_devicename:
        #     NewDeviceTrackers.append(DeviceTracker)
        # else:
        #     NewDeviceTrackers.append(DeviceTracker)

        Gb.async_add_entities_device_tracker(NewDeviceTrackers, True)

        sensors_list = self._build_all_sensors_list()
        self._create_sensor_entity(devicename, conf_device, sensors_list)

#-------------------------------------------------------------------------------------------
    def _remove_device_tracker_entity(self, devicename):
        """ Remove a specific device from the ha entity registry

            Remove device_tracker.[devicename] and all sensor.[devicename]_[sensor_name]
            associated with the device.

            devicename:
                devicename to be removed
        """
        # Inactive devices were not created so they are not in Gb.DeviceTrackers_by_devicename
        ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)
        if devicename not in Gb.DeviceTrackers_by_devicename:
            return

        try:
            for sensor, Sensor in Gb.Sensors_by_devicename[devicename].items():
                Sensor.remove_entity()
        except:
            pass

        try:
            for sensor, Sensor in Gb.Sensors_by_devicename_from_zone[devicename].items():
                Sensor.remove_entity()
        except:
            pass

        try:
            DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
            DeviceTracker.remove_device_tracker()
        except:
            pass
        ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)

#-------------------------------------------------------------------------------------------
    def _devices_form_identify_new_and_removed_tfz_zones(self, user_input):
        """ Determine checked/unchecked track_fm_zones """

        new_tfz_zones_list    = []
        remove_tfz_zones_list = []     # base device sensors
        old_tfz_zones_list    = self.conf_device[CONF_TRACK_FROM_ZONES]
        ui_tfz_zones_list     = user_input[CONF_TRACK_FROM_ZONES]

        # Cycle thru the devices tfz zones before the update to get a list of new
        # and removed zones
        for zone in Gb.HAZones_by_zone.keys():
            if zone in ui_tfz_zones_list and zone not in old_tfz_zones_list:
                new_tfz_zones_list.append(zone)
            elif zone in old_tfz_zones_list and zone not in ui_tfz_zones_list:
                remove_tfz_zones_list.append(zone)

        return new_tfz_zones_list, remove_tfz_zones_list

#-------------------------------------------------------------------------------------------
    def remove_track_fm_zone_sensor_entity(self, devicename, remove_tfz_zones_list):
        '''
        Remove the all tfz sensors for all of the just unchecked zones
        This is called when a zone is removed from the tfz list on the Update Devices
        screen and when a tfz zone is deleted from HA and being removed from iCloud3
        in start_ic3 module
        '''

        if remove_tfz_zones_list == []:
            return

        device_tfz_sensors = Gb.Sensors_by_devicename_from_zone.get(devicename)

        if device_tfz_sensors is None:
            return

        # Cycle through the zones that are no longer tracked from for the device, then cycle
        # through the Device's sensor list and remove all track_from_zone sensors ending with
        # that zone.
        for zone in remove_tfz_zones_list:
            for sensor, Sensor in device_tfz_sensors.copy().items():
                if (sensor.endswith(f"_{zone}")
                        and Sensor.entity_removed_flag is False):
                    Sensor.remove_entity()

#-------------------------------------------------------------------------------------------
    def _create_track_fm_zone_sensor_entity(self, devicename, new_tfz_zones_list):
        """ Add tfz sensors for all zones that were just checked

            This must be done after the devices user_input parameters have been updated
        """

        if new_tfz_zones_list == []:
            return

        # Cycle thru each new zone and then cycle thru the track_from_zone sensors
        # Then add that sensor for the zones just checked
        sensors_list = []
        for sensor in Gb.conf_sensors[CONF_TRACK_FROM_ZONES]:
            sensors_list.append(sensor)

        NewZones = ic3_sensor.create_tracked_device_sensors(devicename, self.conf_device, sensors_list)

        if NewZones is not []:
            Gb.async_add_entities_sensor(NewZones, True)

#-------------------------------------------------------------------------------------------
    def _sensor_form_identify_new_and_removed_sensors(self, user_input):
        """ Add newly checked/delete newly unchecked ha sensor entities """

        new_sensors_list    = []
        remove_sensors_list = []     # base device sensors
        if user_input[CONF_EXCLUDED_SENSORS] == []:
            user_input[CONF_EXCLUDED_SENSORS] = ['None']

        for sensor_group, sensor_list in user_input.items():
            if (sensor_group not in Gb.conf_sensors
                    or user_input[sensor_group] == Gb.conf_sensors[sensor_group]
                    or sensor_group == CONF_EXCLUDED_SENSORS):
                if user_input[CONF_EXCLUDED_SENSORS] != Gb.conf_sensors[CONF_EXCLUDED_SENSORS]:
                    list_add(self.config_parms_update_control, ['restart_ha', 'restart'])
                continue

            # Cycle thru the sensors now in the user_input sensor_group
            # Get list of sensors to be added
            for sensor in sensor_list:
                if sensor not in Gb.conf_sensors[sensor_group]:
                    if sensor == 'last_zone':
                        if 'zone'       in Gb.conf_sensors[sensor_group]: new_sensors_list.append('last_zone')
                        if 'zone_name'  in Gb.conf_sensors[sensor_group]: new_sensors_list.append('last_zone_name')
                        if 'zone_fname' in Gb.conf_sensors[sensor_group]: new_sensors_list.append('last_zone_fname')
                    else:
                        new_sensors_list.append(sensor)

            # Get list of sensors to be removed
            for sensor in Gb.conf_sensors[sensor_group]:
                if sensor not in sensor_list:
                    if sensor == 'last_zone':
                        if 'zone'       in sensor_list: remove_sensors_list.append('last_zone')
                        if 'zone_name'  in sensor_list: remove_sensors_list.append('last_zone_name')
                        if 'zone_fname' in sensor_list: remove_sensors_list.append('last_zone_fname')
                    else:
                        remove_sensors_list.append(sensor)

        return new_sensors_list, remove_sensors_list

#-------------------------------------------------------------------------------------------
    def _remove_sensor_entity(self, remove_sensors_list, select_devicename=None):
        """ Delete sensors from the ha entity registry and ic3 dictionaries

            remove_sensors_list:
                    list of the sensors to be deleted
            selected_devicename:
                    specified       - only delete this devicename's sensors
                    not_specified   - delete the sensors in the remove_sensors_list from all devices
        """

        if remove_sensors_list == []:
            return

        # Remove regular sensors
        device_tracking_mode = {k['ic3_devicename']: k['tracking_mode'] for k in Gb.conf_devices}
        for devicename, devicename_sensors in Gb.Sensors_by_devicename.items():
            if (devicename not in device_tracking_mode
                    or select_devicename and select_devicename != devicename):
                continue

            # Select normal/monitored sensors from the remove_sensors_list for this device
            if device_tracking_mode[devicename] == 'track':      #Device.is_tracked:
                sensors_list = [k for k in remove_sensors_list if k.startswith('md_') is False]
            elif device_tracking_mode[devicename] == 'monitor':      #Device.is_monitored:
                sensors_list = [k for k in remove_sensors_list if k.startswith('md_') is True]
            else:
                sensors_list = []

            # The sensor group is a group of sensors combined under one conf_sensor item
            # Build sensors to be removed from the the sensor or the sensor's group
            device_sensors_list = []
            for sensor in sensors_list:
                if sensor in SENSOR_GROUPS:
                    device_sensors_list.extend(SENSOR_GROUPS[sensor])
                else:
                    device_sensors_list.append(sensor)

            Sensors_list = [v for k, v in devicename_sensors.items() if k in device_sensors_list]
            for Sensor in Sensors_list:
                if Sensor.entity_removed_flag is False:
                    Sensor.remove_entity()

        # Remove track_fm_zone sensors
        device_track_from_zones = {k['ic3_devicename']: k['track_from_zones'] for k in Gb.conf_devices}
        for devicename, devicename_sensors in Gb.Sensors_by_devicename_from_zone.items():
            if (devicename not in device_track_from_zones
                    or select_devicename and select_devicename != devicename):
                continue

            # Create tfz removal list, tfz_sensor --> sensor_zone
            tfz_sensors_list = [f"{k.replace('tfz_', '')}_{z}"
                                            for k in remove_sensors_list if k.startswith('tfz_')
                                            for z in device_track_from_zones[devicename]]

            Sensors_list = [v for k, v in devicename_sensors.items() if k in tfz_sensors_list]
            for Sensor in Sensors_list:
                if Sensor.entity_removed_flag is False:
                    Sensor.remove_entity()

#-------------------------------------------------------------------------------------------
    def _create_sensor_entity(self, devicename, conf_device, new_sensors_list):
        """ Add sensors that were just checked """

        if new_sensors_list == []:
            return

        if conf_device[CONF_TRACKING_MODE] == TRACK_DEVICE:
            sensors_list = [v for v in new_sensors_list if v.startswith('md_') is False]
            NewSensors = ic3_sensor.create_tracked_device_sensors(devicename, conf_device, sensors_list)

        elif conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
            sensors_list = [v for v in new_sensors_list if v.startswith('md_') is True]
            NewSensors = ic3_sensor.create_monitored_device_sensors(devicename, conf_device, sensors_list)
        else:
            return

        Gb.async_add_entities_sensor(NewSensors, True)

#-------------------------------------------------------------------------------------------
    def _build_all_sensors_list(self):
        """ Get a list of all sensors from the ic3 config file  """

        sensors_list = []
        for sensor_group, sensor_list in Gb.conf_sensors.items():
            if sensor_group == CONF_EXCLUDED_SENSORS:
                continue

            for sensor in Gb.conf_sensors[sensor_group]:
                sensors_list.append(sensor)

        return sensors_list

#-------------------------------------------------------------------------------------------
    def update_area_id_personal_device(self, devicename):
        '''
        Change the device's area to Personal Device
        '''

        try:
            kwargs = {}
            kwargs['area_id'] = Gb.area_id_personal_device
            Gb.ha_area_id_by_devicename[devicename] = Gb.area_id_personal_device

            ha_device_id = Gb.ha_device_id_by_devicename[devicename]
            device_registry = dr.async_get(Gb.hass)
            dr_entry = device_registry.async_update_device(ha_device_id, **kwargs)

            log_debug_msg(  "Device Tracker entity changed: device_tracker.icloud3, "
                            "iCloud3, Personal Device")
        except:
            pass

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                      MISCELLANEOUS SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _menu_text_to_item(self, user_input, selection_list):
        '''
        Convert the text of the menu item selected to it's key name.

        selection_list - Field name in user_input to use:
            ''menu_item' 'menu_action_item'
        '''

        if user_input is None:
            return None, None

        selected_text = None
        if selection_list in user_input:
            selected_text = user_input[selection_list]
            selected_text_len = 35 if len(selected_text) > 35 else len(selected_text)
            menu_item = [k for k, v in MENU_KEY_TEXT.items() if v.startswith(selected_text[:selected_text_len])][0]

            user_input.pop(selection_list)
        else:
            menu_item = self.menu_item_selected

        return user_input, menu_item

#--------------------------------------------------------------------
    def _set_header_msg(self):
        '''
        See if any header messages need to be displayed. If so set the self.errors['base']
        '''
        if self.header_msg:
            if self.errors is None: self.errors = {}
            self.errors['base'] = self.header_msg
            self.header_msg = None

#--------------------------------------------------------------------
    def _strip_spaces(self, user_input, parm_list=[]):
        '''
        Remove leading or trailing spaces from items in the parameter list

        '''
        parm_list = [pname  for pname, pvalue in user_input.items()
                                if type(pvalue) is str and pvalue != '']

        for parm in parm_list:
            user_input[parm] = user_input[parm].strip()

        return user_input

#--------------------------------------------------------------------
    def _action_text_to_item(self, user_input):
        '''
        Convert the text of the item selected to it's key name.
        '''

        if user_input is None:
            return None, None

        action_text = None
        if 'action_item' in user_input:
            action_item = user_input['action_item']
            user_input.pop('action_item')

        elif 'action_items' in user_input:
            action_text = user_input['action_items']

            if action_text.startswith('NEXT PAGE ITEMS'):
                action_item = 'next_page_items'
            else:
                action_text_len = len(action_text)
                action_item = [k    for k, v in ACTION_LIST_OPTIONS.items()
                                    if v.startswith(action_text[:action_text_len])][0]
            if 'action_items' in user_input:
                user_input.pop('action_items')

        else:
            action_item = None

        if action_item == 'cancel':
            self.header_msg = None

        return user_input, action_item

#-------------------------------------------------------------------------------------------
    def _parm_or_error_msg(self, pname, conf_group=CF_GENERAL, conf_dict_variable=None):
        '''
        Determine the value that should be displayed in the config_flow parameter entry screen based
        on whether it was entered incorrectly and has an error message.

        Input:
            conf_group
        Return:
            Value in errors if it is in errors
            Value in Gb.conf_general[CONF_pname] if it is valid
        '''
        # pname is in the 'Profile' data fields
        # Example: [profile][version
        if conf_group == CF_PROFILE:
            return self.errors_user_input.get(pname) or Gb.conf_profile[pname]

        # pname is in the 'Tracking' data fields
        # Example: [data][general][tracking][username]
        # Example: [data][general][tracking][devices]
        elif conf_group == CF_TRACKING:
            return self.errors_user_input.get(pname) or Gb.conf_tracking[pname]

        # pname is in a dictionary variable in the 'General Data' data fields grupo. It is a dictionary variable.
        # Example: [data][general][inzone_intervals][phone]
        elif conf_dict_variable is not None:
            pvalue = self.errors_user_input.get(pname) or Gb.conf_data[conf_group][conf_dict_variable][pname]

        # pname is in a dictionary variable in the 'General Data' data fields group. It is a non-dictionary variable.
        # Example: [data][general][unit_of_measurement]
        else:
            pvalue = self.errors_user_input.get(pname) or Gb.conf_data[conf_group][pname]
            if pname in CONF_PARAMETER_FLOAT:
                pvalue = str(pvalue).replace('.0', '')

        return pvalue

#-------------------------------------------------------------------------------------------
    def _parm_or_device(self, pname, suggested_value=''):
        '''
        Get the default value from the various dictionaries to display on the input form
        '''
        try:
            parm_displayed = self.errors_user_input.get(pname) \
                                or self.multi_form_user_input.get(pname) \
                                or self.conf_device.get(pname) \
                                or suggested_value

            if pname == 'device_type':
                parm_displayed = DEVICE_TYPE_FNAME(parm_displayed)
            parm_displayed = ' ' if parm_displayed == '' else parm_displayed

        except Exception as err:
            log_exception(err)

        return parm_displayed

#-------------------------------------------------------------------------------------------
    def _option_parm_to_text(self, pname, option_list_key_text, conf_device=False):
        '''
        Returns the full text string displayed in the config_flow options list for the parameter
        value in the configuration parameter file for the parameter name.

        pname - The name of the config parameter
        option_list_key_text - The option list displayed
        conf_device - Resolves device & general with same parameter name

        Example:
            pname = unit_of_measure field in conf record = 'mi'
            um_key_text = {'mi': 'miles', 'km': 'kilometers'}
        Return:
            'miles'
        '''

        try:

            if pname in self.errors_user_input:
                return option_list_key_text[self.errors_user_input[pname]]

            pvalue_key = pname
            if pname in Gb.conf_profile:
                pvalue_key = Gb.conf_profile[pname]

            elif pname in Gb.conf_tracking:
                pvalue_key = Gb.conf_tracking[pname]

            elif pname in Gb.conf_general and pname in self.conf_device:
                if conf_device:
                    pvalue_key = self.conf_device[pname]
                else:
                    pvalue_key = Gb.conf_general[pname]

            elif pname in self.conf_device:
                pvalue_key = self.conf_device[pname]

            else:
                pvalue_key = Gb.conf_general[pname]

            if type(pvalue_key) in [float, int, str]:
                return option_list_key_text[pvalue_key]

            elif type(pvalue_key) is list:
                return [option_list_key_text[pvalue_key_item] for pvalue_key_item in pvalue_key]

            return option_list_key_text.values()[0]

        except Exception as err:
            log_exception(err)
            # If the parameter value is already the key to the items dict, it is ok.
            if pvalue_key not in option_list_key_text:
                if pname == CONF_FAMSHR_DEVICENAME:
                    self.errors[pname] = 'unknown_icloud'
                elif pname == CONF_MOBILE_APP_DEVICE:
                    self.errors[pname] = 'unknown_mobapp'
                else:
                    self.errors[pname] = 'unknown_value'

            return f"{pvalue_key} {DATA_ENTRY_ALERT}Unknown Selection"

#-------------------------------------------------------------------------------------------
    def key_text_to_text_list(self, key_text):
        return [text for text in key_text.values()]

#-------------------------------------------------------------------------------------------
    def _option_text_to_parm(self, user_input, pname, option_list_key_text):
        '''
        user_input contains the full text of the option list item selected. Replace it with
        the actual parameter value for the item selected.
        '''
        try:
            pvalue_text = '_'
            if user_input is None:
                return None
            if pname not in user_input:
                return user_input

            pvalue_text = user_input[pname]

            # Handle special text added to the end of the key_list
            pvalue_text = pvalue_text.replace(UNKNOWN_DEVICE_TEXT, '')

            if pvalue_text in ['', '.']:
                self.errors[pname] = 'required_field'

            pvalue_key = [k for  k, v in option_list_key_text.items() if v == pvalue_text]
            pvalue_key = pvalue_key[0] if pvalue_key else pvalue_text

            user_input[pname] = pvalue_key

        except:
            # If the parameter value is already the key to the items dict, it is ok.
            if pvalue_text not in option_list_key_text:
                self.errors[pname] = 'invalid_value'

        return  user_input

#-------------------------------------------------------------------------------------------
    def _convert_field_str_to_numeric(self, user_input):
        '''
        Config_flow chokes with malformed input errors when a field is numeric. To avoid this,
        the field's default value is always a string. This converts it back to a float.
        '''
        for pname, pvalue in user_input.items():
            if pname in CONF_PARAMETER_FLOAT:
                user_input[pname] = float(pvalue)

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_numeric_field(self, user_input):
        '''
        Cycle through the user_input fields and, if numeric, validate it
        '''
        for pname, pvalue in user_input.items():
            if pname not in CONF_PARAMETER_FLOAT:
                continue

            if isnumber(pvalue) is False:
                pvalue = pvalue.strip()
                if pvalue == '':
                    self.errors[pname] = "required_field"
                else:
                    self.errors[pname] = "not_numeric"

            if pname in self.errors:
                self.errors_user_input[pname] = pvalue

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_time_str(self, user_input):
        '''
        Cycle through the each of the parameters. If it is a time string, check it's
        value and sec/min/hrs entry
        '''
        new_user_input = {}

        for pname, pvalue in user_input.items():
            if pname in CONF_PARAMETER_TIME_STR:
                time_parts  = (f"{pvalue} mins").split(' ')

                if time_parts[0].strip() == '':
                    self.errors[pname] = "required_field"
                    self.errors_user_input[pname] = ''
                    continue
                elif isnumber(str(time_parts[0])) is False:
                    self.errors[pname] = "not_numeric"
                    self.errors_user_input[pname] = user_input[pname]
                    continue

                if instr(time_parts[1], 'm'):
                    pvalue = f"{time_parts[0]} mins"
                elif instr(time_parts[1], 'h'):
                    pvalue = f"{time_parts[0]} hrs"
                elif instr(time_parts[1], 's'):
                    pvalue = f"{time_parts[0]} secs"
                else:
                    pvalue = f"{time_parts[0]} mins"

                if not self.errors.get(pname):
                    try:
                        if float(time_parts[0]) == 1:
                            pvalue = pvalue.replace('s', '')
                        new_user_input[pname] = pvalue

                    except ValueError:
                        self.errors[pname] = "not_numeric"
                        self.errors_user_input[pname] = user_input[pname]

            else:
                new_user_input[pname] = pvalue

        return new_user_input

#-------------------------------------------------------------------------------------------
    def _parm_with_example_text(self, config_parameter, input_select_list_KEY_TEXT):
        '''
        The input_select_list for the parameter has an example text '(Example: exampletext)'
        as part of list of options display for user selection. The exampletext is not part
        of the configuration parameter. Dydle through the input_select_list and determine which
        one should be the default value.

        Return:
            default - The input_select item to be used for the default value
        '''
        for isli_with_example in input_select_list_KEY_TEXT:
            if isli_with_example.startswith(Gb.conf_general[config_parameter]):
                return isli_with_example

        return input_select_list_KEY_TEXT[0]

#--------------------------------------------------------------------
    def _extract_name_device_type(self, devicename):
        '''
        Extract the name and device type from the devicename
        '''

        try:
            fname       = devicename.lower()
            device_type = ""
            for ic3dev_type in DEVICE_TYPES:
                if devicename == ic3dev_type:
                    return (devicename, devicename)

                elif instr(devicename, ic3dev_type):
                    fnamew = devicename.replace(ic3dev_type, "")
                    fname  = fnamew.replace("_", "").replace("-", "").title().strip()
                    device_type = DEVICE_TYPE_FNAME(ic3dev_type)
                    break

            if device_type == "":
                fname  = fname.replace("_", "").replace("-", "").title().strip()
                device_type = IPHONE_FNAME

        except Exception as err:
            log_exception(err)

        return (fname, device_type)

#--------------------------------------------------------------------
    def action_default_text(self, action_item, action_OPTIONS=None):
        if action_OPTIONS:
            return action_OPTIONS.get(action_item, 'UNKNOWN ACTION > Unknown Action')
        else:
            return ACTION_LIST_OPTIONS.get(action_item, 'UNKNOWN ACTION - Unknown Action')

#--------------------------------------------------------------------
    def _discard_changes(self, user_input):
        '''
        See if user_input 'action_item' item has a 'discard_change' option
        selected. Discard changes is the last item in the list.
        '''
        if user_input:
            return (user_input.get('action_item') == self.action_default_text('cancel'))
        else:
            return False

#--------------------------------------------------------------------
    def log_step_info(self, user_input, action_item=None):

        log_info_msg(  f"{self.step_id.upper()} ({action_item}) > "
                        f"UserInput-{user_input}, Errors-{self.errors}")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                        FORM SCHEMA DEFINITIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def form_schema(self, step_id, actions_list=None, actions_list_default=None):
        '''
        Return the step_id form schema for the data entry forms
        '''
        log_debug_msg(f"Show Form-{step_id}, Errors-{self.errors}")
        schema = {}
        self.actions_list = actions_list or ACTION_LIST_ITEMS_BASE.copy()

        if step_id in ['menu', 'menu_0', 'menu_1']:
            return form_menu(self)
        elif step_id == 'data_source':
            return form_data_source(self)
        elif step_id == 'update_apple_acct':
            return form_update_apple_acct(self)
        elif step_id == 'reauth':
            return form_reauth(self)
        else:
            return {}
