
import asyncio

from ...global_variables    import GlobalVariables as Gb
from ...const               import (CONF_AUTH_CODE, CONF_AUTH_METHODS, CONF_LAST_METHOD, PUSH, HWKEY,
                                    EVLOG_NOTICE, )
from ...utils.utils         import (instr, is_number, is_empty, isnot_empty, dict_del, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ...utils.time_util     import (secs_to_hhmm, )

from ...startup             import config_file
from ...apple_acct.apple_acct_support_cf import (
                                    async_finish_authentication_and_data_refresh,
                                    clear_AppleAcct_auth_alerts, )
#                                    async_authenticate_with_hwkey, )

from .                      import form_reauth as forms
from .                      import form_config_flow as forms_cf
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
                                return_to_step_id=None, reauth_username=None,):


        try:
            self.step_id = 'reauth'
            self.errors = errors or {}
            self.errors_user_input = {}
            self.errors_info_msg = None

            user_input, action_item = utils_cf.action_text_to_item(self, user_input)

            if user_input:
                user_input = self._unpack_ui_reauth(user_input)
                self.AppleAcct, reauth_username = self.get_username_needing_reauth(user_input.get('account_selected'))
                AppleAcct = self.AppleAcct
                lists.build_aa_auth_methods_list(self, AppleAcct)

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
                # if AppleAcct:
                #     AppleAcct.was_auth_code_requested = False
                return self.async_show_form(step_id='reauth',
                            data_schema=forms.form_reauth(self, reauth_username=reauth_username),
                            errors=self.errors)

        except Exception as err:
            log_exception(err)

        try:

            ui_auth_code = user_input.get(CONF_AUTH_CODE, '')
            self.errors[CONF_AUTH_CODE] = ''

            log_debug_msg(  f"⭐ REAUTH HANDLER ({action_item}) > "
                            f"From-{return_to_step_id}, UserInput-{user_input}, Errors-{errors}")

            if self.AppleAcct is None:
                self.errors['account_selected'] = 'reauth_apple_acct_unknown'
                self.errors[CONF_AUTH_CODE] = ''
                return await self.async_step_reauth(user_input=user_input, errors=self.errors)

            if (reauth_username is None
                    or action_item in ['goto_previous', 'goto_ha_auth_done']):
                self.apple_acct_reauth_username = ''
                self.is_another_auth_code_needed()
                return self._reauth_goto_previous()

            if action_item == 'auth_code_from_applecom_login':
                return await self.async_step_reauth_code_from_applecom_login()

            if action_item == 'change_auth_method':
                return await self.async_step_reauth_change_auth_method(reauth_username=reauth_username)

            if AppleAcct.auth_method_PUSH or AppleAcct.auth_method_TEXT:
                if (action_item == 'send_auth_code'
                        and ui_auth_code == ''):
                    action_item = 'request_auth_code'

                if (ui_auth_code != ''
                        and len(ui_auth_code) == 6
                        and is_number(ui_auth_code)):
                    action_item = 'send_auth_code'

            if (Gb.internet_error and action_item != 'goto_previous'):
                self.errors['base'] = 'internet_error_no_change'
                user_input = None
                return await self.async_step_reauth(user_input=user_input, errors=self.errors)

            await self.check_terms_of_use(AppleAcct, action_item, user_input)

            self.errors['account_selected'] = ''

            #.......................................................................
            if action_item == 'request_auth_code':

                # Verify the fido2 hwkey is plugged into the HA server before hwkey authentication
                if AppleAcct.auth_method_HWKEY:
                    is_fido2_key_available = \
                            await Gb.hass.async_add_executor_job(AppleAcct.HwKey.is_fido2_key_available)
                    log_info_msg(   f"{AppleAcct.username_id} > Check Security Key inserted, "
                                    f"Result-{is_fido2_key_available}")
                    if is_fido2_key_available is False:
                        self.errors[CONF_AUTH_CODE] = 'hwkey_auth_not_avail'
                        return await self.async_step_reauth(user_input=user_input, errors=self.errors)

                # Request the auth code or tell user to click Auth button on screen
                await self.request_auth_code_or_trigger_hwkey_keypress(AppleAcct)

                auth_method = f"{AppleAcct.auth_method.title()}"

                if AppleAcct.auth_method_TEXT or AppleAcct.auth_method_HWKEY:
                    auth_method = f": {self.AppleAcct.auth_method_info}"

                post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, "
                            f"Requested a new Auth Code, {auth_method}")

                if AppleAcct.response_code == 423:
                    self.errors[CONF_AUTH_CODE] = 'auth_code_requested_423'

                if AppleAcct.auth_method_PUSH or AppleAcct.auth_method_TEXT:
                    self.errors[CONF_AUTH_CODE] = 'auth_code_requested'

                elif AppleAcct.auth_method_HWKEY:
                    user_input[CONF_AUTH_CODE] = f"Security Key used for Authentication ({AppleAcct.HwKey.fido2_device})"
                    self.errors[CONF_AUTH_CODE] = 'hwkey_waiting_for_keypress'

                # return await self.async_step_reauth(user_input=user_input, errors=self.errors)
                return self.async_show_form(step_id='reauth',
                            data_schema=forms.form_reauth(self, user_input=user_input,
                                                            reauth_username=AppleAcct.username),
                            errors=self.errors)

            #.......................................................................
            # Handle a request new code or or sent the code to Apple actions
            if action_item == 'send_auth_code':
                auth_successful = await self.send_auth_code_or_assert_hwkey_keypress(AppleAcct, ui_auth_code)

                if auth_successful is False:
                    return self.async_show_form(step_id='reauth',
                                data_schema=forms.form_reauth(self, reauth_username=AppleAcct.username),
                                errors=self.errors,
                                description_placeholders=self.errors_info_msg)
                    # return await self.async_step_reauth(errors=self.errors)

                if self.is_another_auth_code_needed() is False:
                    if self.is_config_flow_handler:
                        # Close the config flow reauth window
                        return self._reauth_goto_previous()
                    else:
                        self._clear_ha_reauth_banner()

            log_debug_msg(  f"⭐ REAUTH (From={return_to_step_id}, {action_item}) > "
                            f"UserInput-{user_input}, Errors-{errors}")

            if user_input and 'account_selected' in user_input:
                reauth_username = user_input['account_selected']

            return self.async_show_form(step_id='reauth',
                            data_schema=forms.form_reauth(self, reauth_username=reauth_username),
                            errors=self.errors,
                            description_placeholders=self.errors_info_msg)

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
        user_input = utils_cf.option_text_to_parm( user_input,
                                                'auth_method',
                                                self.aa_auth_methods_by_auth_method)

        return user_input

#--------------------------------------------------------------------
    async def request_auth_code_or_trigger_hwkey_keypress(self, AppleAcct):
        '''
        Reset the current session and authenticate to restart pyicloud_ic3
        and enter a new Authentication code

        The username & password are specified in case the Apple acct is not logged
        into because of an error
        '''
        try:
            post_event(f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.username_id}, Authentication Inprocess")
            log_info_msg(f"{AppleAcct.username_id} > Request Auth code, {AppleAcct.auth_method}")


            if AppleAcct.is_auth_alert_displayed is False:
                AppleAcct.is_auth_alert_displayed = True

            if (AppleAcct.auth_method_PUSH is False
                    and AppleAcct.auth_method not in AppleAcct.conf_apple_acct[CONF_AUTH_METHODS]):
                await self._update_auth_method(PUSH)

            if AppleAcct.auth_method_HWKEY:
                await Gb.hass.async_add_executor_job(AppleAcct.untrust_session_and_authenticate)

                # untrust_session_and_authenticate refreshes hwkey_names from the
                # live account (PasswordSRP path). If no security keys are not
                # registered anymore (e.g. the user deleted them from the Apple
                # Account), fall back to Push Notification authentication. The 6-digit code was
                # triggered by the above untrust_and_auth. It does not have to be done again.
                if AppleAcct.hwkey_names == '':
                    post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, "
                                f"No Security Keys are registered, "
                                f"Push Notification authentication will be used")
                    await self._update_auth_method(PUSH)
                    await Gb.hass.async_add_executor_job(AppleAcct.request_auth_code_via_push_notification)
                    waiting_msg = 'Waiting for the Auth Code to be entered'
                else:
                    waiting_msg = 'Waiting for the Security Key keypress'

            elif AppleAcct.auth_method_PUSH:
                await Gb.hass.async_add_executor_job(AppleAcct.untrust_session_and_authenticate)
                await Gb.hass.async_add_executor_job(AppleAcct.request_auth_code_via_push_notification)
                waiting_msg = 'Waiting for the Auth Code to be entered'

            elif AppleAcct.auth_method_TEXT:
                await Gb.hass.async_add_executor_job(AppleAcct.untrust_session_and_authenticate)
                await Gb.hass.async_add_executor_job(AppleAcct.request_auth_code_via_text_msg, AppleAcct.auth_method)
                waiting_msg = 'Waiting for the Text Auth Code to be entered'


            AppleAcct.was_auth_code_requested = True

            #  Display the orange 'Reconfigure' button on the HA Settings screen
            Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)

            post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.username_id}, {waiting_msg}")
            alert_msg = f"Apple Authentication needed ({secs_to_hhmm(AppleAcct.is_auth_code_needed_secs)})"
            update_alert_sensor(AppleAcct.username_id, alert_msg)

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    async def send_auth_code_or_assert_hwkey_keypress(self, AppleAcct, auth_code, force_PUSH=False):
        '''
        Handle the send_authentication_code action. This is called from the ConfigFlow and OptionFlow
        reauth steps in each Flow. This provides this function with the appropriate data and return objects.
        '''
        try:
            AppleAcct = self.AppleAcct
            AppleAcct.was_ha_auth_code_alert_sent = False
            auth_successful = True
            log_info_msg(f"{AppleAcct.username_id} > Send Auth code, {AppleAcct.auth_method}")

            if AppleAcct.auth_method_PUSH or force_PUSH:
                auth_successful = await Gb.hass.async_add_executor_job(
                                        AppleAcct.validate_2fa_push_popup_window_code,
                                        auth_code)

            elif AppleAcct.auth_method_TEXT:
                auth_successful = await Gb.hass.async_add_executor_job(
                                        AppleAcct.validate_2fa_text_code,
                                        auth_code)

            elif AppleAcct.auth_method_HWKEY:
                auth_successful = await Gb.hass.async_add_executor_job(
                                        AppleAcct.authenticate_with_hwkey)

                if auth_successful is False:
                    self.errors_info_msg = {'info_msg': AppleAcct.HwKey.error_msg}

            self.errors[CONF_AUTH_CODE], evlog_msg = self._finish_auth_status_msg(AppleAcct, auth_successful)

            post_event(f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, {evlog_msg}")
            log_info_msg(f"{AppleAcct.account_owner} > Send Auth code, {AppleAcct.auth_method}, "
                            f"Successful-{auth_successful}")

            if auth_successful is False:
                return False

        except Exception as err:
            log_exception(err)

            return False

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
    async def _finish_auth_success(self, AppleAcct):
        '''
        Shared success handler called by HWKEY, PUSH, and TEXT after
        successful auth.
        '''
        AppleAcct.was_auth_code_requested     = False
        AppleAcct.was_ha_auth_code_alert_sent = False
        if (is_empty(AppleAcct.device_id_by_icloud_dname)
                or (AppleAcct.terms_of_use_update_needed and AppleAcct.terms_of_use_accepted)):
            await async_finish_authentication_and_data_refresh(self)

        await lists.build_icloud_device_selection_list(self)
        lists.build_apple_accounts_auth_list(self)

        if AppleAcct.auth_method_HWKEY:
            self.errors[CONF_AUTH_CODE] = 'hwkey_auth_succeeded'
        else:
            self.errors[CONF_AUTH_CODE] = 'auth_code_accepted'

        Gb.EvLog.clear_greenbar_msg()
        Gb.is_force_icloud_update = True
        update_alert_sensor(AppleAcct.username_id, '')

#------------------------------------------------------------------------------
    def _finish_auth_status_msg(self, AppleAcct, auth_successful):

        if auth_successful:
            if AppleAcct.auth_method_HWKEY:
                display_msg = 'hwkey_auth_succeeded'
                evlog_msg   = 'Security Key Authentication Successful'
            else:
                display_msg = 'auth_code_accepted'
                evlog_msg   =  'Authentication Code Accepted'
        else:
            AppleAcct.was_auth_code_requested = False
            if AppleAcct.auth_method_HWKEY:
                if self.AppleAcct.HwKey.fido2_device is None:
                    display_msg = 'hwkey_auth_not_avail'
                else:
                    display_msg = 'hwkey_auth_failed'
                evlog_msg   = AppleAcct.HwKey.error_msg
            else:
                AppleAcct.was_auth_code_requested = True
                display_msg = 'auth_code_invalid'
                evlog_msg   =  f"Invalid Authentication Code"

        return display_msg, evlog_msg

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
        auth_successful = await self.send_auth_code_or_assert_hwkey_keypress(AppleAcct, ui_auth_code, force_PUSH=True)

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
        user_input = self._unpack_ui_reauth(user_input)
        reauth_username = reauth_username or user_input['account_selected']

        log_debug_msg(  f"⭐ {self.step_id.upper()} ({action_item}) > {reauth_username=}, "
                        f"UserInput-{user_input}, Errors-{errors}")

        if user_input is None:
            return self.async_show_form(step_id='reauth_change_auth_method',
                        data_schema=forms.form_reauth_change_auth_method(self, reauth_username),
                        errors=self.errors,
                        last_step=True)

        if action_item == 'refresh_hwkey_names':
            AppleAcct = self.AppleAcct
            await Gb.hass.async_add_executor_job(AppleAcct.refresh_hwkey_names_preserve_trust)
            AppleAcct.conf_apple_acct[CONF_AUTH_METHODS][HWKEY] = AppleAcct.hwkey_names
            await config_file.async_write_icloud3_configuration_file()
            lists.build_aa_auth_methods_list(self, AppleAcct)

            self.errors['base'] =   'hwkey_names_refreshed' if AppleAcct.hwkey_names != '' else \
                                    'hwkey_names_none'
            return self.async_show_form(step_id='reauth_change_auth_method',
                        data_schema=forms.form_reauth_change_auth_method(self, reauth_username),
                        errors=self.errors,
                        last_step=True)

        auth_method = user_input.get('auth_method', '')
        if auth_method and self.AppleAcct.auth_method != auth_method:
            await self._update_auth_method(auth_method)

        self.apple_acct_reauth_username = reauth_username

        return self.async_show_form(step_id='reauth',
                        data_schema=forms.form_reauth(self, reauth_username=reauth_username),
                        errors=self.errors)

#------------------------------------------------------------------------------
    async def _update_auth_method(self, auth_method):
        '''
        Update the Apple Acct auth method info
        '''

        self.AppleAcct.conf_apple_acct[CONF_AUTH_METHODS][CONF_LAST_METHOD] = auth_method
        self.AppleAcct.conf_apple_acct[CONF_AUTH_METHODS][HWKEY] = self.AppleAcct.hwkey_names

        Gb.OptionsFlowHandler.update_config_file_tracking(force_config_update=True)
        await config_file.async_write_icloud3_configuration_file()
