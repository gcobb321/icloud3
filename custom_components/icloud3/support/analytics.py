

from ..global_variables     import GlobalVariables as Gb
from ..const_config         import (CONF_ANALYTICS_ENABLED, CONF_ANALYTICS_SENT_DATE,
                                    CONF_ANALYTICS_COMMENT, CONF_VERSION_INSTALL_DATE, )

from ..utils.messaging      import (log_info_msg, log_debug_msg, log_exception, post_event, )
from ..utils.time_util      import (today, )
from ..utils.utils          import (is_empty, isnot_empty, )
from ..startup              import config_file

import asyncio
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers  import instance_id
import homeassistant.util.dt as dt_util

ANALYTICS_URL          = 'https://icloud3-analytics.gcobb321.workers.dev'
ANALYTICS_REPORTS_URL  = f'{ANALYTICS_URL}/reports'
ANALYTICS_TIMEOUT_SECS = 15

# Analytics Reports screen display limits
REPORT_MAX_ROWS        = 250    # Rows displayed, the rest are summarized in the footer
REPORT_MAX_COL_LEN     = 55     # Longest text displayed in a column (comments)

# Must match ANALYTICS_KEY in the icloud3-analytics Worker (wrangler.jsonc). The Worker
# rejects the request if it is wrong. It is not stored in the database.
ANALYTICS_KEY          = 'f0115458d27b7b66b65aff88150a5441'


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 ANALYTICS
#       Send the installation's current state to the iCloud3 Analytics Database
#       (Cloudflare Worker + D1). The Worker upserts on the HA instance uuid so
#       one row is kept per installation.
#
#       Sending is best-effort. A network error, timeout or non-200 response is
#       logged and ignored. It never raises or blocks startup/tracking.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def is_analytics_send_due():
    '''
    Analytics are enabled and have not been sent today
    '''
    return (Gb.conf_general.get(CONF_ANALYTICS_ENABLED) is True
            and Gb.conf_general.get(CONF_ANALYTICS_SENT_DATE, '') != today())

#-------------------------------------------------------------------------------------------
def schedule_send_analytics_data():
    '''
    Send the analytics data from a non-event loop thread (icloud3_main 5-sec loop)
    if it is enabled and due
    '''
    try:
        if is_analytics_send_due():
            asyncio.run_coroutine_threadsafe(async_send_analytics_data(), Gb.hass.loop)

    except Exception as err:
        log_exception(err)

#-------------------------------------------------------------------------------------------
async def async_send_analytics_data(write_config_file=True):
    '''
    POST the analytics payload to the iCloud3 Analytics Database

    Parameters:
        write_config_file - Save the analytics_sent_date to the configuration file.
                    config_flow sets this to False and commits the update itself.
    Return:
        True  - Data was accepted (HTTP 200)
        False - Not sent
    '''
    try:
        json_payload = await async_build_json_payload()

        session  = async_get_clientsession(Gb.hass)
        async with session.post(ANALYTICS_URL,
                                json={**json_payload, 'ic3_key': ANALYTICS_KEY},
                                timeout=aiohttp.ClientTimeout(total=ANALYTICS_TIMEOUT_SECS)) as response:
            response_text = await response.text()

            if response.status != 200:
                log_info_msg(f"iCloud3 Analytics > Not Sent, "
                                f"Status-{response.status}, {response_text[:100]}")
                return False

        Gb.conf_general[CONF_ANALYTICS_SENT_DATE] = today()
        if write_config_file:
            await config_file.async_write_icloud3_configuration_file()

        post_event("iCloud3 Analytics > Data Sent")
        log_debug_msg(f"iCloud3 Analytics > Sent, {json_payload}")
        return True

    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        log_info_msg(f"iCloud3 Analytics > Not Sent, {type(err).__name__} {err}")

    except Exception as err:
        log_exception(err)

    return False

#-------------------------------------------------------------------------------------------
async def async_build_json_payload():
    '''
    Build the analytics data payload. The uuid is the HA instance id so it is stable
    for the installation and matches the key the Worker upserts on.
    '''
    return {
        'uuid': await instance_id.async_get(Gb.hass),
        'version': Gb.version,
        'version_date': Gb.conf_profile.get(CONF_VERSION_INSTALL_DATE, '')[:10],
        'country': (Gb.ha_location_info.get('country_code') or '').upper(),
        'region': Gb.ha_location_info.get('region_code') or '',
        'apple_accts': len(Gb.conf_apple_accounts),
        'mobapp_devices': len(Gb.Devices_by_mobapp_dname),
        'devices': len(Gb.conf_devices),
        'tracked': len(Gb.Devices_by_devicename_tracked),
        'monitored': len(Gb.Devices_by_devicename_monitored),
        'inactive': len(Gb.inactive_fname_by_devicename),
        'comment': Gb.conf_general.get(CONF_ANALYTICS_COMMENT, '').strip(),
    }


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 ANALYTICS REPORTS
#       Run the reports in the Analytics Database's report_names table and format
#       the results for the config_flow Analytics Reports screen.
#
#       The report's sql statement is never sent to the Worker. iCloud3 asks for a
#       report by name and the Worker runs the sql statement it has stored for it.
#       The ic3_key is in the iCloud3 source so anything the Worker will accept,
#       anyone can ask it to run.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_request_report(request):
    '''
    POST a report request to the Analytics Database and return the json response.

    Parameters:
        request - {'action': 'names'} .............. The reports in the report_names table
                  {'action': 'run', 'name': name} .. Run the report and return the results
    Return:
        The response json dict. A failure is returned as {'ok': False, 'error': msg} so it
        can be displayed on the Analytics Reports screen.
    '''
    try:
        session = async_get_clientsession(Gb.hass)
        async with session.post(ANALYTICS_REPORTS_URL,
                                json={**request, 'ic3_key': ANALYTICS_KEY},
                                timeout=aiohttp.ClientTimeout(total=ANALYTICS_TIMEOUT_SECS)) as response:
            # A rejected request (bad key, unknown report, rate limited) explains itself in
            # the 'error' item. A non-json response (429, 413) is returned as text.
            try:
                response_json = await response.json(content_type=None)
            except Exception:
                response_json = {}

            if response.status == 200 and response_json.get('ok') is True:
                return response_json

            error_msg = response_json.get('error') or (await response.text())[:100]
            log_info_msg(f"iCloud3 Analytics Report > Failed, "
                            f"Status-{response.status}, {error_msg}")

            return {'ok': False, 'error': f"{error_msg} (Status-{response.status})"}

    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        log_info_msg(f"iCloud3 Analytics Report > Failed, {type(err).__name__} {err}")
        return {'ok': False, 'error': f"The Analytics Database did not respond, {type(err).__name__}"}

    except Exception as err:
        log_exception(err)
        return {'ok': False, 'error': f"{type(err).__name__}, {err}"}

#-------------------------------------------------------------------------------------------
async def async_get_version_downloads():
    '''
    Get the GitHub download counts from the Analytics Database's version_downloads table and
    save them in Gb so they can be displayed on the Analytics screens. The Worker refreshes
    the table from GitHub every night so they are only retrieved once a day.

    Return:
        True  - The counts in Gb are current
        False - They could not be retrieved (the previous counts, if any, are unchanged)
    '''
    if Gb.github_downloads_date == today():
        return True

    response = await async_request_report({'action': 'downloads'})

    if response.get('ok') is not True:
        return False

    Gb.github_version               = response.get('version', '')
    Gb.github_published_date        = response.get('published_date', '')[:10]
    Gb.github_icloud3_downloads     = response.get('icloud3_downloads', 0) or 0
    Gb.github_beta_downloads        = response.get('beta_downloads', 0) or 0
    Gb.github_icloud3_total         = response.get('icloud3_total', 0) or 0
    Gb.github_beta_total            = response.get('beta_total', 0) or 0
    Gb.analytics_installs           = response.get('analytics_installs', 0) or 0
    Gb.github_versions_cnt          = response.get('versions', 0) or 0
    Gb.github_downloads_date        = today()

    log_debug_msg(f"iCloud3 Analytics Downloads > {response}")

    return True

#-------------------------------------------------------------------------------------------
def format_version_downloads_msg():
    '''
    The GitHub download counts displayed on the Analytics screens

        v3.7.5, Downloads-13,389, Analytics-2, Released-9/8/2026
        v3.7.5, Downloads-13,389, Analytics-700 (5.23%), Released-9/8/2026
    '''
    if Gb.github_version == '':
        return 'The GitHub download counts are not available'

    downloads = Gb.github_icloud3_downloads + Gb.github_beta_downloads

    downloads_msg = (f"v{Gb.github_version} "
                    f"({_format_release_date(Gb.github_published_date)}), "
                    f"Downloads-{downloads:,}, "
                    f"AnalyticsUsers-{Gb.analytics_installs:,}")

    # Portion of the downloads that enabled analytics. It is not displayed below 1% - a
    # fraction of a percent says nothing and reads like an error
    if downloads > 0:
        analytics_pct = 100.0 * Gb.analytics_installs / downloads
        downloads_msg += f" ({analytics_pct:.2f}%)" if analytics_pct >= 1 else ""

    return downloads_msg

#-------------------------------------------------------------------------------------------
def _format_release_date(published_date):
    '''
    '2026-09-08' > '9/8/2026', or '8/9/2026' when the 24-hour time format is used
    '''
    yyyy_mm_dd = published_date[:10].split('-')

    if len(yyyy_mm_dd) != 3:
        return published_date

    yyyy, mm, dd = yyyy_mm_dd

    if Gb.time_format_24_hour:
        return f"{int(dd)}/{int(mm)}/{yyyy}"

    return f"{int(mm)}/{int(dd)}/{yyyy}"

#-------------------------------------------------------------------------------------------
async def async_run_query(self, query_name):
    '''
    Run the report selected on the Analytics Reports screen

    Return:
        The json results dict - {'ok': True, 'name', 'columns', 'rows', 'row_count', ...}
    '''
    if query_name in ['', 'none', None]:
        return {'ok': False, 'error': 'A report has not been selected'}

    query_results_json = await async_request_report({'action': 'run', 'name': query_name})

    log_debug_msg(f"iCloud3 Analytics Report > {query_name}, {query_results_json}")

    return query_results_json

#-------------------------------------------------------------------------------------------
def create_reports_from_results(self, query_results_json):
    '''
    Reformat the json results returned by the Analytics Database into a markdown table
    displayed on the Analytics Reports screen by the '{report}' description placeholder.
    '''
    try:
        results = query_results_json or {}

        if results.get('ok') is not True:
            self.query_report_md = f"**{results.get('error', 'The report could not be run')}**"
            return self.query_report_md

        report_name = results.get('name', '')
        columns     = results.get('columns', [])
        rows        = results.get('rows', [])

        if is_empty(columns) or is_empty(rows):
            self.query_report_md = f"**{report_name}** — No data was returned"
            return self.query_report_md

        display_rows = rows[:REPORT_MAX_ROWS]

        # Left align every column, numeric and text
        md  = [f"**{report_name}**", '']
        md.append(f"| {' | '.join(_column_heading(column) for column in columns)} |")
        md.append(f"|{'|'.join(':---' for column in columns)}|")
        md.extend([f"| {' | '.join(_column_value(row.get(column)) for column in columns)} |"
                    for row in display_rows])
        md.append('')

        row_count = results.get('row_count', len(rows))
        footer    = f"{row_count} row{'' if row_count == 1 else 's'}"
        if len(display_rows) < row_count:
            footer += f", first {len(display_rows)} displayed"
        if results.get('truncated'):
            footer += ' (the report returned more rows than the database will send)'
        footer += f" — {results.get('run_date', '')} UTC"

        md.append(footer)

        self.query_report_md = '\n'.join(md)

    except Exception as err:
        log_exception(err)
        self.query_report_md = f"**The report results could not be formatted, {type(err).__name__}**"

    return self.query_report_md

#-------------------------------------------------------------------------------------------
def _column_heading(column):
    '''
    'total_installs' > 'Total Installs'

    A column the sql statement already aliased with capital letters ("iCloud3") is used as
    it is - title() would turn it into 'Icloud3'.
    '''
    column = str(column)

    if column != column.lower():
        return column

    return column.replace('_', ' ').title()

#-------------------------------------------------------------------------------------------
def _column_value(value):
    ''' Format a column's value so it does not break the markdown table '''

    if value is None:
        return ''

    value_str = f"{value:g}" if isinstance(value, float) else str(value)
    value_str = value_str.replace('|', '\\|').replace('\n', ' ').strip()

    if len(value_str) > REPORT_MAX_COL_LEN:
        value_str = f"{value_str[:REPORT_MAX_COL_LEN - 1]}…"

    return value_str

#-------------------------------------------------------------------------------------------
async def async_build_analytics_report_names_list(self):
    '''
    Get the reports in the Analytics Database's report_names table (list_no sequence) and
    build the Analytics Reports screen's report selection list. The list is retrieved when
    the screen is first displayed and reused while the config_flow is open.
    '''
    if isnot_empty([name for name in self.analytic_reports_by_name if name != 'none']):
        return

    self.analytic_reports_by_name = {}
    self.analytic_reports_sql_by_name = {}

    response = await async_request_report({'action': 'names'})

    for report in response.get('reports', []):
        report_name = report.get('name', '').strip()
        if report_name == '':
            continue

        self.analytic_reports_by_name[report_name] = report_name
        self.analytic_reports_sql_by_name[report_name] = report.get('sql_stmt', '')

    if is_empty(self.analytic_reports_by_name):
        log_info_msg(f"iCloud3 Analytics Reports > No reports available, "
                        f"{response.get('error', '')}")

    build_analytics_report_names_list(self)

    return

#-------------------------------------------------------------------------------------------
def build_analytics_report_names_list(self):
    if is_empty(self.analytic_reports_by_name):
        self.analytic_reports_by_name['none'] = 'None > No Queries are Available'

    return
