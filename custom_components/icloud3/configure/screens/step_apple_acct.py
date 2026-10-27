from ...global_variables    import GlobalVariables as Gb
from ...const               import (ICLOUD, MOBAPP, NO_MOBAPP,
                                    INACTIVE, )
from ...const_config        import (PUSH, TEXT, TEXT_1, TEXT_2, HWKEY, CONF_APPLE_ACCT,
                                    CONF_IC3_DEVICENAME, CONF_FNAME, CONF_APPLE_ACCT, CONF_PASSWORD,
                                    CONF_AADEV_NAME, CONF_DATA_SOURCE, CONF_LOCATE_ALL,
                                    CONF_SERVER_LOCATION, CONF_SERVER_LOCATION_NEEDED,
                                    CONF_TRACKING_MODE, DEFAULT_APPLE_ACCOUNT_CONF,
                                    DEFAULT_DEVICE_CONF, )
from ...utils.utils         import (instr, is_empty, isnot_empty, list_to_str, list_add,
                                    encode_password, decode_password, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,
                                    add_log_file_filter,)

from ...startup             import config_file
from ...apple_acct          import apple_acct_support_cf as aascf
from ...apple_acct          import apple_acct_support as aas
from ...apple_acct.apple_acct_upw import ValidateAppleAcctUPW

from ..const_form_lists     import *

from .                      import form_apple_acct as forms
#from .                      import form_icloud3_device as forms_ic3dev
from ..                     import sensors_cf
from ..                     import utils_cf
from ..                     import selection_lists as lists

import copy

# Apple's SRP answer when it rejects the apple_id/password (401-wrong password,
# 403-unknown apple_id or locked acct). A 503 is a throttle and does not invalidate it.
APPLE_REJECTED_UPW_CODES = [401, 403]

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           ICLOUD3 APPLE ACCOUNT CONFIG FLOW STEPS
#
#           - async_step_apple_accounts
#           - ACTION_LIST_OPTIONS['apple_accounts'],
#           - async_step_delete_apple_acct
#           - async_step_other_apple_acct_parameters
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OptionsFlow_AppleAccount_Steps:

    def initialize_apple_acct_variables(self):
        '''
        Initialize the variables used by the Apple Account screens. Called from the
        flow handler's initialize_options (the mixin's __init__ would never be run).
        '''
        self.apple_acct_items_list      = []  # List of the apple_accts in the Gb.conf_tracking[apple_accts] parameter
        self.apple_acct_items_displayed = []  # List of the apple_accts displayed on the device_list form
        self.aa_page_item               = ['', '', '', '', '']  # Apple acct apple_id last displayed on each page
        self.aa_page_no                 = 0   # apple_accts List form page number, starting with 0
        self.add_apple_acct_flag        = False
        self.apple_id                   = ''
        self.password                   = ''

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              APPLE ACCOUNTS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_apple_accounts(self, user_input=None, errors=None):
        '''
        Updata Data Sources form enables/disables finddev and mobile app data sources and
        adds/updates/removes an Apple account using the Update Username/Password screen
        '''
        self.step_id = 'apple_accounts'
        self.errors = errors or utils_cf.set_header_msg(self) or {}
        self.errors_user_input = {}
        self.multi_form_user_input = {}
        await self.async_write_icloud3_configuration_file()

        self.add_apple_acct_flag = False
        self.actions_list_default = ''
        action_item = ''

        if Gb.internet_error:
            self.errors['base'] = 'internet_error'

        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        # No Apple Accts, default to Add, this will transfer to update_apple-acct below
        if self._is_apple_acct_setup() is False:
            # self.errors['apple_accts'] = 'apple_acct_not_set_up'
            user_input = {'apple_accts': '➤ ADD'}

        elif isnot_empty(Gb.conf_apple_accounts):
            self._enable_data_source_ICLOUD()

        if user_input is None:
            self.actions_list_default = 'update_apple_acct'
            return self.async_show_form(step_id='apple_accounts',
                                        data_schema=forms.form_apple_accounts(self),
                                        errors=self.errors)

        self._enable_data_source_ICLOUD()
        utils_cf.log_step_info(self, user_input, action_item)

        #.......................................................................
        match action_item:
            case 'menu':
                self._initialize_self_AppleAcct_fields_from_Gb()
                return await self.async_step_menu()

            case 'import_apple_devices':
                return await self.async_step_import_apple_devices()

        #.......................................................................
        # Set add or display next page now since they are not in apple_acct_items_by_idx
        if user_input['apple_accts'].startswith('➤ ADD'):
            self.add_apple_acct_flag = True
            action_item = 'update_apple_acct'
            self.conf_apple_acct = DEFAULT_APPLE_ACCOUNT_CONF.copy()
            return await self.async_step_update_apple_acct(user_input=None)

        if user_input['apple_accts'].startswith('➤ OTHER'):
            self.aa_page_no += 1
            if self.aa_page_no > int(len(self.apple_acct_items_list)/5):
                self.aa_page_no = 0
            return await self.async_step_apple_accounts()

        # Display the Confirm Actions form which will execute the remove_apple.. function
        user_input = utils_cf.option_text_to_parm(user_input,
                                'apple_accts', self.apple_acct_items_by_apple_id)

        ui_apple_id = user_input['apple_accts']
        self.conf_apple_acct, self.aa_idx = config_file.conf_apple_acct(ui_apple_id)

        utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'other_apple_acct_parameters':
            return await self.async_step_other_apple_acct_parameters(user_input)

        if action_item == 'delete_apple_acct':
            # Drop the tracked/untracked part from the current heading (user_input['account_selected'])
            # Ex: account_selected = 'GaryCobb (gcobb321) -> 4 of 7 iCloud Devices Tracked, Tracked-(Gary-iPad ..'
            confirm_action_form_hdr = ( f"Delete Apple Account - {user_input['apple_accts']}")
            if self.AppleAcct:
                confirm_action_form_hdr += f", Devices-{list_to_str(self.AppleAcct.aadevice_dnames)}"
            self.multi_form_user_input = user_input.copy()

            return await self.async_step_delete_apple_acct(user_input=user_input)

        if self.aa_idx < 0:
            conf_apple_acct_apple_ids = [apple_acct[CONF_APPLE_ACCT]
                                        for apple_acct in Gb.conf_apple_accounts]
            log_info_msg(   f"Error > {ui_apple_id}, Username not found in Apple accts device list, "
                            f"Valid Accts-{list_to_str(conf_apple_acct_apple_ids)}")


        # if (self.apple_id != user_input.get('apple_accts', self.apple_id)
        #         and action_item == 'save'):
        #     action_item = 'update_apple_acct'

        self.apple_id = self.conf_apple_acct[CONF_APPLE_ACCT]
        self.password = self.conf_apple_acct[CONF_PASSWORD]
        self.AppleAcct = Gb.AppleAcct_by_apple_id.get(self.apple_id)

        if Gb.is_log_level_debug:
            log_user_input = user_input.copy()
            utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'update_apple_acct':
            self.aa_page_item[self.aa_page_no] = self.conf_apple_acct[CONF_APPLE_ACCT]
            return await self.async_step_update_apple_acct()

        # An Apple Acct can only be authenticated if it is valid and logged into
        if action_item == 'authenticate_apple_acct':
            if aascf.is_apple_acct_logged_into(self.apple_id):
                return await self.async_step_reauth(reauth_apple_id=self.apple_id)
            self.errors['apple_accts'] = 'apple_acct_not_logged_into'

        if self.errors == {}:
            if action_item == 'add_change_apple_acct':
                return await self.async_step_menu()

        self.step_id = 'apple_accounts'
        return self.async_show_form(step_id='apple_accounts',
                            data_schema=forms.form_apple_accounts(self),
                            errors=self.errors)

#...........................................................
    def _enable_data_source_ICLOUD(self, disable=False):

        enable = not disable

        if enable and instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD):
            return

        if enable:
            Gb.primary_data_source = ICLOUD
            Gb.conf_tracking[CONF_DATA_SOURCE] = f"{ICLOUD},{Gb.conf_tracking[CONF_DATA_SOURCE]}"
        else:
            Gb.primary_data_source = MOBAPP
            Gb.conf_tracking[CONF_DATA_SOURCE] = MOBAPP

        Gb.conf_data_source_ICLOUD = enable
        Gb.used_data_source_ICLOUD = enable
        Gb.use_data_source_ICLOUD  = enable
        self.data_source = Gb.conf_tracking[CONF_DATA_SOURCE]

        return

#...........................................................
    def _is_apple_acct_setup(self):

        if self.apple_id:
            return True
        elif is_empty(Gb.conf_apple_accounts):
            return False
        elif Gb.conf_apple_accounts[0].get(CONF_APPLE_ACCT, '') == '':
            return False

        return True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE APPLE ACCT (USERNAME PASSWORD)
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_update_apple_acct(self, user_input=None, errors=None):
        self.step_id = 'update_apple_acct'
        self.errors = errors or utils_cf.set_header_msg(self) or {}
        self.multi_form_user_input = {}
        self.errors_user_input = user_input or {}
        self.actions_list_default = ''
        action_item = ''
        await self.async_write_icloud3_configuration_file()

        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        utils_cf.log_step_info(self, user_input, action_item)

        #.......................................................................
        match action_item:
            case 'menu':
                self._enable_data_source_ICLOUD(disable=True)
                await self.async_write_icloud3_configuration_file(force_write=True)
                return await self.async_step_menu()

            # exit_repair - Opened from HA Repairs, async_step_apple_accounts ends the repair
            case 'cancel_goto_previous' | 'rtn_apple_accounts' | 'exit_repair':
                self.apple_id = self.conf_apple_acct[CONF_APPLE_ACCT]
                self.password = decode_password(self.conf_apple_acct[CONF_PASSWORD])
                self.AppleAcct = Gb.AppleAcct_by_apple_id.get(self.apple_id)
                return await self.async_step_apple_accounts(user_input=None)

            case 'stop_login_retry':
                AppleAcct = Gb.AppleAcct_by_apple_id.get(self.apple_id)
                if AppleAcct:
                    AppleAcct.error_retry_cnt = 0
                    AppleAcct.error_next_retry_secs = 0
                user_input = None
                post_alert(f"Apple Acct > {AppleAcct.apple_user}, Retry Login Canceled")
                self.errors['base'] = 'conf_updated'
                return await self.async_step_update_apple_acct(
                                                user_input=user_input, errors=self.errors)

        #.......................................................................
        if (user_input is None
                or Gb.internet_error):
            return self._show_update_apple_acct_form()

        user_input = utils_cf.option_text_to_parm(user_input,
                                'account_selected', self.apple_acct_items_by_apple_id)
        user_input = utils_cf.strip_spaces(user_input, [CONF_APPLE_ACCT, CONF_PASSWORD])
        if CONF_SERVER_LOCATION in user_input:
            user_input = utils_cf.option_text_to_parm(user_input,
                                    CONF_SERVER_LOCATION, APPLE_SERVER_LOCATION_OPTIONS)
        else:
            user_input[CONF_SERVER_LOCATION] = 'usa'

        if action_item == 'other_apple_acct_parameters':
            return await self.async_step_other_apple_acct_parameters(user_input)

        if (user_input[CONF_LOCATE_ALL] is False
                and self._can_disable_locate_all(user_input) is False):
            self.errors[CONF_LOCATE_ALL] = 'apple_acct_locate_all_reqd'
            user_input[CONF_LOCATE_ALL] = True
            return self._show_update_apple_acct_form(user_input)

        user_input[CONF_APPLE_ACCT] = user_input[CONF_APPLE_ACCT].lower()
        ui_apple_id = user_input[CONF_APPLE_ACCT]
        ui_password = user_input[CONF_PASSWORD]

        conf_apple_id   = self.conf_apple_acct[CONF_APPLE_ACCT]
        conf_password   = decode_password(self.conf_apple_acct[CONF_PASSWORD])
        conf_locate_all = self.conf_apple_acct[CONF_LOCATE_ALL]

        add_log_file_filter(ui_apple_id, f"**{self.aa_idx}**")
        add_log_file_filter(ui_apple_id.upper(), f"**{self.aa_idx}**")
        add_log_file_filter(ui_password)

        if Gb.is_log_level_debug:
            log_user_input = user_input.copy()
            utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'save_log_into_apple_acct':
            if ui_apple_id == '':
                self.errors[CONF_APPLE_ACCT] = 'required_field'
                action_item = ''

            # Not an email address or phone number, Apple would reject it
            elif self._is_valid_apple_id_format(ui_apple_id) is False:
                self.errors[CONF_APPLE_ACCT] = 'apple_acct_invalid_format'
                action_item = ''

            # Adding an Apple Account but it already exists
            elif (self.add_apple_acct_flag
                    and ui_apple_id in Gb.AppleAcct_by_apple_id):
                self.errors[CONF_APPLE_ACCT] = 'apple_acct_dup_apple_id_error'
                action_item = ''

            if ui_password == '':
                self.errors[CONF_PASSWORD] = 'required_field'
                action_item = ''

            # App Specific Passwords are not valid
            elif aascf.is_asp_password(ui_password):
                self.errors[CONF_PASSWORD] = 'password_asp_invalid'
                action_item = ''

        # Changing a apple_id and the old one is being used and no devices are
        # using the old one, it's ok to change the name
        elif (ui_apple_id != conf_apple_id
                and ui_apple_id in Gb.AppleAcct_by_apple_id
                and instr(self.apple_acct_items_by_apple_id[ui_apple_id], ' 0 of ') is False):
            user_input[CONF_APPLE_ACCT]  = conf_apple_id
            user_input[CONF_PASSWORD]    = conf_password
            self.errors[CONF_APPLE_ACCT] = 'apple_acct_apple_id_inuse_error'
            action_item = ''

        # Saving a logged into account with no changes, nothing to do. Saving an acct
        # whose login failed without changes retries the login.
        if (action_item == 'save_log_into_apple_acct'
                and self.add_apple_acct_flag is False
                and ui_apple_id == conf_apple_id
                and ui_password == conf_password
                and user_input[CONF_LOCATE_ALL] == conf_locate_all
                and user_input[CONF_SERVER_LOCATION] == self.conf_apple_acct[CONF_SERVER_LOCATION]
                and aascf.is_apple_acct_logged_into(ui_apple_id)):
            self.errors['base'] = 'apple_acct_no_changes'
            action_item = ''

        #.......................................................................
        # An Apple Acct can only be authenticated if it is valid and logged into
        if action_item == 'authenticate_apple_acct':
            if aascf.is_apple_acct_logged_into(ui_apple_id):
                return await self.async_step_reauth(reauth_apple_id=ui_apple_id)
            self.errors[CONF_APPLE_ACCT] = 'apple_acct_not_logged_into'
            action_item = ''

        # Display the Confirm Actions form which will execute the remove_apple.. function
        if action_item == 'delete_apple_acct':
            # Drop the tracked/untracked part from the current heading (user_input['account_selected'])
            # Ex: account_selected = 'GaryCobb (gcobb321) -> 4 of 7 iCloud Devices Tracked, Tracked-(Gary-iPad ..'
            confirm_action_form_hdr = ( f"Delete Apple Account - {user_input['account_selected']}")
            if self.AppleAcct:
                confirm_action_form_hdr += f", Devices-{list_to_str(self.AppleAcct.aadevice_dnames)}"
            self.multi_form_user_input = user_input.copy()

            return await self.async_step_delete_apple_acct(user_input=user_input)

        # No action or the action was cleared by an error, redisplay the entered data
        if not action_item:
            return self._show_update_apple_acct_form(user_input)

        #.......................................................................
        upw_valid              = False
        aa_login_info_changed  = False
        other_fields_changed   = False
        login_verifies_upw     = False
        saved_conf_apple_accts = None
        apple_id_items_text    = self.apple_acct_items_by_apple_id.get(ui_apple_id, NOT_LOGGED_IN)
        aa_not_logged_into     = instr(apple_id_items_text, NOT_LOGGED_IN)

        if action_item == 'save_log_into_apple_acct':
            # Apple acct login info changed, validate it without logging in
            if (conf_apple_id != user_input[CONF_APPLE_ACCT]
                    or conf_password != user_input[CONF_PASSWORD]
                    or user_input[CONF_SERVER_LOCATION] != self.conf_apple_acct[CONF_SERVER_LOCATION]
                    or ui_apple_id not in Gb.AppleAcct_by_apple_id
                    or Gb.AppleAcct_by_apple_id.get(ui_apple_id) is None):
                aa_login_info_changed = True

            if (user_input[CONF_LOCATE_ALL] != self.conf_apple_acct[CONF_LOCATE_ALL]):
                other_fields_changed = True

            # Update the Apple config before validating it. The SRP validation updates the
            # trusted device info in the config acct for the apple_id, a new acct must be in
            # it. The update is undone below if Apple rejects the apple_id/password.
            if aa_login_info_changed or other_fields_changed:
                if aa_login_info_changed:
                    saved_conf_apple_accts = self._save_conf_apple_accts()
                self._update_conf_apple_acct(self.aa_idx, user_input)
                await self.async_write_icloud3_configuration_file()

                # Changed login info is not kept until the login is successful. The
                # 'updated' msg is displayed then, not on this save that may be undone.
                if aa_login_info_changed:
                    if self.errors.get('base') == 'conf_updated':
                        self.errors.pop('base')
                    if self.header_msg == 'conf_updated':
                        self.header_msg = None

            # An acct with no session token is signed into with a Password SRP signin that
            # verifies the password. Validating it first would add a 2nd SRP signin (a
            # 30-sec wait and a 2nd 2fa push), go straight to the login.
            if aa_login_info_changed:
                login_verifies_upw = await aascf.async_is_login_verifying_upw(ui_apple_id)

            # Validate the apple_id/password doing an SRP check
            if login_verifies_upw is False:
                if Gb.ValidateAppleAcctUPW is None:
                    Gb.ValidateAppleAcctUPW = ValidateAppleAcctUPW()

                upw_valid = await Gb.ValidateAppleAcctUPW.async_validate_apple_id_password_srp(
                                        ui_apple_id, ui_password)

                Gb.upw_valid_by_apple_id[ui_apple_id] = upw_valid

                if upw_valid is False:
                    self.actions_list_default = 'add_change_apple_acct'
                    self.errors['base'] = ''
                    self.errors[CONF_APPLE_ACCT] = self._login_error_msg('apple_acct_inupw_valid')

                    # Apple rejected it, only keep an acct that could not be invalidated
                    # (throttled, no response). The entered data is still redisplayed.
                    if saved_conf_apple_accts and self._is_upw_rejected_by_apple():
                        await self._restore_conf_apple_accts(saved_conf_apple_accts)

                    return self._show_update_apple_acct_form(user_input)

        # A new config, Log into the account
        if (aa_login_info_changed
                or aa_not_logged_into
                or ui_apple_id not in Gb.AppleAcct_by_apple_id
                or Gb.AppleAcct_by_apple_id.get(ui_apple_id) is None):

            saved_login_state = None
            if login_verifies_upw:
                saved_login_state = await aascf.async_save_apple_acct_login_state(ui_apple_id)

            successful_login = await aascf.async_log_into_apple_account(self, user_input)

            if successful_login is False:
                self.add_apple_acct_flag = False
                failed_AppleAcct = Gb.AppleAcct_by_apple_id.get(ui_apple_id)
                self.errors[CONF_APPLE_ACCT] = self._login_error_msg(AppleAcct=failed_AppleAcct)

                # The login was the apple_id/password validation and Apple rejected it.
                # Undo the login and the config update, only keep an acct that could
                # not be invalidated (throttled, no response).
                if (login_verifies_upw
                        and self._is_upw_rejected_by_apple(failed_AppleAcct)):
                    Gb.upw_valid_by_apple_id[ui_apple_id] = False
                    await aascf.async_restore_apple_acct_login_state(ui_apple_id, saved_login_state)
                    if saved_conf_apple_accts:
                        await self._restore_conf_apple_accts(saved_conf_apple_accts)

                return self._show_update_apple_acct_form(user_input)


        list_add(self.config_parms_update_control, ['restart'])
        self.errors[CONF_APPLE_ACCT] = ''

        # The changed login info was saved and the login was successful
        if saved_conf_apple_accts:
            self.header_msg = 'conf_updated'

        AppleAcct = self.AppleAcct = Gb.AppleAcct_by_apple_id.get(ui_apple_id)

        # We can now set the auth_method using data returned from Apple during the login
        # The first acct defaults to PUSH, others default to TEXT_1 if TEXT_1 is available
        # HWKEY will override this if using a Security Key
        if self.add_apple_acct_flag:
            if (self.aa_idx > 0 and self.AppleAcct.auth_method_value(TEXT_1) != ''):
                self.AppleAcct.update_auth_method(TEXT_1)
                self.update_config_file_tracking(force_config_update=True)

        Gb.AppleAcct_password_by_apple_id[ui_apple_id] = user_input[CONF_PASSWORD]

        if (aa_login_info_changed and
                ui_apple_id in Gb.AppleAcct_error_by_apple_id):
            self.errors[CONF_APPLE_ACCT] = self._login_error_msg()

        self.add_apple_acct_flag = False

        # Just logged into an Apple Acct, an authentication will probably be needed.
        # Display the reauth screen and build a user_input to trigger a code
        # request on entry.
        if AppleAcct.is_reauth_needed:
            # self.aa_reauth_apple_id = self.apple_id
            user_input = {  'account_selected': self.apple_id,
                            'action_items': 'request_auth_code'}
            return await self.async_step_reauth(
                            user_input=user_input, reauth_apple_id=self.apple_id)

        # Just logged into an Apple Acct, if no devices have already been
        # set up for this acct, display the import _apple_devices screen to
        # import them. Not done from HA Repairs, the account is already used by a device.
        if (aascf.any_conf_devices_for_apple_acct(ui_apple_id) is False
                and self.is_repair_flow is False):
            return await self.async_step_import_apple_devices()

        return await self.async_step_apple_accounts(user_input=None)

#...........................................................................................
    async def async_open_update_apple_acct_screen(self, apple_id):
        '''
        Display the Update Apple Account screen for the apple_id. This is the same as
        selecting the account on the Apple Accounts screen. It is also used by the
        HA Repairs flow (repairs.py) to open the account with a configuration error.

        Return:
            - The Update Apple Account form
            - None = The apple_id is not in the iCloud3 configuration
        '''
        # conf_apple_acct returns the first account if the apple_id is not found
        if apple_id not in [conf_apple_acct[CONF_APPLE_ACCT]
                                    for conf_apple_acct in Gb.conf_apple_accounts]:
            return None

        self.conf_apple_acct, self.aa_idx = config_file.conf_apple_acct(apple_id)
        self.apple_id        = self.conf_apple_acct[CONF_APPLE_ACCT]
        self.password        = self.conf_apple_acct[CONF_PASSWORD]
        self.AppleAcct       = Gb.AppleAcct_by_apple_id.get(self.apple_id)
        self.aa_page_item[self.aa_page_no] = self.apple_id

        return await self.async_step_update_apple_acct()

#...........................................................................................
    async def async_open_add_apple_acct_screen(self, apple_id, password=''):
        '''
        Display the Update Apple Account screen in Add mode with the apple_id filled in.
        This is the same as selecting Add on the Apple Accounts screen. It is used by the
        HA Repairs flow (repairs.py) to add an Apple Account that is assigned to a device
        but is not in the iCloud3 configuration.

        Input:
            password - Encoded password to fill in (the one saved in the .tpw file of
                    an Apple Account that was removed), '' if none

        Return:
            - The Update Apple Account form
        '''
        self.add_apple_acct_flag = True
        self.conf_apple_acct     = DEFAULT_APPLE_ACCOUNT_CONF.copy()
        self.conf_apple_acct[CONF_APPLE_ACCT] = apple_id
        self.conf_apple_acct[CONF_PASSWORD]   = password
        self.apple_id            = apple_id
        self.password            = password
        self.AppleAcct           = None

        return await self.async_step_update_apple_acct()

#...........................................................................................
    def _show_update_apple_acct_form(self, user_input=None):
        '''
        Display the Update Apple Account form with the current errors. Return this directly
        on an error instead of calling async_step_update_apple_acct again, which would
        reprocess the user_input and log into the Apple Account again.

        Input:
            user_input - The data that failed. It is redisplayed so the apple_id/password
                    can be corrected.
        '''
        if user_input is not None:
            self.errors_user_input = user_input

        errors = self.errors
        self.errors = {}
        return self.async_show_form(step_id='update_apple_acct',
                        data_schema=forms.form_update_apple_acct(self),
                        errors=errors)

#...........................................................................................
    @staticmethod
    def _is_valid_apple_id_format(apple_id):
        '''
        An Apple Account is an email address or a phone number (some regions).

        Return:
            True  - email address (name@domain.xx) or phone number (7-15 digits)
            False - Apple will reject it as an unknown account
        '''
        if '@' in apple_id:
            name, _, domain = apple_id.partition('@')
            return name != '' and '.' in domain.strip('.')

        phone = apple_id.lstrip('+')
        for phone_char in ' -().':
            phone = phone.replace(phone_char, '')

        return phone.isdigit() and 7 <= len(phone) <= 15

#...........................................................................................
    def _is_upw_rejected_by_apple(self, AppleAcct=None):
        '''
        Input:
            AppleAcct - The AppleAcct that did the SRP signin. None=The validation's

        Return:
            True  - Apple's SRP answer rejected the apple_id/password
            False - Throttled (503), no response or some other error, the apple_id/password
                    could not be invalidated
        '''
        try:
            if AppleAcct is None:
                AppleAcct = Gb.ValidateAppleAcctUPW.AppleAcct

            # A 503 on the srp signin/init is an invalid apple_id
            if getattr(AppleAcct, 'srp_signin_init_503', False):
                return True

            return (AppleAcct.auth_failed_503 is False
                    and AppleAcct.response_code in APPLE_REJECTED_UPW_CODES)

        except Exception as err:
            return False

#...........................................................................................
    def _save_conf_apple_accts(self):
        '''
        Save the Apple Account config and the current account's selection fields
        before they are updated so they can be restored if Apple rejects the update.
        '''
        return {'conf_apple_accounts': copy.deepcopy(Gb.conf_apple_accounts),
                'conf_apple_acct':     copy.deepcopy(self.conf_apple_acct),
                'aa_idx':              self.aa_idx,
                'aa_page_no':          self.aa_page_no,
                'aa_page_item':        copy.deepcopy(self.aa_page_item),
                'add_apple_acct_flag': self.add_apple_acct_flag, }

#...........................................................................................
    async def _restore_conf_apple_accts(self, saved_conf_apple_accts):
        '''
        Undo the _update_conf_apple_acct update of an apple_id/password Apple rejected.
        Gb.conf_apple_accounts is updated in place, it is the conf_tracking list.
        '''
        saved = saved_conf_apple_accts
        Gb.conf_apple_accounts[:] = saved['conf_apple_accounts']
        self.conf_apple_acct      = saved['conf_apple_acct']
        self.aa_idx               = saved['aa_idx']
        self.aa_page_no           = saved['aa_page_no']
        self.aa_page_item         = saved['aa_page_item']
        self.add_apple_acct_flag  = saved['add_apple_acct_flag']

        self.update_config_file_tracking(force_config_update=True)
        lists.build_apple_accounts_list(self)
        lists.build_devices_list(self)
        config_file.build_log_file_filters()
        await self.async_write_icloud3_configuration_file()

#...........................................................................................
    def _login_error_msg(self, default_msg=None, AppleAcct=None):
        '''
        Input:
            AppleAcct - The AppleAcct of the failed login. None=The validation's or self.AppleAcct
        '''
        try:
            if AppleAcct:
                pass
            elif self.AppleAcct is None or default_msg is None:
                AppleAcct = Gb.ValidateAppleAcctUPW.AppleAcct
            else:
                AppleAcct = self.AppleAcct

            if AppleAcct.auth_failed_503:
                return 'apple_acct_login_error_503'
            if AppleAcct.response_code == 302:
                return 'apple_acct_login_error_302'
            if AppleAcct.response_code == 403:
                return 'apple_acct_locked'
            if AppleAcct.response_code == 401:
                return 'apple_acct_inupw_valid'

            if default_msg is not None:
                return default_msg

        except Exception as err:
            # log_exception(err)
            pass

        return 'apple_acct_updated_login_error'

#-------------------------------------------------------------------------------------------
    def _update_conf_apple_acct(self, aa_idx, user_input, remove_acct_flag=False):
        '''
        Update the apple accounts config entry with the new values.

        Input (user_input):
            - apple_id = Updated apple_id
            - password = Updated password
            - apple_account =
                - #  = Index number of the apple_id being updated in the conf_apple_accounts list
                - -1 = Add this apple_id/password to the conf_apple_accounts list

        If the apple_account is the index ('#') and the apple_id & password are empty, that item
        is deleted if it is not the primary account (1st entry).

        '''
        self._enable_data_source_ICLOUD()

        # Updating the account
        if remove_acct_flag is False:
            self.conf_apple_acct[CONF_APPLE_ACCT]   = user_input[CONF_APPLE_ACCT]
            self.conf_apple_acct[CONF_PASSWORD]   = encode_password(user_input[CONF_PASSWORD])
            self.conf_apple_acct[CONF_LOCATE_ALL] = user_input[CONF_LOCATE_ALL]
            self.conf_apple_acct[CONF_SERVER_LOCATION] = user_input[CONF_SERVER_LOCATION]
            self.conf_apple_acct = config_file.sync_apple_id_username_parameter(self.conf_apple_acct)

        # Delete an existing account
        # aa_idx -1 is an acct that is not in the config. A list index of -1 would
        # remove or overwrite the last acct.
        if remove_acct_flag:
            if aa_idx >= 0:
                Gb.conf_apple_accounts.pop(aa_idx)
            self.conf_apple_acct = DEFAULT_APPLE_ACCOUNT_CONF.copy()
            self.aa_idx = aa_idx - 1
            if self.aa_idx < 0: self.aa_idx = 0
            self.aa_page_item[self.aa_page_no] = ''

        # Add a new account
        elif self.add_apple_acct_flag or aa_idx < 0:
            Gb.conf_apple_accounts.append(self.conf_apple_acct)
            self.aa_idx = len(Gb.conf_apple_accounts) - 1
            self.aa_page_no = int(self.aa_idx / 5)
            self.aa_page_item[self.aa_page_no] = self.conf_apple_acct[CONF_APPLE_ACCT]

        # Set the account being updated to the new value
        else:
            Gb.conf_apple_accounts[aa_idx] = self.conf_apple_acct
            self.aa_idx = aa_idx
            self.aa_page_no = int(self.aa_idx / 5)
            self.aa_page_item[self.aa_page_no] = self.conf_apple_acct[CONF_APPLE_ACCT]

        max_aa_idx = len(Gb.conf_apple_accounts) - 1
        if self.aa_idx > max_aa_idx:
            self.aa_idx = max_aa_idx
        elif self.aa_idx < 0:
            self.aa_idx = 0

        user_input['account_selected'] = self.aa_idx
        self.update_config_file_tracking(force_config_update=True)
        lists.build_apple_accounts_list(self)
        lists.build_devices_list(self)
        config_file.build_log_file_filters()

#-------------------------------------------------------------------------------------------
    def _can_disable_locate_all(self, user_input):
        famshr_Devices = [Device    for Device in Gb.Devices
                                    if Device.family_share_device
                                        and Device.conf_apple_acct_apple_id == user_input[CONF_APPLE_ACCT]]

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

        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        user_input = utils_cf.option_text_to_parm(user_input,
                                'device_action', DELETE_APPLE_ACCT_DEVICE_ACTION_OPTIONS)
        utils_cf.log_step_info(self, user_input, action_item)

        if user_input is None or action_item is None:
            return self.async_show_form(step_id='delete_apple_acct',
                                        data_schema=forms.form_delete_apple_acct(self),
                                        errors=self.errors)

        if action_item == 'cancel_goto_previous':
            return await self.async_step_update_apple_acct()

        device_action = user_input['device_action']
        delete_apple_id = self.conf_apple_acct[CONF_APPLE_ACCT]
        self._delete_apple_acct(user_input)

        # Remove its session files. A stale session token or .tpw password left behind is
        # used if the account is added again.
        await aascf.async_delete_apple_acct_files(delete_apple_id)

        list_add(self.config_parms_update_control, ['tracking', 'restart'])
        self.header_msg = 'action_completed'

        return await self.async_step_apple_accounts()

#------------------------------------------------------------------------------------------
    def _delete_apple_acct(self, user_input):
        '''
        Remove Apple Account from the Apple Accounts config list
        and from all devices using it.
        '''

        # Cycle through the devices and see if it is assigned to the acct being removed.
        # If it is, see if the device is in the primary (1st) apple_id Apple acct.
        # If it is, reassign the device to that Apple acct. Otherwise, remove it

        primary_apple_id = Gb.conf_apple_accounts[0][CONF_APPLE_ACCT]
        device_action = user_input['device_action']
        conf_apple_id = self.conf_apple_acct[CONF_APPLE_ACCT]

        # Cycle thru config and get the apple_id being deleted. Delete or update it
        updated_conf_devices = []
        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]
            if conf_device[CONF_APPLE_ACCT] != conf_apple_id:
                updated_conf_devices.append(conf_device)

            elif device_action == 'delete_devices':
                sensors_cf.remove_device_tracker_and_sensor_entities(self, devicename)

            elif device_action == 'set_devices_inactive':
                conf_device[CONF_APPLE_ACCT] = ''
                conf_device[CONF_AADEV_NAME] ='None'
                conf_device[CONF_TRACKING_MODE] = INACTIVE
                updated_conf_devices.append(conf_device)

            elif device_action == 'reassign_devices':
                icloud_dname = conf_device[CONF_AADEV_NAME]
                other_apple_acct = [AppleAcct.apple_id
                                        for apple_id, AppleAcct in Gb.AppleAcct_by_apple_id.items()
                                        if icloud_dname in AppleAcct.device_id_by_aadev_dname]
                if other_apple_acct == []:
                    conf_device[CONF_APPLE_ACCT] = ''
                    conf_device[CONF_TRACKING_MODE] = INACTIVE
                else:
                    conf_device[CONF_APPLE_ACCT] = other_apple_acct[0]
                updated_conf_devices.append(conf_device)

        Gb.conf_devices = updated_conf_devices
        self.update_config_file_tracking(user_input={}, force_config_update=True)

        aas.delete_AppleAcct_Gb_variables_apple_id(conf_apple_id)
        self._update_conf_apple_acct(self.aa_idx, user_input, remove_acct_flag=True)

        return user_input


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            OTHER APPLE ACCT PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_other_apple_acct_parameters(self, user_input=None, errors=None):
        self.step_id = 'other_apple_acct_parameters'
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        save_user_input = None

        user_input = utils_cf.option_text_to_parm(user_input,
                                    CONF_SERVER_LOCATION, APPLE_SERVER_LOCATION_OPTIONS)
        utils_cf.log_step_info(self, user_input, action_item)

        if user_input[CONF_SERVER_LOCATION] != 'usa':
            user_input[CONF_SERVER_LOCATION_NEEDED] = True


        #.......................................................................
        match action_item:
            case None:
                save_user_input = user_input

            case 'rtn_update_apple_acct':
                return await self.async_step_update_apple_acct(
                                            user_input=save_user_input, errors=self.errors)

            case 'save':
                Gb.conf_tracking[CONF_SERVER_LOCATION_NEEDED] = user_input[CONF_SERVER_LOCATION_NEEDED]
                self.conf_apple_acct[CONF_SERVER_LOCATION]    = user_input[CONF_SERVER_LOCATION]
                self.update_config_file_tracking(user_input, force_config_update=True)
                return await self.async_step_update_apple_acct(
                                            user_input=save_user_input, errors=self.errors)

        #.......................................................................
        if utils_cf.any_errors(self):
            self.errors['base'] = 'update_aborted'

        return self.async_show_form(step_id='other_apple_acct_parameters',
                        data_schema=forms.form_other_apple_acct_parameters(self),
                        errors=self.errors)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             IMPORT APPLE ACCOUNT DEVICES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_import_apple_devices(self, user_input=None, errors=None):

        self.step_id = 'import_apple_devices'
        self.errors = errors or utils_cf.set_header_msg(self) or {}
        self.errors_user_input = {}
        self.errors_info_msg = None

        await self.async_write_icloud3_configuration_file()
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        utils_cf.log_step_info(self, user_input, action_item)

        #.......................................................................
        match action_item:
            case 'rtn_device_list':
                self.menu_item = 'device_list'
                return await self.async_step_device_list()

            case 'rtn_apple_accounts':
                self.menu_item = 'apple_accounts'
                return await self.async_step_apple_accounts()

            case 'menu':
                return await self.async_step_menu()

        #.......................................................................
        if Gb.internet_error:
            self.errors['base'] = 'internet_error_no_change'

        # if is_empty(Gb.conf_apple_accounts):
        #     self.header_msg = 'apple_acct_not_set_up'

        if (user_input is None or self.errors):
            forms_schema = forms.form_import_apple_devices(self)
            if is_empty(self.imported_aa_ic3_conf_devices):
                self.errors['action_items'] = 'import_aa_no_devices_avail'

            return self.async_show_form(step_id='import_apple_devices',
                        data_schema=forms_schema,
                        errors=self.errors)

        #.......................................................................
        if action_item == 'add_imported_apple_devices':
            await self._add_imported_devices(user_input)
            if self.menu_item in ['apple_accounts', 'device_list']:
                self.menu_item = 'device_list'
                return await self.async_step_device_list()

        utils_cf.log_step_info(self, user_input, action_item)

        forms_schema = forms.form_import_apple_devices(self)
        if is_empty(self.imported_aa_ic3_conf_devices):
                self.errors['action_items'] = 'import_aa_no_devices_avail'

        return self.async_show_form(step_id='import_apple_devices',
                            data_schema=forms_schema,
                            errors=self.errors)

#--------------------------------------------------------------------
    async def _add_imported_devices(self, user_input):

        imported_aadevices_keys =  (
                            user_input.get('imported_aadevices_track', []) +
                            user_input.get('imported_aadevices_monitor', []) +
                            user_input.get('imported_aadevices_inactive', []))

        if is_empty(imported_aadevices_keys):
            return

        self.errors['base'] = 'conf_updated'

        for imported_aadevices_key in imported_aadevices_keys:
            self.conf_device = DEFAULT_DEVICE_CONF.copy()

            conf_device = self.imported_aa_ic3_conf_devices[imported_aadevices_key]
            devicename  = conf_device[CONF_IC3_DEVICENAME]

            # The devicename is already in the config file and probably set to inactive
            # Update the current entry instead of adding it again
            conf_device_idx = Gb.conf_devices_idx_by_devicename.get(devicename, -1)

            if conf_device_idx == -1:
                self._add_new_device_to_conf_devices(conf_device)
            else:
                self.conf_device.update(conf_device)
                Gb.conf_devices[conf_device_idx] = self.conf_device.copy()

            self.update_config_file_tracking(force_config_update=True)
            self.create_device_tracker_sensor_enities_on_exit = True
            self.rebuild_ic3db_dashboards = True
            log_info_msg(f'Add Imported Apple Device-({imported_aadevices_key}), '
                            f'Device-{conf_device[CONF_FNAME]=}, '
                            f'/{conf_device[CONF_IC3_DEVICENAME]=}')

#--------------------------------------------------------------------
    def _unpack_ui_import_apple_devices(self, user_input):
        if user_input is None: return None

        user_input = utils_cf.option_text_to_parm(user_input,
                                                    'account_selected',
                                                    self.apple_acct_items_by_apple_id)

        return user_input
