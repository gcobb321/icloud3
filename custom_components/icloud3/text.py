#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module sets up the text platform for the user auth code Enter Auth Code
#   entity (text.auth_send_[name]). The code entered is sent to Apple for it's Apple
#   Acct when Enter is pressed. The entity's state is the status message, the code is
#   never saved in it. The entities are created and handled in
#   apple_acct/user_auth_code_handler.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from .global_variables  import GlobalVariables as Gb
from .const             import (DOMAIN, PLATFORM_TEXT, )
from .apple_acct        import user_auth_code_handler as uach
from .utils.messaging   import (log_exception, )

#--------------------------------------------------------------------
from homeassistant.components.text      import TextEntity, TextMode
from homeassistant.config_entries       import ConfigEntry
from homeassistant.core                 import HomeAssistant
from homeassistant.helpers.entity       import DeviceInfo
from homeassistant.util                 import slugify
import asyncio


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    '''Set up the iCloud3 text platform'''

    # Saved for user_auth_code_handler.create_auth_entities
    Gb.text_async_add_entities  = async_add_entities
    Gb.AuthSendText_by_auth_key = {}


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class AuthSendText(TextEntity):
    '''Enter Auth Code (text.auth_send_[name])'''

    _attr_should_poll = False
    _attr_icon        = 'mdi:form-textbox-password'

    # The status message is displayed in the text box. A password mode box would hide
    # it and a 6-digit pattern would show it as invalid. The code is checked when it
    # is sent.
    _attr_mode        = TextMode.TEXT
    _attr_native_min  = 0
    _attr_native_max  = 100

    def __init__(self, auth_key, auth_name):
        self.auth_key  = auth_key
        self.auth_name = auth_name

        # The entity registry keeps the entity_id after the entity is first added
        self.entity_id          = f"{PLATFORM_TEXT}.{uach.AUTH_SEND}_{slugify(auth_name)}"
        self._attr_unique_id    = f"{DOMAIN}_{uach.AUTH_SEND}_{auth_key}"
        self._attr_name         = f"Enter Auth Code ({auth_name})"
        self._attr_native_value = ''
        self.status_msg         = ''    # The status without the STATUS_MSG_SPACER

#..........................................................................................
    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(  identifiers  = {(DOMAIN, DOMAIN)},
                            manufacturer = 'gcobb321',
                            model        = 'Integration',
                            name         = 'iCloud3 Integration')

#..........................................................................................
    async def async_set_value(self, value):
        '''Enter was pressed, send the code to Apple'''
        prev_status_msg = self.status_msg

        # The code is typed after the status message in the text box (Code requested
        # 123456). Remove the status, some have digits in them (Wait 45s, Text
        # blocked (423)). The handler removes everything else that is not a digit.
        value = str(value or '')
        if prev_status_msg and value.startswith(prev_status_msg):
            value = value[len(prev_status_msg):]

        # HA does not send a state that did not change to the browser, the code that was
        # entered would stay in the text box if the result is the same as the current
        # status (Auth not needed, Invalid code). Display 'Checking code' long enough
        # for the browser to show it so the result always replaces the code.
        self._set_status_value(uach.CHECKING_CODE)
        self.async_write_ha_state()
        await asyncio.sleep(1)

        try:
            await uach.async_user_auth_code_send(self.auth_key, value)

        except Exception as err:
            log_exception(err)

        if self.status_msg == uach.CHECKING_CODE:
            self.set_status(prev_status_msg)

#..........................................................................................
    def set_status(self, status_msg):
        '''
        Display the status message in the text box. This is called from the event loop
        and the 5-sec loop's executor thread.
        '''
        self._set_status_value(status_msg)

        if self.hass is None or self.enabled is False:
            return

        try:
            self.schedule_update_ha_state()

        except (RuntimeError, AttributeError):
            pass
        except Exception as err:
            log_exception(err)

#..........................................................................................
    def _set_status_value(self, status_msg):
        '''
        The state is the status with a space after it so the code can be typed after
        the status without clearing the text box
        '''
        self.status_msg         = status_msg
        self._attr_native_value = f"{status_msg}{uach.STATUS_MSG_SPACER}" if status_msg else ''

#..........................................................................................
    def __repr__(self):
        return (f"<AuthSendText: {self.entity_id}>")
