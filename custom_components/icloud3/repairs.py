'''
HA Repairs platform. Runs the iCloud3 fix handler for a fixable issue created by
messaging.post_repair_issue when Submit is selected in Settings > Repairs.

    iCloud3RepairFlow           - Submit runs the handler registered for the fix_action
    iCloud3DeviceRepairFlow     - fix_action 'update_device'. Submit opens the iCloud3
                                  Configure Update Device screen for the device
    iCloud3AppleAcctRepairFlow  - fix_action 'update_apple_acct'. Submit opens the iCloud3
                                  Configure Update Apple Account screen for the account
    iCloud3AnalyticsRepairFlow  - fix_action 'analytics_approval'. Submit enables sending
                                  the iCloud3 Analytics data, the X disables it
'''

import voluptuous as vol

from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core               import HomeAssistant
from homeassistant.helpers            import issue_registry as ir

from .global_variables  import GlobalVariables as Gb
from .const             import (DOMAIN, )
from .const_config      import (CONF_DATA_SOURCE, CONF_ANALYTICS_ENABLED, CONF_APPLE_ACCT, )
from .utils.utils       import (is_empty, )
from .utils.messaging   import (repair_fix_handlers, remove_open_repair_issue,
                                FIX_ACTION_UPDATE_DEVICE, FIX_ACTION_UPDATE_APPLE_ACCT,
                                FIX_ACTION_ANALYTICS_APPROVAL,
                                post_event, log_exception, )

from .startup                                   import config_file
from .support                                   import analytics
from .apple_acct                                import apple_acct_support as aas
from .configure                                 import selection_lists as lists
from .configure.screens.step_common             import OptionsFlow_Common_Steps
from .configure.screens.step_apple_acct         import OptionsFlow_AppleAccount_Steps
from .configure.screens.step_reauth             import OptionsFlow_Reauth_Steps
from .configure.screens.step_icloud3_device     import OptionsFlow_iCloud3Device_Steps


class iCloud3RepairFlow(ConfirmRepairFlow):
    '''
    Display the issue's error and message with Submit. Submit runs the handler
    registered for the issue's fix_action. The issue is removed if it was fixed and
    stays in Repairs if the handler is not available or failed.

    The message displayed after it was fixed is the issue's
    fix_flow.create_entry.<key> text in strings.json & translations/en.json, with the
    issue's placeholders. The handler returns True ('default' key) or the key. HA
    displays its own 'fixed' message if the issue does not have the text.
    '''

    async def async_step_confirm(self, user_input=None):
        if user_input is None:
            return await super().async_step_confirm()

        fix_data   = dict(self.data or {})
        devicename = fix_data.get('devicename', '')
        handler    = repair_fix_handlers.get(fix_data.get('fix_action'))

        if handler is None:
            return self.async_abort(reason='fix_action_not_available')

        try:
            fixed = await self.hass.async_add_executor_job(handler, fix_data)
        except Exception as err:
            log_exception(err)
            fixed = False

        if fixed is False:
            return self.async_abort(reason='fix_action_failed')

        remove_open_repair_issue(self.issue_id)
        post_event(devicename, f"HA Repairs > Fixed, {self.issue_id}")

        issue = ir.async_get(self.hass).async_get_issue(DOMAIN, self.issue_id)
        return self.async_create_entry(
                        data={},
                        description=fixed if isinstance(fixed, str) else 'default',
                        description_placeholders=issue.translation_placeholders if issue else None)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3ConfigRepairFlow(ConfirmRepairFlow, OptionsFlow_Common_Steps,
                                OptionsFlow_AppleAccount_Steps, OptionsFlow_Reauth_Steps,
                                OptionsFlow_iCloud3Device_Steps):
    '''
    Fix an iCloud3 configuration error. The issue's error and message are displayed
    with Submit. Submit opens the iCloud3 Configure screen for the item in error
    (async_open_config_screen) the same way it is opened from iCloud3 Configure.

    The step_... screens return to a list screen or the Menu when they are done.
    Those steps are replaced here to end the repair:
        - The configuration was changed - Save it, restart iCloud3 and remove the issue
        - Nothing was changed           - Close the dialog, the issue stays in Repairs

    The screen text is in the issue's fix_flow in strings.json & translations/en.json,
    not in the 'options' section used by iCloud3 Configure.
    '''
    # The step_id the step_... screens return to when they are done
    menu_item_return = ''
    # fix_flow.abort reason when the item is no longer in the configuration
    not_found_reason = ''
    # fix_flow.create_entry key displayed when the configuration was updated
    fixed_description = 'default'

    def __init__(self):
        # The step_... classes are mixins, their variables are set here as the
        # OptionsFlow initialize_options does
        self.initialize_common_variables()
        lists.initialize_lists(self)
        self.initialize_apple_acct_variables()
        self.initialize_reauth_variables()
        self.initialize_icloud3_device_variables()

        self.is_repair_flow = True      # form_... & step_... modules use it to change the screens
        self.menu_item   = self.menu_item_return
        self.data_source = Gb.conf_tracking.get(CONF_DATA_SOURCE, '') if Gb.conf_tracking else ''
        self.repair_item = ''           # devicename or apple_id being repaired, for the Event Log

#..............................................................................
    async def async_step_confirm(self, user_input=None):
        if user_input is None:
            return await super().async_step_confirm()

        if Gb.is_icloud3_startup_inprocess or self._is_config_available() is False:
            return self._abort_repair('fix_action_not_available')

        try:
            form = await self.async_open_config_screen(self.data or {})
        except Exception as err:
            log_exception(err)
            return self._abort_repair('fix_action_failed')

        if form is None:
            return self._abort_repair(self.not_found_reason)

        return form

    def _is_config_available(self):
        return True

    async def async_open_config_screen(self, fix_data):
        '''Display the configuration screen. Return None if the item is not configured.'''
        return None

#..............................................................................
    def _issue_placeholders(self):
        issue = ir.async_get(self.hass).async_get_issue(DOMAIN, self.issue_id)
        return issue.translation_placeholders if issue else None

    def _abort_repair(self, reason):
        '''Close the dialog with the fix_flow.abort text, the issue stays in Repairs'''
        return self.async_abort(reason=reason, description_placeholders=self._issue_placeholders())

#..............................................................................
    # The step_... screens return to these when they are done
    async def async_step_menu(self, user_input=None, errors=None):
        return await self._async_finish_repair()

    async def exit_configure_settings_final_tasks(self, exit_by_x_click=False):
        return await self._async_finish_repair()

#..............................................................................
    async def _async_finish_repair(self):
        '''
        Save the updated configuration and restart iCloud3 using the same process as
        exiting iCloud3 Configure. HA removes the issue when the entry is created.
        '''
        if is_empty(self.config_parms_update_control):
            return self._abort_repair('no_changes')

        await self.async_write_icloud3_configuration_file(force_write=True)
        Gb.config_parms_update_control = self.config_parms_update_control.copy()

        placeholders = self._issue_placeholders()

        remove_open_repair_issue(self.issue_id)
        post_event(f"HA Repairs > Fixed, {self.repair_item}, {self.issue_id}, "
                    f"The configuration was updated")

        return self.async_create_entry(
                        data={},
                        description=self.fixed_description,
                        description_placeholders=placeholders)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3DeviceRepairFlow(iCloud3ConfigRepairFlow):
    '''
    Fix an iCloud3 device configuration error. Submit opens the iCloud3 Configure
    Update Device screen for the device (issue data 'devicename') the same way it is
    opened when the device is selected on the iCloud3 Devices screen.
    '''
    menu_item_return = 'device_list'
    not_found_reason = 'device_not_found'

    def _is_config_available(self):
        return not is_empty(Gb.conf_devices)

    async def async_open_config_screen(self, fix_data):
        self.repair_item = fix_data.get('devicename', '')
        return await self.async_open_update_device_screen(self.repair_item)

    # The step_icloud3_device screens return to this when they are done
    async def async_step_device_list(self, user_input=None, errors=None):
        return await self._async_finish_repair()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
REPAIR_ACTION_UPDATE_APPLE_ACCT = 'update_apple_acct'
REPAIR_ACTION_UPDATE_DEVICE     = 'update_device'
APPLE_ACCT_REPAIR_ACTION_OPTIONS = {
        REPAIR_ACTION_UPDATE_APPLE_ACCT:
                'UPDATE APPLE ACCOUNT > Add/Update this Apple Account',
        REPAIR_ACTION_UPDATE_DEVICE:
                'UPDATE ICLOUD3 DEVICE > Display the Update iCloud3 Device screen to '
                'select the correct Apple Account'}

class iCloud3AppleAcctRepairFlow(iCloud3ConfigRepairFlow):
    '''
    Fix an iCloud3 Apple Account configuration error. The error can be the account or
    the device using it, the action selected on the confirm screen is done on Submit:
        - Update Apple Account  - Open the iCloud3 Configure Update Apple Account screen
                                  for the account (issue data 'apple_id') the same way it
                                  is opened when the account is selected on the Apple
                                  Accounts screen. It is opened in Add mode with the
                                  apple_id filled in if the account is not configured. The
                                  Reauth screen is displayed if the login needs an
                                  authentication code.
        - Update iCloud3 Device - Open the Update Device screen for the first device
                                  using the account so the correct account can be
                                  selected. The repair is then an update_device repair.

    The issue data 'apple_acct_status' of an unknown Apple Acct
    (start_ic3.unknown_apple_acct_status) selects the actions:
        - 'deleted'   - Both, Add is filled in with the password saved in the .tpw file
        - 'exists'    - Both
        - 'not_found' - Update iCloud3 Device, Apple does not have the account
        - ''          - Both
    '''
    menu_item_return = 'apple_accounts'
    not_found_reason = 'apple_acct_not_found'

    def __init__(self):
        super().__init__()
        self.repair_action = REPAIR_ACTION_UPDATE_APPLE_ACCT
        self.repair_fname  = ''         # Device fname for the update_device action text

#..............................................................................
    async def async_step_confirm(self, user_input=None):
        if user_input is None:
            repair_action_options = self._repair_action_options()
            self.repair_action    = next(iter(repair_action_options))

            # Only one action, Submit does it without a selection
            if len(repair_action_options) == 1:
                return await super().async_step_confirm()

            return self.async_show_form(step_id='confirm',
                                        data_schema=vol.Schema({
                                            vol.Required('repair_action',
                                                    default=self.repair_action):
                                                    vol.In(repair_action_options)}),
                                        description_placeholders=self._issue_placeholders())

        self.repair_action = user_input.get('repair_action', self.repair_action)
        return await super().async_step_confirm(user_input)

    def _repair_action_options(self):
        '''
        The Update Device action is only available if a device uses the account. It is
        not a device error if no Apple Accounts are configured, the account must be added.
        It is the only action if Apple does not have the account.
        '''
        apple_id = (self.data or {}).get('apple_id', '')
        if (is_empty(Gb.conf_apple_ids)
                or not any(Device.isnot_inactive
                                for Device in Gb.Devices_by_apple_id.get(apple_id, []))):
            return {REPAIR_ACTION_UPDATE_APPLE_ACCT:
                        APPLE_ACCT_REPAIR_ACTION_OPTIONS[REPAIR_ACTION_UPDATE_APPLE_ACCT]}

        if (self.data or {}).get('apple_acct_status') == 'not_found':
            return {REPAIR_ACTION_UPDATE_DEVICE:
                        APPLE_ACCT_REPAIR_ACTION_OPTIONS[REPAIR_ACTION_UPDATE_DEVICE]}

        return APPLE_ACCT_REPAIR_ACTION_OPTIONS

    def _issue_placeholders(self):
        # The update_device action's abort & create_entry text use the device's name
        placeholders = super()._issue_placeholders() or {}
        return {**placeholders, 'device': self.repair_fname}

#..............................................................................
    async def async_open_config_screen(self, fix_data):
        apple_id = fix_data.get('apple_id', '')

        if self.repair_action == REPAIR_ACTION_UPDATE_DEVICE:
            return await self._async_open_update_device_screen(apple_id)

        self.repair_item = apple_id
        if apple_id in [conf_apple_acct[CONF_APPLE_ACCT]
                                for conf_apple_acct in Gb.conf_apple_accounts]:
            return await self.async_open_update_apple_acct_screen(apple_id)

        # A removed Apple Acct, fill in the password saved in its .tpw file
        password = ''
        if fix_data.get('apple_acct_status') == 'deleted':
            password = await self.hass.async_add_executor_job(
                                    aas.apple_acct_saved_password, apple_id)

        return await self.async_open_add_apple_acct_screen(apple_id, password)

    async def _async_open_update_device_screen(self, apple_id):
        '''
        Change this to an update_device repair for the first device using the account.
        The step_icloud3_device screens return to async_step_device_list when done.
        '''
        # Inactive Devices do not get an issue, use the first active one
        Devices = [Device for Device in Gb.Devices_by_apple_id.get(apple_id, [])
                            if Device.isnot_inactive]
        if is_empty(Devices):
            return None

        Device = Devices[0]
        self.repair_item       = Device.devicename
        self.repair_fname      = Device.fname
        self.menu_item         = 'device_list'
        self.not_found_reason  = 'device_not_found'
        self.fixed_description = 'device_updated'

        return await self.async_open_update_device_screen(self.repair_item)

#..............................................................................
    # The step_apple_acct & step_reauth screens return to this when they are done
    async def async_step_apple_accounts(self, user_input=None, errors=None):
        return await self._async_finish_repair()

    # The step_icloud3_device screens return to this when they are done
    async def async_step_device_list(self, user_input=None, errors=None):
        return await self._async_finish_repair()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ANALYTICS_APPROVAL_OPTIONS = {
        'enable':  'ENABLE > Send the iCloud3 Analytics data',
        'disable': 'DISABLE > Do not send the iCloud3 Analytics data'}

class iCloud3AnalyticsRepairFlow(ConfirmRepairFlow):
    '''
    Request approval to send the iCloud3 Analytics data. The iCloud3 Configure >
    Analytics screen's description and the data that is sent are displayed with an
    Enable/Disable selection.
        - Submit  - analytics_enabled = True (Enable) or False (Disable). The
                    configuration file is updated and the issue is removed.
        - Close   - Nothing is changed, the issue stays in Repairs. The X and a click
                    outside the dialog can not be told apart (both delete the flow).
    '''
    async def async_step_confirm(self, user_input=None):
        if user_input is None:
            json_payload = await analytics.async_build_json_payload()
            json_payload['uuid'] = 'HA Installation ID'
            await analytics.async_get_version_downloads()

            return self.async_show_form(step_id='confirm',
                                        data_schema=vol.Schema({
                                            vol.Required('analytics_approval'):
                                                    vol.In(ANALYTICS_APPROVAL_OPTIONS)}),
                                        description_placeholders={
                                                'json_payload': str(json_payload),
                                                'downloads': analytics.format_version_downloads_msg()})

        analytics_enabled = user_input.get('analytics_approval') == 'enable'
        await self._async_update_analytics_enabled(analytics_enabled)

        return self.async_create_entry(
                        data={},
                        description='default' if analytics_enabled else 'disabled')

    async def _async_update_analytics_enabled(self, analytics_enabled):
        try:
            Gb.conf_general[CONF_ANALYTICS_ENABLED] = analytics_enabled
            Gb.analytics_enabled = analytics_enabled
            await config_file.async_write_icloud3_configuration_file()

            remove_open_repair_issue(self.issue_id)
            post_event(f"HA Repairs > iCloud3 Analytics "
                        f"{'Enabled' if analytics_enabled else 'Disabled'}")

        except Exception as err:
            log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data) -> RepairsFlow:
    fix_action = (data or {}).get('fix_action')
    if fix_action == FIX_ACTION_UPDATE_DEVICE:
        return iCloud3DeviceRepairFlow()
    if fix_action == FIX_ACTION_UPDATE_APPLE_ACCT:
        return iCloud3AppleAcctRepairFlow()
    if fix_action == FIX_ACTION_ANALYTICS_APPROVAL:
        return iCloud3AnalyticsRepairFlow()

    return iCloud3RepairFlow()
