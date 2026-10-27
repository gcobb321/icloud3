

from ...global_variables    import GlobalVariables as Gb
from ...const_config        import (CONF_APPLE_ACCT, CONF_PASSWORD, CONF_VERSION, CONF_LOG_LEVEL,
                                    CONF_APPLE_ACCOUNTS, CONF_DEVICES, CONF_PARAMETER_FLOAT,
                                    CF_GENERAL, )
from ...utils.utils         import (isnot_empty, list_add, encode_password, decode_password, )
from ...utils.messaging     import (log_exception, post_event, )

from ...startup             import config_file
from ...startup             import start_ic3

from .                      import form_config_flow as forms
from ..                     import utils_cf


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   COMMON STEPS AND SUPPORT FUNCTIONS
#
#   Used by every step_... module. Any flow handler that uses one of the step_...
#   classes (the OptionsFlow and the Repairs flows) must also inherit this class
#   and call initialize_common_variables before a step is run.
#
#       - initialize_common_variables
#       - async_step_confirm_action
#       - async_write_icloud3_configuration_file
#       - update_config_file
#       - _update_config_file_general
#       - update_config_file_tracking
#       - initialize_step
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OptionsFlow_Common_Steps:

    def initialize_common_variables(self):
        '''
        Initialize the variables shared by all of the step_... and form_... modules.
        The flow handler calls this before the step_... initialize_xxx_variables.
        '''
        self.errors                         = {}    # Errors en.json error key
        self.multi_form_user_input          = {}    # multi-form - user_input to be restored when returning to calling form
        self.errors_user_input              = {}    # user_input text for a value with an error
        self.errors_info_msg                = None  # dict that maps to a en.json msg for a 'description_placeholders' in the show_form stmt
        self.step_id                        = ''    # step_id for the window displayed
        self.menu_item                      = ''
        self.is_repair_flow                 = False # The screen was opened from HA Repairs (repairs.py)
        self.header_msg                     = None  # Message displayed on menu after update

        self.actions_list                   = []    # Actions list at the bottom of the screen
        self.actions_list_default           = ''    # Default action_items to reassign on screen redisplay
        self.config_parms_update_control    = []    # Stores the type of parameters that were updated, used to reinitialize parms
        self.config_file_commit_updates     = False # The config file has been updated and needs to be written

        # The step displaying the Confirm Action screen sets all of the fields,
        # including the return_to_func_async step
        self.confirm_action                 = {
            'action_desc':          'Confirm Action',
            'yes_func':             None,
            'yes_func_async':       None,
            'return_to_func_async': None,
            'return_to_next_yes_func_async': None}

        self.create_device_tracker_sensor_enities_on_exit = False
        self.rebuild_ic3db_dashboards       = False    # Set when a devices is added or deleted. Used to update the Dashboards

        self.conf_apple_acct                = {}       # apple acct item selected
        self.aa_idx                         = 0
        self.is_reauth_needed               = False


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
        # The apple_id/password may be in the user_input from the update_data_sources form
        # or it's subforms. If so, make sure it is set the the primary apple_id/password
        force_config_update = False if force_config_update is None else True
        was_config_fle_changed = False

        if CONF_APPLE_ACCT in user_input:
            conf_apple_acct, _idx = config_file.conf_apple_acct(0)
            conf_apple_id = conf_apple_acct[CONF_APPLE_ACCT]
            conf_password = conf_apple_acct[CONF_PASSWORD]
            user_input[CONF_APPLE_ACCT] = conf_apple_id
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

        # The apple_id/password may be in the user_input from the update_data_sources form
        # or it's subforms. If so, make sure it is set the the primary apple_id/password
        if CONF_APPLE_ACCT in user_input:
            conf_apple_acct, _idx = config_file.conf_apple_acct(0)
            conf_apple_id_0 = conf_apple_acct[CONF_APPLE_ACCT]
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
            Gb.conf_tracking[CONF_APPLE_ACCOUNTS] = Gb.conf_apple_accounts
            Gb.conf_tracking[CONF_DEVICES]        = Gb.conf_devices
            list_add(self.config_parms_update_control, ['tracking', 'restart'])
            self.config_file_commit_updates = True


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
