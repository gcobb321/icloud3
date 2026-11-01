

from ...global_variables    import GlobalVariables as Gb
from ...const               import (MONITOR, INACTIVE, )
from ...const_config        import (CONF_TFZ_TRACKING_MAX_DISTANCE, CONF_WAZE_HISTORY_MAX_DISTANCE, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE, CONF_DISPLAY_TEXT_AS,
                                    CONF_IC3_DEVICENAME, CONF_FNAME, CONF_DATA_SOURCE,
                                    CONF_TRACKING_MODE, CONF_AWAY_TIME_ZONE_1_OFFSET,
                                    CONF_AWAY_TIME_ZONE_1_DEVICES, CONF_AWAY_TIME_ZONE_2_OFFSET,
                                    CONF_AWAY_TIME_ZONE_2_DEVICES, CONF_EVLOG_BTNCONFIG_URL,
                                    CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE,
                                    CONF_TRACK_FROM_HOME_ZONE, CONF_INZONE_INTERVALS,
                                    CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT,
                                    CONF_TRAVEL_TIME_FACTOR, CONF_PASSTHRU_ZONE_TIME,
                                    CONF_DISPLAY_ZONE_FORMAT, CONF_DEVICE_TRACKER_STATE_SOURCE,
                                    CONF_WAZE_USED, CONF_WAZE_SERVER,
                                    CONF_WAZE_HISTORY_DATABASE_USED,
                                    CONF_WAZE_HISTORY_TRACK_DIRECTION, CONF_STAT_ZONE_STILL_TIME,
                                    CONF_PARAMETER_TIME_STR, CONF_PARAMETER_FLOAT,
                                    DEFAULT_GENERAL_CONF, CF_GENERAL, CF_TRACKING, )

from ...utils.utils         import (instr, is_number, is_empty, isnot_empty, list_to_str, str_to_list,
                                    is_running_in_event_loop, is_between, list_del, list_add,
                                    dict_sort_values, apple_user,
                                    encode_password, decode_password, )
from ...utils.messaging     import (log_exception, log_debug_msg, log_info_msg, add_log_file_filter,
                                    _log, _evlog, more_info, write_config_file_to_ic3log, close_ic3log_file,
                                    post_event, post_alert, post_monitor_msg, post_greenbar_msg,
                                    update_alert_sensor, )

from .                      import form_parameters as forms
from ..                     import selection_lists as lists
from ..                     import sensors_cf
from ..                     import utils_cf
from ..const_form_lists     import *


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   PARAMETERS FLOW STEPS
#
#       - async_step_away_time_zone
#       - async_step_tracking_parameters
#       - async_step_format_settings
#       - async_step_inzone_intervals
#       - async_step_waze_main
#       - async_step_special_zones
#       - async_step_display_text_as
#       - async_step_display_text_as_update
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OptionsFlow_Parameters_Steps:

    def initialize_parameters_variables(self):
        '''
        Initialize the variables used by the Parameters screens. Called from the
        flow handler's initialize_options (the mixin's __init__ would never be run).
        '''
        # Variables used for the display_text_as update
        self.dta_selected_idx               = UNSELECTED_IDX # Current conf index being updated
        self.dta_working_copy               = {0: '', 1: '', 2: '', 3: '', 4: '', 5: '', 6: '', 7: '', 8: '', 9: '',}

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            AWAY TIME ZONE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_away_time_zone(self, user_input=None, errors=None):
        user_input = utils_cf.flatten_sections(user_input)
        user_input, action_item = self.initialize_step('away_time_zone', user_input, errors)

        lists.build_away_time_zone_devices_list(self)
        lists.build_away_time_zone_hours_list(self)

        if user_input is None:
            return self.async_show_form(step_id='away_time_zone',
                            data_schema=forms.form_away_time_zone(self),
                            errors=self.errors)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        user_input = self._unpack_ui_away_time_zone(user_input)

        user_input = self._update_away_time_zone_changes(user_input)

        if utils_cf.no_errors(self):
            self.update_config_file(CF_GENERAL, user_input, action_item)
            return await self.async_step_menu()

        return self.async_show_form(step_id= 'away_time_zone',
                            data_schema=forms.form_away_time_zone(self),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _unpack_ui_away_time_zone(self, user_input):

        '''
        Validate and reinitialize the local zone parameters
        '''
        if user_input is None: return

        user_input = utils_cf.option_text_to_parm( user_input,
                                                CONF_AWAY_TIME_ZONE_1_OFFSET,
                                                self.away_time_zone_hours_key_text)
        user_input = utils_cf.option_text_to_parm( user_input,
                                                CONF_AWAY_TIME_ZONE_2_OFFSET,
                                                self.away_time_zone_hours_key_text)

        return user_input

#-------------------------------------------------------------------------------------------
    def _update_away_time_zone_changes(self, user_input):

        conf_devices_1 = Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]
        conf_devices_2 = Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]
        conf_offset_1  = Gb.conf_general[CONF_AWAY_TIME_ZONE_1_OFFSET]
        conf_offset_2  = Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET]
        ui_devices_1   = user_input[CONF_AWAY_TIME_ZONE_1_DEVICES]
        ui_devices_2   = user_input[CONF_AWAY_TIME_ZONE_2_DEVICES]
        ui_offset_1    = user_input[CONF_AWAY_TIME_ZONE_1_OFFSET]
        ui_offset_2    = user_input[CONF_AWAY_TIME_ZONE_2_OFFSET]

        if (ui_devices_1 == conf_devices_1 and ui_devices_2 == conf_devices_2
                and ui_offset_1 == conf_offset_1 and ui_offset_2 == conf_offset_2):
            return user_input

        try:
            # none/all in ui and was not in conf -> remove any devices
            if 'none' in ui_devices_1 and conf_devices_1 != ['none']: ui_devices_1 = ['none']
            if 'none' in ui_devices_2 and conf_devices_2 != ['none']: ui_devices_2 = ['none']
            if 'all'  in ui_devices_1 and conf_devices_1 != ['all']:  ui_devices_1  = ['all']
            if 'all'  in ui_devices_2 and conf_devices_2 != ['all']:  ui_devices_2  = ['all']

            # none/all in ui and was in conf -> remove non/all and keep devices
            if 'none' in ui_devices_1 and conf_devices_1 == ['none']: list_del(ui_devices_1, 'none')
            if 'none' in ui_devices_2 and conf_devices_2 == ['none']: list_del(ui_devices_2, 'none')
            if 'all' in ui_devices_1  and conf_devices_1 == ['all']:  list_del(ui_devices_1, 'all')
            if 'all' in ui_devices_2  and conf_devices_2 == ['all']:  list_del(ui_devices_2, 'all')

            # Remove a device in _2 if it is also in _1
            for _devices in ui_devices_1:
                if _devices in ui_devices_2:
                    list_del(ui_devices_2, _devices)

            if ui_devices_1 == []: ui_devices_1 = ['none']
            if ui_devices_2 == []: ui_devices_2 = ['none']

            if ui_offset_1 == 0: ui_devices_1 = ['none']
            if ui_offset_2 == 0: ui_devices_2 = ['none']

        except Exception as err:
            log_exception(err)

        user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] = ui_devices_1
        user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] = ui_devices_2
        user_input[CONF_AWAY_TIME_ZONE_1_OFFSET]  = ui_offset_1
        user_input[CONF_AWAY_TIME_ZONE_2_OFFSET]  = ui_offset_2

        list_add(self.config_parms_update_control, 'devices')

        return user_input


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            TRACKING PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_tracking_parameters(self, user_input=None, errors=None):
        user_input = utils_cf.flatten_sections(user_input)
        user_input, action_item = self.initialize_step('tracking_parameters', user_input, errors)

        if user_input is None:
            return self.async_show_form(step_id='tracking_parameters',
                            data_schema=forms.form_tracking_parameters(self),
                            errors=self.errors)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        user_input = self._unpack_ui_tracking_parameters(user_input)

        if utils_cf.no_errors(self):
            user_input = utils_cf.select_value(user_input,
                                                                CONF_DATA_SOURCE,
                                                                DATA_SOURCE_OPTIONS)

            self.update_config_file(CF_GENERAL, user_input, action_item)
            return await self.async_step_menu()

        return self.async_show_form(step_id='tracking_parameters',
                            data_schema=forms.form_tracking_parameters(self),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _unpack_ui_tracking_parameters(self, user_input):
        if user_input is None: return None

        user_input = utils_cf.km_fields_from_ui(user_input, [CONF_TFZ_TRACKING_MAX_DISTANCE])

        user_input = utils_cf.select_value( user_input,
                                                CONF_TRAVEL_TIME_FACTOR,
                                                TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT)

        return user_input


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              FORMAT SETTINGS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_format_settings(self, user_input=None, errors=None):
        user_input = utils_cf.flatten_sections(user_input)
        user_input, action_item = self.initialize_step('format_settings', user_input, errors)

        if user_input is None:
            await lists.build_www_directory_filter_list(self)
            return self.async_show_form(step_id='format_settings',
                            data_schema=forms.form_format_settings(self),
                            errors=self.errors)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        user_input = self._unpack_ui_format_settings(user_input)

        if utils_cf.no_errors(self):
            self._apply_format_settings_changes(user_input)
            self.update_config_file(CF_GENERAL, user_input, action_item)
            return await self.async_step_menu()

        return self.async_show_form(step_id='format_settings',
                            data_schema=forms.form_format_settings(self),
                            errors=self.errors)


#-------------------------------------------------------------------------------------------
    def _unpack_ui_format_settings(self, user_input):
        if user_input is None: return None

        user_input = utils_cf.select_value( user_input,
                                                CONF_DEVICE_TRACKER_STATE_SOURCE,
                                                DEVICE_TRACKER_STATE_SOURCE_OPTIONS)
        user_input = utils_cf.select_value( user_input,
                                                CONF_UNIT_OF_MEASUREMENT,
                                                UNIT_OF_MEASUREMENT_OPTIONS)
        user_input = utils_cf.select_value(user_input,
                                                CONF_TIME_FORMAT,
                                                TIME_FORMAT_OPTIONS)

        user_input = utils_cf.strip_spaces(user_input, [CONF_EVLOG_BTNCONFIG_URL])

        return user_input

#-------------------------------------------------------------------------------------------
    def _apply_format_settings_changes(self, user_input):
        '''
        The zone name and time format changes that are used before Configure closes
        '''
        if (Gb.display_zone_format != user_input[CONF_DISPLAY_ZONE_FORMAT]):
            list_add(self.config_parms_update_control, 'special_zone')

        if Gb.conf_general[CONF_TIME_FORMAT] != user_input[CONF_TIME_FORMAT]:
            self.away_time_zone_hours_key_text = {}
            Gb.time_format_12_hour = user_input[CONF_TIME_FORMAT].startswith('12')
            Gb.time_format_24_hour = not Gb.time_format_12_hour

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _format_device_text_hdr(conf_device):
        device_text = ( f"{conf_device[CONF_FNAME]} "
                        f"({conf_device[CONF_IC3_DEVICENAME]})")
        if conf_device[CONF_TRACKING_MODE] == MONITOR:
            device_text += f", {utils_cf.tr('dev_status_monitored')}"
        elif conf_device[CONF_TRACKING_MODE] == INACTIVE:
            device_text += f", {utils_cf.tr('dev_status_inactive')}"

        return device_text


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            INZONE INTERVALS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_inzone_intervals(self, user_input=None, errors=None):
        self.step_id = 'inzone_intervals'
        user_input = utils_cf.flatten_sections(user_input)
        user_input, action_item = self.initialize_step('inzone_intervals', user_input, errors)

        if user_input is None:
            return self.async_show_form(step_id='inzone_intervals',
                            data_schema=forms.form_inzone_intervals(self),
                            errors=self.errors)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        user_input = self._unpack_ui_inzone_intervals(user_input)

        if utils_cf.no_errors(self):
            self.update_config_file(CF_GENERAL, user_input, action_item)
            return await self.async_step_menu()

        return self.async_show_form(step_id='inzone_intervals',
                            data_schema=forms.form_inzone_intervals(self),
                            errors=self.errors)


#-------------------------------------------------------------------------------------------
    def _unpack_ui_inzone_intervals(self, user_input):
        '''
        Cycle through the inzone_interval items, validate them and rebuild the inzone_interval
        list in the config file.

        Return = valid inzone_interval diction item as part of the user_input field

        user_input:
            {'iphone': {'hours': 3, 'minutes': 11, 'seconds': 0},
            'ipad': {'hours': 2, 'minutes': 55, 'seconds': 0},
            'watch': {'hours': 0, 'minutes': 44, 'seconds': 0},
            'airpods': {'hours': 0, 'minutes': 33, 'seconds': 0},
            'no_mobapp': {'hours': 0, 'minutes': 22, 'seconds': 0},
            'center_in_zone': True,
            'discard_poor_gps_inzone': True}
        '''
        if user_input is None: return None

        user_input_copy = user_input.copy()
        config_inzone_interval = Gb.conf_general[CONF_INZONE_INTERVALS].copy()

        for pname, pvalue in user_input_copy.items():
            if (pname not in self.errors and pname in config_inzone_interval):
                config_inzone_interval[pname] = pvalue
                user_input.pop(pname, '')

        user_input[CONF_INZONE_INTERVALS] = config_inzone_interval

        return user_input

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            WAZE MAIN
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_waze_main(self, user_input=None, errors=None):
        user_input = utils_cf.flatten_sections(user_input)
        user_input, action_item = self.initialize_step('waze_main', user_input, errors)

        if user_input is None:
            return self.async_show_form(step_id='waze_main',
                            data_schema=forms.form_waze_main(self),
                            errors=self.errors)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        user_input = self._unpack_ui_waze_main(user_input)

        if utils_cf.no_errors(self):
            self.update_config_file(CF_GENERAL, user_input, action_item)
            return await self.async_step_menu()

        return self.async_show_form(step_id='waze_main',
                            data_schema=forms.form_waze_main(self),
                            errors=self.errors)


#-------------------------------------------------------------------------------------------
    def _unpack_ui_waze_main(self, user_input):
        '''
        Validate the Waze numeric fields
        '''
        if user_input is None: return None

        user_input = utils_cf.km_fields_from_ui(user_input,
                            [CONF_WAZE_MIN_DISTANCE, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_HISTORY_MAX_DISTANCE])

        user_input = utils_cf.select_value( user_input,
                                                CONF_WAZE_SERVER,
                                                WAZE_SERVER_OPTIONS)
        user_input = utils_cf.validate_numeric_field(self, user_input)
        user_input = utils_cf.select_value( user_input,
                                                CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                                WAZE_HISTORY_TRACK_DIRECTION_OPTIONS)

        user_input = utils_cf.validate_numeric_field(self, user_input)

        user_input[CONF_WAZE_USED] = bool(user_input[CONF_WAZE_USED])
        user_input[CONF_WAZE_HISTORY_DATABASE_USED] = bool(user_input[CONF_WAZE_HISTORY_DATABASE_USED])

        # If Waze Used changes, also change the History DB used
        if user_input[CONF_WAZE_USED] != Gb.conf_general[CONF_WAZE_USED]:
            user_input[CONF_WAZE_HISTORY_DATABASE_USED] = user_input[CONF_WAZE_USED]

        return user_input

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SPECIAL ZONES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_special_zones(self, user_input=None, errors=None):
        user_input = utils_cf.flatten_sections(user_input)
        user_input, action_item = self.initialize_step('special_zones', user_input, errors)
        await lists.build_zone_selection_list(self)

        if user_input is None:
            return self.async_show_form(step_id='special_zones',
                            data_schema=forms.form_special_zones(self),
                            errors=self.errors)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        user_input = self._unpack_ui_special_zones(user_input)

        if utils_cf.no_errors(self):
            if (user_input[CONF_TRACK_FROM_BASE_ZONE_USED] != Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE_USED]
                    or user_input[CONF_TRACK_FROM_BASE_ZONE] != Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE]
                    or user_input[CONF_TRACK_FROM_HOME_ZONE] != Gb.conf_general[CONF_TRACK_FROM_HOME_ZONE]):
                list_add(self.config_parms_update_control, 'restart')
            self.update_config_file(CF_GENERAL, user_input, action_item)
            return await self.async_step_menu()

        return self.async_show_form(step_id='special_zones',
                            data_schema=forms.form_special_zones(self),
                            errors=self.errors)


#-------------------------------------------------------------------------------------------
    def _unpack_ui_special_zones(self, user_input):
        """ Validate the stationary one fields

        user_input:
            {'stat_zone_fname': 'Stationary',
            'stat_zone_still_time': {'hours': 0, 'minutes': 10, 'seconds': 0},
            'stat_zone_inzone_interval': {'hours': 0, 'minutes': 30, 'seconds': 0},
            'stat_zone_base_latitude': '1',
            'stat_zone_base_longitude': '0'}
        """
        if user_input is None: return None

        user_input = utils_cf.validate_numeric_field(self, user_input)
        user_input = utils_cf.zones_from_ui(self, user_input, [CONF_TRACK_FROM_BASE_ZONE], Gb.conf_general)
        user_input[CONF_TRACK_FROM_BASE_ZONE_USED] = bool(user_input[CONF_TRACK_FROM_BASE_ZONE_USED])

        if 'passthru_zone_header' in user_input:
            if not user_input['passthru_zone_header']:
                user_input[CONF_PASSTHRU_ZONE_TIME] = 0
            elif user_input[CONF_PASSTHRU_ZONE_TIME] == 0:
                user_input[CONF_PASSTHRU_ZONE_TIME] = DEFAULT_GENERAL_CONF[CONF_PASSTHRU_ZONE_TIME]

        if 'stat_zone_header' in user_input:
            if not user_input['stat_zone_header']:
                user_input[CONF_STAT_ZONE_STILL_TIME] = 0
            elif user_input[CONF_STAT_ZONE_STILL_TIME] == 0:
                user_input[CONF_STAT_ZONE_STILL_TIME] = DEFAULT_GENERAL_CONF[CONF_STAT_ZONE_STILL_TIME]

        return user_input

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISPLAY TEXT AS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_display_text_as(self, user_input=None, errors=None):
        '''
        Display the text replacement items that are set up as menu rows (original → displayed)
        and an Add row when an item is free. Selecting a row opens the Update screen. The
        changes are saved to the configuration by the Save row.
        '''
        self.step_id = 'display_text_as'
        self.errors = errors or {}
        self.errors_user_input = {}

        if self.dta_selected_idx == UNSELECTED_IDX:
            self.dta_selected_idx = 0
            for idx, dta_text in enumerate(Gb.conf_general[CONF_DISPLAY_TEXT_AS]):
                self.dta_working_copy[idx] = dta_text

        utils_cf.log_step_info(self, user_input)

        menu_options = {f"display_text_as_item_{idx}": dta_text.replace('>', '→')
                            for idx, dta_text in self.dta_working_copy.items()
                            if instr(dta_text, '>')}
        if any(instr(dta_text, '>') is False for dta_text in self.dta_working_copy.values()):
            menu_options['display_text_as_add'] = None
        menu_options['display_text_as_save'] = None
        menu_options['display_text_as_back'] = None

        return await utils_cf.async_show_list_menu(self, 'display_text_as', menu_options)

#...........................................................
    async def open_display_text_as_item(self, idx):
        self.dta_selected_idx = idx
        return await self.async_step_display_text_as_update()

    async def async_step_display_text_as_add(self, user_input=None):
        free_idxs = [idx    for idx, dta_text in self.dta_working_copy.items()
                            if instr(dta_text, '>') is False]
        if free_idxs == []:
            return await self.async_step_display_text_as()
        return await self.open_display_text_as_item(free_idxs[0])

    async def async_step_display_text_as_save(self, user_input=None):
        idx = UNSELECTED_IDX
        dta_working_copy_list = DEFAULT_GENERAL_CONF[CONF_DISPLAY_TEXT_AS].copy()
        for temp_dta_text in self.dta_working_copy.values():
            if instr(temp_dta_text,'>'):
                idx += 1
                dta_working_copy_list[idx] = temp_dta_text

        self.dta_selected_idx = UNSELECTED_IDX
        self.update_config_file(CF_GENERAL, {CONF_DISPLAY_TEXT_AS: dta_working_copy_list}, 'save')
        return await self.async_step_menu()

    async def async_step_display_text_as_back(self, user_input=None):
        self.dta_selected_idx = UNSELECTED_IDX
        return await self.async_step_menu()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISPLAY TEXT AS UPDATE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_display_text_as_update(self, user_input=None, errors=None):
        '''
        Update the selected text replacement item. Saving it with both fields empty clears it.
        '''
        user_input, action_item = self.initialize_step('display_text_as_update', user_input, errors)

        if user_input is None:
            return self.async_show_form(step_id='display_text_as_update',
                            data_schema=forms.form_display_text_as_update(self),
                            errors=self.errors)

        if action_item == 'update_text_as':
            text_from = user_input.get('text_from', '').strip()
            text_to   = user_input.get('text_to', '').strip()
            if text_from and text_to:
                self.dta_working_copy[self.dta_selected_idx] = f"{text_from} > {text_to}"
            else:
                action_item = 'delete_text_as'

        if action_item == 'delete_text_as':
            self.dta_working_copy[self.dta_selected_idx] = f"#{self.dta_selected_idx + 1}"

        return await self.async_step_display_text_as()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   The text replacement items on the Display Text As menu are menu options. HA opens
#   a menu option's async_step_[option] function so one is created for each item.
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def _open_display_text_as_item_step(idx):
    async def async_step_display_text_as_item(self, user_input=None):
        return await self.open_display_text_as_item(idx)
    return async_step_display_text_as_item

for _idx in range(DISPLAY_TEXT_AS_ITEM_CNT):
    setattr(OptionsFlow_Parameters_Steps, f"async_step_display_text_as_item_{_idx}",
            _open_display_text_as_item_step(_idx))
