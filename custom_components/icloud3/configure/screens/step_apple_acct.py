from ...global_variables    import GlobalVariables as Gb
from ...const               import (ICLOUD, MOBAPP, NO_MOBAPP,
                                    INACTIVE, PUSH, TEXT, TEXT_1, TEXT_2, HWKEY,
                                    CONF_APPLE_ACCOUNT, CONF_IC3_DEVICENAME, CONF_FNAME,
                                    CONF_USERNAME, CONF_PASSWORD, CONF_FAMSHR_DEVICENAME,
                                    CONF_DATA_SOURCE, CONF_LOCATE_ALL,
                                    CONF_SERVER_LOCATION, CONF_SERVER_LOCATION_NEEDED,
                                    CONF_TRACKING_MODE,  DEFAULT_APPLE_ACCOUNT_CONF, DEFAULT_DEVICE_CONF,
                                    )
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

        if self._is_apple_acct_setup() is False:
            self.errors['apple_accts'] = 'apple_acct_not_set_up'

            user_input = {'apple_accts': '➤ ADD'}

        elif isnot_empty(Gb.conf_apple_accounts):
            self._verify_data_source_ICLOUD()

        if user_input is None:
            self.actions_list_default = 'update_apple_acct'
            return self.async_show_form(step_id='apple_accounts',
                                        data_schema=forms.form_apple_accounts(self),
                                        errors=self.errors)

        self._verify_data_source_ICLOUD()
        utils_cf.log_step_info(self, user_input, action_item)

        #.......................................................................
        match action_item:
            case 'menu':
                self._initialize_self_AppleAcct_fields_from_Gb()
                return await self.async_step_menu()

            case 'authenticate_apple_acct':
                # if self.AppleAcct.is_reauth_needed:
                # self.aa_reauth_username = self.username
                # else:
                #     self.aa_reauth_username = ''

                return await self.async_step_reauth(reauth_username=self.username)

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
                                'apple_accts', self.apple_acct_items_by_username)

        ui_username = user_input['apple_accts']
        self.conf_apple_acct, self.aa_idx = config_file.conf_apple_acct(ui_username)

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
            conf_apple_acct_usernames = [apple_acct[CONF_USERNAME]
                                        for apple_acct in Gb.conf_apple_accounts]
            log_info_msg(   f"Error > {ui_username}, Username not found in Apple accts device list, "
                            f"Valid Accts-{list_to_str(conf_apple_acct_usernames)}")


        # if (self.username != user_input.get('apple_accts', self.username)
        #         and action_item == 'save'):
        #     action_item = 'update_apple_acct'

        self.username = self.conf_apple_acct[CONF_USERNAME]
        self.password = self.conf_apple_acct[CONF_PASSWORD]
        self.AppleAcct = Gb.AppleAcct_by_username.get(self.username)

        if Gb.is_log_level_debug:
            log_user_input = user_input.copy()
            utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'update_apple_acct':
            self.aa_page_item[self.aa_page_no] = self.conf_apple_acct[CONF_USERNAME]
            return await self.async_step_update_apple_acct()

        # if user_input[CONF_DATA_SOURCE] == '':
        #     self.errors['base'] = 'apple_acct_no_data_source'

        if self.errors == {}:
            if action_item == 'add_change_apple_acct':
                return await self.async_step_menu()

        self.step_id = 'apple_accounts'
        return self.async_show_form(step_id='apple_accounts',
                            data_schema=forms.form_apple_accounts(self),
                            errors=self.errors)

#...........................................................
    def _verify_data_source_ICLOUD(self):

        if instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD):
            return

        Gb.conf_tracking[CONF_DATA_SOURCE] = f"{ICLOUD},{Gb.conf_tracking[CONF_DATA_SOURCE]}"

        return

#...........................................................
    def _is_apple_acct_setup(self):

        if self.username:
            return True
        elif is_empty(Gb.conf_apple_accounts):
            return False
        elif Gb.conf_apple_accounts[0].get(CONF_USERNAME, '') == '':
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

        #.......................................................................
        match action_item:
            case 'cancel_goto_previous' | 'rtn_apple_accounts':
                self.username = self.conf_apple_acct[CONF_USERNAME]
                self.password = decode_password(self.conf_apple_acct[CONF_PASSWORD])
                self.AppleAcct = Gb.AppleAcct_by_username.get(self.username)
                return await self.async_step_apple_accounts(user_input=None)

            case 'stop_login_retry':
                AppleAcct = Gb.AppleAcct_by_username.get(self.username)
                if AppleAcct:
                    AppleAcct.error_retry_cnt = 0
                    AppleAcct.error_next_retry_secs = 0
                user_input = None
                post_alert(f"Apple Acct > {AppleAcct.username_id}, Retry Login Canceled")
                self.errors['base'] = 'conf_updated'
                return await self.async_step_update_apple_acct(
                                                user_input=user_input, errors=self.errors)

        #.......................................................................
        if (user_input is None
                or Gb.internet_error
                or instr(self.errors.get(CONF_USERNAME, ''), 'invalid')
                or instr(self.errors.get(CONF_USERNAME, ''), 'error')
                or instr(self.errors.get(CONF_USERNAME, ''), 'required')
                or instr(self.errors.get(CONF_PASSWORD, ''), 'required')):
            errors=self.errors
            self.errors = {}
            return self.async_show_form(step_id='update_apple_acct',
                        data_schema=forms.form_update_apple_acct(self),
                        errors=errors)

        user_input = utils_cf.option_text_to_parm(user_input,
                                'account_selected', self.apple_acct_items_by_username)
        user_input = utils_cf.strip_spaces(user_input, [CONF_USERNAME, CONF_PASSWORD])
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
            action_item = ''
            return await self.async_step_update_apple_acct(
                                            user_input=user_input, errors=self.errors)

        if (Gb.internet_error and action_item == 'save_log_into_apple_acct'):
            self.errors['base'] = 'internet_error_no_change'
            user_input = None
            return await self.async_step_update_apple_acct(
                                            user_input=user_input, errors=self.errors)

        if action_item == 'cancel_goto_previous':
            self.username = self.conf_apple_acct[CONF_USERNAME]
            self.password = decode_password(self.conf_apple_acct[CONF_PASSWORD])
            self.AppleAcct = Gb.AppleAcct_by_username.get(self.username)
            return await self.async_step_apple_accounts(user_input=None)

        user_input[CONF_USERNAME] = user_input[CONF_USERNAME].lower()
        ui_username = user_input[CONF_USERNAME]
        ui_password = user_input[CONF_PASSWORD]

        # Make an apple acct dict to compare to the current one
        ui_apple_acct = DEFAULT_APPLE_ACCOUNT_CONF.copy()
        ui_apple_acct[CONF_USERNAME]   = ui_username
        ui_apple_acct[CONF_PASSWORD]   = ui_password
        ui_apple_acct[CONF_LOCATE_ALL] = user_input[CONF_LOCATE_ALL]
        ui_apple_acct[CONF_SERVER_LOCATION] = user_input[CONF_SERVER_LOCATION]

        conf_username   = self.conf_apple_acct[CONF_USERNAME]
        conf_password   = decode_password(self.conf_apple_acct[CONF_PASSWORD])
        conf_locate_all = self.conf_apple_acct[CONF_LOCATE_ALL]

        add_log_file_filter(ui_username, f"**{self.aa_idx}**")
        add_log_file_filter(ui_username.upper(), f"**{self.aa_idx}**")
        add_log_file_filter(ui_password)

        if Gb.is_log_level_debug:
            log_user_input = user_input.copy()
            utils_cf.log_step_info(self, user_input, action_item)

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
                and user_input[CONF_LOCATE_ALL] != conf_locate_all
                and Gb.AppleAcct_by_username.get(ui_username) is not None):
            action_item = ''

        #.......................................................................
        match action_item:
            case '':
                return await self.async_step_update_apple_acct(user_input=user_input, errors=self.errors)

            case 'authenticate_apple_acct':
                return await self.async_step_reauth(reauth_username=self.username)

            # Display the Confirm Actions form which will execute the remove_apple.. function
            case 'delete_apple_acct':
                # Drop the tracked/untracked part from the current heading (user_input['account_selected'])
                # Ex: account_selected = 'GaryCobb (gcobb321) -> 4 of 7 iCloud Devices Tracked, Tracked-(Gary-iPad ..'
                confirm_action_form_hdr = ( f"Delete Apple Account - {user_input['account_selected']}")
                if self.AppleAcct:
                    confirm_action_form_hdr += f", Devices-{list_to_str(self.AppleAcct.aadevice_dnames)}"
                self.multi_form_user_input = user_input.copy()

                return await self.async_step_delete_apple_acct(user_input=user_input)

        #.......................................................................
        valid_upw             = False
        aa_login_info_changed = False
        other_fields_changed  = False
        username_items_text   = self.apple_acct_items_by_username.get(ui_username, NOT_LOGGED_IN)
        aa_not_logged_into    = instr(username_items_text, NOT_LOGGED_IN)

        if action_item == 'save_log_into_apple_acct':
            # Apple acct login info changed, validate it without logging in
            if (conf_username != user_input[CONF_USERNAME]
                    or conf_password != user_input[CONF_PASSWORD]
                    or user_input[CONF_SERVER_LOCATION] != self.conf_apple_acct[CONF_SERVER_LOCATION]
                    or ui_username not in Gb.AppleAcct_by_username
                    or Gb.AppleAcct_by_username.get(ui_username) is None):
                aa_login_info_changed = True

            if (user_input[CONF_LOCATE_ALL] != self.conf_apple_acct[CONF_LOCATE_ALL]):
                other_fields_changed = True

            # if valid_upw:
            #     if aa_login_info_changed or other_fields_changed:
            #         self._update_conf_apple_acct(self.aa_idx, user_input)
            #         await self.async_write_icloud3_configuration_file()
            #         self.add_apple_acct_flag = False


            # Update the Apple config even though it is not validated. Otherwise, the
            # entered data will not be available to be corrected
            if aa_login_info_changed or other_fields_changed:
                self._update_conf_apple_acct(self.aa_idx, user_input)
                await self.async_write_icloud3_configuration_file()

            # App Specific Passwords are not valid
            if aascf.is_asp_password(ui_password):
                self.errors[CONF_PASSWORD] = 'password_asp_invalid'

            # Validate the username/password doing an SRP check
            elif valid_upw is False or aa_login_info_changed:
                if Gb.ValidateAppleAcctUPW is None:
                    Gb.ValidateAppleAcctUPW = ValidateAppleAcctUPW()

                valid_upw = await Gb.ValidateAppleAcctUPW.async_validate_username_password_srp(
                                        ui_username, ui_password)

                Gb.valid_upw_by_username[ui_username] = valid_upw

                if valid_upw is False:
                    self.actions_list_default = 'add_change_apple_acct'
                    self.errors['base'] = ''
                    self.errors[CONF_USERNAME] = self._login_error_msg('apple_acct_invalid_upw')

                    return await self.async_step_update_apple_acct(
                                                user_input=user_input, errors=self.errors)

        # A new config, Log into the account
        if (aa_login_info_changed
                or aa_not_logged_into
                or ui_username not in Gb.AppleAcct_by_username
                or Gb.AppleAcct_by_username.get(ui_username) is None):

            successful_login = await aascf.async_log_into_apple_account(self, user_input)

            if successful_login is False:
                self.add_apple_acct_flag = False

                self.errors[CONF_USERNAME] = self._login_error_msg()
                return await self.async_step_update_apple_acct(
                                            user_input=user_input, errors=self.errors)


        # Update the Apple config even if it is not validated. If the un/pw has been tried
        # multiple times and it  was wrong, Apple will still refuse it even if it correct.
        # A 401 is returned from validate_upw and 403 from PasswordSRP. If it is not saved,
        # It will still be invalid on a restart because a failed valid one will not have
        # been saved

        list_add(self.config_parms_update_control, ['restart'])
        self.errors[CONF_USERNAME] = ''

        AppleAcct = self.AppleAcct = Gb.AppleAcct_by_username.get(ui_username)

        # We can now set the auth_method using data returned from Apple during the login
        # The first acct defaults to PUSH, others default to TEXT_1 if TEXT_1 is available
        # HWKEY will override this if using a Security Key
        if self.add_apple_acct_flag:
            if (self.aa_idx > 0 and self.AppleAcct.auth_method_value(TEXT_1) != ''):
                self.AppleAcct.update_auth_method(TEXT_1)
                self.update_config_file_tracking(force_config_update=True)

        Gb.AppleAcct_password_by_username[ui_username] = user_input[CONF_PASSWORD]

        if (aa_login_info_changed and
                ui_username in Gb.AppleAcct_error_by_username):
            self.errors[CONF_USERNAME] = self._login_error_msg()

        self.add_apple_acct_flag = False

        # Just logged into an Apple Acct, an authentication will probably be needed.
        # Display the reauth screen and build a user_input to trigger a code
        # request on entry.
        if AppleAcct.is_reauth_needed:
            # self.aa_reauth_username = self.username
            user_input = {  'account_selected': self.username,
                            'action_items': 'request_auth_code'}
            # user_input = None
            return await self.async_step_reauth(
                            user_input=user_input, reauth_username=self.username)

        # Just logged into an Apple Acct, if no devices have already been
        # set up for this acct, display the import _apple_devices screen to
        # import them
        if aascf.any_conf_devices_for_apple_acct(ui_username) is False:
            return await self.async_step_import_apple_devices()

        return await self.async_step_apple_accounts(user_input=None)

#...........................................................................................
    def _login_error_msg(self, default_msg=None):
        if self.AppleAcct is None or default_msg is None:
            AppleAcct = Gb.ValidateAppleAcctUPW.AppleAcct
        else:
            AppleAcct = self.AppleAcct

        if AppleAcct.auth_failed_503:
            return 'apple_acct_login_error_503'
        if AppleAcct.response_code == 302:
            return 'apple_acct_login_error_302'
        if AppleAcct.response_code == 403:
            return 'apple_acct_locked'

        if default_msg is not None:
            return default_msg

        return 'apple_acct_updated_login_error'

#-------------------------------------------------------------------------------------------
    def _update_conf_apple_acct(self, aa_idx, user_input, remove_acct_flag=False):
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
        self._verify_data_source_ICLOUD()

        # Updating the account
        if remove_acct_flag is False:
            self.conf_apple_acct[CONF_USERNAME]   = user_input[CONF_USERNAME]
            self.conf_apple_acct[CONF_PASSWORD]   = encode_password(user_input[CONF_PASSWORD])
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
        self.update_config_file_tracking(force_config_update=True)
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
        self._delete_apple_acct(user_input)

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
                sensors_cf.remove_device_tracker_and_sensor_entities(self, devicename)

            elif device_action == 'set_devices_inactive':
                conf_device[CONF_APPLE_ACCOUNT] = ''
                conf_device[CONF_FAMSHR_DEVICENAME] ='None'
                conf_device[CONF_TRACKING_MODE] = INACTIVE
                updated_conf_devices.append(conf_device)

            elif device_action == 'reassign_devices':
                icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
                other_apple_acct = [AppleAcct.username
                                        for username, AppleAcct in Gb.AppleAcct_by_username.items()
                                        if icloud_dname in AppleAcct.device_id_by_icloud_dname]
                if other_apple_acct == []:
                    conf_device[CONF_APPLE_ACCOUNT] = ''
                    conf_device[CONF_TRACKING_MODE] = INACTIVE
                else:
                    conf_device[CONF_APPLE_ACCOUNT] = other_apple_acct[0]
                updated_conf_devices.append(conf_device)

        Gb.conf_devices = updated_conf_devices
        self.update_config_file_tracking(user_input={}, force_config_update=True)

        aas.delete_AppleAcct_Gb_variables_username(conf_username)
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

        if len(Gb.conf_apple_accounts) == 0:
            self.header_msg = 'apple_acct_not_set_up'

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
            log_debug_msg(f'Add Imported Apple Device-({imported_aadevices_key}), '
                            f'Device-{conf_device[CONF_FNAME]=}, '
                            f'/{conf_device[CONF_IC3_DEVICENAME]=}')

#--------------------------------------------------------------------
    def _unpack_ui_import_apple_devices(self, user_input):
        if user_input is None: return None

        user_input = utils_cf.option_text_to_parm(user_input,
                                                    'account_selected',
                                                    self.apple_acct_items_by_username)

        return user_input
