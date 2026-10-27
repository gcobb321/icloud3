#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module sets up the button platform for the user auth code Request Auth Code
#   entity (button.auth_get_[name]). Pressing it requests a new Authentication Code
#   for it's Apple Acct. The entities are created and handled in
#   apple_acct/user_auth_code_handler.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from .global_variables  import GlobalVariables as Gb
from .const             import (DOMAIN, PLATFORM_BUTTON, )
from .apple_acct        import user_auth_code_handler as uach
from .utils.messaging   import (log_exception, )

#--------------------------------------------------------------------
from homeassistant.components.button    import ButtonEntity
from homeassistant.config_entries       import ConfigEntry
from homeassistant.core                 import HomeAssistant
from homeassistant.helpers.entity       import DeviceInfo
from homeassistant.util                 import slugify


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    '''Set up the iCloud3 button platform'''

    # Saved for user_auth_code_handler.create_auth_entities
    Gb.button_async_add_entities = async_add_entities
    Gb.AuthGetButton_by_auth_key = {}


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class AuthGetButton(ButtonEntity):
    '''Request Auth Code (button.auth_get_[name])'''

    _attr_should_poll = False
    _attr_icon        = 'mdi:message-lock-outline'

    def __init__(self, auth_key, auth_name):
        self.auth_key  = auth_key
        self.auth_name = auth_name

        # The entity registry keeps the entity_id after the entity is first added
        self.entity_id       = f"{PLATFORM_BUTTON}.{uach.AUTH_GET}_{slugify(auth_name)}"
        self._attr_unique_id = f"{DOMAIN}_{uach.AUTH_GET}_{auth_key}"
        self._attr_name      = f"Request Auth Code ({auth_name})"

#..........................................................................................
    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(  identifiers  = {(DOMAIN, DOMAIN)},
                            manufacturer = 'gcobb321',
                            model        = 'Integration',
                            name         = 'iCloud3 Integration')

#..........................................................................................
    async def async_press(self):
        try:
            await uach.async_user_auth_code_request(self.auth_key)

        except Exception as err:
            log_exception(err)

#..........................................................................................
    def __repr__(self):
        return (f"<AuthGetButton: {self.entity_id}>")
