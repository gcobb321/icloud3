

from ...global_variables    import GlobalVariables as Gb
from ...const               import (IPHONE, IPAD, WATCH, AIRPODS, NO_MOBAPP, OTHER,
                                    PICTURE_WWW_STANDARD_DIRS, CONF_PICTURE_WWW_DIRS,
                                    CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_BTNCONFIG_URL,
                                    CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                                    CONF_INZONE_INTERVALS,
                                    CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT,
                                    CONF_MAX_INTERVAL, CONF_OFFLINE_INTERVAL, CONF_EXIT_ZONE_INTERVAL, CONF_MOBAPP_ALIVE_INTERVAL,
                                    CONF_GPS_ACCURACY_THRESHOLD, CONF_OLD_LOCATION_THRESHOLD, CONF_OLD_LOCATION_ADJUSTMENT,
                                    CONF_TRAVEL_TIME_FACTOR, CONF_TFZ_TRACKING_MAX_DISTANCE,
                                    CONF_PASSTHRU_ZONE_TIME,
                                    CONF_DISPLAY_ZONE_FORMAT, CONF_DEVICE_TRACKER_STATE_SOURCE, CONF_DISPLAY_GPS_LAT_LONG,
                                    CONF_DISCARD_POOR_GPS_INZONE,
                                    CONF_DISTANCE_BETWEEN_DEVICES,
                                    CONF_WAZE_USED, CONF_WAZE_SERVER, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                                    CONF_WAZE_REALTIME, CONF_WAZE_HISTORY_DATABASE_USED, CONF_WAZE_HISTORY_MAX_DISTANCE,
                                    CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                    CONF_STAT_ZONE_FNAME, CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                    CONF_DISPLAY_TEXT_AS,
                                    CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                    CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                    CF_PROFILE,
                                    )

from ...utils.utils         import (instr, is_empty, dict_value_to_list, six_item_list, six_item_dict, )
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
#       - form_display_text_as
#       - form_display_text_as_update
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            AWAY TIME ZONE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_away_time_zone(self):
    self.actions_list = []
    self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

    return vol.Schema({
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

        vol.Required('action_items',
                    default=utils_cf.default_action_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            TRACKING PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_tracking_parameters(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()

    return vol.Schema({
        vol.Required(CONF_DISTANCE_BETWEEN_DEVICES,
                    default=Gb.conf_general[CONF_DISTANCE_BETWEEN_DEVICES]):
                    selector.BooleanSelector(),
        vol.Optional(CONF_DISCARD_POOR_GPS_INZONE,
                    default=Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]):
                    selector.BooleanSelector(),
        vol.Required(CONF_GPS_ACCURACY_THRESHOLD,
                    default=Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=300, step=5, unit_of_measurement='m')),
        vol.Required(CONF_OLD_LOCATION_THRESHOLD,
                    default=Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=1, max=60, step=1, unit_of_measurement='minutes')),
        vol.Required(CONF_OLD_LOCATION_ADJUSTMENT,
                    default=Gb.conf_general[CONF_OLD_LOCATION_ADJUSTMENT]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=60, step=1, unit_of_measurement='minutes')),
        vol.Required(CONF_MAX_INTERVAL,
                    default=Gb.conf_general[CONF_MAX_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=15, max=480, step=5, unit_of_measurement='minutes')),
        vol.Required(CONF_EXIT_ZONE_INTERVAL,
                    default=Gb.conf_general[CONF_EXIT_ZONE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=.5, max=10, step=.5, unit_of_measurement='minutes')),
        vol.Required(CONF_MOBAPP_ALIVE_INTERVAL,
                    default=Gb.conf_general[CONF_MOBAPP_ALIVE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=15, max=240, step=5, unit_of_measurement='minutes')),
        vol.Required(CONF_OFFLINE_INTERVAL,
                    default=Gb.conf_general[CONF_OFFLINE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=240, step=5, unit_of_measurement='minutes')),
        vol.Required(CONF_TFZ_TRACKING_MAX_DISTANCE,
                    default=Gb.conf_general[CONF_TFZ_TRACKING_MAX_DISTANCE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=1, max=100, unit_of_measurement='Km')),
        vol.Optional(CONF_TRAVEL_TIME_FACTOR,
                    default=utils_cf.option_parm_to_text(self, CONF_TRAVEL_TIME_FACTOR, TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT), mode='dropdown')),

        vol.Required('action_items',
                    default=utils_cf.default_action_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              FORMAT SETTINGS & ICLOUD3 DIRECTORIES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_format_settings(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()
    display_zone_format_options = build_display_zone_format_options(self)

    self.picture_by_filename = {}
    if PICTURE_WWW_STANDARD_DIRS in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
        Gb.conf_profile[CONF_PICTURE_WWW_DIRS] = []

    return vol.Schema({
        vol.Optional(CONF_DISPLAY_ZONE_FORMAT,
                    default=utils_cf.option_parm_to_text(self, CONF_DISPLAY_ZONE_FORMAT, display_zone_format_options)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(display_zone_format_options), mode='dropdown')),
        vol.Optional(CONF_DEVICE_TRACKER_STATE_SOURCE,
                    default=utils_cf.option_parm_to_text(self, CONF_DEVICE_TRACKER_STATE_SOURCE, DEVICE_TRACKER_STATE_SOURCE_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(DEVICE_TRACKER_STATE_SOURCE_OPTIONS), mode='dropdown')),
        vol.Optional(CONF_UNIT_OF_MEASUREMENT,
                    default=utils_cf.option_parm_to_text(self, CONF_UNIT_OF_MEASUREMENT, UNIT_OF_MEASUREMENT_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list( UNIT_OF_MEASUREMENT_OPTIONS), mode='dropdown')),
        vol.Optional(CONF_TIME_FORMAT,
                    default=utils_cf.option_parm_to_text(self, CONF_TIME_FORMAT, TIME_FORMAT_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(TIME_FORMAT_OPTIONS), mode='dropdown')),
        vol.Optional(CONF_PICTURE_WWW_DIRS,
                    default=Gb.conf_profile[CONF_PICTURE_WWW_DIRS] or self.www_directory_list):
                    cv.multi_select(six_item_list(self.www_directory_list)),
        vol.Optional(CONF_DISPLAY_GPS_LAT_LONG,
                    default=Gb.conf_general[CONF_DISPLAY_GPS_LAT_LONG]):
                    # cv.boolean,
                    selector.BooleanSelector(),

        vol.Optional('evlog_header',
                    default=IC3_DIRECTORY_HEADER):
                    # cv.multi_select([IC3_DIRECTORY_HEADER]),
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=[IC3_DIRECTORY_HEADER], mode='list')),
        vol.Optional(CONF_EVLOG_CARD_DIRECTORY,
                    default=utils_cf.parm_or_error_msg(self, CONF_EVLOG_CARD_DIRECTORY, conf_group=CF_PROFILE)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.www_directory_list), mode='dropdown')),
        vol.Optional(CONF_EVLOG_BTNCONFIG_URL,
                    default=f"{utils_cf.parm_or_error_msg(self, CONF_EVLOG_BTNCONFIG_URL, conf_group=CF_PROFILE)} "):
                    selector.TextSelector(),

        vol.Optional('action_items',
                    default=utils_cf.default_action_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#-------------------------------------------------------------------------------------------
def build_display_zone_format_options(self):
    '''
    This is used in config_flow_forms

    'fname': 'HA Zone Friendly Name used by zone automation triggers (TheShores)',
    'zone': 'HA Zone entity_id (the_shores)',
    'name': 'iCloud3 reformated Zone entity_id (zone.the_shores → TheShores)',
    'title': 'iCloud3 reformated Zone entity_id (zone.the_shores → The Shores)'

    example_to_real = { 'the_shores': 'the_point',
                        'The Shores': 'The Point',
                        'TheShores': 'The Point'}
    '''
    display_zone_format_options = DISPLAY_ZONE_FORMAT_OPTIONS_BASE.copy()

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
#            DISPLAY TEXT AS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_display_text_as(self):
    self.dta_selected_idx = self.dta_selected_idx_page[self.dta_page_no]
    if self.dta_selected_idx <= 4:
        dta_page_display_list = [v for k,v in self.dta_working_copy.items()
                                        if k <= 4]
        dta_next_page_display_list = [v.split('>')[0] for k,v in self.dta_working_copy.items()
                                        if k >= 5]
    else:
        dta_page_display_list = [v for k,v in self.dta_working_copy.items()
                                        if k >= 5]
        dta_next_page_display_list = [v.split('>')[0] for k,v in self.dta_working_copy.items()
                                        if k <= 4]

    dta_next_page_display_items = ", ".join(dta_next_page_display_list)
    next_page_text = ACTION_LIST_OPTIONS['next_page_items']
    next_page_text = next_page_text.replace('^add-text^', dta_next_page_display_items)

    self.actions_list = [next_page_text]
    self.actions_list.extend([ACTION_LIST_OPTIONS['select_text_as']])
    self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

    return vol.Schema({
        vol.Required(CONF_DISPLAY_TEXT_AS,
                    default=self.dta_working_copy[self.dta_selected_idx]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dta_page_display_list)),
        vol.Required('action_items',
                    default=utils_cf.default_action_text('select_text_as')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISPLAY TEXT AS UPDATE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_display_text_as_update(self):
    self.actions_list = [ACTION_LIST_OPTIONS['clear_text_as']]
    self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

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
        vol.Required('action_items',
                    default=utils_cf.default_action_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            INZONE INTERVALS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_inzone_intervals(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()
    return vol.Schema({
        vol.Optional(IPHONE,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][IPHONE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
        vol.Optional(IPAD,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][IPAD]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
        vol.Optional(WATCH,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][WATCH]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
        vol.Optional(AIRPODS,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][AIRPODS]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
        vol.Optional(NO_MOBAPP,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][NO_MOBAPP]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
        vol.Optional(OTHER,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][OTHER]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),

        vol.Optional('action_items',
                    default=utils_cf.default_action_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            WAZE MAIN
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_waze_main(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()

    wuh_default  = [WAZE_USED_HEADER] if Gb.conf_general[CONF_WAZE_USED] else []
    whuh_default = [WAZE_HISTORY_USED_HEADER] if Gb.conf_general[CONF_WAZE_HISTORY_DATABASE_USED] else []
    return vol.Schema({
        vol.Optional(CONF_WAZE_USED,
                    default=wuh_default):
                    cv.multi_select([WAZE_USED_HEADER]),
        vol.Optional(CONF_WAZE_SERVER,
                    default=utils_cf.option_parm_to_text(self, CONF_WAZE_SERVER, WAZE_SERVER_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(WAZE_SERVER_OPTIONS), mode='dropdown')),
        vol.Optional(CONF_WAZE_MIN_DISTANCE,
                    default=Gb.conf_general[CONF_WAZE_MIN_DISTANCE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=100, step=5, unit_of_measurement='km')),
        vol.Optional(CONF_WAZE_MAX_DISTANCE,
                    default=Gb.conf_general[CONF_WAZE_MAX_DISTANCE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=1000, step=5, unit_of_measurement='km')),
        vol.Optional(CONF_WAZE_REALTIME,
                    default=Gb.conf_general[CONF_WAZE_REALTIME]):
                    selector.BooleanSelector(),

        vol.Required(CONF_WAZE_HISTORY_DATABASE_USED,
                    default=whuh_default):
                    cv.multi_select([WAZE_HISTORY_USED_HEADER]),
        vol.Required(CONF_WAZE_HISTORY_MAX_DISTANCE,
                    default=Gb.conf_general[CONF_WAZE_HISTORY_MAX_DISTANCE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=1000, step=5, unit_of_measurement='km')),
        vol.Optional(CONF_WAZE_HISTORY_TRACK_DIRECTION,
                    default=utils_cf.option_parm_to_text(self, CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                                        WAZE_HISTORY_TRACK_DIRECTION_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(WAZE_HISTORY_TRACK_DIRECTION_OPTIONS), mode='dropdown')),

        vol.Required('action_items',
                    default=utils_cf.default_action_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SPECIAL ZONES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_special_zones(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()

    try:
        pass_thru_zone_used  = (Gb.conf_general[CONF_PASSTHRU_ZONE_TIME] > 0)
        stat_zone_used       = (Gb.conf_general[CONF_STAT_ZONE_STILL_TIME] > 0)
        track_from_base_zone_used = Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE_USED]

        ptzh_default = [PASSTHRU_ZONE_HEADER] if pass_thru_zone_used else []
        szh_default  = [STAT_ZONE_HEADER] if stat_zone_used else []
        tfzh_default = [TRK_FROM_HOME_ZONE_HEADER] if track_from_base_zone_used else []

        return vol.Schema({
            vol.Required('stat_zone_header',
                        default=szh_default):
                        cv.multi_select([STAT_ZONE_HEADER]),
            vol.Required(CONF_STAT_ZONE_FNAME,
                        default=utils_cf.parm_or_error_msg(self, CONF_STAT_ZONE_FNAME)):
                        selector.TextSelector(),
            vol.Required(CONF_STAT_ZONE_STILL_TIME,
                        default=Gb.conf_general[CONF_STAT_ZONE_STILL_TIME]):
                        selector.NumberSelector(selector.NumberSelectorConfig(
                            min=0, max=60, unit_of_measurement='minutes')),
            vol.Required(CONF_STAT_ZONE_INZONE_INTERVAL,
                        default=Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL]):
                        selector.NumberSelector(selector.NumberSelectorConfig(
                            min=5, max=60, step=5, unit_of_measurement='minutes')),

            vol.Optional('passthru_zone_header',
                        default=ptzh_default):
                        cv.multi_select([PASSTHRU_ZONE_HEADER]),
            vol.Required(CONF_PASSTHRU_ZONE_TIME,
                        default=Gb.conf_general[CONF_PASSTHRU_ZONE_TIME]):
                        selector.NumberSelector(selector.NumberSelectorConfig(
                            min=0, max=5, step=.5, unit_of_measurement='minutes')),

            vol.Optional(CONF_TRACK_FROM_BASE_ZONE_USED,
                        default=tfzh_default):
                        cv.multi_select([TRK_FROM_HOME_ZONE_HEADER]),
            vol.Optional(CONF_TRACK_FROM_BASE_ZONE,
                        default=utils_cf.option_parm_to_text(self, CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text)):
                        selector.SelectSelector(selector.SelectSelectorConfig(
                            options=dict_value_to_list(self.zone_name_key_text), mode='dropdown')),
            vol.Optional(CONF_TRACK_FROM_HOME_ZONE,
                        default=Gb.conf_general[CONF_TRACK_FROM_HOME_ZONE]):
                        # cv.boolean,
                        selector.BooleanSelector(),

            vol.Required('action_items',
                        default=utils_cf.default_action_text('save')):
                        selector.SelectSelector(selector.SelectSelectorConfig(
                            options=self.actions_list, mode='list')),
            })
    except Exception as err:
        log_exception(err)
