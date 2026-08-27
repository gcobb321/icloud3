

from ...global_variables    import GlobalVariables as Gb
from ...const               import (PLATFORM_DEVICE_TRACKER,
                                    CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES,
                                    DEFAULT_GENERAL_CONF,
                                    DEFAULT_DEVICE_APPLE_ACCT_DATA_SOURCE, DEFAULT_DEVICE_MOBAPP_DATA_SOURCE,
                                    DEFAULT_TRACKING_CONF,
                                    )

from ...utils.utils         import (is_empty, isnot_empty, list_to_str, list_del, list_add, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)


from ...support             import service_handler
from ...utils               import entity_reg_util as er_util
from ...utils               import file_io

from .                      import form_tools as forms
from .                      import form_config_flow as forms_cf
from ..                     import sensors_cf
from ..                     import utils_cf
from ..const_form_lists     import *


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#    TOOLS CONFIG FLOW
#        - async_step_tools
#        - async_step_cleanup_entity_registry
#        - async_step_restart_ha
#        - async_step_restart_ha_reload_icloud3
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OptionsFlow_Tools_Steps:


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           TOOLS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_tools(self, user_input=None, errors=None):
        '''
        1. Delete the device from the tracking devices list and adjust the device index
        2. Delete all devices
        3. Clear the iCloud, Mobile App and track_from_zone fields from all devices
        '''
        self.step_id = 'tools'
        self.errors = errors or {}
        self.errors_user_input = {}

        await self.async_write_icloud3_configuration_file()

        if user_input is None or 'confrm_action_item' in user_input:
            return self.async_show_form(step_id='tools',
                                        data_schema=forms.form_tools(self, user_input),
                                        errors=self.errors)

        action_item = TOOL_LIST_ITEMS_KEY_BY_TEXT.get(user_input['action_items'], '')
        user_input['action_items'] = action_item
        user_input = utils_cf.option_text_to_parm(user_input,
                                CONF_LOG_LEVEL, LOG_LEVEL_OPTIONS)

        utils_cf.log_step_info(self, user_input, action_item)

        match action_item:
            case 'menu':
                return await self.async_step_menu()

            case 'log_level':
                return await self.async_step_log_level()

            case 'cleanup_entity_registry':
                return await self.async_step_cleanup_entity_registry()

        self.confirm_action = {
                'action_desc': TOOL_LIST[action_item],
                'yes_func': None,
                'yes_func_async': None,
                'return_to_func_async': self.async_step_tools,
                'return_to_next_yes_func_async': None}

        match action_item:
            case 'restart_icloud3':
                self.confirm_action['yes_func'] = self.restart_icloud3

            case 'reset_data_source':
                self.confirm_action['yes_func'] = self.reset_all_devices_data_source_fields

            case 'reset_tracking':
                self.confirm_action['yes_func'] = self.reset_icloud3_config_file_tracking

            case 'reset_general':
                self.confirm_action['yes_func'] = self.reset_icloud3_config_file_general

            case 'reset_config':
                self.confirm_action['yes_func'] = self.reset_icloud3_config_file_tracking_general

            case 'del_apple_acct_cookies':
                self.confirm_action['yes_func_async'] = self.async_delete_all_apple_cookie_files

            case 'del_icloud3_config_files':
                self.confirm_action['yes_func_async'] = self.async_delete_all_ic3_configuration_files

        if (self.confirm_action['yes_func']
                or self.confirm_action['yes_func_async']):
            return await self.async_step_confirm_action()

        list_add(self.config_parms_update_control, ['tracking', 'restart'])

        return await self.async_step_tools(errors=self.errors)

#------------------------------------------------------------------------------------------
    def restart_icloud3(self):

        # The restart will be done immediately in the 5-sec
        # polling loop in icloud33_main
        Gb.was_icloud3_restart_requested = True

#------------------------------------------------------------------------------------------
    def reset_icloud3_config_file_tracking(self):

        self._delete_all_devices()
        Gb.conf_apple_accounts = []
        Gb.conf_devices        = []
        Gb.conf_tracking       = DEFAULT_TRACKING_CONF.copy()

#------------------------------------------------------------------------------------------
    def reset_icloud3_config_file_general(self):

        Gb.conf_general = DEFAULT_GENERAL_CONF.copy()
        Gb.log_level    = Gb.conf_general[CONF_LOG_LEVEL]

#------------------------------------------------------------------------------------------
    def reset_icloud3_config_file_tracking_general(self):

        self.reset_icloud3_config_file_tracking()
        self.reset_icloud3_config_file_general()

#------------------------------------------------------------------------------------------
    async def async_delete_all_apple_cookie_files(self):
        '''
        Delete all files in the .storage/icloud3 directory
        '''

        post_alert(f"All iCloud3 Configuration files are being deleted")
        list_add(self.config_parms_update_control, ['restart'])

        await self.delete_all_files_and_remove_directory(Gb.icloud_cookies_directory)
        # return await self.async_step_restart_ha_reload_icloud3()

#------------------------------------------------------------------------------------------
    async def async_delete_all_ic3_configuration_files(self):
        '''
        Delete all files in the .storage/icloud3 directory
        '''

        post_alert(f"All iCloud3 Configuration files are being deleted")

        return await self.delete_all_files_and_remove_directory(Gb.ha_storage_icloud3)

#------------------------------------------------------------------------------------------
    async def delete_all_files_and_remove_directory(self, start_dir):
        for Device in Gb.Devices:
            Device.pause_tracking()

        # start_dir = Gb.ha_storage_icloud3
        file_filter = []
        files = await Gb.hass.async_add_executor_job(
                                            file_io.get_filename_list,
                                            start_dir,
                                            file_filter)

        try:
            for file in files:
                await file_io.async_delete_file(f"{ start_dir}/{file}")

            if isnot_empty(files):
                await file_io.async_delete_directory( start_dir)

                list_add(self.config_parms_update_control, 'restart')

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def reset_all_devices_data_source_fields(self, reset_mobapp=None):
        """
        Reset the iCloud & Mobile App fields to their initiial values.
        Keep the devicename, friendly name, picture and other fields
        """

        reset_mobapp = True if reset_mobapp is None else False
        for conf_device in Gb.conf_devices:
            conf_device.update(DEFAULT_DEVICE_APPLE_ACCT_DATA_SOURCE)
            if reset_mobapp:
                conf_device.update(DEFAULT_DEVICE_MOBAPP_DATA_SOURCE)

        self.update_config_file_tracking(force_config_update=True)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           LOG LEVEL
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_log_level(self, user_input=None, errors=None):
        '''
        Update the Log Level
        '''
        self.step_id = 'log_level'
        self.errors = errors or {}
        self.errors_user_input = {}

        await self.async_write_icloud3_configuration_file()

        if user_input is None:
            return self.async_show_form(step_id='log_level',
                                        data_schema=forms.form_log_level(self),
                                        errors=self.errors)

        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        user_input = utils_cf.option_text_to_parm(user_input,
                                CONF_LOG_LEVEL, LOG_LEVEL_OPTIONS)

        utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'menu':
            return await self.async_step_menu()

        # Log Level not was changed
        if (user_input[CONF_LOG_LEVEL] == Gb.conf_general[CONF_LOG_LEVEL]
                and user_input[CONF_LOG_LEVEL_DEVICES] == Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
            return await self.async_step_menu()

        if (is_empty(user_input[CONF_LOG_LEVEL_DEVICES])
                or len(user_input[CONF_LOG_LEVEL_DEVICES]) >= len(Gb.Devices)):
            user_input[CONF_LOG_LEVEL_DEVICES] = ['all']

        elif len(user_input[CONF_LOG_LEVEL_DEVICES]) > 1:
            list_del(user_input[CONF_LOG_LEVEL_DEVICES], 'all')

        Gb.log_level_devices = user_input[CONF_LOG_LEVEL_DEVICES].copy()

        self._update_config_file_general(user_input)

        return await self.async_step_menu()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           CLEANUP ENTITY REGISTRY
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_cleanup_entity_registry(self, user_input=None, errors=None):
        self.step_id = 'cleanup_entity_registry'
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        utils_cf.log_step_info(self, user_input, action_item)

        if user_input is None:
            return self.async_show_form(step_id='cleanup_entity_registry',
                                        data_schema=forms.form_cleanup_entity_registry(self),
                                        errors=self.errors)

        match action_item:
            case 'check_all':
                self.tools_entity_reg_check_all = True

            case 'check_none':
                self.tools_entity_reg_check_all = False

            case 'show_all_sensors':
                self.tools_cleanup_er_sensor_all = True

            case 'show_some_sensors':
                self.tools_cleanup_er_sensor_all = False

            case 'goto_previous':
                return await self.async_step_tools()

            case 'delete_device_sensors':
                for status in list(user_input.keys()):
                    if isnot_empty(user_input[status]):
                        break
                else:
                    return await self.async_step_tools()

                self._tools_delete_device_sensors(user_input)
                self.repair_entity_show_check_all = False
                er_util.scan_entity_reg_for_icloud3_items()
                self.errors['base'] = 'action_completed'

        return self.async_show_form(step_id='cleanup_entity_registry',
                            data_schema=forms.form_cleanup_entity_registry(self, user_input),
                            errors=self.errors)

#......................................................
    def _tools_delete_device_sensors(self, user_input):
        '''
        user_input contains the status groups and devices selected in each group.
        Cycle through the status groups and delete the specified devices.

        UserInput-{'active': ['lillian_ipad'], 'inactive': [], 'deleted_devices': ['bens_iphone],
                    'deleted_sensors': ['lillian_ipad2]}

        Active Devices: Delete and recreate the sensors for the selected device using
                        using the same routines that are used to delete and add a device
                        to the iC3 configuration since these devices are tracked. This is done
                        after all other devices are deleted in case orphaned or disabled
                        devices with the same name are also deleted. This ensures the entitity_id
                        is assigned correctly.
        All Others:     Delete from the device & entity registry as normal.
        '''

        # Cycle thru status groups, delete all devices selected in each group
        for status in list(user_input.keys()):
            if status != 'active' and isnot_empty(user_input[status]):
                self._tools_delete_nonactive_devices(status, user_input[status])

        # Delete active devices after the others have been deleted so they can be
        # recreated correctly
        if 'active' in user_input and isnot_empty(user_input['active']):
            self._tools_delete_active_devices(user_input['active'])

#......................................................
    def _tools_delete_active_devices(self, devicenames):

        try:
            for devicename in devicenames:
                self.create_device_tracker_sensor_enities_on_exit = True

                if Device := Gb.Devices_by_devicename.get(devicename):
                    Device.pause_tracking

                sensors_cf.remove_device_tracker_and_sensor_entities(
                                                        self, devicename,
                                                        rebuild_ic3db_dashboards=False)

                if Device:
                    Device.resume_tracking

        except Exception as err:
            log_exception(err)
            pass

#......................................................
    def _tools_delete_nonactive_devices(self, status, devicenames):

        for devicename in devicenames:
            device_sensors = Gb.entity_reg_items_by_status[status][devicename]
            for sensor, sensor_data in device_sensors.items():
                platform   = sensor_data['platform']
                entity_key = sensor_data["entity_key"]
                entity_id  = sensor_data['entity_id']
                device_id  = sensor_data["device_id"]

                try:
                    # Delete from device_registry
                    _device_msg = ''
                    if platform == PLATFORM_DEVICE_TRACKER:
                        _device_msg = f"Device: device_tracker.{devicename}, "
                        if device_id is not None:
                            if status.startswith('deleted_') is False:
                                er_util.remove_device(device_id)
                            er_util.remove_deleted_device(device_id)

                    # Delete from entity_registry
                    if status.startswith('deleted_') is False:
                        er_util.remove_sensor(entity_key)
                    er_util.remove_deleted_entity(entity_key)

                except Exception as err:
                    log_exception(err)

            _sensors = list(device_sensors.keys())
            _deleted_msg = (f"{_device_msg}"
                            f"BaseName: sensor.{devicename}_",
                            f"Count: {len(_sensors)}, "
                            f"Entities: {list_to_str(_sensors)}")

            log_info_msg(f"ENTITIES REMOVED ({status}): {_deleted_msg}")
