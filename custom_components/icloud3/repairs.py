'''
HA Repairs platform. Runs the iCloud3 fix handler for a fixable issue created by
messaging.post_repair_issue when Submit is selected in Settings > Repairs.
'''

from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core               import HomeAssistant

from .utils.messaging   import (repair_fix_handlers, clear_repair_issue_alert_msg,
                                post_event, log_exception, )


class iCloud3RepairFlow(ConfirmRepairFlow):
    '''
    Display the issue's title and message with Submit. Submit runs the handler
    registered for the issue's fix_action. The issue is removed if it was fixed and
    stays in Repairs if the handler is not available or failed.
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

        clear_repair_issue_alert_msg(fix_data.get('alert_key', ''))
        post_event(devicename, f"HA Repairs > Fixed, {self.issue_id}")

        return self.async_create_entry(data={})


async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data) -> RepairsFlow:
    return iCloud3RepairFlow()
