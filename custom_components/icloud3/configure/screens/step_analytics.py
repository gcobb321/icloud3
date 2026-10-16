

from ...global_variables    import GlobalVariables as Gb
from ...const               import (CF_GENERAL,
                                    CONF_ANALYTICS_ENABLED, CONF_ANALYTICS_SENT_DATE,
                                    CONF_ANALYTICS_COMMENT, CONF_VERSION_INSTALL_DATE,
                                    )

from ...utils.utils         import (is_empty, isnot_empty, list_to_str, list_del, list_add, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ...support             import analytics
from .                      import form_analytics as forms
from ..                     import utils_cf
from ..const_form_lists     import *


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#    ANALYTICS CONFIG FLOW
#        - async_step_analytics
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OptionsFlow_Analytics_Steps:


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           ANALYTICS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_analytics(self, user_input=None, errors=None):
        '''
        1. Delete the device from the tracking devices list and adjust the device index
        2. Delete all devices
        3. Clear the iCloud, Mobile App and track_from_zone fields from all devices
        '''
        self.step_id = 'analytics'
        self.errors = errors or {}
        self.errors_user_input = {}

        await self.async_write_icloud3_configuration_file()

        json_payload = await analytics.async_build_json_payload()
        json_payload['uuid'] = 'HA Installation ID'

        # GitHub download counts, refreshed once a day
        await analytics.async_get_version_downloads()

        if user_input is None:
            return self.async_show_form(step_id='analytics',
                                        data_schema=forms.form_analytics(self, user_input),
                                        description_placeholders={
                                                'json_payload': str(json_payload),
                                                'downloads': analytics.format_version_downloads_msg()},
                                        errors=self.errors)

        user_input = self._unpack_ui_analytics(user_input)
        user_input, action_item = utils_cf.action_text_to_item(self, user_input)

        utils_cf.log_step_info(self, user_input, action_item)

        match action_item:
            case 'menu':
                return await self.async_step_menu()

            case 'analytics_reports':
                # The OptionsFlowHandler is reused until HA restarts so the report list
                # would be kept for the life of HA. Refresh it when the screen is opened
                # to pick up reports that have been added, renamed or reordered.
                self.analytic_reports_by_name = {}
                return await self.async_step_analytics_reports()

            case 'send_analytics_data':
                user_input[CONF_ANALYTICS_ENABLED] = True
                self.update_config_file(CF_GENERAL, user_input, action_item)
                if await analytics.async_send_analytics_data(write_config_file=False):
                    self.config_file_commit_updates = True
                    self.errors['base'] = 'analytics_sent'
                else:
                    self.errors['base'] = 'analytics_not_sent'

            case 'save':
                self.update_config_file(CF_GENERAL, user_input, action_item)
                Gb.analytics_enabled = Gb.conf_general[CONF_ANALYTICS_ENABLED]
                return await self.async_step_menu()


        return await self.async_step_analytics(errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _unpack_ui_analytics(self, user_input):

        user_input['analytics_enabled'] = isnot_empty(user_input['analytics_enabled'])

        return user_input


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           ANALYTICS REPORTS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_analytics_reports(self, user_input=None, errors=None):
        '''
        1. Delete the device from the tracking devices list and adjust the device index
        2. Delete all devices
        3. Clear the iCloud, Mobile App and track_from_zone fields from all devices
        '''
        self.step_id = 'analytics_reports'
        self.errors = errors or {}
        self.errors_user_input = {}

        await self.async_write_icloud3_configuration_file()

        # Get the reports in the Analytics Database's report_names table the first time
        # the screen is displayed
        await analytics.async_build_analytics_report_names_list(self)

        # GitHub download counts, refreshed once a day
        await analytics.async_get_version_downloads()

        if user_input is None:
            return self.async_show_form(step_id='analytics_reports',
                                        data_schema=forms.form_analytics_reports(self, user_input),
                                        description_placeholders={
                                                'report': str(self.query_report_md),
                                                'downloads': analytics.format_version_downloads_msg()},
                                        errors=self.errors)

        user_input, action_item = utils_cf.action_text_to_item(self, user_input)
        user_input = self._unpack_ui_analytics_reports(user_input)

        utils_cf.log_step_info(self, user_input, action_item)

        match action_item:
            case 'menu':
                return await self.async_step_menu()

            case 'analytics':
                return await self.async_step_analytics()

            case 'run_report':
                self.report_selected = user_input['report_selected']
                query_results_json   = await analytics.async_run_query(self, self.report_selected)
                self.query_report_md = analytics.create_reports_from_results(self, query_results_json)

        return await self.async_step_analytics_reports(errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _unpack_ui_analytics_reports(self, user_input):


        user_input = utils_cf.option_text_to_parm(user_input,
                                                'report_selected',
                                                self.analytic_reports_by_name)

        return user_input