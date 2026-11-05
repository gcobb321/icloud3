'''
HA Repairs platform hook for iCloud3

HA imports this module and calls async_create_fix_flow when Submit is selected for an
iCloud3 fixable issue in Settings > Repairs. The repair flows open Configure screens, so
they are in the configure_vN directories with the Configure version they use. The
Gb.conf_profile[CONF_CONFIG_FLOW_VERSION] parameter selects the version:

    1 - configure_v1/repairs_v1.py

HA can import this module before the iCloud3 configuration file has been read, so the
version is checked when the repair flow is started, not when the module is imported.
'''

from .config_flow                   import (config_flow_version, DEFAULT_CONFIG_FLOW_VERSION, )
from .configure_v1                  import repairs_v1

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core             import HomeAssistant

# version: Configure version repairs module
REPAIRS_MODULES = {
        1: repairs_v1,
}


#--------------------------------------------------------------------
async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data) -> RepairsFlow:
    repairs_module = REPAIRS_MODULES.get(config_flow_version(),
                                         REPAIRS_MODULES[DEFAULT_CONFIG_FLOW_VERSION])

    return await repairs_module.async_create_fix_flow(hass, issue_id, data)
