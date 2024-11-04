
from ..global_variables import GlobalVariables as Gb
from ..const            import ( HIGH_INTEGER, NOT_SET,
                                HOME, ZONE, UTC_TIME, MOBAPP_TRIGGER_ABBREVIATIONS,
                                TRACE_ICLOUD_ATTRS_BASE, TRACE_ATTRS_BASE,
                                BATTERY_LEVEL, BATTERY_STATUS, BATTERY_STATUS_CODES,
                                LAST_CHANGED_SECS, LAST_CHANGED_TIME,
                                LAST_UPDATED_SECS, LAST_UPDATED_TIME,
                                STATE, LOCATION, ATTRIBUTES, TRIGGER, RAW_MODEL)
from .common            import (instr,  )
from .messaging         import (log_debug_msg, log_exception, log_debug_msg, log_error_msg, log_rawdata,
                                _evlog, _log, )
from .time_util         import (secs_to_time)

from homeassistant.helpers import entity_registry, device_registry
from datetime import datetime

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#    Entity State and Attributes functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def get_state(entity_id):
    """
    Return the state of an entity

    from datetime import datetime

    # Timezone Name.
    date_String = "23/Feb/2012:09:15:26 UTC +0900"
    dt_format = datetime.strptime(date_String, '%d/%b/%Y:%H:%M:%S %Z %z')
    print("Date with Timezone Name::", dt_format)

    # Timestamp
    timestamp = dt_format.timestamp()
    """

    try:
        entity_data = Gb.hass.states.get(entity_id)

        if entity_data is None: return NOT_SET

        entity_state = entity_data.state

        if entity_state in MOBAPP_TRIGGER_ABBREVIATIONS:
            state = MOBAPP_TRIGGER_ABBREVIATIONS[entity_state]
        else:
            state = Gb.state_to_zone.get(entity_state, entity_state.lower())

        if instr(entity_id, 'battery_state'):
            state = BATTERY_STATUS_CODES.get(state.lower(), state)

        if instr(entity_id, BATTERY_LEVEL) and state == 'not_set':
            state = 0

    # When starting iCloud3, the device_tracker for the mobapp might
    # not have been set up yet. Catch the entity_id error here.
    except Exception as err:
        #log_exception(err)
        state = NOT_SET

    return state

#--------------------------------------------------------------------
def get_attributes(entity_id):
    """
    Return the attributes of an entity.
    """

    try:
        entity_data  = Gb.hass.states.get(entity_id)
        entity_state = entity_data.state
        entity_attrs = entity_data.attributes.copy()

        last_changed_secs = int(entity_data.last_changed.timestamp())
        last_updated_secs = int(entity_data.last_updated.timestamp())
        last_reported_secs = int(entity_data.last_reported.timestamp())

        entity_attrs[LAST_CHANGED_SECS] = last_changed_secs
        entity_attrs[LAST_CHANGED_TIME] = secs_to_time(last_changed_secs)
        entity_attrs[LAST_UPDATED_SECS] = last_updated_secs
        entity_attrs[LAST_UPDATED_TIME] = secs_to_time(last_updated_secs)
        entity_attrs['last_reported_secs'] = last_reported_secs
        entity_attrs['last_reported_time'] = secs_to_time(last_reported_secs)
        entity_attrs[STATE] = entity_state

        if BATTERY_STATUS in entity_attrs:
            battery_status = entity_attrs[BATTERY_STATUS].lower()
            entity_attrs[BATTERY_STATUS] = BATTERY_STATUS_CODES.get(battery_status, battery_status)

    except (KeyError, AttributeError):
        entity_attrs = {}

    except Exception as err:
        log_exception(err)
        entity_attrs = {}
        entity_attrs[TRIGGER] = (f"Error {err}")

    return entity_attrs

#--------------------------------------------------------------------
def get_last_changed_time(entity_id):
    """
    Return the entity's last changed time attribute in secs
    Last changed time format '2019-09-09 14:02:45.12345+00:00' (utc value)
    """

    try:
        if entity_id == '':
            return 0

        States = Gb.hass.states.get(entity_id)
        if States is None:
            return 0

        last_changed  = States.last_changed
        last_updated  = States.last_updated

        if lc := last_changed.timestamp():
            time_secs = int(lc)
        elif lu := last_updated.timestamp():
            time_secs = int(lu)
        else:
            time_secs = 0

    except Exception as err:
        log_exception(err)
        time_secs = 0


    return time_secs

#--------------------------------------------------------------------
def get_entity_registry_data(platform=None, domain=None) -> list:
    """
    Cycle through the entity registry and extract the entities in a platform.

    Parameter:
        platform - platform to extract from the entity_registry
    Returns:
        [platform_entity_ids], [platform_entity_data]

    Example data:
        platform_entity_ids  = ['zone.quail', 'zone.warehouse', 'zone.the_point', 'zone.home']
        platform_entity_data = {'zone.quail': {'entity_id': 'zone.quail', 'unique_id': 'quail',
                    'platform': 'zone', 'area_id': None, 'capabilities': {}, 'config_entry_id': None,
                    'device_class': None, 'device_id': None, 'disabled_by': None, 'entity_category': None,
                    'icon': None, 'id': 'e064e09a8f8c51f6f1d8bb3313bf5e1f', 'name': None, 'options': {},
                    'original_device_class': None, 'original_icon': 'mdi:map-marker',
                    'original_name': 'quail', 'supported_features': 0, 'unit_of_measurement': None}, {...}}
    """

    try:
        entity_reg = entity_registry.async_get(Gb.hass)
        entities   = {k:_registry_data_str_to_dict(k, v, platform, domain)
                        for k, v in entity_reg.entities.items()
                        if _base_domain(k) in ['device_tracker', 'zone', 'sensor']}

        if platform is None and domain:
            platform_entity_data = {k:v for k, v in entities.items()
                                        if _base_domain(k) == domain}

        elif platform and domain is None:
            platform_entity_data = {k:v for k, v in entities.items()
                                        if v['platform'] == platform}

        elif platform and domain:
            platform_entity_data = {k:v for k, v in entities.items()
                                        if (v['platform'] == platform and _base_domain(k) == domain)}

        else:
            return [], {}

        platform_entity_ids  = [k for k in platform_entity_data.keys()]

        # Get raw_model from HA device_registry
        if platform == 'mobile_app' or domain == 'device_tracker':
            device_reg = device_registry.async_get(Gb.hass)
            for dev_trkr_entity, dev_trkr_entity_data in platform_entity_data.items():
                raw_model = 'Unknown'
                try:
                    # 12/18/2022 (beta 1)-Check to see if in device_reg
                    device_id = dev_trkr_entity_data['device_id']
                    device_reg_data = device_reg.async_get(device_id)
                    if device_reg_data:
                        raw_model = device_reg_data.model

                except Exception as err:
                    # 12/18/2022 (beta 1)-Don't display error msg if no device_reg data
                    # log_exception(err)
                    pass

                dev_trkr_entity_data[RAW_MODEL] = raw_model

        # Remove 'zone.' and add Home zone to the zone platform items
        if platform == 'zone':
            platform_entity_ids = [v.replace('zone.', '') for v in platform_entity_ids]
            platform_entity_ids.append(HOME)

        return platform_entity_ids, platform_entity_data

    except Exception as err:
        log_exception(err)
        return [], {}

#-------------------------------------------------------------------------------------------
def _base_domain(domain_entity_id):
    return domain_entity_id.split('.')[0]

def _base_entity_id(domain_entity_id):
    return domain_entity_id.split('.')[1]

#--------------------------------------------------------------------
def _registry_data_str_to_dict(key, text, platform, domain):
    """ Convert the entity/device registry data to a dictionary

        Input (EntityRegistry or DeviceRegistry attribute items for an entity/device):
            key:        The key of the items data
            text:       String that is in the form a dictioary.
            platform:   Requested platform

            Input text:
                "RequestedEntry(entity_id='zone.quail', area_id=None, capabilities={},
                version='11.22', item_type=[], supported_features=0,
                unit_of_measurement=None)"
            Reformatted:
                ['entity_id:'zone.quail', 'area_id': None, 'capabilities': {},
                'version': 11.22, item_tupe: [], 'supported_features': 0,
                'unit_of_measurement': None}
    """
    text = str(text).replace('RegistryEntry(', '')[:-1]
    items = [item.replace("'", "") for item in text.split(', ')]

    # Do not reformat items if not requested platform
    if (f"platform={platform}" in items
            and (domain is None or _base_domain(key) == domain)):
        pass
    elif platform is None and _base_domain(key) == domain:
        pass
    else:
        return {'platform': 'not_platform_domain'}

    items_dict = {}
    for item in items:
        try:
            if instr(item, '=') is False:
                continue

            key_value = item.split('=')
            key = key_value[0]
            value = key_value[1]
            if value == 'None':
                items_dict[key] = None
            elif value.isnumeric():
                items_dict[key] = int(value)
            elif value.find('.') and value.split('.')[0].isnumeric() and value.split('.')[1].isnumeric():
                items_dict[key] = float(value)
            elif value.startswith('{'):
                items_dict[key] = eval(value)
            elif value.startswith('['):
                items_dict[key] = eval(value)
            else:
                items_dict[key] = value.replace('xa0', '')
        except:
            pass

    return items_dict

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#    ZONE - Entity State and Attributes functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def ha_zone_entity_ids():
    return Gb.hass.states.entity_ids(ZONE)

def ha_zone_attrs_id(zone):
    zone_entity_id = zone if zone.startswith('zone.') else f"zone.{zone}"
    try:
        return id(Gb.hass.states.get(zone_entity_id).attributes)
    except:
        return 0

def ha_zone_attrs(zone):
    zone_entity_id = zone if zone.startswith('zone.') else f"zone.{zone}"
    try:
        ha_zone_attrs = Gb.hass.states.get(zone_entity_id).attributes
        return ha_zone_attrs

    except Exception as err:
        # log_exception(err)
        return None

def ha_zone_entities():
    '''
    Entities zone item:
    'zone.the_point': RegistryEntry(entity_id='zone.the_point', unique_id='thepoint',
    platform='zone', aliases=set(), area_id=None, capabilities=None, config_entry_id=None,
    device_class=None, device_id=None, disabled_by=None, entity_category=None,
    hidden_by=None, icon=None, id='bf4bf5bfa8d70ce5f705f62618def820', has_entity_name=False,
    name='The Point', options={}, original_device_class=None, original_icon='mdi:map-marker',
    original_name='The.Point', supported_features=0, translation_key=None, unit_of_measurement=None)
    '''
    entity_reg = entity_registry.async_get(Gb.hass)
    ha_zone_entities = {zone_entity_id: RegEntry
                        for zone_entity_id, RegEntry in entity_reg.entities.items()
                        if zone_entity_id.startswith('zone')}

    ha_zone_entity_ids = [zone_entity_id.replace('zone.', '')
                        for zone_entity_id in ha_zone_entities.keys()]
    ha_zone_entity_ids.append(HOME)

    return ha_zone_entity_ids

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#    OTHER SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def set_state_attributes(entity_id, state_value, attrs_value):
    """
    Update the state and attributes of an entity_id
    """

    try:
        Gb.hass.states.set(entity_id, state_value, attrs_value, force_update=True)

    except Exception as err:
        log_msg =   (f"Error updating entity > <{entity_id} >, StateValue-{state_value}, "
                    f"AttrsValue-{attrs_value}")
        log_error_msg(log_msg)
        log_exception(err)

#--------------------------------------------------------------------
def extract_attr_value(attributes, attribute_name, numeric=False):
    ''' Get an attribute out of the attrs attributes if it exists'''

    try:
        if attribute_name in attributes:
            return attributes[attribute_name]
        elif numeric:
            return 0
        else:
            return ''

    except:
        return ''

#--------------------------------------------------------------------
def trace_device_attributes(Device, description, fct_name, attrs):

    try:
        #Extract only attrs needed to update the device
        if attrs is None:
            return

        attrs_in_attrs = {}
        if description.find("iCloud") >= 0:
            attrs_base_elements = TRACE_ICLOUD_ATTRS_BASE
            if LOCATION in attrs:
                attrs_in_attrs  = attrs[LOCATION]
        elif 'Zone' in description:
            attrs_base_elements = attrs
        else:
            attrs_base_elements = TRACE_ATTRS_BASE
            if ATTRIBUTES in attrs:
                attrs_in_attrs  = attrs[ATTRIBUTES]

        trace_attrs = {k: v for k, v in attrs.items() \
                            if k in attrs_base_elements}

        trace_attrs_in_attrs = {k: v for k, v in attrs_in_attrs.items() \
                            if k in attrs_base_elements}

        ls = Device.state_last_poll
        cs = Device.state_this_poll
        log_msg = (f"{description} Attrs ___ ({fct_name})")
        log_debug_msg(Device.devicename, log_msg)

        log_msg = (f"{description} Last State-{ls}, This State-{cs}")
        log_debug_msg(Device.devicename, log_msg)

        log_msg = (f"{description} Attrs-{trace_attrs}{trace_attrs_in_attrs}")
        log_debug_msg(Device.devicename, log_msg)

        log_rawdata(f"iCloud Rawdata - <{Device.devicename}> {description}", attrs)

    except Exception as err:
        pass

    return
