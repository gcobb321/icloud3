#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   HA RECORDER - EXCLUDE entities FROM BEING ADDED TO HISTORY DATABASE
#
#
#   The HA Recorder module was modified in HA 2023.6.0 to no longer allow a custom
#   component to insert entity entity names in the '_exclude_e' list that defined
#   entity entities to not be added to the History database (home_assistant_v2.db).
#
#   This module fixes that problem by using a code injection process to provide a
#   local prefilter to determine if an entity should be added before the Recorder filter.
#
#
#   This injection has two methods:
#       add_filter - Add entities to the filter list
#       ----------
#           hass - HomeAssistant
#           entities to be filtered -
#                   single entity - entity_id (string)
#                   multiple entities - list of entity ids
#
#                   'sensor.' will be added to the beginning of the entity id if
#                   it's type is not specifid
#
#           recorder_prefilter.add_filter(hass, 'filter_id1')
#           recorder_prefilter.add_filter(hass, ['filter_entity2', 'filter_entity3'])
#
#
#       remove_filter - Remove entities from the filter list
#       -------------
#           Same arguments for add_filter
#
#           recorder_prefilter.remove_filter(hass, 'filter_id1')
#           recorder_prefilter.remove_filter(hass, ['filter_entity2', 'filter_entity3'])
#
#
#   Gary Cobb, iCloud3 iDevice Tracker, aka geekstergary
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from homeassistant.core import HomeAssistant
from inspect import getframeinfo, stack
import logging
_LOGGER = logging.getLogger(__name__)

VERSION = 1.0

def add_filter(hass: HomeAssistant, entities=None):
    '''
    Inject the entity prefilter into the Recorder, remove Recorder listeners,
    reinitialize the Recorder

    Arguments:
        hass - HomeAssistant
        entities - A list of entity entities
                        (['gary_last_update', 'lillian_last_update', '*_next_update'])
                      - A single entity entity ('gary_last_zone')

    Returns:
        True - The injection was successful
        False - The injection was not successful
    '''

    ha_recorder = hass.data['recorder_instance']

    if ha_recorder is None:
        return False

    if hass.data.get('recorder_prefilter') is None:
        rp_data = hass.data['recorder_prefilter'] = {}
        rp_data['injected'] = True
        rp_data['legacy'] = True
        rp_data['exclude_entities'] = []

        try:
            ha_recorder.entity_filter._exclude_e.add(entities)
            return True
        except:
            pass

        rp_data['legacy'] = False

        if _inject_filter(hass) is False:
            return

    _update_filter(hass, entities)


def remove_filter(hass: HomeAssistant, entities):
    if hass.data['recorder_prefilter']['legacy']:
        try:
            ha_recorder = hass.data['recorder_instance']
            ha_recorder.entity_filter._exclude_e.discard(entities)
            return True
        except Exception as err:
            _LOGGER.exception(err)

    _update_filter(hass, entities, remove=True)


def _inject_filter(hass: HomeAssistant):
    ha_recorder = hass.data['recorder_instance']
    rp_data = hass.data['recorder_prefilter']
    recorder_entity_filter   = ha_recorder.entity_filter
    recorder_remove_listener = ha_recorder._event_listener

    def entity_filter(entity_id):
        """
        Prefilter an entity to see if it should be excluded from
        the recorder history.

        This function is injected into the recorder, replacing the
        original HA recorder_entity_filter module.

        Return:
            False - The entity should is in the filter list
            Run the original HA recorder_entity_filter function -
                The entity is not in the filter list.
        """
        if (entity_id
                and entity_id in hass.data['recorder_prefilter']['exclude_entities']):
            return False

        return recorder_entity_filter(entity_id)

    try:
        _LOGGER.info("Recorder Prefilter Injection Started")
        _LOGGER.debug("Injecting Custom Exclude Entity Prefilter into Recorder")
        ha_recorder.entity_filter = entity_filter

        _LOGGER.debug("Removing Recorder Event Listener")
        recorder_remove_listener()

        _LOGGER.debug("Reinitializing Recorder Event Listener")
        hass.add_job(ha_recorder.async_initialize)

        _LOGGER.info(f"Recorder Prefilter Injection Completed")

        return True

    except Exception as err:
        _LOGGER.info(f"Recorder Prefilter Injection Failed ({err})")
        _LOGGER.exception(err)

    return False


def _update_filter(hass: HomeAssistant, entities=None, remove=False):
    """ Update the filtered entity list """

    mode = 'Removed' if remove else 'Added'
    cust_component = _called_from()
    entities_cnt = 1 if type(entities) is str else len(entities)

    _LOGGER.debug(f"{mode} Prefilter Entities ({cust_component})-{entities}")
    _LOGGER.info(f"{mode} Recorder Prefilter Entities "
                    f"({cust_component})-{entities_cnt}")

    entities =  [entities]  if type(entities) is str else \
                entities    if type(entities) is list else \
                []


    rp_data = hass.data.get('recorder_prefilter')
    rp_exclude_entities = rp_data['exclude_entities']

    for entity in entities:
        if entity.find('.') == -1:
            entity = f"sensor.{entity}"
        if entity not in rp_exclude_entities:
            if remove is False:
                rp_exclude_entities.append(entity)
            elif entity in rp_exclude_entities:
                rp_exclude_entities.remove(entity)

    _LOGGER.debug(f"All Prefiltered Entities-{sorted(rp_exclude_entities)}")
    _LOGGER.info(f"Recorder Prefilter Entities Updated, "
                    f"Entities Filtered-{len(rp_exclude_entities)}")


def _called_from():
    cust_component = getframeinfo(stack()[0][0]).filename
    return cust_component.split('custom_components/')[1].split('/')[0]
