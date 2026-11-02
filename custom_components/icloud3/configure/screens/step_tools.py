

from ...global_variables    import GlobalVariables as Gb
from ...const               import (PLATFORM_DEVICE_TRACKER, )
from ...const_config        import (CONF_APPLE_ACCT, CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES, DEFAULT_GENERAL_CONF,
                                    DEFAULT_DEVICE_APPLE_ACCT_DATA_SOURCE,
                                    DEFAULT_DEVICE_MOBAPP_DATA_SOURCE, DEFAULT_TRACKING_CONF, )

from ...utils.utils         import (is_empty, isnot_empty, list_to_str, list_del, list_add, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)


from ...support             import service_handler
from ...support             import marketplace as mp
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

    def initialize_tools_variables(self):
        '''
        Initialize the variables used by the Tools screens. Called from the
        flow handler's initialize_options (the mixin's __init__ would never be run).
        '''
        # Tools > Entity Registry Maintenance
        self.tools_cleanup_er_sensor_all    = False
        self.tools_entity_reg_check_all     = None    # Show action check all instead of check none

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           TOOLS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_tools(self, user_input=None, errors=None):
        '''
        Display the tools as menu rows:
        1. Delete the device from the tracking devices list and adjust the device index
        2. Delete all devices
        3. Clear the iCloud, Mobile App and track_from_zone fields from all devices
        '''
        self.step_id = 'tools'
        self.errors = errors or utils_cf.set_header_msg(self) or {}
        self.errors_user_input = {}

        await self.async_write_icloud3_configuration_file()
        utils_cf.log_step_info(self, user_input)

        menu_options = {f"tools_{tool_item}": None for tool_item in TOOL_ITEMS}
        menu_options['tools_back'] = None

        return await utils_cf.async_show_list_menu(self, 'tools', menu_options)

#...........................................................
    async def async_step_tools_back(self, user_input=None):
        return await self.async_step_menu()

    async def open_tool(self, tool_item):
        utils_cf.log_step_info(self, None, tool_item)

        match tool_item:
            case 'log_level':
                return await self.async_step_log_level()

            case 'beta_version':
                return await self.async_step_beta_version()

            case 'cleanup_entity_registry':
                return await self.async_step_cleanup_entity_registry()

        is_confirm_item = tool_item in TOOL_CONFIRM_ITEMS
        removed_cnts = {
                'devices': utils_cf.tr_cnt('cnt_devices', len(Gb.conf_devices)),
                'apple_accts': utils_cf.tr_cnt('cnt_apple_accts',
                                    len([conf_apple_acct for conf_apple_acct in Gb.conf_apple_accounts
                                                        if conf_apple_acct[CONF_APPLE_ACCT]]))}
        self.confirm_action = {
                'action_desc': utils_cf.tr(f"confirm_{tool_item}", **removed_cnts) if is_confirm_item else None,
                'yes_label': utils_cf.tr(f"confirm_yes_{tool_item}") if is_confirm_item else None,
                'no_label': utils_cf.tr(f"confirm_no_{tool_item}") if is_confirm_item else None,
                'yes_func': None,
                'yes_func_async': None,
                'done_msg': f"{tool_item}_done" if is_confirm_item else None,
                'return_to_func_async': self.async_step_tools,
                'return_to_next_yes_func_async': None}

        match tool_item:
            case 'restart_icloud3':
                self.confirm_action['yes_func'] = self.restart_icloud3

            case 'reset_data_source':
                self.confirm_action['yes_func'] = self.reset_all_devices_data_source_fields

            case 'reset_tracking':
                self.confirm_action['yes_func'] = self.reset_icloud3_config_file_tracking

            case 'reset_general':
                self.confirm_action['yes_func'] = self.reset_icloud3_config_file_general

            case 'del_apple_acct_cookies':
                self.confirm_action['yes_func_async'] = self.async_delete_all_apple_cookie_files

            case 'del_icloud3_config_files':
                self.confirm_action['yes_func_async'] = self.async_delete_all_ic3_configuration_files

        if (self.confirm_action['yes_func']
                or self.confirm_action['yes_func_async']):
            return await self.async_step_confirm_action()

        list_add(self.config_parms_update_control, ['tracking', 'restart'])

        return await self.async_step_tools(errors=self.errors)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           BETA VERSIONS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_beta_version(self, user_input=None, errors=None):
        '''
        Turn the iCloud3 Pre-release switch in HACS or the Marketplace on or off. The
        configuration is not changed and iCloud3 is not restarted.
        '''
        self.step_id = 'beta_version'
        self.errors = errors or {}
        utils_cf.log_step_info(self, user_input)

        is_prerelease_on = mp.icloud3_prerelease_switch_state()
        store_domain, _update_entity_id = mp.repo_update_entity(mp.IC3_REPO_ID)
        store = mp.STORE_FNAME.get(store_domain) or utils_cf.tr('beta_version_store_unknown')
        state = utils_cf.tr('beta_version_state_unknown') if is_prerelease_on is None \
                    else utils_cf.tr('beta_version_state_on') if is_prerelease_on \
                    else utils_cf.tr('beta_version_state_off')

        # The row that changes the switch is first
        menu_options = {'beta_version_on': None, 'beta_version_off': None}
        if is_prerelease_on:
            menu_options = {'beta_version_off': None, 'beta_version_on': None}
        menu_options['beta_version_back'] = None

        return await utils_cf.async_show_list_menu(self, 'beta_version', menu_options,
                                    placeholders={'store': store, 'state': state})

    async def async_step_beta_version_on(self, user_input=None):
        return await self._async_set_beta_version(turn_on=True)

    async def async_step_beta_version_off(self, user_input=None):
        return await self._async_set_beta_version(turn_on=False)

    async def async_step_beta_version_back(self, user_input=None):
        return await self.async_step_tools()

    async def _async_set_beta_version(self, turn_on):
        self.errors = {}
        if turn_on:
            await self.async_enable_icloud3_beta_downloads()
        else:
            await self.async_disable_icloud3_beta_downloads()
        self.errors = self.errors or {'base': 'beta_version_on_done' if turn_on else 'beta_version_off_done'}

        return await self.async_step_tools(errors=self.errors)

#------------------------------------------------------------------------------------------
    async def async_disable_icloud3_beta_downloads(self):
        '''
        Turn off the iCloud3 Pre-release switch in HACS/Marketplace
        '''
        result = await mp.async_set_icloud3_prerelease_switch(turn_on=False)
        self._set_prerelease_switch_error(result)

#------------------------------------------------------------------------------------------
    async def async_enable_icloud3_beta_downloads(self):
        '''
        Turn on the iCloud3 Pre-release switch in HACS/Marketplace
        '''
        result = await mp.async_set_icloud3_prerelease_switch(turn_on=True)
        self._set_prerelease_switch_error(result)

#------------------------------------------------------------------------------------------
    def _set_prerelease_switch_error(self, result):
        '''
        Set the error message displayed when the Pre-release switch was not changed.
        The done message is displayed if it was.
        '''
        if result == '':
            return

        self.errors = {'base': PRERELEASE_SWITCH_ERRORS.get(result, 'prerelease_switch_failed')}

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
        Delete all files in the .storage/icloud3.apple_acct directory
        '''

        post_alert("All Apple Account cookie and session files are being deleted, "
                    "tracking is paused until iCloud3 restarts")
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
        user_input = utils_cf.select_value(user_input,
                                CONF_LOG_LEVEL, LOG_LEVEL_OPTIONS)

        utils_cf.log_step_info(self, user_input, action_item)

        if action_item == 'cancel_goto_menu':
            return await self.async_step_tools()

        # Log Level not was changed
        if (user_input[CONF_LOG_LEVEL] == Gb.conf_general[CONF_LOG_LEVEL]
                and user_input[CONF_LOG_LEVEL_DEVICES] == Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
            return await self.async_step_tools()

        if (is_empty(user_input[CONF_LOG_LEVEL_DEVICES])
                or len(user_input[CONF_LOG_LEVEL_DEVICES]) >= len(Gb.Devices)):
            user_input[CONF_LOG_LEVEL_DEVICES] = ['all']

        elif len(user_input[CONF_LOG_LEVEL_DEVICES]) > 1:
            list_del(user_input[CONF_LOG_LEVEL_DEVICES], 'all')

        Gb.log_level_devices = user_input[CONF_LOG_LEVEL_DEVICES].copy()

        self.saved_item = 'log_level'
        self._update_config_file_general(user_input)

        self.header_msg = 'conf_updated'
        return await self.async_step_tools()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           CLEANUP ENTITY REGISTRY
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_cleanup_entity_registry(self, user_input=None, errors=None):
        self.step_id = 'cleanup_entity_registry'
        self.errors = {}
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        utils_cf.log_step_info(self, user_input, action_item)

        if user_input is None:
            return self.async_show_form(step_id='cleanup_entity_registry',
                                        data_schema=forms.form_cleanup_entity_registry(self),
                                        errors=self.errors)

        placeholders = {}
        match action_item:
            case 'goto_previous':
                return await self.async_step_tools()

            case 'select_all':
                self.tools_entity_reg_check_all = True

            case 'toggle_sensor_lists':
                self.tools_cleanup_er_sensor_all = not self.tools_cleanup_er_sensor_all

            case 'delete_device_sensors':
                if all(is_empty(devicenames) for devicenames in user_input.values()):
                    return await self.async_step_tools()

                if isnot_empty(user_input.get('active')):
                    return await self._confirm_delete_active_device_sensors(user_input)

                placeholders = self._tools_delete_device_sensors(user_input)

        return self.async_show_form(step_id='cleanup_entity_registry',
                            data_schema=forms.form_cleanup_entity_registry(self, user_input),
                            description_placeholders=placeholders,
                            errors=self.errors)

#......................................................
    async def _confirm_delete_active_device_sensors(self, user_input):
        '''
        The sensors of the active (tracked) devices are deleted and created again. Confirm it.
        '''
        async def _async_delete_device_sensors():
            self.cleanup_er_placeholders = self._tools_delete_device_sensors(user_input)

        # The items checked in the other groups are deleted with the active devices
        other_groups = [f"{utils_cf.tr_path(f'options.step.cleanup_entity_registry.data.{status}')} "
                        f"({len(devicenames)})"
                                for status, devicenames in user_input.items()
                                if status != 'active' and isnot_empty(devicenames)]
        other_groups_msg = ' ' + utils_cf.tr('confirm_cleanup_other_groups', groups=list_to_str(other_groups)) \
                                if other_groups else ''
        self.confirm_action = {
                'action_desc': utils_cf.tr('confirm_cleanup_active_devices',
                                            devices=list_to_str(user_input['active']),
                                            other_groups=other_groups_msg),
                'yes_label': utils_cf.tr('confirm_yes_cleanup_active_devices'),
                'no_label': utils_cf.tr('confirm_no_cleanup_active_devices'),
                'yes_func': None,
                'yes_func_async': _async_delete_device_sensors,
                'done_msg': 'deleted_device_sensors',
                'return_to_func_async': self.async_step_cleanup_entity_registry_done,
                'return_to_next_yes_func_async': None}
        return await self.async_step_confirm_action()

    async def async_step_cleanup_entity_registry_done(self, user_input=None, errors=None):
        '''
        Redisplay the cleanup screen with the result of the Confirm Action screen
        '''
        self.errors = errors or {}
        placeholders = getattr(self, 'cleanup_er_placeholders', None) or {}
        self.cleanup_er_placeholders = None
        if self.errors.get('base') == 'deleted_device_sensors' and is_empty(placeholders):
            self.errors = {}
        return self.async_show_form(step_id='cleanup_entity_registry',
                            data_schema=forms.form_cleanup_entity_registry(self),
                            description_placeholders=placeholders,
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

        # The device registry item (.dr:) is a device, the device_tracker and the other
        # entities of a device are counted as sensors without its device_tracker entity
        device_cnt = sensor_cnt = 0
        for status, devicenames in user_input.items():
            for devicename in devicenames:
                device_items = Gb.entity_reg_items_by_status.get(status, {}).get(devicename, {})
                if any(item.startswith('.dr:') for item in device_items):
                    device_cnt += 1
                sensor_cnt += len([item for item, item_data in device_items.items()
                                        if item.startswith('.') is False
                                            and item_data.get('platform') != PLATFORM_DEVICE_TRACKER])

        # Cycle thru status groups, delete all devices selected in each group
        for status in list(user_input.keys()):
            if status != 'active' and isnot_empty(user_input[status]):
                self._tools_delete_nonactive_devices(status, user_input[status])

        # Delete active devices after the others have been deleted so they can be
        # recreated correctly
        if 'active' in user_input and isnot_empty(user_input['active']):
            self._tools_delete_active_devices(user_input['active'])

        er_util.scan_entity_reg_for_icloud3_items()
        self.errors['base'] = 'deleted_device_sensors'

        return {'devices': utils_cf.tr_cnt('cnt_devices', device_cnt),
                'sensors': utils_cf.tr_cnt('cnt_sensors', sensor_cnt)}

#......................................................
    def _tools_delete_active_devices(self, devicenames):

        try:
            for devicename in devicenames:
                self.create_device_tracker_sensor_enities_on_exit = True

                if Device := Gb.Devices_by_devicename.get(devicename):
                    Device.pause_tracking()

                sensors_cf.remove_device_tracker_and_sensor_entities(
                                                        self, devicename,
                                                        rebuild_ic3db_dashboards=False)

                if Device:
                    Device.resume_tracking()

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
                            er_util.remove_deleted_device(device_id, devicename)

                    # Delete from entity_registry
                    if status.startswith('deleted_') is False:
                        er_util.remove_sensor(entity_key)
                    er_util.remove_deleted_entity(entity_key)

                except Exception as err:
                    log_exception(err)

            _sensors = list(device_sensors.keys())
            _deleted_msg = (f"{_device_msg}"
                            f"BaseName: sensor.{devicename}_, "
                            f"Count: {len(_sensors)}, "
                            f"Entities: {list_to_str(_sensors)}")

            log_info_msg(f"ENTITIES REMOVED ({status}): {_deleted_msg}")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   The tools on the Tools menu are menu options. HA opens a menu option's
#   async_step_[option] function so one is created for each tool.
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def _open_tool_step(tool_item):
    async def async_step_tool(self, user_input=None):
        return await self.open_tool(tool_item)
    return async_step_tool

for _tool_item in TOOL_ITEMS:
    setattr(OptionsFlow_Tools_Steps, f"async_step_tools_{_tool_item}", _open_tool_step(_tool_item))
