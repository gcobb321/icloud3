

from ...global_variables    import GlobalVariables as Gb
from ...const               import (IPHONE, IPAD, IPAD_CELL, MAC, WATCH, WATCH_WIFI, AIRPODS, NO_MOBAPP, OTHER, )
from ...const_config        import (CONF_EVLOG_CARD_DIRECTORY,
                                    CONF_EVLOG_BTNCONFIG_URL, CONF_TRACK_FROM_BASE_ZONE_USED,
                                    CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                                    CONF_INZONE_INTERVALS, CONF_UNIT_OF_MEASUREMENT,
                                    CONF_TIME_FORMAT, CONF_MAX_INTERVAL, CONF_OFFLINE_INTERVAL,
                                    CONF_EXIT_ZONE_INTERVAL, CONF_MOBAPP_ALIVE_INTERVAL,
                                    CONF_GPS_ACCURACY_THRESHOLD, CONF_OLD_LOCATION_THRESHOLD,
                                    CONF_OLD_LOCATION_ADJUSTMENT, CONF_TRAVEL_TIME_FACTOR,
                                    CONF_TFZ_TRACKING_MAX_DISTANCE, CONF_PASSTHRU_ZONE_TIME,
                                    CONF_DISPLAY_ZONE_FORMAT, CONF_DEVICE_TRACKER_STATE_SOURCE,
                                    CONF_DISPLAY_GPS_LAT_LONG, CONF_DISCARD_POOR_GPS_INZONE,
                                    CONF_DISTANCE_BETWEEN_DEVICES, CONF_WAZE_USED,
                                    CONF_WAZE_SERVER, CONF_WAZE_MAX_DISTANCE,
                                    CONF_WAZE_MIN_DISTANCE, CONF_WAZE_REALTIME,
                                    CONF_WAZE_HISTORY_DATABASE_USED,
                                    CONF_WAZE_HISTORY_MAX_DISTANCE,
                                    CONF_WAZE_HISTORY_TRACK_DIRECTION, CONF_STAT_ZONE_FNAME,
                                    CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                    CONF_DATA_SOURCE,
                                    CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                    CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                    CF_PROFILE, )

from ...utils.utils         import (instr, is_empty, dict_value_to_list, six_item_dict, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..                     import utils_cf
from ..const_form_lists     import *


from   homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   PARAMETERS FLOW FORMS
#
#       - form_away_time_zone
#       - form_tracking_parameters
#       - form_format_settings
#       - form_inzone_intervals
#       - form_waze_main
#       - form_special_zones
#       - form_display_text_as_update
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            AWAY TIME ZONE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_away_time_zone(self):
    zone_2_used = (Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET] != 0
                    and Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES] != ['none'])

    schema = {
        vol.Required(CONF_AWAY_TIME_ZONE_1_DEVICES,
                    default=Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]):
                    cv.multi_select(six_item_dict(self.away_time_zone_devices_key_text)),
        vol.Required(CONF_AWAY_TIME_ZONE_1_OFFSET,
                    default=self.away_time_zone_hours_key_text[Gb.conf_general[CONF_AWAY_TIME_ZONE_1_OFFSET]]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.away_time_zone_hours_key_text), mode='dropdown')),

        vol.Required(CONF_AWAY_TIME_ZONE_2_DEVICES,
                    default=Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]):
                    cv.multi_select(six_item_dict(self.away_time_zone_devices_key_text)),
        vol.Required(CONF_AWAY_TIME_ZONE_2_OFFSET,
                    default=self.away_time_zone_hours_key_text[Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET]]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.away_time_zone_hours_key_text), mode='dropdown')),

        }

    return utils_cf.sectioned_schema(self, schema, [
            ('zone_1_section', [CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES], True),
            ('zone_2_section', [CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES],
                                    zone_2_used),
            ],
            utils_cf.submit_back_field(self, 'save', 'cancel_goto_menu', utils_cf.menu_name(self)))


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            TRACKING PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_tracking_parameters(self):

    schema = {
        vol.Optional('data_source',
                    default=utils_cf.option_parm_key(self, CONF_DATA_SOURCE, DATA_SOURCE_OPTIONS)):
                    utils_cf.select(DATA_SOURCE_OPTIONS, translation_key='data_source', mode='dropdown'),
        vol.Optional(CONF_DISTANCE_BETWEEN_DEVICES,
                    default=Gb.conf_general[CONF_DISTANCE_BETWEEN_DEVICES]):
                    selector.BooleanSelector(),
        vol.Optional(CONF_DISCARD_POOR_GPS_INZONE,
                    default=Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]):
                    selector.BooleanSelector(),
        vol.Optional(CONF_GPS_ACCURACY_THRESHOLD,
                    default=Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=300, step=5, unit_of_measurement='m')),
        vol.Optional(CONF_OLD_LOCATION_THRESHOLD,
                    default=Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=1, max=60, step=1, unit_of_measurement='min')),
        vol.Optional(CONF_OLD_LOCATION_ADJUSTMENT,
                    default=Gb.conf_general[CONF_OLD_LOCATION_ADJUSTMENT]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=60, step=1, unit_of_measurement='min')),
        vol.Optional(CONF_MAX_INTERVAL,
                    default=Gb.conf_general[CONF_MAX_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=15, max=480, step=5, unit_of_measurement='min')),
        vol.Optional(CONF_EXIT_ZONE_INTERVAL,
                    default=Gb.conf_general[CONF_EXIT_ZONE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=.5, max=10, step=.5, unit_of_measurement='min')),
        vol.Optional(CONF_MOBAPP_ALIVE_INTERVAL,
                    default=Gb.conf_general[CONF_MOBAPP_ALIVE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=15, max=240, step=5, unit_of_measurement='min')),
        vol.Optional(CONF_OFFLINE_INTERVAL,
                    default=Gb.conf_general[CONF_OFFLINE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=240, step=5, unit_of_measurement='min')),
        vol.Optional(CONF_TFZ_TRACKING_MAX_DISTANCE,
                    default=utils_cf.km_field_default(CONF_TFZ_TRACKING_MAX_DISTANCE)):
                    utils_cf.km_field_selector(CONF_TFZ_TRACKING_MAX_DISTANCE, 1, 100),
        vol.Optional(CONF_TRAVEL_TIME_FACTOR,
                    default=utils_cf.option_parm_key(self, CONF_TRAVEL_TIME_FACTOR, TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT)):
                    utils_cf.select(TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT, translation_key='travel_time_factor', mode='dropdown'),

        }

    return utils_cf.sectioned_schema(self, schema, [
            ('data_sources_section', ['data_source'], True),
            ('location_accuracy_section', [CONF_GPS_ACCURACY_THRESHOLD, CONF_DISCARD_POOR_GPS_INZONE,
                                    CONF_OLD_LOCATION_THRESHOLD], False),
            ('intervals_section', [CONF_MAX_INTERVAL, CONF_EXIT_ZONE_INTERVAL, CONF_OFFLINE_INTERVAL,
                                    CONF_TRAVEL_TIME_FACTOR], False),
            (ADVANCED_SECTION, [CONF_OLD_LOCATION_ADJUSTMENT, CONF_MOBAPP_ALIVE_INTERVAL,
                                    CONF_DISTANCE_BETWEEN_DEVICES, CONF_TFZ_TRACKING_MAX_DISTANCE], False),
            ],
            utils_cf.submit_back_field(self, 'save', 'cancel_goto_menu', utils_cf.menu_name(self)))


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              FORMAT SETTINGS & ICLOUD3 DIRECTORIES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_format_settings(self):
    display_zone_format_options = build_display_zone_format_options(self)

    schema = {
        vol.Optional(CONF_DISPLAY_ZONE_FORMAT,
                    default=utils_cf.option_parm_key(self, CONF_DISPLAY_ZONE_FORMAT, display_zone_format_options)):
                    utils_cf.select(display_zone_format_options),
        vol.Optional(CONF_DEVICE_TRACKER_STATE_SOURCE,
                    default=utils_cf.option_parm_key(self, CONF_DEVICE_TRACKER_STATE_SOURCE, DEVICE_TRACKER_STATE_SOURCE_OPTIONS)):
                    utils_cf.select(DEVICE_TRACKER_STATE_SOURCE_OPTIONS, translation_key='device_tracker_state_source', mode='dropdown'),
        vol.Optional(CONF_UNIT_OF_MEASUREMENT,
                    default=utils_cf.option_parm_key(self, CONF_UNIT_OF_MEASUREMENT, UNIT_OF_MEASUREMENT_OPTIONS)):
                    utils_cf.select(UNIT_OF_MEASUREMENT_OPTIONS, translation_key='unit_of_measurement', mode='dropdown'),
        vol.Optional(CONF_TIME_FORMAT,
                    default=utils_cf.option_parm_key(self, CONF_TIME_FORMAT, TIME_FORMAT_OPTIONS)):
                    utils_cf.select(TIME_FORMAT_OPTIONS, translation_key='time_format', mode='dropdown'),
        vol.Optional(CONF_DISPLAY_GPS_LAT_LONG,
                    default=Gb.conf_general[CONF_DISPLAY_GPS_LAT_LONG]):
                    # cv.boolean,
                    selector.BooleanSelector(),

        vol.Optional(CONF_EVLOG_CARD_DIRECTORY,
                    default=utils_cf.parm_or_error_msg(self, CONF_EVLOG_CARD_DIRECTORY, conf_group=CF_PROFILE)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.www_directory_list), mode='dropdown')),
        vol.Optional(CONF_EVLOG_BTNCONFIG_URL,
                    default=f"{utils_cf.parm_or_error_msg(self, CONF_EVLOG_BTNCONFIG_URL, conf_group=CF_PROFILE)} "):
                    selector.TextSelector(),

        }

    return utils_cf.sectioned_schema(self, schema, [
            ('units_time_section', [CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT], True),
            ('zone_names_section', [CONF_DISPLAY_ZONE_FORMAT, CONF_DEVICE_TRACKER_STATE_SOURCE], False),
            ('event_log_section', [CONF_DISPLAY_GPS_LAT_LONG], False),
            (ADVANCED_SECTION, [CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_BTNCONFIG_URL], False),
            ],
            utils_cf.submit_back_field(self, 'save', 'cancel_goto_menu', utils_cf.menu_name(self)))


#-------------------------------------------------------------------------------------------
def build_display_zone_format_options(self):
    '''
    The selector.display_zone_format.options labels, the examples (the_shores, The Shores,
    TheShores) are replaced with a zone of this HA
    '''
    display_zone_format_options = {key: utils_cf.tr_option('display_zone_format', key)
                                        for key in DISPLAY_ZONE_FORMAT_OPTIONS_BASE}

    Zone = [Zone    for zone, Zone in Gb.HAZones_by_zone.items()
                    if instr(Zone.zone, '_')]
    if Zone == []:
        Zone = [Zone    for zone, Zone in Gb.HAZones_by_zone.items()
                        if  zone != 'home']

    if is_empty(Zone) :
        return display_zone_format_options

    exZone = Zone[0]
    example_to_real = {
        # 'zone.the_shores → TheShores': f"zone.{exZone.zone} → {exZone.fname}",
        # 'zone.the_shores → The Shores': f"zone.{exZone.zone} → {exZone.title}",
        'the_shores': exZone.zone,
        'The Shores': exZone.title,
        'TheShores': exZone.fname.replace(' ', ''),
    }

    for key, text in display_zone_format_options.items():
        for example, real in example_to_real.items():
            if instr(text, example) is False:
                continue
            text = text.replace(example, real)
        display_zone_format_options[key] = text

    return display_zone_format_options


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISPLAY TEXT AS UPDATE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_display_text_as_update(self):
    if instr(self.dta_working_copy[self.dta_selected_idx], '>'):
        text_from_to_parts = self.dta_working_copy[self.dta_selected_idx].split('>')
        text_from = text_from_to_parts[0].strip()
        text_to   = text_from_to_parts[1].strip()
    else:
        text_from = ''
        text_to   = ''

    return vol.Schema({
        vol.Optional('text_from',
                    default=text_from):
                    selector.TextSelector(),
        vol.Optional('text_to'  ,
                    default=text_to):
                    selector.TextSelector(),
        **utils_cf.submit_back_field(self, 'update_text_as', 'cancel_goto_previous',
                                        'text_list',
                                        other_actions={'delete_text_as': utils_cf.tr('action_delete_text_as')}
                                                        if text_from else None),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            INZONE INTERVALS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_inzone_intervals(self):
    schema = {
        vol.Optional(IPHONE,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][IPHONE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=360, step=5, unit_of_measurement='min')),
        vol.Optional(WATCH,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][WATCH]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=360, step=5, unit_of_measurement='min')),
        vol.Optional(WATCH_WIFI,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][WATCH_WIFI]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=360, step=5, unit_of_measurement='min')),
        vol.Optional(IPAD,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][IPAD]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=360, step=5, unit_of_measurement='min')),
        vol.Optional(IPAD_CELL,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][IPAD_CELL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=360, step=5, unit_of_measurement='min')),
        vol.Optional(MAC,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][MAC]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=360, step=5, unit_of_measurement='min')),
        # vol.Optional(AIRPODS,
        #             default=Gb.conf_general[CONF_INZONE_INTERVALS][AIRPODS]):
        #             selector.NumberSelector(selector.NumberSelectorConfig(
        #                 min=5, max=480, step=5, unit_of_measurement='min')),
        vol.Optional(NO_MOBAPP,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][NO_MOBAPP]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=360, step=5, unit_of_measurement='min')),
        vol.Optional(OTHER,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][OTHER]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=360, step=5, unit_of_measurement='min')),

        }

    return utils_cf.sectioned_schema(self, schema, [
            ('phones_watches_section', [IPHONE, WATCH, WATCH_WIFI], True),
            ('tablets_macs_section', [IPAD, IPAD_CELL, MAC], False),
            ('special_section', [NO_MOBAPP, OTHER], False),
            ],
            utils_cf.submit_back_field(self, 'save', 'cancel_goto_menu', utils_cf.menu_name(self)))

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            WAZE MAIN
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_waze_main(self):

    schema = {
        vol.Optional(CONF_WAZE_USED,
                    default=Gb.conf_general[CONF_WAZE_USED]):
                    selector.BooleanSelector(),
        vol.Optional(CONF_WAZE_SERVER,
                    default=utils_cf.option_parm_key(self, CONF_WAZE_SERVER, WAZE_SERVER_OPTIONS)):
                    utils_cf.select(WAZE_SERVER_OPTIONS, translation_key='waze_server', mode='dropdown'),
        vol.Optional(CONF_WAZE_MIN_DISTANCE,
                    default=utils_cf.km_field_default(CONF_WAZE_MIN_DISTANCE)):
                    utils_cf.km_field_selector(CONF_WAZE_MIN_DISTANCE, 0, 100, 5),
        vol.Optional(CONF_WAZE_MAX_DISTANCE,
                    default=utils_cf.km_field_default(CONF_WAZE_MAX_DISTANCE)):
                    utils_cf.km_field_selector(CONF_WAZE_MAX_DISTANCE, 0, 1000, 5),
        vol.Optional(CONF_WAZE_REALTIME,
                    default=Gb.conf_general[CONF_WAZE_REALTIME]):
                    selector.BooleanSelector(),

        vol.Required(CONF_WAZE_HISTORY_DATABASE_USED,
                    default=Gb.conf_general[CONF_WAZE_HISTORY_DATABASE_USED]):
                    selector.BooleanSelector(),
        vol.Required(CONF_WAZE_HISTORY_MAX_DISTANCE,
                    default=utils_cf.km_field_default(CONF_WAZE_HISTORY_MAX_DISTANCE)):
                    utils_cf.km_field_selector(CONF_WAZE_HISTORY_MAX_DISTANCE, 0, 1000, 5),
        vol.Optional(CONF_WAZE_HISTORY_TRACK_DIRECTION,
                    default=utils_cf.option_parm_key(self, CONF_WAZE_HISTORY_TRACK_DIRECTION, WAZE_HISTORY_TRACK_DIRECTION_OPTIONS)):
                    utils_cf.select(WAZE_HISTORY_TRACK_DIRECTION_OPTIONS, translation_key='waze_history_track_direction', mode='dropdown'),

        }

    return utils_cf.sectioned_schema(self, schema, [
            ('route_service_section', [CONF_WAZE_USED, CONF_WAZE_SERVER, CONF_WAZE_REALTIME,
                                    CONF_WAZE_MIN_DISTANCE, CONF_WAZE_MAX_DISTANCE], True),
            ('history_database_section', [CONF_WAZE_HISTORY_DATABASE_USED, CONF_WAZE_HISTORY_MAX_DISTANCE,
                                    CONF_WAZE_HISTORY_TRACK_DIRECTION],
                                    Gb.conf_general[CONF_WAZE_HISTORY_DATABASE_USED]),
            ],
            utils_cf.submit_back_field(self, 'save', 'cancel_goto_menu', utils_cf.menu_name(self)))


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SPECIAL ZONES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_special_zones(self):

    try:
        pass_thru_zone_used  = (Gb.conf_general[CONF_PASSTHRU_ZONE_TIME] > 0)
        stat_zone_used       = (Gb.conf_general[CONF_STAT_ZONE_STILL_TIME] > 0)
        track_from_base_zone_used = Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE_USED]


        schema = {
            vol.Required('stat_zone_header',
                        default=stat_zone_used):
                        selector.BooleanSelector(),
            vol.Required(CONF_STAT_ZONE_FNAME,
                        default=utils_cf.parm_or_error_msg(self, CONF_STAT_ZONE_FNAME)):
                        selector.TextSelector(),
            vol.Required(CONF_STAT_ZONE_STILL_TIME,
                        default=Gb.conf_general[CONF_STAT_ZONE_STILL_TIME]):
                        selector.NumberSelector(selector.NumberSelectorConfig(
                            min=0, max=60, unit_of_measurement='min')),
            vol.Required(CONF_STAT_ZONE_INZONE_INTERVAL,
                        default=Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL]):
                        selector.NumberSelector(selector.NumberSelectorConfig(
                            min=5, max=60, step=5, unit_of_measurement='min')),

            vol.Optional('passthru_zone_header',
                        default=pass_thru_zone_used):
                        selector.BooleanSelector(),
            vol.Required(CONF_PASSTHRU_ZONE_TIME,
                        default=Gb.conf_general[CONF_PASSTHRU_ZONE_TIME]):
                        selector.NumberSelector(selector.NumberSelectorConfig(
                            min=0, max=5, step=.5, unit_of_measurement='min')),

            vol.Optional(CONF_TRACK_FROM_BASE_ZONE_USED,
                        default=track_from_base_zone_used):
                        selector.BooleanSelector(),
            vol.Optional(CONF_TRACK_FROM_BASE_ZONE,
                        default=utils_cf.zone_entity_ids(Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE])):
                        utils_cf.zone_selector(self),
            vol.Optional(CONF_TRACK_FROM_HOME_ZONE,
                        default=Gb.conf_general[CONF_TRACK_FROM_HOME_ZONE]):
                        # cv.boolean,
                        selector.BooleanSelector(),

            }

        return utils_cf.sectioned_schema(self, schema, [
                ('stat_zone_section', ['stat_zone_header', CONF_STAT_ZONE_FNAME, CONF_STAT_ZONE_STILL_TIME,
                                    CONF_STAT_ZONE_INZONE_INTERVAL], True),
                ('enter_zone_delay_section', ['passthru_zone_header', CONF_PASSTHRU_ZONE_TIME],
                                    pass_thru_zone_used),
                ('home_zone_override_section', [CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE,
                                    CONF_TRACK_FROM_HOME_ZONE], track_from_base_zone_used),
                ],
                utils_cf.submit_back_field(self, 'save', 'cancel_goto_menu', utils_cf.menu_name(self)))
    except Exception as err:
        log_exception(err)
