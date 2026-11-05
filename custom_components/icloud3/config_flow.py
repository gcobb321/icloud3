'''
HA config_flow hook for iCloud3

HA imports this module and uses the class registered with 'domain=DOMAIN' for the
initial setup, reauth and Configure (options) flows. The iCloud3 Configure handlers are
in the configure_vN directories. The Gb.conf_profile[CONF_CONFIG_FLOW_VERSION] parameter
selects the version that is run when a flow is started:

    1 - configure_v1/config_flow_v1.py

Only the iCloud3_ConfigFlow hook class below can have 'domain=DOMAIN'. A configure_vN
handler class with it would replace the hook as the HA handler when it is imported.

HA can import this module before the iCloud3 configuration file has been read, so the
version is checked when a flow is started, not when the module is imported.
'''

from .global_variables      import GlobalVariables as Gb
from .const                 import (DOMAIN, )
from .const_config          import (CONF_CONFIG_FLOW_VERSION, )

from .configure_v1.config_flow_v1   import (iCloud3_ConfigFlow_v1,
                                            iCloud3_OptionsFlowHandler_v1, )

from homeassistant                  import config_entries
from homeassistant.core             import callback

# version: (ConfigFlow handler, OptionsFlow handler)
CONFIG_FLOW_HANDLERS = {
        1: (iCloud3_ConfigFlow_v1, iCloud3_OptionsFlowHandler_v1),
}
DEFAULT_CONFIG_FLOW_VERSION = 1


#--------------------------------------------------------------------
def config_flow_version():
    '''
    The Configure version from the configuration file. The default version is used
    before the configuration file has been read (initial setup) or if the version is
    not available.
    '''
    version = Gb.conf_profile.get(CONF_CONFIG_FLOW_VERSION, DEFAULT_CONFIG_FLOW_VERSION)

    return version if version in CONFIG_FLOW_HANDLERS else DEFAULT_CONFIG_FLOW_VERSION

# #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                     ICLOUD3 CONFIG FLOW - HA HOOK
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class iCloud3_ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    '''
    HA creates the flow with 'iCloud3_ConfigFlow()'. __new__ returns the selected
    version's ConfigFlow handler instead, so HA runs that handler's steps. This class
    is never used as a flow itself.
    '''

    # The config entry's version, not the Configure version. HA compares it to the
    # config entry's version on startup and fails setup if they do not match.
    VERSION = 1

    def __new__(cls, *args, **kwargs):
        ConfigFlowHandler, _ = CONFIG_FLOW_HANDLERS[config_flow_version()]

        return ConfigFlowHandler(*args, **kwargs)

#----------------------------------------------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        '''
        Create the options flow handler of the selected version. This is called when the
        iCloud3 > Configure is selected on the Devices & Services screen. A new handler is
        created for each Configure window.
        '''
        _, OptionsFlowHandler = CONFIG_FLOW_HANDLERS[config_flow_version()]

        return OptionsFlowHandler()

#----------------------------------------------------------------------
    async def async_step_reauth(self, user_input=None):
        '''
        HA only starts a reauth flow (async_start_reauth_if_available) if the registered
        class has an async_step_reauth step. It is never called, HA runs the selected
        version's async_step_reauth.
        '''
        raise NotImplementedError
