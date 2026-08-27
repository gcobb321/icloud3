
import asyncio

from ...global_variables    import GlobalVariables as Gb
from ...const               import (CONF_AUTH_CODE, CONF_AUTH_METHODS, CURRENT, PUSH, HWKEY,
                                    EVLOG_NOTICE, )
from ...utils.utils         import (instr, is_number, is_empty, isnot_empty, dict_del, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ...utils.time_util     import (secs_to_hhmm, )

from ...apple_acct          import apple_acct_support_cf as aascf
from ...startup             import config_file

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
    async def async_step_reauth(self, user_input=None, errors=None, reauth_username='',):

        try:
            self.step_id = 'reauth'
            self.errors = errors or utils_cf.set_header_msg(self) or {}
            self.errors_user_input = {}
            self.errors_info_msg = None
            if self.errors.get('base', '') == 'auth_code_accepted':
                self.errors[CONF_AUTH_CODE] = self.errors.pop('base')

            user_input, action_item = utils_cf.action_text_to_item(self, user_input)

            if user_input:
                user_input = self._unpack_ui_reauth(user_input)
                AppleAcct, reauth_username = \
                        self.get_AppleAcct_reauth_needed(user_input.get('account_selected'))
                self.AppleAcct = AppleAcct
                lists.build_aa_auth_methods_list(self, AppleAcct)

            utils_cf.log_step_info(self, user_input, action_item, 'ENTER')

            # Set up the reauthentication process based on the entry point - iCloud3_ConfigFlow
            # from the HA notifications or iCloud3_OptionsFlow from the iCloud3 Menu or the
            # Apple Account screen.
            #   ConfigFlow  - Initialize on the first pass ('is_reauth_initialized' is False).
            #                 The ConfigFlow is exited (_exit_reauth_screen_handler) when reauth is done.
            #   OptionsFlow - The calling step added it's step_id to the 'return_to_step_id' list
            #                 before branching here. It is removed and redisplayed when reauth is done.
            if self.menu_item == 'config_flow_reauth':
                if self.is_reauth_initialized is False:
                    await self._initialize_config_flow_reauth()
                    user_input = None

            elif user_input is None:
                await self.async_write_icloud3_configuration_file()

            if Gb.internet_error:
                self.errors['base'] = 'internet_error_no_change'

            if len(Gb.conf_apple_accounts) == 0:
                self.header_msg = 'apple_acct_not_set_up'

            elif self.AppleAcct is None:
                self.errors['account_selected'] = 'apple_acct_not_logged_into'

            if user_input is None or (self.errors and action_item is None):
                return self.async_show_form(step_id='reauth',
                            data_schema=forms.form_reauth(self, reauth_username=reauth_username),
                            errors=self.errors)

        except Exception as err:
            log_exception(err)

        try:
            ui_auth_code = user_input.get(CONF_AUTH_CODE, '')
            self.errors[CONF_AUTH_CODE] = ''

            utils_cf.log_step_info(self, user_input, action_item, 'ENTER')

            if self.AppleAcct is None:
                self.errors['account_selected'] = 'reauth_apple_acct_unknown'
                self.errors[CONF_AUTH_CODE] = ''
                return await self.async_step_reauth(user_input=user_input, errors=self.errors)

            #.......................................................................
            self._set_or_reset_ha_orange_reauth_button()
            match action_item:
                case 'auth_code_from_applecom_login':
                    if AppleAcct.is_auth_method_HWKEY is False:
                        return await self.async_step_reauth_code_from_applecom_login()

                case 'change_auth_method':
                    return await self.async_step_reauth_change_auth_method(reauth_username=reauth_username)

                case 'exit_ha_reconfigure_reauth':
                    return self.ha_reconfigure_reauth_exit()

                case 'reauth' | 'menu':
                    return await self.async_step_menu()

                case 'rtn_apple_accounts':
                    return await self.async_step_apple_accounts()

                case 'config_flow_reauth' | 'exit_ha_reconfigure_reauth':
                    return self.ha_reconfigure_reauth_exit()

            #.......................................................................
            if AppleAcct.is_auth_method_PUSH or AppleAcct.is_auth_method_TEXT:
                if (action_item == 'send_auth_code'
                        and ui_auth_code == ''):
                    action_item = 'request_auth_code'

                if (ui_auth_code != ''
                        and len(ui_auth_code) == 6
                        and is_number(ui_auth_code)):
                    action_item = 'send_auth_code'

            if (Gb.internet_error and action_item != 'menu'):
                self.errors['base'] = 'internet_error_no_change'
                user_input = None
                return await self.async_step_reauth(user_input=user_input, errors=self.errors)

            await self.check_terms_of_use(AppleAcct, action_item, user_input)

            self.errors['account_selected'] = ''

            #.......................................................................
            try:
                if action_item == 'request_auth_code':

                    # Verify the hwkey is plugged into the HA server before hwkey authentication
                    # if AppleAcct.hwkey_names != '':
                    #     AppleAcct.conf_apple_acct[CONF_AUTH_METHODS][CURRENT] = HWKEY
                    if AppleAcct.is_auth_method_PUSH and AppleAcct.hwkey_names != '':
                        self.update_auth_method(HWKEY)

                    if AppleAcct.is_auth_method_HWKEY:
                        is_hwkey_key_available = \
                                await Gb.hass.async_add_executor_job(AppleAcct.HwKey.is_hwkey_key_available)
                        log_info_msg(   f"{AppleAcct.username_id} > Check Security Key inserted, "
                                        f"Result-{is_hwkey_key_available}")
                        if is_hwkey_key_available is False:
                            self.errors[CONF_AUTH_CODE] = 'hwkey_auth_not_avail'
                            return await self.async_step_reauth(user_input=user_input, errors=self.errors)

                    # Request the auth code or tell user to click Auth button on screen
                    await self.request_auth_code_or_trigger_hwkey_keypress(AppleAcct)

                    auth_method = f"{AppleAcct.current_auth_method.title()}"
                    auth_msg_method = auth_method.upper()

                    if AppleAcct.is_auth_method_TEXT or AppleAcct.is_auth_method_HWKEY:
                        auth_method = f": {self.AppleAcct.current_auth_method_value}"

                    if AppleAcct.is_auth_method_TEXT:
                        auth_msg_method = f"{auth_msg_method[:4]}{auth_method}"

                    post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, "
                                f"Requested a new Auth Code, {auth_method}")

                    # The 423 (Too many codes requested) message must win - the
                    # generic 'code was requested, waiting for it' message below
                    # would otherwise overwrite it and tell the user to wait for
                    # a code that Apple has refused to send.
                    if AppleAcct.response_code == 423:
                        self.errors[CONF_AUTH_CODE] = 'auth_code_requested_423'

                    elif AppleAcct.is_auth_method_PUSH or AppleAcct.is_auth_method_TEXT:
                        self.errors[CONF_AUTH_CODE] = 'auth_code_requested'

                    elif AppleAcct.is_auth_method_HWKEY:
                        user_input[CONF_AUTH_CODE] = f"Security Key used for Authentication ({AppleAcct.HwKey.hwkey_device})"
                        self.errors[CONF_AUTH_CODE] = 'hwkey_waiting_for_keypress'

                    # return await self.async_step_reauth(user_input=user_input, errors=self.errors)
                    return self.async_show_form(step_id='reauth',
                                data_schema=forms.form_reauth(self, user_input=user_input,
                                                                reauth_username=AppleAcct.username),
                                errors=self.errors,
                                description_placeholders={'auth_method': auth_msg_method})

            except Exception as err:
                log_exception(err)

            #.......................................................................
            # Handle a request new code or or sent the code to Apple actions
            try:
                if action_item == 'send_auth_code':
                    auth_successful = await self.send_auth_code_or_assert_hwkey_keypress(AppleAcct, ui_auth_code)

                    if auth_successful is False:
                        return self.async_show_form(step_id='reauth',
                                    data_schema=forms.form_reauth(self, reauth_username=AppleAcct.username),
                                    errors=self.errors,
                                    description_placeholders=self.errors_info_msg)

                    if self.is_another_auth_code_needed() is False:
                        self._reset_ha_orange_reauth_button()

                        # Called from ConfigFlow Class via the Orange HA Reauth button
                        # All done, return to HA
                        if self.menu_item == 'config_flow_reauth':
                            return self.ha_reconfigure_reauth_exit()

                        self.errors['base'] = self.header_msg = 'auth_code_accepted'
                        # Display import_apple_devices screen if auth is done and that is
                        # the screen to display next
                        if aascf.any_conf_devices_for_apple_acct(AppleAcct.username) is False:
                            return await self.async_step_import_apple_devices()

                        match self.menu_item:
                            case 'reauth':
                                # self.errors[CONF_AUTH_CODE] = 'auth_code_accepted'
                                return await self.async_step_reauth()
                            case 'apple_accounts':
                                return await self.async_step_apple_accounts()
                            case 'config_flow_reauth' | 'exit_ha_reconfigure_reauth':
                                return self.ha_reconfigure_reauth_exit()
                            case _:
                                return await self.async_step_menu()

            except Exception as err:
                log_exception(err)

            utils_cf.log_step_info(self, user_input, action_item, 'SEND')

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
            log_info_msg(f"{AppleAcct.username_id} > Request Auth code, {AppleAcct.current_auth_method}")

            if AppleAcct.is_auth_alert_displayed is False:
                AppleAcct.is_auth_alert_displayed = True

            if (AppleAcct.is_auth_method_PUSH is False
                    and AppleAcct.current_auth_method not in AppleAcct.conf_apple_acct[CONF_AUTH_METHODS]):
                await self.update_auth_method(PUSH)

            if AppleAcct.is_auth_method_HWKEY:
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
                    await self.update_auth_method(PUSH)
                    await Gb.hass.async_add_executor_job(AppleAcct.request_auth_code_via_push_notification)
                    waiting_msg = 'Waiting for the Auth Code to be entered'
                else:
                    waiting_msg = 'Waiting for the Security Key keypress'

            elif AppleAcct.is_auth_method_PUSH:
                await Gb.hass.async_add_executor_job(AppleAcct.untrust_session_and_authenticate)
                await Gb.hass.async_add_executor_job(AppleAcct.request_auth_code_via_push_notification)
                waiting_msg = 'Waiting for the Auth Code to be entered'

            elif AppleAcct.is_auth_method_TEXT:
                # Apple sends the trusted-device push popup when the 2FA challenge
                # is CREATED by the password sign-in, not when a code is requested.
                # If the previous sign-in's challenge is still live, request the
                # text code against it so a resend does not pop up a new
                # notification on every device on the account.
                text_code_sent = False
                if AppleAcct.is_2fa_challenge_session_live:
                    text_code_sent = await Gb.hass.async_add_executor_job(
                                            AppleAcct.request_auth_code_via_text_msg,
                                            AppleAcct.current_auth_method)
                    log_info_msg(   f"{AppleAcct.username_id} > Reused the 2fa challenge for the "
                                    f"Text Auth code, Successful-{text_code_sent}")

                # A 423 is Apple's account level 'Too many codes sent' throttle
                # (serviceError -22981), not a problem with this signin session.
                # Signing in again would only create another challenge, send
                # another device popup and spend another request against the
                # throttle, so the retry is skipped when that is the reason.
                if (text_code_sent is False
                        and AppleAcct.response_code != 423):
                    await Gb.hass.async_add_executor_job(AppleAcct.untrust_session_and_authenticate)
                    text_code_sent = await Gb.hass.async_add_executor_job(
                                            AppleAcct.request_auth_code_via_text_msg,
                                            AppleAcct.current_auth_method)

                if text_code_sent:
                    waiting_msg = 'Waiting for the Text Auth Code to be entered'
                elif AppleAcct.response_code == 423:
                    post_alert(f"Apple Acct > {AppleAcct.account_owner}, Apple has temporarily "
                                f"stopped sending Text Authentication Codes to "
                                f"{AppleAcct.current_auth_method_value} (too many codes "
                                f"requested). Use the code from the device popup or use the "
                                f"Push Notification authentication method")
                    waiting_msg = ('Apple is not sending Text Auth Codes right now, enter the '
                                    'code from the device popup or retry later')
                else:
                    post_alert(f"Apple did not send the Text Authentication Code to "
                                f"{AppleAcct.current_auth_method_value}, "
                                f"{AppleAcct.response_code_desc}")
                    waiting_msg = ('Apple did not send the Text Auth Code, enter the code '
                                    'from the device popup or retry later')


            AppleAcct.was_auth_code_requested = True
            Gb.AppleAcct_reauth_needed = AppleAcct

            #  Display the orange 'Reconfigure' button on the HA Settings screen.
            #  Skip it while the Configure (OptionsFlow) dialog is open - starting the HA
            #  reauth ConfigFlow also displays the ConfigFlow's reauth screen on top of
            #  this one. The button is set when iCloud3 restarts on the Configure exit.
            if Gb.config_entry and Gb.is_config_flow_open is False:
                self._set_ha_orange_reauth_button()

            post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.username_id}, {waiting_msg}")
            alert_msg = f"Apple Authentication needed ({secs_to_hhmm(AppleAcct.is_reauth_needed_secs)})"
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
            log_info_msg(f"{AppleAcct.username_id} > Send Auth code, {AppleAcct.current_auth_method}")

            if AppleAcct.is_auth_method_PUSH or force_PUSH:
                auth_successful = await Gb.hass.async_add_executor_job(
                                        AppleAcct.validate_2fa_push_popup_window_code,
                                        auth_code)

            elif AppleAcct.is_auth_method_TEXT:
                auth_successful = await Gb.hass.async_add_executor_job(
                                        AppleAcct.validate_2fa_text_code,
                                        auth_code)

            elif AppleAcct.is_auth_method_HWKEY:
                auth_successful = await Gb.hass.async_add_executor_job(
                                        AppleAcct.authenticate_with_hwkey)

                if auth_successful is False:
                    self.errors_info_msg = {'info_msg': AppleAcct.HwKey.error_msg}

            self.errors[CONF_AUTH_CODE], evlog_msg = self._finish_auth_status_msg(AppleAcct, auth_successful)

            post_event(f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, {evlog_msg}")
            log_info_msg(f"{AppleAcct.account_owner} > Send Auth code, {AppleAcct.current_auth_method}, "
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
            await aascf.async_finish_authentication_and_data_refresh(self)

        await lists.build_icloud_device_selection_list(self)
        lists.build_apple_accounts_auth_list(self)

        Gb.AppleAcct_reauth_needed = None
        Gb.EvLog.clear_greenbar_msg()
        Gb.is_force_icloud_update = True
        AppleAcct.was_auth_code_requested = False
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
            await aascf.async_finish_authentication_and_data_refresh(self)

        await lists.build_icloud_device_selection_list(self)
        lists.build_apple_accounts_auth_list(self)

        if AppleAcct.is_auth_method_HWKEY:
            self.errors[CONF_AUTH_CODE] = 'hwkey_auth_succeeded'
        else:
            self.errors[CONF_AUTH_CODE] = 'auth_code_accepted'

        Gb.EvLog.clear_greenbar_msg()
        Gb.is_force_icloud_update = True
        update_alert_sensor(AppleAcct.username_id, '')

#------------------------------------------------------------------------------
    def _finish_auth_status_msg(self, AppleAcct, auth_successful):

        if auth_successful:
            if AppleAcct.is_auth_method_HWKEY:
                display_msg = 'hwkey_auth_succeeded'
                evlog_msg   = 'Security Key Authentication Successful'
            else:
                display_msg = 'auth_code_accepted'
                evlog_msg   =  'Authentication Code Accepted'
        else:
            AppleAcct.was_auth_code_requested = False
            if AppleAcct.is_auth_method_HWKEY:
                if self.AppleAcct.HwKey.hwkey_device is None:
                    display_msg = 'hwkey_auth_not_avail'
                else:
                    display_msg = 'hwkey_auth_failed'
                evlog_msg   = AppleAcct.HwKey.error_msg
            else:
                AppleAcct.was_auth_code_requested = True
                display_msg = 'auth_code_invalid'
                if AppleAcct.is_auth_method_TEXT:
                    display_msg += '_text'

                evlog_msg   = f"Invalid Authentication Code"

        return display_msg, evlog_msg

#------------------------------------------------------------------------------
    async def _exit_reauth_screen_handler(self):
        '''Go to the next screen or back to the menu'''

        match self.menu_item:
            case 'reauth':
                return await self.async_step_menu()
            case 'rtn_apple_accounts':
                return await self.async_step_apple_accounts()
            case 'config_flow_reauth' | 'exit_ha_reconfigure_reauth':
                return self.ha_reconfigure_reauth_exit()

        return await self.async_step_menu()

#--------------------------------------------------------------------
    def get_AppleAcct_reauth_needed(self, reauth_username=None):
        '''
        Return the:
            - first Apple Acct and username needing reauthentication
            - or the selectedApple Acct and username
            - or the first Apple Acct and username
        '''
        if reauth_username:
            AppleAcct = Gb.AppleAcct_reauth_needed = \
                        Gb.AppleAcct_by_username[reauth_username]
            return AppleAcct, AppleAcct.username

        if Gb.AppleAcct_reauth_needed and Gb.AppleAcct_reauth_needed.is_reauth_needed:
            return Gb.AppleAcct_reauth_needed, Gb.AppleAcct_reauth_needed.username

        for username, _AppleAcct in Gb.AppleAcct_by_username.items():
            if _AppleAcct.is_reauth_needed:
                Gb.AppleAcct_reauth_needed = _AppleAcct
                return _AppleAcct, _AppleAcct.username

        Gb.AppleAcct_reauth_needed = None
        first_AppleAcct = list(Gb.AppleAcct_by_username.values())[0]

        return first_AppleAcct, first_AppleAcct.username

#------------------------------------------------------------------------------
    def is_another_auth_code_needed(self):
        _AppleAcct, _ = self.get_AppleAcct_reauth_needed()

        return _AppleAcct.is_reauth_needed

#------------------------------------------------------------------------------
    def _set_or_reset_ha_orange_reauth_button(self):

        if Gb.AppleAcct_reauth_needed is None:
            self._reset_ha_orange_reauth_button()
            return

        if Gb.AppleAcct_reauth_needed.is_reauth_needed is False:
            self._reset_ha_orange_reauth_button()
            return

        Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)

#------------------------------------------------------------------------------
    def _set_ha_orange_reauth_button(self):
        if Gb.AppleAcct_reauth_needed:
            Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)

#------------------------------------------------------------------------------
    def _reset_ha_orange_reauth_button(self):
        '''
        Clear the orange Reauthentication notification button that will launch
        the ConfigFlow step_reauth routine
        '''

        Gb.AppleAcct_reauth_needed = None
        aascf.clear_AppleAcct_auth_alerts()
        post_greenbar_msg('')

        if self.menu_item == 'config_flow_reauth':
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
            await aascf.async_finish_authentication_and_data_refresh(self)


    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #            REAUTH CODE FROM APPLE.COM LOGIN
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_reauth_code_from_applecom_login(self, user_input=None, errors=None):

        self.step_id = 'reauth_code_from_applecom_login'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        utils_cf.log_step_info(self, user_input, action_item)

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

        utils_cf.log_step_info(self, user_input, 'appledotcomlogin')

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

        if user_input:
            user_input = self._unpack_ui_reauth(user_input)
            # reauth_username = reauth_username or user_input['account_selected']
            AppleAcct, reauth_username = \
                        self.get_AppleAcct_reauth_needed(user_input.get('account_selected'))
            lists.build_aa_auth_methods_list(self, AppleAcct)

            utils_cf.log_step_info(self, user_input, action_item)

        AppleAcct = self.AppleAcct
        if user_input is None:
            return self.async_show_form(step_id='reauth_change_auth_method',
                        data_schema=forms.form_reauth_change_auth_method(self, reauth_username),
                        errors=self.errors,
                        last_step=True)


        if action_item == 'refresh_hwkey_names':
            await Gb.hass.async_add_executor_job(AppleAcct.refresh_hwkey_names_preserve_trust)

            AppleAcct.conf_apple_acct[CONF_AUTH_METHODS][HWKEY] = AppleAcct.hwkey_names
            if AppleAcct.is_auth_method_PUSH and AppleAcct.hwkey_names != '':
                    self.update_auth_method(HWKEY)

            await config_file.async_write_icloud3_configuration_file()
            lists.build_aa_auth_methods_list(self, AppleAcct)

            if (is_empty(AppleAcct.trusted_phone_data)
                    and AppleAcct.hwkey_names == ''):
                self.errors['base'] = 'text_or_hwkey_none'

            return self.async_show_form(step_id='reauth_change_auth_method',
                        data_schema=forms.form_reauth_change_auth_method(self, reauth_username),
                        errors=self.errors,
                        last_step=True)

        auth_method = user_input.get('auth_method', '')
        await self.update_auth_method(auth_method)

        return self.async_show_form(step_id='reauth',
                        data_schema=forms.form_reauth(self, reauth_username=reauth_username),
                        errors=self.errors)

#------------------------------------------------------------------------------
    async def update_auth_method(self, auth_method):
        '''
        Update the Apple Acct auth method info
        '''
        self.AppleAcct.update_auth_method(auth_method)

        Gb.OptionsFlowHandler.update_config_file_tracking(force_config_update=True)
        await config_file.async_write_icloud3_configuration_file()
