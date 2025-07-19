
from ..global_variables import GlobalVariables as Gb
from ..const            import (PLATFORM_SENSOR, DOMAIN, SENSOR,
                                HIGH_INTEGER, NOT_SET,
                                HOME, ZONE, UTC_TIME, MOBAPP_TRIGGER_ABBREVIATIONS,
                                TRACE_ICLOUD_ATTRS_BASE, TRACE_ATTRS_BASE,
                                BATTERY_LEVEL, BATTERY_STATUS, BATTERY_STATUS_CODES,
                                LAST_CHANGED_SECS, LAST_CHANGED_TIME,
                                LAST_UPDATED_SECS, LAST_UPDATED_TIME,
                                STATE, LOCATION, ATTRIBUTES, TRIGGER, RAW_MODEL)
from .utils             import (instr,  is_empty, isnot_empty, list_add, list_del,)
from .messaging         import (log_debug_msg, log_exception, log_debug_msg, log_error_msg, log_data,
                                _evlog, _log, )
from .time_util         import (secs_to_time)

from homeassistant.helpers import entity_registry as er, device_registry as dr
from datetime import datetime
import json

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
        # _log(f"{entity_id=} {entity_data.state=}")

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
def get_entity_registry_data(platform=None, domain=None):
    """
    Cycle through the entity registry and extract the entities in a platform.

    Parameter:
        platform - platform filter ('icloud3')
        domain   - domain filter ('sensor')
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
        entity_reg = er.async_get(Gb.hass)
        entity_ids_attrs   = {entity_id: EntRegItem.as_partial_dict
                        for entity_id, EntRegItem in entity_reg.entities.items()
                        if _select_entity_reg_item(EntRegItem, platform, domain)}

        if is_empty(entity_ids_attrs):
            return [], {}

        entity_ids  = [entity_id for entity_id in entity_ids_attrs.keys()]

        # Get raw_model from device_registry
        if platform == 'mobile_app' or domain == 'device_tracker':
            device_reg = dr.async_get(Gb.hass)
            for entity_id, entity_id_attrs in entity_ids_attrs.items():
                model = 'Unknown'
                try:
                    device_id = entity_id_attrs['device_id']
                    device_reg_data = device_reg.async_get(device_id)
                    if device_reg_data:
                        model = device_reg_data.model

                except Exception as err:
                    # log_exception(err)
                    pass

                entity_id_attrs[RAW_MODEL] = model

        # Remove 'zone.' and add Home zone to the zone platform items
        if platform == 'zone':
            entity_ids = [entity_id.replace('zone.', '') for entity_id in entity_ids]
            entity_ids.append(HOME)

        return entity_ids, entity_ids_attrs

    except Exception as err:
        log_exception(err)
        return [], {}

#...........................................................................................
def _select_entity_reg_item(EntRegItem, platform, domain):

    '''
    Determine if this Entity Registry item is selected based on the platform
    and domain criteria
    '''

    _domain = EntRegItem.entity_id.split('.')[0]

    if _domain not in ['device_tracker', 'zone', 'sensor']:
        return False

    if platform is None and domain == _domain:
        return True

    if domain is None and EntRegItem.platform == platform:
        return True

    if EntRegItem.platform == platform and domain == _domain:
        return True

    return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#    HA STATES ENTITY FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def get_states_entity_ids(domain=None, integration=None):
    '''
    Parameter:
        domain - domain filter, default=sensor
        integration - integration name, default=iCloud3
    Return:
        entity_ids (list)

    Sample data:
        entity_ids=['sensor.ipad_mini_zone_distance', 'sensor.ipad_mini_home_distance',
            'sensor.ipad_mini_battery', 'sensor.ipad_mini_name', ...
    '''
    domain = SENSOR if domain is None else domain
    integration = DOMAIN if integration is None else integration

    entity_ids = []
    for Entity in Gb.hass.states.async_all(domain):

        if Entity.entity_id.startswith(domain) is False:
            continue

        entity_id_attrs = Gb.hass.states.get(Entity.entity_id).attributes
        if entity_id_attrs and entity_id_attrs.get('integration') is not None:
            if entity_id_attrs['integration'].lower() == integration.lower():
                list_add(entity_ids, Entity.entity_id)

    return entity_ids


def get_states_entity_data(domain=None, integration=None):
    '''
    Parameter:
        domain - domain filter, default=sensor
        integration - integration name, default=iCloud3
    Return:
        entity_ids (list), attributes (dict)

    Sample data:
        entity_ids=['sensor.ipad_mini_zone_distance', 'sensor.ipad_mini_home_distance',
            'sensor.ipad_mini_battery', 'sensor.ipad_mini_name', ...
        entity_ids_attrs={'sensor.ipad_mini_zone_distance': {'integration': 'iCloud3',
            'sensor_updated': '2025-01-09 12:34:09', 'from_zone': 'home', 'distance (meters)': 25.838,
            'distance_to_zone_edge (meters)': 74.162, 'distance (miles)': 0.01605,
            'distance_units (attributes)': 'mi', 'calculated_distance': 0.02584,
            'waze_route_distance': '×Paused', 'max_distance': 0.0, 'nearby_device_used': '',
            'went_3km': 'false', 'unit_of_measurement': 'mi', 'icon': 'mdi:map-marker-distance',
            'friendly_name': 'iPad-Mini ZoneDistance'}, ...
    '''
    entity_ids = get_states_entity_ids(domain, integration)

    entity_ids_attrs = {}
    for entity_id in entity_ids:
        entity_ids_attrs[entity_id] = Gb.hass.states.get(entity_id).attributes

    return entity_ids, entity_ids_attrs

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
    entity_reg = er.async_get(Gb.hass)
    ha_zone_entity_items = {zone_entity_id: RegEntry
                        for zone_entity_id, RegEntry in entity_reg.entities.items()
                        if zone_entity_id.startswith('zone')}

    ha_zone_entity_ids = [zone_entity_id.replace('zone.', '')
                        for zone_entity_id in ha_zone_entity_items.keys()]
    ha_zone_entity_ids.append(HOME)

    zone_entity_ids, zone_entity_items = get_entity_registry_data(domain='zone')

    return ha_zone_entity_ids

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ENTITY REGISTRY MAINTENANCE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def get_entity(entity_id):
    try:
        entity_reg = er.async_get(Gb.hass)
        return entity_reg.async_get(entity_id)
    except:
        return {}

def remove_entity(entity_id):
    try:
        entity_reg = er.async_get(Gb.hass)
        entity_reg.async_remove(entity_id)
    except Exception as err:
        pass

    try:
        if Gb.hass.states.async_available(entity_id) is False:
            Gb.hass.async_add_executor_job(Gb.hass.states.remove, entity_id)

    except Exception as err:
        #log_exception(err)
        pass

def get_assigned_sensor_entity(unique_id):
    try:
        entity_reg = er.async_get(Gb.hass)
        return entity_reg.async_get_entity_id(PLATFORM_SENSOR, DOMAIN, unique_id)
    except:
        return None

def change_entity_id(from_entity_id, to_entity_id):
    try:
        entity_reg = er.async_get(Gb.hass)
        entity_reg.async_update_entity(from_entity_id, new_entity_id=to_entity_id)
    except Exception as err:
        log_exception(err)

def update_entity(entity_id, **kwargs):
    try:
        entity_reg = er.async_get(Gb.hass)
        entity_reg.async_update_entity(entity_id, **kwargs)
    except Exception as err:
        # log_exception(err)
        return False

def is_entity_available(entity_id):
    try:
        entity_reg = er.async_get(Gb.hass)
        entity_reg._entity_id_available(entity_id, None)
    except:
        return True

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

        log_data(f"iCloud Rawdata - <{Device.devicename}> {description}", attrs)

    except Exception as err:
        pass

    return
