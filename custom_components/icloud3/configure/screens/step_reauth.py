
from ...global_variables    import GlobalVariables as Gb
from ...const               import (CONF_AUTH_CODE, CONF_AUTH_METHODS, CONF_LAST_METHOD, PUSH,
                                    EVLOG_NOTICE, )
from ...utils.utils         import (instr, is_number, is_empty, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ...utils.time_util     import (secs_to_hhmm, )

from ...startup             import config_file
from ...apple_acct.apple_acct_support_cf import (
                                    async_finish_authentication_and_data_refresh,
                                    clear_AppleAcct_auth_alerts, )

from .                      import form_reauth as forms
from ..                     import utils_cf
from ..                     import selection_lists as lists

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#     ICLOUD3 REAUTH STEPS
#
#        - async_step_reauth
#        - async_step_reauth_code_from_applecom_login
#        - async_step_reauth_change_auth_method
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OptionsFlow_Reauth_Steps:


    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #            REAUTH
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_reauth(self, user_input=None, errors=None,
                                return_to_step_id=None, reauth_username=None):


        try:
            self.step_id = 'reauth'
            self.errors = errors or {}
            self.errors_user_input = {}

            user_input = self._unpack_ui_reauth(user_input)
            user_input, action_item = utils_cf.action_text_to_item(self, user_input)

            log_debug_msg(  f"⭐ REAUTH ENTER {self.step_id.upper()} ({action_item}) > "
                            f"UserInput-{user_input}, Errors-{errors}")

            # Set up the reauthentication process based on the entry point - iCloud3_ConfigFlow
            # from the HA notifications or iCloud3_OptionsFlow from the iCloud3 Menu. 'self.return_to_step_id_1'
            # is set if this has already been done
            if self.return_to_step_id_1 != '':
                pass
            elif self.is_config_flow_handler:
                # Initialize using the config_flow info
                await self._initialize_config_flow_reauth()
                user_input = None
            else:
                # Initialize using the options_flow info
                user_input = await self._initialize_options_flow_reauth(user_input, return_to_step_id)

            if Gb.internet_error:
                self.errors['base'] = 'internet_error_no_change'

            if len(Gb.conf_apple_accounts) == 0:
                self.header_msg = 'apple_acct_not_set_up'

            elif self.AppleAcct is None:
                self.errors['account_selected'] = 'apple_acct_not_logged_into'

            if user_input is None or self.errors:
                return self.async_show_form(step_id='reauth',
                            data_schema=forms.form_reauth(self, reauth_username=reauth_username),
                            errors=self.errors)

        except Exception as err:
            log_exception(err)

        try:
            AppleAcct, reauth_username = self.get_username_needing_reauth(user_input.get('account_selected'))

            ui_auth_code    = user_input.get(CONF_AUTH_CODE, '')
            self.errors[CONF_AUTH_CODE] = ''

            log_debug_msg(  f"⭐ REAUTH HANDLER ({action_item}) > "
                            f"From-{return_to_step_id}, UserInput-{user_input}, Errors-{errors}")

            # ui_conf_fido_key_name = user_input['fido2_key_name']
            # if Gb.fido2_security_keys_enabled:
            #     user_input = utils_cf.option_text_to_parm(user_input, 'fido2_key_name',
            #                                         self.reauth_form_fido2_key_names_list)
            # else:
            #     user_input['fido2_key_name'] = ['']

            if (reauth_username is None
                    or action_item in ['goto_previous', 'goto_ha_auth_done']):
                self.apple_acct_reauth_username = ''
                self.is_another_auth_code_needed()
                return self._reauth_goto_previous()

            if action_item == 'auth_code_from_applecom_login':
                return await self.async_step_reauth_code_from_applecom_login()

            if action_item == 'change_auth_method':
                return await self.async_step_reauth_change_auth_method(reauth_username=reauth_username)

            if (action_item == 'send_auth_code'
                    and ui_auth_code == ''):
                action_item = 'request_auth_code'

            if (ui_auth_code != ''
                    and len(ui_auth_code) == 6
                    and is_number(ui_auth_code)):
                action_item = 'send_auth_code'

            elif (Gb.internet_error and action_item != 'goto_previous'):
                self.errors['base'] = 'internet_error_no_change'
                user_input = None
                return await self.async_step_reauth(user_input=user_input, errors=self.errors)

            AppleAcct = self.AppleAcct = Gb.AppleAcct_by_username.get(reauth_username)
            if AppleAcct is None:
                self.errors['account_selected'] = 'reauth_apple_acct_unknown'
                self.errors[CONF_AUTH_CODE] = ''
                return await self.async_step_reauth(user_input=user_input, errors=self.errors)

            await self.check_terms_of_use(AppleAcct, action_item, user_input)

            self.errors['account_selected'] = ''

            #.......................................................................
            # Handle a request new code or or sent the code to Apple actions
            if action_item == 'send_auth_code':
                auth_successful = await self.send_auth_code_back_to_apple(AppleAcct, ui_auth_code)

                if auth_successful is False:
                    return await self.async_step_reauth(errors=self.errors)

                if self.is_another_auth_code_needed() is False:
                    if self.is_config_flow_handler:
                        # Close the config flow reauth window
                        return self._reauth_goto_previous()
                    else:
                        self._clear_ha_reauth_banner()

            #.......................................................................
            elif action_item == 'request_auth_code':
                self.errors[CONF_AUTH_CODE] = 'auth_code_requested'
                auth_method = f"{self.AppleAcct.auth_method.title()}"
                if AppleAcct.auth_method_PUSH is False:
                    auth_method = f": {self.AppleAcct.auth_method_info}"
                post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, "
                            f"Requested a new Auth Code, {auth_method}")

                await self.async_request_new_auth_code(AppleAcct)

                if AppleAcct.response_code == 423:
                    self.errors[CONF_AUTH_CODE] = 'auth_code_requested_423'

                return await self.async_step_reauth(user_input=user_input, errors=self.errors)

            log_debug_msg(  f"⭐ REAUTH (From={return_to_step_id}, {action_item}) > "
                            f"UserInput-{user_input}, Errors-{errors}")

            if user_input and 'account_selected' in user_input:
                reauth_username = user_input['account_selected']

            return self.async_show_form(step_id='reauth',
                            data_schema=forms.form_reauth(self, reauth_username=reauth_username),
                            errors=self.errors)

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    def _unpack_ui_reauth(self, user_input):
        if user_input is None: return

        if 'terms_of_use' not in user_input: user_input['terms_of_use'] = False
        user_input = utils_cf.strip_spaces(user_input, [CONF_AUTH_CODE])
        user_input = utils_cf.option_text_to_parm( user_input,
                                                'account_selected',
                                                self.apple_acct_auth_items_by_username)

        return user_input

#--------------------------------------------------------------------
    async def async_request_new_auth_code(self, AppleAcct):
        '''
        Reset the current session and authenticate to restart pyicloud_ic3
        and enter a new Authentication code

        The username & password are specified in case the Apple acct is not logged
        into because of an error
        '''
        try:
            post_event(f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.username_id}, Authentication Inprocess")

            if AppleAcct.is_auth_alert_displayed is False:
                AppleAcct.is_auth_alert_displayed = True

            if (AppleAcct.auth_method_PUSH is False
                    and AppleAcct.auth_method not in AppleAcct.conf_apple_acct[CONF_AUTH_METHODS]):
                await self._update_auth_method(PUSH)

            if AppleAcct.auth_method_PUSH:
                # AppleAcct.iCloudSession.cookies.list()
                await Gb.hass.async_add_executor_job(AppleAcct.untrust_session_and_authenticate)
                await Gb.hass.async_add_executor_job(AppleAcct.request_auth_code_via_push_notification)

            # Send a code via a text message
            elif AppleAcct.auth_method_TEXT:
                await Gb.hass.async_add_executor_job(AppleAcct.untrust_session_and_authenticate)
                await Gb.hass.async_add_executor_job(AppleAcct.request_auth_code_via_text_msg, AppleAcct.auth_method)

            elif AppleAcct.auth_method_HWKEY:
                pass

            # await async_get_fido2_key_names(AppleAcct)
            # AppleAcct.auth_code = None

            AppleAcct.was_auth_code_requested = True
            Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)
            post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.username_id}, "
                        f"Waiting for the Authentication Code to be entered")
            alert_msg = f"Apple Authentication needed ({secs_to_hhmm(AppleAcct.is_auth_code_needed_secs)})"
            update_alert_sensor(AppleAcct.username_id, alert_msg)

        except Exception as err:
            login_err = str(err)
            log_exception(err)


#--------------------------------------------------------------------
    async def send_auth_code_back_to_apple(self, AppleAcct, auth_code, force_PUSH=False):
        '''
        Handle the send_authentication_code action. This is called from the ConfigFlow and OptionFlow
        reauth steps in each Flow. This provides this function with the appropriate data and return objects.
        '''
        try:
            AppleAcct = self.AppleAcct
            AppleAcct.was_ha_auth_code_alert_sent = False

            if AppleAcct.auth_method_PUSH or force_PUSH:
                auth_successful = await Gb.hass.async_add_executor_job(
                                        AppleAcct.validate_2fa_push_popup_window_code,
                                        auth_code)

            elif AppleAcct.auth_method_TEXT:
                auth_successful = await Gb.hass.async_add_executor_job(
                                        AppleAcct.validate_2fa_text_code,
                                        auth_code)

            if auth_successful is False:
                if auth_code != '':
                    AppleAcct.was_auth_code_requested = False
                    self.errors[CONF_AUTH_CODE] = 'auth_code_invalid'
                    post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, "
                                f"Auth Code invalid "
                                f"({auth_code})")
                return False

        except Exception as err:
            log_exception(err)

            return False

        post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, "
                    f"Authentication Successful")

        # Refresh the device list if the apple acct is being setup for the first time
        # If AppleAcct.device_id_by_icloud_dname is empty, a Authentication code was needed
        # when first logged in and the apple acct data was not authenticated and it's
        # device data was never loaded/initialized by refreshed_icloud_data. This
        # prevents the device's list tables to ever be initialized and location data
        # is not available. Do this now.
        if (is_empty(AppleAcct.device_id_by_icloud_dname)
                or (AppleAcct.terms_of_use_update_needed and AppleAcct.terms_of_use_accepted)):
            await async_finish_authentication_and_data_refresh(self)

        await lists.build_icloud_device_selection_list(self)
        lists.build_apple_accounts_auth_list(self)

        self.errors[CONF_AUTH_CODE] = 'auth_code_accepted'
        AppleAcct.was_auth_code_requested = False
        Gb.EvLog.clear_greenbar_msg()
        Gb.is_force_icloud_update = True
        update_alert_sensor(AppleAcct.username_id, '')

        if self.is_another_auth_code_needed():
            self.errors['action_items'] = 'auth_code_another_auth_needed'
        else:
            self.errors['action_items'] = ''

        return True

#------------------------------------------------------------------------------
    async def _initialize_options_flow_reauth(self, user_input, return_to_step_id):
        '''
        Sets self.return_to_step_id_1 and performs any per-class initialisation.
        This runs the first tune the reauth is entered
        '''
        self.return_to_step_id_1 = return_to_step_id or self.return_to_step_id_1 or 'menu_0'
        await self.async_write_icloud3_configuration_file()
        return user_input

#------------------------------------------------------------------------------
    def _reauth_goto_previous(self):
        '''Flow result returned when the user navigates back from reauth.'''
        log_debug_msg(  f"⭐ REAUTH EXIT {self.step_id.upper()} ({self.return_to_step_id_1}) > "
                            f"Errors-{self.errors}")

        return_to_step_id = f'{self.return_to_step_id_1}'
        self.return_to_step_id_1 = ''

        return self.async_show_form(step_id=return_to_step_id,
                                    data_schema=self.return_to_step_id_form(return_to_step_id),
                                    errors=self.errors)

#--------------------------------------------------------------------
    def get_username_needing_reauth(self, reauth_username=None):
        '''
        Return the:
            - first Apple Acct and username needing reauthentication
            - or the selectedApple Acct and username
            - or the first Apple Acct  and username
        '''
        if reauth_username:
            AppleAcct = self.AppleAcct = Gb.AppleAcct_needing_reauth_via_ha = \
                        Gb.AppleAcct_by_username[reauth_username]
            return AppleAcct, reauth_username

        if Gb.AppleAcct_needing_reauth_via_ha:
            AppleAcct = self.AppleAcct = Gb.AppleAcct_needing_reauth_via_ha
            return AppleAcct, AppleAcct.username

        if self.is_another_auth_code_needed():
            AppleAcct = self.AppleAcct = Gb.AppleAcct_needing_reauth_via_ha
            return AppleAcct, AppleAcct.username

        # Get first username and it's AppleAcct
        reauth_username = list(Gb.AppleAcct_by_username.keys())[0]
        return  Gb.AppleAcct_by_username[reauth_username], reauth_username

#------------------------------------------------------------------------------
    def is_another_auth_code_needed(self):
        for AppleAcct in Gb.AppleAcct_by_username.values():
            if AppleAcct.is_auth_code_needed:
                Gb.AppleAcct_needing_reauth_via_ha = AppleAcct
                Gb.AppleAcct_needing_reauth_via_ha.was_ha_auth_code_alert_sent = True

                return True
        else:
            if Gb.AppleAcct_needing_reauth_via_ha:
                Gb.AppleAcct_needing_reauth_via_ha = None
                clear_AppleAcct_auth_alerts()
                post_greenbar_msg('')

        return False

#------------------------------------------------------------------------------
    def _display_ha_reauth_banner(self):
        Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)

#------------------------------------------------------------------------------
    def _clear_ha_reauth_banner(self):
        '''
        Clear the orange Reauthentication notification button that will launch
        the ConfigFlow step_reauth routine
        '''

        Gb.AppleAcct_needing_reauth_via_ha = None
        clear_AppleAcct_auth_alerts()
        if self.is_config_flow_handler:
            return

        try:
            for flow in Gb.hass.config_entries.flow.async_progress():
                if (flow['handler'] == 'icloud3'
                        and flow.get('context', {}).get('source') == 'reauth'):
                    Gb.hass.config_entries.flow.async_abort(flow['flow_id'])
                    return

        except Exception as err:
            pass
            # log_exception(err)

#------------------------------------------------------------------------------
    async def check_terms_of_use(self, AppleAcct, action_item, user_input):
        if (AppleAcct
                and AppleAcct.terms_of_use_update_needed
                and user_input['terms_of_use']):
            AppleAcct.terms_of_use_accepted = True

        if (action_item == 'accept_terms_of_use'
                and user_input['terms_of_use']
                and AppleAcct.terms_of_use_update_needed):
            await async_finish_authentication_and_data_refresh(self)


    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #            REAUTH CODE FROM APPLE.COM LOGIN
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_reauth_code_from_applecom_login(self, user_input=None, errors=None):

        self.step_id = 'reauth_code_from_applecom_login'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        log_debug_msg(  f"⭐ {self.step_id.upper()} ({action_item}) > "
                        f"UserInput-{user_input}, Errors-{errors}")

        if user_input is None:
            return self.async_show_form(step_id='reauth_code_from_applecom_login',
                        data_schema=forms.form_reauth_code_from_applecom_login(self),
                        errors=self.errors,
                        last_step=True)

        user_input = utils_cf.strip_spaces(user_input, [CONF_AUTH_CODE])

        if action_item == 'send_auth_code':
            auth_successful = await self.async_send_applecom_login_auth_code(user_input)

            if auth_successful is False:
                return await self.async_step_reauth_code_from_applecom_login(errors=self.errors)

        return self.async_show_form(step_id='reauth',
                                    data_schema=forms.form_reauth(self),
                                    errors=self.errors)

#---------------------------------------------------------------------------------------------------
    async def async_send_applecom_login_auth_code(self, user_input=None, errors=None):
        '''
        Send code back to apple when on the Auth Code from apple,com manual instructions
        screen
        '''

        AppleAcct  = self.AppleAcct
        user_input = utils_cf.strip_spaces(user_input, [CONF_AUTH_CODE])
        ui_auth_code = user_input.get(CONF_AUTH_CODE, '')

        log_debug_msg(f"⭐ {self.step_id.upper()} Handler > UserInput-{user_input}, Errors-{errors}")

        if (ui_auth_code == ''
                or len(ui_auth_code) != 6
                or is_number(ui_auth_code) is False):
            return user_input

        await Gb.hass.async_add_executor_job(self.AppleAcct.untrust_session_and_authenticate)
        auth_successful = await self.send_auth_code_back_to_apple(AppleAcct, ui_auth_code, force_PUSH=True)

        return auth_successful


    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #            CHANGE AUTH METHOD
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_reauth_change_auth_method(self,
                        user_input=None, errors=None, reauth_username=None):

        self.step_id = 'reauth_change_auth_method'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        log_debug_msg(  f"⭐ {self.step_id.upper()} ({action_item}) > "
                        f"UserInput-{user_input}, Errors-{errors}")

        if user_input is None:
            return self.async_show_form(step_id='reauth_change_auth_method',
                        data_schema=forms.form_reauth_change_auth_method(self, reauth_username),
                        errors=self.errors,
                        last_step=True)

        user_input = utils_cf.option_text_to_parm( user_input,
                                                'auth_method',
                                                self.aa_auth_methods_by_auth_method)

        auth_method = user_input['auth_method']
        if self.AppleAcct.auth_method != auth_method:
            await self._update_auth_method(auth_method)

        self.apple_acct_reauth_username = reauth_username

        return self.async_show_form(step_id='reauth',
                        data_schema=forms.form_reauth(self, reauth_username=reauth_username),
                        errors=self.errors)

#------------------------------------------------------------------------------
    async def _update_auth_method(self, auth_method):
        self.AppleAcct.conf_apple_acct[CONF_AUTH_METHODS][CONF_LAST_METHOD] = auth_method
        Gb.OptionsFlowHandler.update_config_file_tracking(force_config_update=True)
        await config_file.async_write_icloud3_configuration_file()
