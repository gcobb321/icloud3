

from ...global_variables    import GlobalVariables as Gb
from ...const               import (DOMAIN,
                                    LINK,
                                    IPHONE, MAC, ICLOUD,
                                    DEVICE_TYPE_FNAME, DEVICE_TYPE_FNAMES,
                                    MOBAPP, NO_MOBAPP,
                                    TRACK, MONITOR, INACTIVE,
                                    DEVICE_TRACKER,
                                    CONF_APPLE_ACCOUNT,
                                    CONF_DEVICES,
                                    CONF_DATA_SOURCE,
                                    CONF_TRACK_FROM_ZONES, CONF_TRACK_FROM_BASE_ZONE, CONF_LOG_ZONES,
                                    CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVALS,
                                    CONF_RAW_MODEL, CONF_MODEL, CONF_MODEL_DISPLAY_NAME, CONF_FAMSHR_DEVICE_ID,
                                    CONF_LOG_LEVEL_DEVICES,
                                    CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE, CONF_FMF_EMAIL, CONF_FMF_DEVICE_ID,
                                    CONF_TRACKING_MODE, CONF_INZONE_INTERVAL, CONF_FIXED_INTERVAL,
                                    CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                    CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                    CONF_EXCLUDED_SENSORS,
                                    DEFAULT_DEVICE_CONF, DEFAULT_GENERAL_CONF,
                                    CONF_PICTURE_WWW_DIRS
                                    )

from ...utils.utils         import (instr, is_empty, isnot_empty, list_del, list_add, isbetween, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ...startup             import config_file
from ...utils               import entity_io
from ...utils               import entity_reg_util as er_util

from .                      import form_icloud3_device as forms
from ..                     import selection_lists as lists
from ..                     import sensors_cf
from ..                     import utils_cf
from ..const_form_lists     import *


from homeassistant.util    import  slugify


DEVICE_NON_TRACKING_FIELDS =   [CONF_FNAME, CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                                CONF_FIXED_INTERVAL, CONF_LOG_ZONES,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES]

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           ICLOUD3 APPLE ACCOUNT CONFIG FLOW STEPS
#
#           - async_step_device_list
#           - async_step_add_device
#           - async_step_update_device
#           - async_step_update_other_device_parameters
#           - async_step_change_device_order
#           - async_step_picture_dir_filter
#           - async_step_review_inactive_devices
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OptionsFlow_iCloud3Device_Steps:

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DEVICE LIST
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_device_list(self, user_input=None, errors=None):
        '''
        Display the list of devices form and the function to be performed
        (add, update, delete) on the selected device.
        '''
        self.step_id = 'device_list'
        self.errors = errors or {}
        self.errors_user_input = {}
        self.add_device_flag = self.display_rarely_updated_parms = False
        await self.async_write_icloud3_configuration_file()

        if Gb.internet_error:
            self.errors['base'] = 'internet_error'

        if user_input is None:
            await lists.build_icloud_device_selection_list(self)
            await lists.build_mobapp_entity_selection_list(self)
            self._set_inactive_devices_header_msg()
            utils_cf.set_header_msg(self)
            lists.build_devices_list(self)
            self.update_device_ha_sensor_entity = {}

            return self.async_show_form(step_id='device_list',
                        data_schema=forms.form_device_list(self),
                        errors=self.errors,
                        last_step=False)


        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'goto_menu':
            self.update_device_ha_sensor_entity = {}
            return await self.async_step_menu()

        if instr(self.data_source, ICLOUD):
            if self._is_apple_acct_setup() is False:
                self.header_msg = 'apple_acct_not_set_up'

            if self.header_msg:
                errors = {'base': self.header_msg}

        device_cnt = len(Gb.conf_devices)

        if (action_item in ['update_device', 'delete_device']
                and CONF_DEVICES not in user_input):
            action_item = ''

        if action_item == 'goto_menu':
            self.dev_page_no = 0
            self.update_device_ha_sensor_entity = {}
            return await self.async_step_menu()

        if action_item == 'change_device_order':
            self.cdo_devicenames = [self._format_device_text_hdr(conf_device)
                                        for conf_device in Gb.conf_devices]
            self.cdo_new_order_idx = [x for x in range(0, len(Gb.conf_devices))]
            self.actions_list_default = 'move_down'
            return await self.async_step_change_device_order()

        if user_input.get('devices', '').startswith('➤ OTHER DEVICES'):
            if action_item == 'delete_device':
                action_item = 'update_device'
            self.dev_page_no = 1 if self.dev_page_no == 0 else 0
            return await self.async_step_device_list()

        if user_input.get('devices', '').startswith('➤ ADD'):
            self.update_device_ha_sensor_entity['add_device'] = True
            self.conf_device = DEFAULT_DEVICE_CONF.copy()
            return await self.async_step_add_device()

        user_input = utils_cf.option_text_to_parm(user_input,
                                'devices', self.device_items_by_devicename)
        user_input[CONF_IC3_DEVICENAME] = user_input['devices']

        utils_cf.log_step_info(self, user_input, action_item)
        self._get_conf_device_selected(user_input)

        if action_item == 'update_device':
            self.update_device_ha_sensor_entity['update_device'] = True
            return await self.async_step_update_device()

        if action_item == 'delete_device':
            action_desc = ( f"Delete Device > {self.conf_device[CONF_FNAME]} "
                            f"({self.conf_device[CONF_IC3_DEVICENAME]})")
            self.confirm_action = {
                'action_desc': action_desc,
                'yes_func': self._delete_device,
                'return_to_func_async': self.async_step_device_list,
                'return_to_next_yes_func_async': self.async_step_device_list}

            return await self.async_step_confirm_action()

        await lists.build_icloud_device_selection_list(self)
        await lists.build_mobapp_entity_selection_list(self)
        self._set_inactive_devices_header_msg()
        utils_cf.set_header_msg(self)

        lists.build_devices_list(self)
        self.update_device_ha_sensor_entity = {}

        return self.async_show_form(step_id='device_list',
                        data_schema=forms.form_device_list(self),
                        errors=self.errors,
                        last_step=False)

#............................................................-
    def _get_conf_device_selected(self, user_input):
        '''
        Cycle through the devices listed on the device_list screen. If one was selected,
        get it's device name and position in the Gb.config_tracking[DEVICES] parameter.
        If Found, tThe position was saved in conf_device_idx
        Returns:
            - True = The devicename was found.
            - False = The devicename was not found.
        '''
        idx = -1
        for conf_device in Gb.conf_devices:
            idx += 1
            if conf_device[CONF_IC3_DEVICENAME] == user_input[CONF_IC3_DEVICENAME]:
                self.conf_device     = conf_device
                self.conf_device_idx = idx
                break

        return (idx >= 0)

#-------------------------------------------------------------------------------------------
    def _delete_device(self):
        '''
        Delete the device_tracker entity and associated ic3 configuration
        '''

        try:
            devicename = self.conf_device[CONF_IC3_DEVICENAME]
            event_msg = (f"Configuration Changed > DeleteDevice-{devicename}, "
                        f"{self.conf_device[CONF_FNAME]}/"
                        f"{DEVICE_TYPE_FNAME(self.conf_device[CONF_DEVICE_TYPE])}")
            post_event(event_msg)

            # if deleting last device, use _delete all to simplifying table resetting
            if len(Gb.conf_devices) <= 1:
                return self._delete_all_devices()

            sensors_cf.remove_device_tracker_and_sensor_entities(self, devicename)

            self.dev_page_last_selected_devicename[self.dev_page_no] = ''
            Gb.conf_devices.pop(self.conf_device_idx)
            self.update_config_file_tracking(force_config_update=True)

            if devicename in Gb.log_level_devices:
                list_del(Gb.log_level_devices, devicename)
                if is_empty(Gb.log_level_devices):
                    Gb.log_level_devices = ['all']
                self._update_config_file_general(user_input={CONF_LOG_LEVEL_DEVICES: Gb.log_level_devices})

            # The lists may have not been built if deleting a device when deleting an Apple acct
            if devicename in self.device_items_by_devicename:
                del self.device_items_by_devicename[devicename]

            if devicename in Gb.conf_device_sensors:
                del Gb.conf_device_sensors[devicename]

            # Remove any excluded sensors for this device from the conf_sensors and conf_device_sensors
            # excluded sensors list
            if instr(str(Gb.conf_device_sensors[CONF_EXCLUDED_SENSORS]), devicename):
                deleted_excluded_sensors = []
                for excluded_sensor in Gb.conf_device_sensors[CONF_EXCLUDED_SENSORS].copy():
                    _devicename, _sensor_base = er_util.get_devicename_sensor_base(excluded_sensor)
                    if devicename == _devicename:
                        list_del(Gb.conf_device_sensors[CONF_EXCLUDED_SENSORS], devicename)
                        list_add(deleted_excluded_sensors, excluded_sensor)

                if isnot_empty(deleted_excluded_sensors):
                    for excluded_sensor_text in Gb.conf_device_sensors[CONF_EXCLUDED_SENSORS].copy():
                        for deleted_excluded_sensor in deleted_excluded_sensors:
                            if instr(excluded_sensor_text, deleted_excluded_sensor):
                                list_del(Gb.conf_device_sensors[CONF_EXCLUDED_SENSORS], excluded_sensor_text)
                                break


        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def _delete_all_devices(self):
        """
        Erase all ic3 devices,
        Delete the device_tracker entity and associated ic3 configuration
        """

        try:
            for conf_device in Gb.conf_devices:
                devicename = conf_device[CONF_IC3_DEVICENAME]
                sensors_cf.remove_device_tracker_and_sensor_entities(self, devicename)

            Gb.conf_devices = []
            self.device_items_by_devicename = {}       # List of the Devices in the Gb.conf_tracking[apple_accts] parameter
            self.device_items_displayed     = []       # List of the Devices displayed on the device_list form
            self.dev_page_last_selected_devicename = ['', ''] # Device's devicename last displayed on each page
            self.dev_page_no                = 0        # Device List form page number, starting with 0

            self.update_config_file_tracking(force_config_update=True)

        except Exception as err:
            log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            ADD DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_add_device(self, user_input=None, errors=None):
        '''
        Display the device form. Validate and update the device parameters
        '''
        self.step_id = 'add_device'
        self.errors = errors or {}
        self.errors_user_input = {}
        self.multi_form_user_input = {}
        self.add_device_flag = self.display_rarely_updated_parms = True

        await lists.build_update_device_selection_lists(self, self.conf_device[CONF_IC3_DEVICENAME])

        if Gb.internet_error:
            self.errors['base'] = 'internet_error'

        if user_input is None or isnot_empty(self.errors):
            return self.async_show_form(step_id='add_device',
                                        data_schema=forms.form_add_device(self),
                                        errors=self.errors,
                                        last_step=False)

        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        if (action_item == 'cancel_goto_menu'
                or user_input[CONF_IC3_DEVICENAME] == ''):
            return await self.async_step_device_list()

        user_input = utils_cf.strip_special_text_from_user_input(user_input, CONF_IC3_DEVICENAME)
        user_input = utils_cf.strip_special_text_from_user_input(user_input, CONF_FNAME)
        user_input = utils_cf.strip_special_text_from_user_input(user_input, CONF_MOBILE_APP_DEVICE)

        user_input = utils_cf.option_text_to_parm(user_input,
                                CONF_MOBILE_APP_DEVICE, self.mobapp_list_text_by_entity_id)
        user_input = utils_cf.option_text_to_parm(user_input,
                                CONF_PICTURE, self.picture_by_filename)
        user_input = utils_cf.option_text_to_parm(user_input,
                                CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)

        utils_cf.log_step_info(self, user_input, action_item)
        user_input = self._validate_ic3_devicename(user_input)

        user_input = self._resolve_selection_list_items(user_input)
        user_input = self._validate_data_source_selections(user_input)
        ui_devicename = user_input[CONF_IC3_DEVICENAME]

        utils_cf.log_step_info(self, user_input, action_item)

        if utils_cf.any_errors(self):
            self.errors['base'] = 'update_aborted'
            self.multi_form_user_input = user_input

            return self.async_show_form(step_id='add_device',
                        data_schema=forms.form_add_device(self),
                        errors=self.errors,
                        last_step=False)

        user_input = self._set_other_device_field_values(user_input)

        self.create_device_tracker_sensor_enities_on_exit = True
        self.conf_device.update(user_input)
        Gb.conf_devices.append(self.conf_device)

        # Add the new device to the device_list form and and set it's position index
        self.conf_device_idx = len(Gb.conf_devices) - 1
        self.dev_page_no     = 1 if self.dev_page_no == 0 else 0
        ui_devicename        = user_input[CONF_IC3_DEVICENAME]
        self.device_items_by_devicename[ui_devicename] = \
                    lists.format_device_list_item(self, self.conf_device)

        return await self.async_step_update_other_device_parameters()

#.....................................................
    def _set_other_device_field_values(self, user_input):
        '''
        Set the device type and inZone interval fields
        '''

        # Get device_type from iCloud device info
        device_type = ''
        model       = IPHONE
        if user_input[CONF_FAMSHR_DEVICENAME] != 'None':
            icloud_dname = user_input[CONF_FAMSHR_DEVICENAME]
            username = user_input[CONF_APPLE_ACCOUNT]
            if username in Gb.AppleAcct_by_username:
                AppleAcct = Gb.AppleAcct_by_username[username]
                raw_model, model, model_display_name = \
                                AppleAcct.device_model_info_by_fname[icloud_dname]
                model = model.lower()
                if model in DEVICE_TYPE_FNAMES:
                    device_type = model

        # Get device_type from mobapp info
        if (device_type == ''
                and user_input[CONF_MOBILE_APP_DEVICE] != 'None'):
            mobapp_dname = user_input[CONF_MOBILE_APP_DEVICE]
            if mobapp_dname in Gb.device_info_by_mobapp_dname:
                _device_type = Gb.device_info_by_mobapp_dname[mobapp_dname][2].lower() # ipad6,3 --> ipad
                for device_type, device_type_fname in DEVICE_TYPE_FNAMES.items():
                    if _device_type.startswith(device_type):
                        break

        # Get device_type from ic3_devicename
        if device_type == '':
            ic3_devicename = user_input[CONF_IC3_DEVICENAME].lower()
            ic3_fname = user_input[CONF_FNAME].lower()
            for device_type, device_type_fname in DEVICE_TYPE_FNAMES.items():
                if device_type == MAC:
                    continue
                if instr(ic3_devicename, device_type) or instr(ic3_fname.lower(), device_type):
                    break

        if device_type == '':
            device_type = IPHONE

        user_input[CONF_DEVICE_TYPE] = device_type
        inzone_interval_item = NO_MOBAPP if user_input[CONF_MOBILE_APP_DEVICE] == 'None' else device_type
        user_input[CONF_INZONE_INTERVAL] = DEFAULT_GENERAL_CONF[CONF_INZONE_INTERVALS][inzone_interval_item]
        return user_input


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_update_device(self, user_input=None, errors=None):
        '''
        Display the device form. Validate and update the device parameters
        '''
        self.step_id = 'update_device'
        self.errors = errors or {}
        self.errors_user_input = {}

        await lists.build_update_device_selection_lists(self, self.conf_device[CONF_IC3_DEVICENAME])
        log_debug_msg(f"⭐ {self.step_id.upper()} ( > UserInput-{user_input}, Errors-{errors}")

        if Gb.internet_error:
            self.errors['base'] = 'internet_error'

        if user_input is None:
            return self.async_show_form(step_id='update_device',
                                        data_schema=forms.form_update_device(self),
                                        errors=self.errors)

        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        utils_cf.log_step_info(self, user_input, action_item)

        if self.add_device_flag is False:
            self.dev_page_last_selected_devicename[self.dev_page_no] = self.conf_device[CONF_IC3_DEVICENAME]

        if action_item == 'cancel_goto_select_device':
            return await self.async_step_device_list()
        elif action_item == 'cancel_goto_menu':
            return await self.async_step_menu()

        utils_cf.log_step_info(self, user_input, action_item)

        user_input = utils_cf.strip_special_text_from_user_input(user_input, CONF_IC3_DEVICENAME)
        user_input = utils_cf.strip_special_text_from_user_input(user_input, CONF_FNAME)
        user_input = utils_cf.strip_special_text_from_user_input(user_input, CONF_MOBILE_APP_DEVICE)

        user_input = utils_cf.option_text_to_parm(user_input,
                                CONF_MOBILE_APP_DEVICE, self.mobapp_list_text_by_entity_id)
        user_input = utils_cf.option_text_to_parm(user_input,
                                CONF_PICTURE, self.picture_by_filename)

        user_input = utils_cf.option_text_to_parm(user_input,
                                CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)
        utils_cf.log_step_info(self, user_input, action_item)

        user_input = self._validate_ic3_devicename(user_input)

        if (CONF_IC3_DEVICENAME not in self.errors
                and CONF_FNAME not in self.errors):
            user_input = self._resolve_selection_list_items(user_input)
            user_input = self._validate_data_source_selections(user_input)
            user_input = self._update_device_fields(user_input)
            change_flag = self._was_device_data_changed(user_input)

        if utils_cf.any_errors(self):
            self.errors['base'] = 'update_aborted'
            self.multi_form_user_input  = user_input

            return self.async_show_form(step_id='update_device',
                            data_schema=forms.form_update_device(self),
                            errors=self.errors)

        if user_input[CONF_PICTURE] == 'setup_dir_filter':
            self.multi_form_user_input = user_input
            self.multi_form_user_input[CONF_PICTURE] = self.conf_device[CONF_PICTURE]
            return await self.async_step_picture_dir_filter()

        if change_flag is False:
            if action_item == 'update_other_device_parameters':
                return await self.async_step_update_other_device_parameters()

            return await self.async_step_device_list()

        # Device fname was changed --> change name on all of it's sensors
        if user_input[CONF_FNAME] != self.conf_device[CONF_FNAME]:
            self.update_device_ha_sensor_entity[CONF_FNAME] = user_input[CONF_FNAME]

        # Picture was changed to None, display Icon mdi: selector later on
        picture_changed_to_none = (user_input[CONF_PICTURE] == 'None' \
                                        and self.conf_device[CONF_PICTURE] != 'None')

        ui_devicename = user_input[CONF_IC3_DEVICENAME]

        only_non_tracked_field_updated = self._is_only_non_tracked_field_updated(user_input)
        self.conf_device.update(user_input)
        Gb.conf_devices[self.conf_device_idx] = self.conf_device

        # Update the configuration file
        add_change_msg = 'Add' if self.add_device_flag else 'Change'
        post_event( f"Configuration Changed > {add_change_msg}Device-{ui_devicename}, "
                    f"{self.conf_device[CONF_FNAME]}/"
                    f"{DEVICE_TYPE_FNAME(self.conf_device[CONF_DEVICE_TYPE])}")

        self.dev_page_last_selected_devicename[self.dev_page_no] = ui_devicename
        self.update_config_file_tracking(force_config_update=True)

        # Rebuild this list in case anything changed
        Gb.devicenames_by_icloud_dname = {}
        Gb.icloud_dnames_by_devicename = {}
        for conf_device in Gb.conf_devices:
            devicename   = conf_device.get(CONF_IC3_DEVICENAME)
            icloud_dname = conf_device.get(CONF_FAMSHR_DEVICENAME)
            Gb.devicenames_by_icloud_dname[icloud_dname] = devicename
            Gb.icloud_dnames_by_devicename[devicename]   = icloud_dname

        await lists.build_icloud_device_selection_list(self)

        self.header_msg = 'conf_updated'
        if only_non_tracked_field_updated:
            list_add(self.config_parms_update_control, ['devices', devicename])
        else:
            list_add(self.config_parms_update_control, ['tracking', 'restart'])

        # Update the device_tracker & sensor entities now that the configuration has been updated
        if self.add_device_flag is False:
            self._update_changed_sensor_entities()

        if action_item == 'update_other_device_parameters':
            return await self.async_step_update_other_device_parameters()

        # Picture was changed to None, display Icon mdi: selector
        if picture_changed_to_none:
            return await self.async_step_update_device()

        return await self.async_step_device_list()

#-------------------------------------------------------------------------------------------
    def _resolve_selection_list_items(self, user_input):
        '''
        Extract the apple_acct and icloud_dname (conf_famshr_devicename) from the
        user_input icloud_dname-LINK-apple_acct value

        Note: The value in self.icloud_list_text_by_fname ends with a '.' when the item
        is in an apple acts list but without the '.' whe it has been selected and is 'this' device
        This Device:
            'Gary-AirPods Pro⟢gcobb321@gmail.com': 'Gary-AirPods Pro⟢GaryCobb, AirPods Pro 2nd gen'
        To be selected (in an accts list):
            'Gary-AirPods Pro⟢gcobb321@gmail.com': 'Gary-AirPods Pro⟢GaryCobb, AirPods Pro 2nd gen.'

        From: 'famshr_devicename': 'Gary-AirPods Pro⟢GaryCobb, AirPods Pro 2nd gen.'
        To:   'apple_account': 'gcobb321@gmail.com', 'famshr_devicename': 'Gary-AirPods Pro',
        '''

        # Get the dname_apple_acct key from the value description of FAMSHR_DEVICENAME field
        if user_input[CONF_FAMSHR_DEVICENAME] == 'nodev':
            user_input[CONF_FAMSHR_DEVICENAME] = 'None'
        if user_input[CONF_MOBILE_APP_DEVICE] == 'nodev':
            user_input[CONF_MOBILE_APP_DEVICE] = 'None'

        _icloud_dname_apple_acct = [icloud_dname_apple_acct
                            for icloud_dname_apple_acct, v in self.icloud_list_text_by_fname.items()
                            if (v == user_input[CONF_FAMSHR_DEVICENAME])]

        if is_empty(_icloud_dname_apple_acct):
            _icloud_dname_apple_acct = 'None'
        else:
            _icloud_dname_apple_acct = _icloud_dname_apple_acct[0]

        # Get the dname_apple_acct key from the value description of FAMSHR_DEVICENAME field
        if (_icloud_dname_apple_acct.startswith('.')
                or _icloud_dname_apple_acct.startswith('ⓧ')):
            user_input[CONF_APPLE_ACCOUNT]      = self.conf_device[CONF_APPLE_ACCOUNT]
            user_input[CONF_FAMSHR_DEVICENAME]  = self.conf_device[CONF_FAMSHR_DEVICENAME]
            self.errors[CONF_FAMSHR_DEVICENAME] = 'invalid_selection'

        elif _icloud_dname_apple_acct == 'None':
            user_input[CONF_APPLE_ACCOUNT]     = ''
            user_input[CONF_FAMSHR_DEVICENAME] = 'None'
            user_input[CONF_FAMSHR_DEVICE_ID]   = ''
            user_input[CONF_RAW_MODEL]          = ''
            user_input[CONF_MODEL]              = ''
            user_input[CONF_MODEL_DISPLAY_NAME] = ''

        elif instr(_icloud_dname_apple_acct, LINK):
            icloud_dname_part, username_part   = _icloud_dname_apple_acct.split(LINK)
            user_input[CONF_APPLE_ACCOUNT]     = username_part
            user_input[CONF_FAMSHR_DEVICENAME] = icloud_dname_part
        else:
            user_input[CONF_APPLE_ACCOUNT]     = self.conf_device[CONF_APPLE_ACCOUNT]
            user_input[CONF_FAMSHR_DEVICENAME] = self.conf_device[CONF_FAMSHR_DEVICENAME]

        if CONF_FMF_EMAIL in user_input:
            user_input[CONF_FMF_EMAIL]     = 'None'
            user_input[CONF_FMF_DEVICE_ID] = ''

        # Check the MobApp for an invalid selection
        if (user_input[CONF_MOBILE_APP_DEVICE].startswith('.')
                or user_input[CONF_MOBILE_APP_DEVICE].startswith('ⓧ')):
            user_input[CONF_MOBILE_APP_DEVICE] = self.conf_device[CONF_MOBILE_APP_DEVICE]
            self.errors[CONF_MOBILE_APP_DEVICE] = 'invalid_selection'

        # Check the MobApp for an invalid selection
        if user_input[CONF_PICTURE].startswith('.'):
            user_input[CONF_PICTURE] = self.conf_device[CONF_PICTURE]
            self.errors[CONF_PICTURE] = 'invalid_selection'

        return user_input

#-------------------------------------------------------------------------------------------
    def _is_only_non_tracked_field_updated(self, user_input):
        '''
        Cycle through the fields in the working fields dictionary for the device and see if
        only non-tracked fields were updated.

        Update the device's fields if only non-tracked fields were updated
        Restart iCloud3 if a tracked field was updated
        '''

        try:
            if Gb.conf_devices == []:
                return False

            for pname, pvalue in user_input.items():
                if (Gb.conf_devices[self.conf_device_idx][pname] != pvalue
                        and pname not in DEVICE_NON_TRACKING_FIELDS):
                    return False
        except:
            return False

        return True

#-------------------------------------------------------------------------------------------
    def _validate_ic3_devicename(self, user_input):
        '''
        Validate the add device parameters
        '''

        ui_devicename = user_input[CONF_IC3_DEVICENAME] = slugify(user_input[CONF_IC3_DEVICENAME]).strip()
        ui_fname      = user_input[CONF_FNAME]          = user_input[CONF_FNAME].strip()

        if ui_devicename == '':
            self.errors[CONF_IC3_DEVICENAME] = 'required_field'
            return user_input

        if ui_fname == '':
            self.errors[CONF_FNAME] = 'required_field'
            return user_input

        # ic3 devicename was changed or adding a new device
        if ui_devicename != self.conf_device[CONF_IC3_DEVICENAME]:
            # Already used if the new ic3_devicename is in the ic3 devicename list
            if ui_devicename in self.device_items_by_devicename:
                self.errors[CONF_IC3_DEVICENAME] = 'duplicate_ic3_devicename'
                self.errors_user_input[CONF_IC3_DEVICENAME] = ( f"{ui_devicename}{DATA_ENTRY_ALERT}"
                                                                f"Assigned to another iCloud3 device")

            # Already used if the new ic3_devicename is in the ha device_tracker entity list
            device_tracker_entities, device_tracker_entity_data = \
                    entity_io.get_entity_registry_data(domain=DEVICE_TRACKER)
            dt_devicename = f"{DEVICE_TRACKER}.{ui_devicename}"

            if (dt_devicename in device_tracker_entities
                    and device_tracker_entity_data[dt_devicename]['platform'] != DOMAIN):
                self.errors[CONF_IC3_DEVICENAME] = 'duplicate_other_devicename'
                self.errors_user_input[CONF_IC3_DEVICENAME] = (
                                    f"{ui_devicename}{DATA_ENTRY_ALERT}Used by Integration > "
                                    f"{device_tracker_entity_data[dt_devicename]['platform']}")
        if ui_fname != self.conf_device[CONF_FNAME]:
            # Get any devicenames with the same ui_fname to see if it is already used by another
            # ic3 device. Exclude the self.conf_device instead of ui_devicename in case he ic3
            # devicename is being changed
            used_by_devicename = [conf_device[CONF_IC3_DEVICENAME]
                                    for conf_device in Gb.conf_devices
                                    if (conf_device[CONF_IC3_DEVICENAME] != self.conf_device[CONF_IC3_DEVICENAME]
                                        and conf_device[CONF_FNAME] == ui_fname)]

            if isnot_empty(used_by_devicename):
                self.errors[CONF_FNAME] = 'duplicate_ic3_devicename'
                self.errors_user_input[CONF_FNAME] = (  f"{ui_fname}{DATA_ENTRY_ALERT}Used by iCloud3 device > "
                                                        f"{used_by_devicename[0]}")

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_data_source_selections(self, user_input):
        '''
        Check the devicenames in device's configuration for any errors in the iCloud and
        Mobile App fields.

        Parameters:
            - user_input - the conf_device or user_input item for the device

        Return:
            - self.errors[xxx] will be set if any errors are found
            - user_input
        '''
        if user_input[CONF_FAMSHR_DEVICENAME].strip() == '':
            user_input[CONF_FAMSHR_DEVICENAME] = 'None'
            user_input[CONF_APPLE_ACCOUNT]     = ''

        if (user_input[CONF_MOBILE_APP_DEVICE].strip() == ''
                or user_input[CONF_MOBILE_APP_DEVICE] == 'scan_hdr'):
            user_input[CONF_MOBILE_APP_DEVICE] = 'None'

        ui_apple_acct      = user_input[CONF_APPLE_ACCOUNT]
        ui_icloud_dname    = user_input[CONF_FAMSHR_DEVICENAME]
        ui_mobile_app_name = user_input[CONF_MOBILE_APP_DEVICE]
        icloud_dname_apple_acct = f"{ui_icloud_dname}{LINK}{ui_apple_acct}"

        if (ui_apple_acct  == ''
                and ui_icloud_dname != 'None'):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'unknown_apple_acct'

        elif (ui_icloud_dname != 'None'
                and icloud_dname_apple_acct not in self.icloud_list_text_by_fname
                and instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD)):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'unknown_icloud'

        elif (ui_icloud_dname == 'None'
                and ui_mobile_app_name == 'None'
                and user_input.get(CONF_TRACKING_MODE, TRACK) != INACTIVE):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'no_data_source'
            self.errors[CONF_TRACKING_MODE] = 'no_data_source_set_inactive'

        if (ui_mobile_app_name != 'None'
                and ui_mobile_app_name not in self.mobapp_list_text_by_entity_id
                and instr(Gb.conf_tracking[CONF_DATA_SOURCE], MOBAPP)):
            self.errors[CONF_MOBILE_APP_DEVICE] = 'unknown_mobapp'

        return user_input

#-------------------------------------------------------------------------------------------
    def _update_device_fields(self, user_input):
        """ Validate the device parameters

            Sets:
                self.error[] for fields that are in error
            Returns:
                user_input
                change_flag: True if a field was changed
                change_fname_flag: True if the fname was changed and the device_tracker entity needs to be updated
                change_tfz_flag: True if the track_fm_zones zone was changed and the sensors need to be updated
        """

        if self.AppleAcct:
            _AppleDev = self.AppleAcct.AADevices
            conf_icloud_dname = user_input[CONF_FAMSHR_DEVICENAME]
            device_id = self.AppleAcct.device_id_by_icloud_dname.get(conf_icloud_dname, '')
            raw_model, model, model_display_name = self.AppleAcct.device_model_info_by_fname.get(conf_icloud_dname, ['', '', ''])
            user_input[CONF_FAMSHR_DEVICE_ID]   = device_id
            user_input[CONF_RAW_MODEL]          = raw_model
            user_input[CONF_MODEL]              = model
            user_input[CONF_MODEL_DISPLAY_NAME] = model_display_name

        return user_input

#-------------------------------------------------------------------------------------------
    def _was_device_data_changed(self, user_input):
        """ Cycle thru old and new data and identify changed fields

            Returns:
                True if anything was changed
            Updates:
                sensor_entity_attrs_changed based on changes detected
        """

        if utils_cf.any_errors(self):
            return False

        change_flag = False
        if CONF_IC3_DEVICENAME in user_input:
            self.update_device_ha_sensor_entity[CONF_IC3_DEVICENAME]  = self.conf_device[CONF_IC3_DEVICENAME]
            self.update_device_ha_sensor_entity['new_ic3_devicename'] = user_input[CONF_IC3_DEVICENAME]
        if CONF_TRACKING_MODE in user_input:
            self.update_device_ha_sensor_entity[CONF_TRACKING_MODE]   = self.conf_device[CONF_TRACKING_MODE]
            self.update_device_ha_sensor_entity['new_tracking_mode']  = user_input[CONF_TRACKING_MODE]

        for pname, pvalue in self.conf_device.items():
            if pname not in user_input:
                continue

            if user_input[pname] != pvalue:
                change_flag = True

        return change_flag

#-------------------------------------------------------------------------------------------
    def _update_changed_sensor_entities(self):
        """ Update the device_tracker sensors if needed"""

        # Use the current ic3_devicename since that is how the Device & DeviceTracker objects with the
        # device_tracker and sensor entities are stored. If the devicename was also changed, the
        # device_tracker and sensor entity names will be changed later

        devicename        = self.update_device_ha_sensor_entity[CONF_IC3_DEVICENAME]
        new_devicename    = self.update_device_ha_sensor_entity['new_ic3_devicename']
        tracking_mode     = self.update_device_ha_sensor_entity[CONF_TRACKING_MODE]
        new_tracking_mode = self.update_device_ha_sensor_entity['new_tracking_mode']

        # fname was changed - change the fname of device_tracker and all sensors to the new fname
        # Inactive devices were not created so they are not in Gb.DeviceTrackers_by_devicename
        if (devicename == new_devicename
                and CONF_FNAME in self.update_device_ha_sensor_entity
                and Gb.DeviceTrackers_by_devicename.get(devicename)):
            DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
            DeviceTracker.update_entity_attribute(new_fname=self.conf_device[CONF_FNAME])

            for sensor, Sensor in Gb.Sensors_by_devicename[devicename].items():
                try:
                    Sensor.update_entity_attribute(new_fname=self.conf_device[CONF_FNAME])
                except  Exception as err:
                    # log_exception(err)
                    pass

        # devicename was changed - delete device_tracker and all sensors for
        # devicename and add them for new_devicename
        if devicename != new_devicename:
            self.update_config_file_tracking(force_config_update=True)
            self.create_device_tracker_sensor_enities_on_exit = True

            sensors_cf.remove_device_tracker_and_sensor_entities(self, devicename)

        # If the device was 'inactive' it's entity may not exist since they are not created for
        # inactive devices. If so, create it now if it is no longer 'inactive'.
        elif (tracking_mode == INACTIVE
                and new_tracking_mode != INACTIVE
                and Gb.DeviceTrackers_by_devicename.get(new_devicename) is None):
            self.create_device_tracker_sensor_enities_on_exit = True

        # If the device is now 'inactive' it's entity exists, delete iit
        elif (new_tracking_mode == INACTIVE
                and tracking_mode != INACTIVE
                and Gb.DeviceTrackers_by_devicename.get(new_devicename)):
            sensors_cf.remove_device_tracker_and_sensor_entities(self, devicename)

        # If the device was 'monitored' and is now tracked, create the tracked sensors
        elif (tracking_mode == MONITOR
                and new_tracking_mode == TRACK):
            sensors_list = sensors_cf.build_all_sensors_list()
            self.create_device_tracker_sensor_enities_on_exit = True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE OTHER DEVICE PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_update_other_device_parameters(self, user_input=None, errors=None):
        self.step_id = 'update_other_device_parameters'
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        if user_input is None:
            return self.async_show_form(step_id='update_other_device_parameters',
                                        data_schema=forms.form_update_other_device_parameters(self),
                                        errors=self.errors)

        utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'cancel_goto_previous':
            if self.add_device_flag:
                return await self.async_step_device_list()
            else:
                return await self.async_step_update_device()

        user_input = utils_cf.option_text_to_parm(user_input,
                                CONF_DEVICE_TYPE, DEVICE_TYPE_FNAMES)
        user_input = utils_cf.option_text_to_parm(user_input,
                                CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text)

        user_input  = self._finalize_other_parameters_selections(user_input)
        change_flag = self.add_device_flag or self._was_device_data_changed(user_input)
        devicename  = self.conf_device[CONF_IC3_DEVICENAME]

        if utils_cf.any_errors(self):
            self.errors['base'] = 'update_aborted'
            return self.async_show_form(step_id='async_step_update_other_device_parameters',
                            data_schema=forms.form_update_other_device_parameters(self),
                            errors=self.errors)

        elif change_flag and action_item == 'save':
            list_add(self.config_parms_update_control, ['devices', devicename])
            tfz_changed = (user_input[CONF_TRACK_FROM_ZONES] != self.conf_device[CONF_TRACK_FROM_ZONES])
            self.conf_device.update(user_input)

            if tfz_changed:
                sensors_cf.update_track_from_zones_sensors(self, user_input)

        if self.add_device_flag:
            self.header_msg = 'conf_updated'
            return await self.async_step_device_list(errors)
            # errors = {'base': 'conf_updated'}
            # return await self.async_step_device_list(errors)

        return await self.async_step_update_device()

#-------------------------------------------------------------------------------------------
    def _finalize_other_parameters_selections(self, user_input):
        '''
        Check the devicenames in device's configuration for any errors in the iCloud and
        Mobile App fields.

        Parameters:
            - user_input - the conf_device or user_input item for the device

        Return:
            - self.errors[xxx] will be set if any errors are found
            - user_input
        '''
        # Build 'log_zones' list
        if ('none' in user_input[CONF_LOG_ZONES]
                and 'none' not in self.conf_device[CONF_LOG_ZONES]):
            log_zones = []
        else:
            log_zones = [zone   for zone in self.zone_name_key_text.keys()
                                if zone in user_input[CONF_LOG_ZONES] and zone != '.' ]
        if log_zones == []:
            log_zones = ['none']
        else:
            user_input[CONF_LOG_ZONES].append('name-zone')
            log_zones.append([item  for item in user_input[CONF_LOG_ZONES]
                                    if item.startswith('name')][0])
        user_input[CONF_LOG_ZONES] = log_zones

        # See if there are any track_from_zone changes that will be processed after the
        # device is updated
        new_tfz_zones_list, remove_tfz_zones_list = \
                    sensors_cf.devices_form_identify_new_and_removed_tfz_zones(self, user_input)

        self.update_device_ha_sensor_entity['new_tfz_zones']    = new_tfz_zones_list
        self.update_device_ha_sensor_entity['remove_tfz_zones'] = remove_tfz_zones_list

        # Build 'track_from_zones' list
        track_from_zones = [zone    for zone in self.zone_name_key_text.keys()
                                    if (zone in user_input[CONF_TRACK_FROM_ZONES]
                                        and zone not in ['.',
                                            self.conf_device[CONF_TRACK_FROM_BASE_ZONE]])]

        track_from_zones.append(self.conf_device[CONF_TRACK_FROM_BASE_ZONE])
        list_add(track_from_zones, user_input[CONF_TRACK_FROM_BASE_ZONE])
        user_input[CONF_TRACK_FROM_ZONES] = track_from_zones

        if isbetween(user_input[CONF_FIXED_INTERVAL], 1, 2):
            user_input[CONF_FIXED_INTERVAL] = 3
            self.errors[CONF_FIXED_INTERVAL] = 'fixed_interval_invalid_range'

        return user_input


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           CHANGE DEVICE ORDER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_change_device_order(self, user_input=None, errors=None):
        self.step_id = 'change_device_order'
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        if user_input is None:
            utils_cf.log_step_info(self, user_input, action_item)
            self.cdo_devicenames = [self._format_device_text_hdr(conf_device)
                                        for conf_device in Gb.conf_devices]
            self.cdo_new_order_idx = [x for x in range(0, len(Gb.conf_devices))]
            self.actions_list_default = 'move_down'
            return self.async_show_form(step_id='change_device_order',
                                        data_schema=forms.form_change_device_order(self),
                                        errors=self.errors)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_device_list()

        if action_item == 'save':
            new_conf_devices = []
            for idx in self.cdo_new_order_idx:
                new_conf_devices.append(Gb.conf_devices[idx])

            Gb.conf_devices = new_conf_devices
            config_file.set_conf_devices_index_by_devicename()
            self.update_config_file_tracking(force_config_update=True)
            lists.build_devices_list(self)
            list_add(self.config_parms_update_control, ['restart', 'profile'])

            self.header_msg = 'conf_updated'
            return await self.async_step_device_list(errors)
            # errors = {'base': 'conf_updated'}
            # return await self.async_step_device_list(errors)

        self.cdo_curr_idx = self.cdo_devicenames.index(user_input['device_desc'])
        new_idx = self.cdo_curr_idx

        if action_item == 'move_up':
            if new_idx > 0:
                new_idx = new_idx - 1

        elif action_item == 'move_down':
            if new_idx < len(self.cdo_devicenames) - 1:
                new_idx = new_idx + 1
        self.actions_list_default = action_item

        if new_idx != self.cdo_curr_idx:
            self.cdo_devicenames[self.cdo_curr_idx], self.cdo_devicenames[new_idx] = \
                    self.cdo_devicenames[new_idx], self.cdo_devicenames[self.cdo_curr_idx]
            self.cdo_new_order_idx[self.cdo_curr_idx], self.cdo_new_order_idx[new_idx] = \
                    self.cdo_new_order_idx[new_idx], self.cdo_new_order_idx[self.cdo_curr_idx]

            self.cdo_curr_idx = new_idx

        return self.async_show_form(step_id='change_device_order',
                            data_schema=forms.form_change_device_order(self),
                            errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              PICTURE DIRECTORY FILTER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_picture_dir_filter(self, user_input=None, errors=None):
        self.step_id = 'picture_dir_filter'
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'goto_previous':
            return await self.async_step_update_device()

        await lists.build_www_directory_filter_list(self)

        if action_item == 'save':
            Gb.picture_www_dirs = []
            for group_no in ['1', '2', '3', '4', '5']:
                ui_group_name = f"www_group_{group_no}"
                if ui_group_name in user_input:
                    for dir in user_input[ui_group_name]:
                        list_add(Gb.picture_www_dirs, dir)

            Gb.conf_profile[CONF_PICTURE_WWW_DIRS] = Gb.picture_www_dirs
            self.picture_by_filename = {}
            await lists.build_picture_filename_selection_list(self)
            self._update_config_file_general(user_input)
            return await self.async_step_update_device()

        return self.async_show_form(step_id='picture_dir_filter',
                            data_schema=forms.form_picture_dir_filter(self),
                            errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REVIEW INACTIVE DEVICES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_review_inactive_devices(self, user_input=None, errors=None):
        '''
        There are inactive devices. Display the list of devices and confirm they should
        remain active.
        ACTION_LIST_OPTIONS['inactive_to_track'],
        ACTION_LIST_OPTIONS['inactive_keep_inactive']]
        '''
        self.step_id = 'review_inactive_devices'
        self.errors = errors or {}
        self.errors_user_input = {}

        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        utils_cf.log_step_info(self, user_input, action_item)

        if user_input is None and action_item is None:
            return self.async_show_form(step_id='review_inactive_devices',
                        data_schema=forms.form_review_inactive_devices(self),
                        errors=self.errors,
                        last_step=False)

        if action_item == 'next_page_devices':
            return self.async_show_form(step_id='review_inactive_devices',
                    data_schema=forms.form_review_inactive_devices(self, start_cnt=5),
                    errors=self.errors,
                    last_step=False)

        if action_item == 'inactive_to_track':
            devicename_list = [self.inactive_devices_key_text.values()] \
                                if   user_input['inactive_devices'] == [] \
                                else user_input['inactive_devices']

            for conf_device in Gb.conf_devices:
                devicename = conf_device[CONF_IC3_DEVICENAME]
                if devicename in devicename_list:
                    conf_device[CONF_TRACKING_MODE] = TRACK

                if Gb.DeviceTrackers_by_devicename.get(devicename) is None:
                    self.create_device_tracker_sensor_enities_on_exit = True

            self.header_msg = 'action_completed'
            list_add(self.config_parms_update_control, 'restart')
            self.update_config_file_tracking(force_config_update=True)
            action_item = 'goto_previous'

        if action_item == 'goto_previous':
            if self.return_to_step_id_1 == 'restart_icloud3':
                return await self.async_step_restart_icloud3()

        return await self.async_step_menu()


#-------------------------------------------------------------------------------------------
    def _check_inactive_devices(self):

        inactive_list = [conf_device[CONF_IC3_DEVICENAME]
                            for conf_device in Gb.conf_devices
                            if conf_device[CONF_TRACKING_MODE] == INACTIVE]

        return inactive_list != [] or self.inactive_devices_key_text.get('keep_inactive', False)

#-------------------------------------------------------------------------------------------
    def _set_inactive_devices_header_msg(self):
        '''
        Display the All/Most/Some Devices are Inactive message by setting the header message key.

        Return none, few, some, most, all based on the number of inactive devices
        '''

        if instr(self.data_source, ICLOUD):
            if self._is_apple_acct_setup() is False:
                self.header_msg = 'apple_acct_not_set_up'

            if self.header_msg:
                errors = {'base': self.header_msg}
                return 'none'

        device_cnt = self._device_cnt()
        if device_cnt == 0:
            self.header_msg = 'inactive_no_devices'
            return 'none'

        inactive_device_cnt = self._inactive_device_cnt()
        if inactive_device_cnt == 0:
            return 'none'

        inactive_pct = inactive_device_cnt / device_cnt

        if device_cnt == inactive_device_cnt:
            self.header_msg = f'inactive_all_devices'
        return 'none'

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _inactive_device_cnt():
        '''
        Return the number of inactive Devices
        '''

        return len([conf_device[CONF_IC3_DEVICENAME]
                        for conf_device in Gb.conf_devices
                        if conf_device[CONF_TRACKING_MODE] == INACTIVE])

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _device_cnt():
        '''
        Return the number of Devices
        '''

        return len(Gb.conf_devices)
