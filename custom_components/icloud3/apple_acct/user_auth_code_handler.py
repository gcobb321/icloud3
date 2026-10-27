#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   USER AUTH CODE HANDLER
#
#   Only an HA admin user can open the Configure and HA Repairs screens to enter an
#   Apple Acct Authentication Code. Each Apple Acct has a Request Auth Code button
#   entity and an Enter Auth Code text entity that can be placed on a dashboard so
#   any HA user can authenticate the Apple Acct.
#
#       button.auth_get_[name]  - Request a new code (async_user_auth_code_request)
#       text.auth_send_[name]   - Send the code to Apple when Enter is pressed
#                                   (async_user_auth_code_send). The text entity's
#                                   state is the status message, the code is never
#                                   saved in it.
#
#   The [name] is the Apple Acct name (AppleAcct.name). The apple_id is not saved on
#   the entities, it's auth_key (hash) is in the unique_id and Gb.apple_id_by_auth_key
#   maps the auth_key back to the apple_id.
#
#   Only the Push Notification and Text Message auth methods are supported. The
#   request/send code is from step_reauth's request_auth_code_or_trigger_hwkey_keypress
#   and send_auth_code_or_assert_hwkey_keypress.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from ..global_variables import GlobalVariables as Gb
from ..const            import (DOMAIN, EVLOG_NOTICE, EVLOG_ALERT, )
from ..const_config     import (CONF_APPLE_ACCT, )

from ..utils.utils      import (is_empty, apple_user, get_string_hash, )
from ..utils.messaging  import (post_event, post_greenbar_msg, update_alert_sensor,
                                log_info_msg, log_exception, _run_in_event_loop, )
from ..utils.time_util  import (time_now_secs, )

from .                  import apple_acct_support_cf as aascf

#--------------------------------------------------------------------
from types                  import SimpleNamespace
from homeassistant.core     import callback
from homeassistant.helpers  import entity_registry as er
from homeassistant.util     import slugify

AUTH_GET                    = 'auth_get'
AUTH_SEND                   = 'auth_send'
AUTH_CODE_REQUEST_WAIT_SECS = 60

# Enter Auth Code text entity status messages, these are displayed in the text box
AUTH_NEEDED         = 'Auth needed'
AUTH_NOT_NEEDED     = 'Auth not needed'
# Added to the status message in the text entity state so the code can be typed after
# it without clearing the text box. The status is removed when the code is sent.
STATUS_MSG_SPACER   = ' '
CODE_REQUESTED      = 'Code requested'
CHECKING_CODE       = 'Checking code'
CODE_ACCEPTED       = 'Code accepted'
CODE_INVALID        = 'Invalid code'
ENTER_6_DIGITS      = 'Enter 6-digit code'
TEXT_BLOCKED_423    = 'Text blocked (423)'
TEXT_NOT_SENT       = 'Text not sent'
SIGNIN_FAILED       = 'Sign-in failed'
NOT_LOGGED_IN       = 'Not logged in'
INTERNET_ERROR      = 'Internet error'
NOT_FOR_HWKEY       = 'Not for Security Key'
UNKNOWN_ACCT        = 'Unknown account'


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            CREATE & REMOVE THE ENTITIES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def make_auth_key(apple_id):
    '''
    The auth_key in the entity's unique_id. It is the same on every restart (sha256),
    the Python hash() value is not.
    '''
    return get_string_hash(apple_id.lower())[:8]

#--------------------------------------------------------------------
def create_auth_entities():
    '''
    Create the Request Auth Code button and Enter Auth Code text entities for the
    Apple Accts that do not have them. This is called at the end of Stage 4 and from
    the 5-sec loop for an Apple Acct that is logged into after startup.

    The entities are not created until the Apple Acct name is known. It is set from the
    accountLogin response, which is also what sets is_reauth_needed, so an Apple Acct
    can not need a code before it's name is available. The entity_id is set when the
    entity is added to the entity registry and HA keeps it after that.

    This runs in an executor thread, the entities are added in the event loop.
    '''
    if (Gb.button_async_add_entities is None
            or Gb.text_async_add_entities is None):
        return

    # Imported here, button and text import this module
    from ..button   import AuthGetButton
    from ..text     import AuthSendText

    AuthGetButtons = []
    AuthSendTexts  = []
    for apple_id, AppleAcct in list(Gb.AppleAcct_by_apple_id.items()):
        if _apple_acct_position(apple_id) == 0:
            continue

        auth_key = make_auth_key(apple_id)
        Gb.apple_id_by_auth_key[auth_key] = apple_id

        if (auth_key in Gb.AuthSendText_by_auth_key
                or (AppleAcct.name == '' and AppleAcct.login_successful is False)):
            continue

        auth_name = _auth_entity_name(AppleAcct)
        _AuthGetButton = Gb.AuthGetButton_by_auth_key[auth_key] = AuthGetButton(auth_key, auth_name)
        _AuthSendText  = Gb.AuthSendText_by_auth_key[auth_key]  = AuthSendText(auth_key, auth_name)
        AuthGetButtons.append(_AuthGetButton)
        AuthSendTexts.append(_AuthSendText)

        log_info_msg(   f"Apple Acct > {AppleAcct.account_owner}, User Auth Code Entities "
                        f"Created, {_AuthGetButton.entity_id}, {_AuthSendText.entity_id}")

    if AuthGetButtons:
        _run_in_event_loop(Gb.button_async_add_entities, AuthGetButtons)
        _run_in_event_loop(Gb.text_async_add_entities, AuthSendTexts)

#--------------------------------------------------------------------
def _auth_entity_name(AppleAcct):
    '''
    The name used in the entity_id and friendly name (GaryCobb):
        - The Apple Acct name. A name used by an Apple Acct before this one in the
            configuration gets this one's position number added (GaryCobb3)
        - The apple_id log filter text (gca**2**678@) if Apple did not return the
            fullName in the accountLogin dsInfo
    '''
    aa_pos = _apple_acct_position(AppleAcct.apple_id)

    if AppleAcct.name == '':
        email_id = apple_user(AppleAcct.apple_id)
        if len(email_id) < 4: email_id = '***'
        return f"{email_id[:3]}**{aa_pos}**{email_id[-3:]}"

    used_names = [slugify(_AuthSendText.auth_name)
                        for _AuthSendText in Gb.AuthSendText_by_auth_key.values()]
    used_names.extend([slugify(_AppleAcct.name)
                        for apple_id, _AppleAcct in Gb.AppleAcct_by_apple_id.items()
                        if (_AppleAcct.name
                                and 0 < _apple_acct_position(apple_id) < aa_pos)])

    if slugify(AppleAcct.name) in used_names:
        return f"{AppleAcct.name}{aa_pos}"

    return AppleAcct.name

#--------------------------------------------------------------------
def _apple_acct_position(apple_id):
    '''
    The Apple Acct's position (1, 2, ...) in the configuration, 0 if it is not there
    '''
    for aa_idx, conf_apple_acct in enumerate(Gb.conf_apple_accounts):
        if conf_apple_acct[CONF_APPLE_ACCT].lower() == apple_id.lower():
            return aa_idx + 1

    return 0

#--------------------------------------------------------------------
def remove_orphan_auth_entities():
    '''
    Remove the user auth code entities of an Apple Acct that is no longer in the
    configuration. Deleting an Apple Acct restarts iCloud3, this is done in Stage 4.
    '''
    _run_in_event_loop(_async_remove_orphan_auth_entities)

@callback
def _async_remove_orphan_auth_entities():
    try:
        conf_auth_keys = [make_auth_key(conf_apple_acct[CONF_APPLE_ACCT])
                                for conf_apple_acct in Gb.conf_apple_accounts
                                if conf_apple_acct[CONF_APPLE_ACCT]]

        entity_reg = er.async_get(Gb.hass)
        for RegEntry in er.async_entries_for_config_entry(entity_reg, Gb.config_entry_id):
            auth_key = _auth_key_from_unique_id(RegEntry.unique_id)
            if auth_key is None or auth_key in conf_auth_keys:
                continue

            # HA removes the entity when it's entity registry entry is removed
            entity_reg.async_remove(RegEntry.entity_id)
            Gb.AuthGetButton_by_auth_key.pop(auth_key, None)
            Gb.AuthSendText_by_auth_key.pop(auth_key, None)
            Gb.apple_id_by_auth_key.pop(auth_key, None)

            log_info_msg(f"User Auth Code Entity Removed, Apple Acct deleted, {RegEntry.entity_id}")

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def _auth_key_from_unique_id(unique_id):
    for auth_type in [AUTH_GET, AUTH_SEND]:
        unique_id_prefix = f"{DOMAIN}_{auth_type}_"
        if unique_id.startswith(unique_id_prefix):
            return unique_id.replace(unique_id_prefix, '')

    return None


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE THE ENTER AUTH CODE STATUS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def update_auth_entities_state():
    '''
    Called from the 5-sec loop. Create the entities for an Apple Acct that was logged
    into after startup and set the 'Auth needed/not needed' status. The status of a
    request or send action is not changed while the code is still needed. This also
    picks up an authentication done on the Configure or HA Repairs screens.
    '''
    try:
        create_auth_entities()

        for auth_key, _AuthSendText in list(Gb.AuthSendText_by_auth_key.items()):
            AppleAcct = get_AppleAcct(auth_key)
            if AppleAcct is None:
                continue

            if AppleAcct.is_reauth_needed:
                if _AuthSendText.status_msg in ['', AUTH_NOT_NEEDED, CODE_ACCEPTED]:
                    _AuthSendText.set_status(AUTH_NEEDED)

            elif _AuthSendText.status_msg != CODE_ACCEPTED:
                _AuthSendText.set_status(AUTH_NOT_NEEDED)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def get_AppleAcct(auth_key):
    apple_id = Gb.apple_id_by_auth_key.get(auth_key)

    return Gb.AppleAcct_by_apple_id.get(apple_id) if apple_id else None

#--------------------------------------------------------------------
def _post_auth_status(auth_key, AppleAcct, action, status_msg, evlog_msg=None):
    '''
    Display the status in the Enter Auth Code text box and the Event Log
    '''
    _AuthSendText = Gb.AuthSendText_by_auth_key.get(auth_key)
    if _AuthSendText:
        _AuthSendText.set_status(status_msg)

    account_owner = AppleAcct.account_owner if AppleAcct else UNKNOWN_ACCT
    post_event( f"{EVLOG_NOTICE}Apple Acct > {account_owner}, "
                f"{action} (Dashboard), {evlog_msg or status_msg}")

#--------------------------------------------------------------------
def _verify_auth_code_action(auth_key):
    '''
    Return the AppleAcct and None if the code can be requested/sent or None/AppleAcct
    and the status message if it can not
    '''
    AppleAcct = get_AppleAcct(auth_key)

    if AppleAcct is None:
        return None, UNKNOWN_ACCT
    if aascf.is_apple_acct_logged_into(AppleAcct.apple_id) is False:
        return AppleAcct, NOT_LOGGED_IN
    if Gb.internet_error:
        return AppleAcct, INTERNET_ERROR
    if (AppleAcct.is_auth_method_PUSH is False
            and AppleAcct.is_auth_method_TEXT is False):
        return AppleAcct, NOT_FOR_HWKEY

    # Requesting a code untrusts a valid session. Only an admin can do that from the
    # Configure screens.
    if AppleAcct.is_reauth_needed is False:
        return AppleAcct, AUTH_NOT_NEEDED

    return AppleAcct, None


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REQUEST AUTH CODE (BUTTON PRESS)
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_user_auth_code_request(auth_key):
    '''
    Request a new Authentication Code for the Apple Acct (Push Notification or Text
    Message). From step_reauth.request_auth_code_or_trigger_hwkey_keypress.
    '''
    action = 'Request Auth Code'
    AppleAcct, status_msg = _verify_auth_code_action(auth_key)

    if status_msg is None:
        requested_secs = Gb.auth_code_requested_secs_by_apple_id.get(AppleAcct.apple_id, 0)
        wait_secs = AUTH_CODE_REQUEST_WAIT_SECS - (time_now_secs() - requested_secs)
        if wait_secs > 0:
            status_msg = f"Wait {wait_secs}s"

    if status_msg:
        _post_auth_status(auth_key, AppleAcct, action, status_msg)
        return

    # Set before the request so another press while it is running is refused
    Gb.auth_code_requested_secs_by_apple_id[AppleAcct.apple_id] = time_now_secs()

    try:
        log_info_msg(   f"{AppleAcct.apple_user} > Request Auth code (Dashboard), "
                        f"{AppleAcct.current_auth_method}")

        if AppleAcct.is_auth_method_PUSH:
            # The login's password sign-in created the 2fa challenge and sent the
            # push popup. If it is still live, request the code against it instead of
            # signing in again, which waits out the SRP signin interval and sends
            # a 2nd popup.
            code_requested = False
            if AppleAcct.is_2fa_challenge_session_live:
                code_requested = await Gb.hass.async_add_executor_job(
                                        AppleAcct.request_auth_code_via_push_notification)
                log_info_msg(   f"{AppleAcct.apple_user} > Reused the 2fa challenge for the "
                                f"Push Auth code, Successful-{code_requested}")

            if code_requested is False:
                await Gb.hass.async_add_executor_job(AppleAcct.untrust_session_and_authenticate)
                if AppleAcct.login_successful_srp is not False:
                    await Gb.hass.async_add_executor_job(AppleAcct.request_auth_code_via_push_notification)

            status_msg = CODE_REQUESTED
            evlog_msg  = 'Push Notification, Waiting for the Auth Code to be entered'

        else:
            # Apple sends the trusted-device push popup when the 2FA challenge is
            # CREATED by the password sign-in, not when a code is requested. If the
            # previous sign-in's challenge is still live, request the text code
            # against it so a resend does not pop up a new notification on every
            # device on the account.
            text_code_sent = False
            if AppleAcct.is_2fa_challenge_session_live:
                text_code_sent = await Gb.hass.async_add_executor_job(
                                        AppleAcct.request_auth_code_via_text_msg,
                                        AppleAcct.current_auth_method)
                log_info_msg(   f"{AppleAcct.apple_user} > Reused the 2fa challenge for the "
                                f"Text Auth code, Successful-{text_code_sent}")

            # A 423 is Apple's 'Too many codes sent' throttle for the phone number
            # (serviceError -22981). Signing in again would only spend another
            # request against the throttle.
            if (text_code_sent is False
                    and AppleAcct.response_code != 423):
                await Gb.hass.async_add_executor_job(AppleAcct.untrust_session_and_authenticate)
                if AppleAcct.login_successful_srp is not False:
                    text_code_sent = await Gb.hass.async_add_executor_job(
                                            AppleAcct.request_auth_code_via_text_msg,
                                            AppleAcct.current_auth_method)

            phone_number = AppleAcct.current_auth_method_value
            if text_code_sent:
                status_msg = CODE_REQUESTED
                evlog_msg  = f"Text Msg: {phone_number}, Waiting for the Auth Code to be entered"
            elif AppleAcct.response_code == 423:
                status_msg = TEXT_BLOCKED_423
                evlog_msg  = (  f"{EVLOG_ALERT}Text Msg: {phone_number}, Apple has temporarily "
                                f"stopped sending Text Authentication Codes (too many codes "
                                f"requested). Use the code from the device popup")
            else:
                status_msg = TEXT_NOT_SENT
                evlog_msg  = (  f"{EVLOG_ALERT}Text Msg: {phone_number}, Apple did not send "
                                f"the Text Authentication Code, {AppleAcct.response_code_desc}")

        # The session was untrusted and Apple rejected the password sign-in that creates
        # the 2fa challenge, a code can not be requested or used
        if AppleAcct.login_successful_srp is False:
            status_msg = SIGNIN_FAILED
            evlog_msg  = (  f"{EVLOG_ALERT}Apple rejected the Password Sign-in, an Auth Code "
                            f"can not be requested, "
                            f"{AppleAcct.code_description(AppleAcct.response_code_pw)}")

        AppleAcct.was_auth_code_requested = True
        Gb.AppleAcct_reauth_needed = AppleAcct

        _post_auth_status(auth_key, AppleAcct, action, status_msg, evlog_msg)

    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SEND AUTH CODE (TEXT ENTITY, ENTER PRESSED)
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_user_auth_code_send(auth_key, auth_code):
    '''
    Send the Authentication Code entered in the text entity to Apple. From
    step_reauth.send_auth_code_or_assert_hwkey_keypress. The code is not logged
    or saved.
    '''
    action = 'Send Auth Code'
    AppleAcct, status_msg = _verify_auth_code_action(auth_key)

    # The text entity removed the status message the code was typed after. Remove
    # spaces, dashes, etc the user may have entered with the code.
    auth_code = ''.join([code_char for code_char in str(auth_code or '')
                                    if code_char.isdigit()])
    if (status_msg is None
            and len(auth_code) != 6):
        status_msg = ENTER_6_DIGITS

    if status_msg:
        _post_auth_status(auth_key, AppleAcct, action, status_msg)
        return

    try:
        AppleAcct.was_ha_auth_code_alert_sent = False
        auth_successful = False

        if AppleAcct.is_auth_method_PUSH:
            auth_successful = await Gb.hass.async_add_executor_job(
                                    AppleAcct.validate_2fa_push_popup_window_code,
                                    auth_code)
        else:
            auth_successful = await Gb.hass.async_add_executor_job(
                                    AppleAcct.validate_2fa_text_code,
                                    auth_code)

        log_info_msg(   f"{AppleAcct.account_owner} > Send Auth code (Dashboard), "
                        f"{AppleAcct.current_auth_method}, Successful-{auth_successful}")

        if auth_successful is False:
            AppleAcct.was_auth_code_requested = True
            _post_auth_status(auth_key, AppleAcct, action, CODE_INVALID,
                                'Invalid Authentication Code')
            return

        await _async_finish_auth_code_accepted(AppleAcct)

        _post_auth_status(auth_key, AppleAcct, action, CODE_ACCEPTED,
                            'Authentication Code Accepted')

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
async def _async_finish_auth_code_accepted(AppleAcct):
    '''
    Refresh the device data if the Apple Acct's devices were never loaded, clear the
    auth_needed alert and the HA reauth request (orange Reconfigure button)
    '''
    # If AppleAcct.device_id_by_aadev_dname is empty, the code was needed when it was
    # first logged into and the devices were never loaded. Only the caller's AppleAcct
    # is used by async_finish_authentication_and_data_refresh.
    if is_empty(AppleAcct.device_id_by_aadev_dname):
        await aascf.async_finish_authentication_and_data_refresh(
                                        SimpleNamespace(AppleAcct=AppleAcct))

    Gb.EvLog.clear_greenbar_msg()
    Gb.is_force_icloud_update = True
    AppleAcct.was_auth_code_requested = False
    AppleAcct.is_reauth_needed_secs   = 0
    update_alert_sensor(Source=AppleAcct, error='auth_needed', clear=True)

    _cancel_ha_reauth_request()

#--------------------------------------------------------------------
def _cancel_ha_reauth_request():
    '''
    Point the HA reauth request to the next Apple Acct needing a code or, if none
    do, cancel it (the orange Reconfigure button on the HA Settings screen)
    '''
    for _AppleAcct in Gb.AppleAcct_by_apple_id.values():
        if _AppleAcct.is_reauth_needed:
            Gb.AppleAcct_reauth_needed = _AppleAcct
            return

    Gb.AppleAcct_reauth_needed = None
    aascf.clear_AppleAcct_auth_alerts()
    post_greenbar_msg('')

    try:
        for flow in Gb.hass.config_entries.flow.async_progress():
            if (flow['handler'] == DOMAIN
                    and flow.get('context', {}).get('source') == 'reauth'):
                Gb.hass.config_entries.flow.async_abort(flow['flow_id'])

    except Exception as err:
        log_exception(err)
