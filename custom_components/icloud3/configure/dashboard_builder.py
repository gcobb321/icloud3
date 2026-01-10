
# from ...lovelace import dashboard
from homeassistant.components.lovelace import dashboard
from homeassistant.components.lovelace import _register_panel
from homeassistant.components.lovelace.const import (LOVELACE_DATA,
                                                    STORAGE_DASHBOARD_CREATE_FIELDS,
                                                    STORAGE_DASHBOARD_UPDATE_FIELDS)

from ..global_variables     import GlobalVariables as Gb
from ..const                import (IPHONE_FNAME, DEVICE_TYPES, IPHONE,
                                    CONF_IC3_DEVICENAME, CONF_TRACKING_MODE, CONF_DEVICE_TYPE,
                                    TRACK, INACTIVE)

from ..utils.utils          import (instr, is_number, is_empty, isnot_empty, list_to_str, str_to_list,
                                    list_add, list_del, dict_value_to_list, six_item_list, six_item_dict, )
from ..utils.messaging      import (log_exception, log_debug_msg, log_info_msg, _log,  _evlog, )
from ..utils                import file_io

from .const_form_lists      import *
from .                      import utils_configure as utils
from .                      import selection_lists as lists

#-------------------------------------------------------------------------------------------
DASHBOARD_ICONS = [
        'mdi:cloud-download-outline',
        'mdi:cloud-upload-outline',
        'mdi:cloud-check-variant-outline',
        'mdi:cloud-refresh-variant-outline',
        'mdi:cloud-alert-outline',
        'mdi:cloud-percent-outline',
        'mdi:cloud-question-outline',

        'mdi:cloud-cog-outline',
        'mdi:cloud-plus-outline',
        'mdi:cloud-remove-outline',
        'mdi:cloud-sync-outline',

        'mdi:cloud-arrow-up-outline',
        'mdi:cloud-arrow-down-outline',
        'mdi:cloud-arrow-left-outline',
        'mdi:cloud-arrow-right-outline',
]
DASHBOARD_TEMPLATE_FILES = [
        'template',
        'master',
        'filler',
        'json'
]

MAIN_VIEW_STYLE_TEMPLATE = 'Main-View-Template-Style: '
CONFIGURE_DASHBOARD_TEMPLATES_DIR = '/configure/dashboard_templates'

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           BUILD INITIAL DASHBOARD WHEN ICLOUD3 INTEGRATION IS INSTALLED
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def build_initial_icloud3_dashboard(self):
    '''
    This is run when iCloud3 is being installed
    '''
    try:
        self.ui_selected_dbname = ADD

        await build_existing_dashboards_selection_list(self)
        await update_or_create_dashboard(self)
        return True

    except Exception as err:
        log_exception(err)

    return False

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           UPDATE IC3DB- VIEWS ON ALL DASHBOARDS WHEN DEVICES ARE ADDED OR DELETED
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def update_ic3db_dashboards_new_deleted_devices(self):
    '''
    This is run when devices are added or deleted on the add_device or update_device
    screens after all device_tracker entities have been processed.

    The *All Info, *Tracking Results and *Badge, Battery views are reset with the
    current devices.
    '''

    await build_existing_dashboards_selection_list(self)

    if is_empty(self.ic3db_Dashboards_by_dbname):
        return

    try:
        await _load_templates(self)

        for dbname, Dashboard in self.ic3db_Dashboards_by_dbname.items():
            self.dbname = dbname
            self.ui_selected_dbname  = dbname
            self.ui_main_view_style  = self.main_view_info_style_by_dbname[dbname]
            self.ui_main_view_dnames = self.main_view_info_dnames_by_dbname[dbname]

            updated_db_layout_str    = _build_updated_db_layout_all_views(self)
            updated_db_layout_json   = file_io.str_to_json_str(self, updated_db_layout_str)
            updated_db_layout_dict   = file_io.json_str_to_dict(updated_db_layout_json)
            updated_db_views         = updated_db_layout_dict[DATA][CONFIG][VIEWS]

            if file_io.is_valid_json_str(updated_db_layout_json) is False:
                log_debug_msg(f"Error Preparing Initial Dashboard, Invalid Json string > {updated_db_layout_json}")
                continue

            # Update all of the ic3db's with the current devices
            dashboard_dict = await _update_selected_views_from_master_dashboard(self, dbname, updated_db_views,
                                                                                add_del_device_flag=True)
            await _write_lovelace_dashboard_layout_file(self, dbname, dashboard_dict)
            await _update_lovelace_dashboard_layout_ha_data(self, dbname, dashboard_dict)
            log_debug_msg(f"Updated Dashboard with Added/Deleted Devices-{dbname}")

    except Exception as err:
        log_exception(err)
        return False

    return True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           BUILD DASHBOARD
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def update_or_create_dashboard(self):

    if is_empty(self.db_templates):
        await _load_templates(self)

    if self.ui_selected_dbname == ADD:
        dbname = self.dbname = get_next_dashboard_name(self)
    else:
        dbname = self.dbname = self.ui_selected_dbname

    try:
        updated_db_layout_str  = _build_updated_db_layout_all_views(self)
        updated_db_layout_json = file_io.str_to_json_str(self, updated_db_layout_str)
        updated_db_layout_json = _replace_json_text_items(self, updated_db_layout_json)

    except Exception as err:
        log_exception(err)
        return

    if file_io.is_valid_json_str(updated_db_layout_json) is False:
        self.errors['base'] = 'dashboard_json_error'
        log_debug_msg(f"Error Preparing Dashboard, Invalid Json string > {updated_db_layout_json}")
        return

    try:
        if self.ui_selected_dbname == ADD:
            updated_db_layout_str = updated_db_layout_str.replace('ic3db_template_master', dbname)
            await _add_dashboard_to_lovelace_dashboards(self, dbname)
            await _write_lovelace_dashboard_layout_file(self, dbname, updated_db_layout_json)
            await _update_lovelace_dashboard_layout_ha_data(self, dbname, updated_db_layout_json)
            self.ui_selected_dbname = dbname
            self.errors['base'] = 'dashboard_created'
            log_debug_msg(f"Created Dashboard-{self.dbname}, Devices-{self.ui_main_view_dnames}")

        else:
            current_db_layout_dict = file_io.json_str_to_dict(updated_db_layout_json)
            updated_db_layout_dict = await _prepare_selected_from_master_dashboard(self,
                                                        dbname, current_db_layout_dict)

            await _write_lovelace_dashboard_layout_file(self, dbname, updated_db_layout_dict)
            await _update_lovelace_dashboard_layout_ha_data(self, dbname, updated_db_layout_dict)

            self.errors['base'] = 'dashboard_updated'

    except Exception as err:
        log_exception(err)

    return

#............................................................................................
def get_next_dashboard_name(self):
    number_suffix = len(self.AllDashboards_by_dbname)
    if number_suffix == 0:
        return 'ic3db-icloud3'

    url_path = f"ic3db-icloud3-{number_suffix}"

    while url_path in self.AllDashboards_by_dbname:
        number_suffix += 1
        url_path = f"ic3db-icloud3-{number_suffix}"

        if number_suffix > 1000000:
            break

    return url_path

#-------------------------------------------------------------------------------------------
async def _prepare_selected_from_master_dashboard(self, dbname, updated_db_layout_dict):
    '''
    The already built updated_db_layout will become the created dashboard.
    If recreating an existing dashboard, the current main view will be added to the
    end and serve as a backup view in case the user just meant to update it
    '''
    try:
        updated_db_views = updated_db_layout_dict[DATA][CONFIG][VIEWS]

        all_db_views = _dashboard_layout_views(dbname)

        updated_db_main_view = [all_db_views[idx]
                                    for idx in range(0, len(all_db_views))
                                    if all_db_views[idx][PATH] == 'main']
        updated_db_main_backup_view = [idx
                                    for idx in range(0, len(updated_db_views))
                                    if updated_db_views[idx][PATH] == 'main-backup']
        updated_db_main_backup_idx = updated_db_main_backup_view[0] if isnot_empty(updated_db_main_backup_view) else -1

        # Backup the main view to main-backup view. Update it if it exists. Add it if it does not exist
        if isnot_empty(updated_db_main_view):
            updated_db_main_view = updated_db_main_view[0].copy()
            updated_db_main_view[TITLE] = 'Main (Backup)'
            updated_db_main_view[PATH]  = 'main-backup'
            if updated_db_main_backup_idx < 0:
                updated_db_views.append(updated_db_main_view)
            else:
                updated_db_views[updated_db_main_backup_idx] = updated_db_main_view

    except Exception as err:
        log_exception(err)

    current_db_layout_dict = await _update_selected_views_from_master_dashboard(self, dbname,
                                                                                updated_db_views,
                                                                                update_main_view=True)
    return current_db_layout_dict

#-------------------------------------------------------------------------------------------
async def _update_selected_views_from_master_dashboard(self, dbname,
                                                        updated_db_views,
                                                        update_main_view=False,
                                                        add_del_device_flag=False):
    '''
    The master dashboards has 6-views - Main, Other Devices, *All Info, *Track Results (Summary),
    *Badge, Battery, Event Log.

    - Recreating a dashboard (update_main_view=True) - Each view on the master dashboard layout is copied to the
        appropriate view on the selected dashboard and the Main view becomes the Main (Backup) view.
    - Updating a dashboard - The *All Info, *Track Results (Summary), *Badge, Battery are copied from
        the master dashboard. The other Main and Other Devices are not changed.
    '''

    current_db_layout_dict = await _read_dashboard_layout_file(dbname)

    if self.ui_selected_dbname == ADD:
        return updated_db_views

    current_db_views       = current_db_layout_dict[DATA][CONFIG][VIEWS]

    # If the dashboards are being updated because a device was added or deleted, recreate the main view
    # if the current main view was not customized. We know this if the length of the main_view_str from
    # the lovelace_db file is the same that is stored in the main_view_info fields on the event_log view

    if add_del_device_flag:
        update_main_view = (self.main_view_dbfile_length_by_dbname[dbname] == self.main_view_infomsg_length_by_dbname[dbname])

    # Get master views to copy to the selected dashboard
    updated_db_views_idx_by_path = {updated_db_views[idx][PATH]: idx
                                    for idx in range(0, len(updated_db_views))
                                    if (update_main_view
                                        or updated_db_views[idx][PATH].startswith(IC3DB))}

    # Copy the master view tabs to the selected view tabs
    for current_view_idx in range(0, len(current_db_views)):
        updated_view_path = current_db_views[current_view_idx][PATH]

        if updated_view_path in updated_db_views_idx_by_path:
            updated_view_idx = updated_db_views_idx_by_path[updated_view_path]
            current_db_views[current_view_idx] = updated_db_views[updated_view_idx]
            del updated_db_views_idx_by_path[updated_view_path]

    # Add any master views that were deleted from the selected dashboard. The user needs
    # to delete them again
    for updated_view_path, updated_view_idx in updated_db_views_idx_by_path.items():
        current_db_views.append(updated_db_views[updated_view_idx])

    return current_db_layout_dict

#-------------------------------------------------------------------------------------------
def _build_updated_db_layout_all_views(self):
    '''
    Cycle through the various templates and insert the devicename & fname into them.
    Then update the dashboard 'Device_#-templatename' templates with the new template.

    Return:
        - Updated Dashboard data
    '''

    dashboard_str = self.db_templates['master-dashboard']
    dashboard_str = _build_updated_db_layout_main_other_views(self, dashboard_str)

    for template_name, template in self.db_templates_used.items():
        template_fname = template_name.title()
        if (template_name.startswith('template') is False
                or instr(dashboard_str, template_fname) is False):
            continue

        template_base = self.db_templates['master-template-base']
        template_base = template_base.replace('^template_name', template_fname)

        log_debug_msg(f"Inserting Template > {template_fname}")

        if instr(template, 'multi-template'):
            template_str = _build_multi_template_str(self, template_name, template)
        else:
            devicenames  = list(self.conf_fnames_by_devicename().keys())
            template_str = _build_devices_str(self, template_name, devicenames)

        dashboard_str = dashboard_str.replace(template_base, template_str)
        dashboard_str = _replace_json_text_items(self, dashboard_str)

    return dashboard_str

#............................................................................................
def _build_updated_db_layout_main_other_views(self, dashboard_str):
    # Main dashboard is built based on the option type or devices selected

    template_fname = 'Template-Main-View'
    template_base  = self.db_templates['master-template-base']
    template_base  = template_base.replace('^template_name', template_fname)

    devicenames_main, devices_str = _build_devices_str_main_view(self)
    dashboard_str  = dashboard_str.replace(template_base, devices_str)
    dashboard_str = _insert_main_view_style_str(self, dashboard_str)

    template_fname = 'Template-Other-View'
    template_base = self.db_templates['master-template-base']
    template_base  = template_base.replace('^template_name', template_fname)

    devicenames_other, devices_str = _build_devices_str_other_view(self, devicenames_main)
    dashboard_str  = dashboard_str.replace(template_base, devices_str)

    return dashboard_str

#............................................................................................
def _build_multi_template_str(self, template_name, template):
    '''
    A multi-template is one with a placeholder in the master-dashboard.json file
    that is really made up of other templates that are handled as device pairs.
    Each of the actual templates in the multi-templated definition fill create a
    template_str with a structure of:
        Template 1/Device 1, Template 1/Device 2
        Template 2/Device 1, Template 2/Device 2
        Template 3/Device 1, Template 3/Device 2
        Template 1/Device 3, Template 1/Device 4
        Template 2/Device 3, Template 2/Device 4
        Template 3/Device 3, Template 3/Device 4
        etc.

    Ths is done to have all of the templates in a device group in two side-by-side
    columns. Otherwise, template 1 with all devices is together, tehplate 2 for all
    devices it together below it, etc.

    The template definition is:
        {
            "multi-template": [
            "template-device-group-trk-results",
            "template-device-group-trk-status",
            "template-device-group-devinfomsg"
            ]
        }
    '''
    template_items = template.split('[')[1][:-2].replace("'", "").replace(' ', '')
    template_names = template_items.split(',')

    # Make a list of each Device pair
    devicename_pairs = []
    devicenames = list(self.conf_fnames_by_devicename().keys())
    for pos in range(0, len(devicenames), 2):
        if pos+1 < len(devicenames):
            devicename_pair = [devicenames[pos], devicenames[pos+1]]
        else:
            devicename_pair = [devicenames[pos], '']
        devicename_pairs.append(devicename_pair)

    template_str = ''
    for devicename_pair in devicename_pairs:
        for sub_template_name in template_names:
            template_str += _build_devices_str(self, sub_template_name, devicename_pair)
            template_str += ','

    if template_str.endswith(','): template_str = template_str[:-1]

    return template_str

#............................................................................................
def _build_devices_str_main_view(self):
    '''
    Build the devices_str from the selected main view options (temp[late style & devices)

    Template styles are:
        'iphone-first-2': 'Display the first 2 iPhones',
        'all-devices': 'Display all iPhones',
        'result-summary': 'Display the Tracking Result Summary for all Devices'}
        devicename

    Return:
        - devicenames on the main view
        - devices string to be inserted into the main view on the Master Dashboard
    '''
    dbname = self.dbname
    active_devicenames = {conf_device[CONF_IC3_DEVICENAME]: (
                                            f"{conf_device[CONF_TRACKING_MODE]},"
                                            f"{conf_device[CONF_DEVICE_TYPE]}")
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_TRACKING_MODE] != INACTIVE}
    selected_devicenames = [devicename
                                    for devicename in self.ui_main_view_dnames
                                    if devicename in active_devicenames]

    # Extract dashboard style
    style_result_summary = (self.ui_main_view_style == RESULT_SUMMARY)
    style_track_details  = (self.ui_main_view_style == TRACK_DETAILS)
    if style_result_summary is False and style_track_details is False:
        style_result_summary = True
    elif style_result_summary and style_track_details:
        style_result_summary = False

    all_devices    = ALL_DEVICES    in self.ui_main_view_dnames
    devices_2_iphn = IPHONE_FIRST_2 in self.ui_main_view_dnames

    if isnot_empty(selected_devicenames):
        all_devices = False
        devices_2_iphn = False
        list_del(self.ui_main_view_dnames, ALL_DEVICES)
        list_del(self.ui_main_view_dnames, IPHONE_FIRST_2)
    if all_devices and devices_2_iphn:
        all_devices = False
        list_del(self.ui_main_view_dnames, ALL_DEVICES)
    if devices_2_iphn is False and is_empty(selected_devicenames):
        all_devices = True
    if all_devices is False and devices_2_iphn is False:
        self.ui_main_view_dnames = [devicename
                                    for devicename in self.ui_main_view_dnames
                                    if devicename in active_devicenames]


    if devices_2_iphn:
        selected_devicenames = [devicename
                                    for devicename, device_info in active_devicenames.items()
                                    if (instr(device_info, TRACK)
                                        and instr(device_info, IPHONE))]
        selected_devicenames = selected_devicenames[:2]

    self.main_view_extracted_dnames_by_dbname[dbname] = selected_devicenames

    # Build dashboard 'summary-all/sel' screen for all or selected devices
    if style_result_summary:
        trk_results_devicenames = [devicename
                                        for devicename, device_info in active_devicenames.items()
                                        if (instr(device_info, TRACK)
                                            and (all_devices or devicename in selected_devicenames))]

        template_name = 'template-trk-results-group'
        devices_str   = _build_devices_str(self, template_name, trk_results_devicenames)

        bat_devicenames = list(active_devicenames.keys())
        template_name = 'template-battery'
        devices_str  += ','
        bat_devices_str  = _build_devices_str(self, template_name, bat_devicenames)
        devices_str += bat_devices_str

    # Build dashboard  'Tracking results' screen for all or  first 2 iPhones
    elif style_track_details:
        trk_results_devicenames = [devicename   for devicename, device_info in active_devicenames.items()
                                        if (instr(device_info, TRACK)
                                            and (all_devices or devicename in selected_devicenames))]

        template_name = 'template-device-block'
        devices_str   = _build_devices_str(self, template_name, trk_results_devicenames)

    else:
        trk_results_devicenames = []
        devices_str = ''

    self.main_view_created_length_by_dbname[dbname] = len(devices_str.replace(' ', ''))

    return trk_results_devicenames, devices_str

#............................................................................................
def _extract_saved_main_view_layout_info(dashboard_str):
    '''
    The type, device selection and devices on the main screen are at the end of the dashboard
    and displayed as a heading

    Extract the style (type, devices and devicenames) from the dashboard layout. Search for the
    "Main-View-Template-Style: text, find the next quote mark and extract the text.

        "...'heading': 'Main-View-Template-Style:
                                result-summary, devices-all, gary_iphone;
                                length
                                ',
        'heading_style': 'subtitle' ..."
    '''
    main_view_style  = RESULT_SUMMARY
    main_view_dnames = [ALL_DEVICES]
    main_view_length = 0
    main_view_info_str = ''

    p = dashboard_str.find(MAIN_VIEW_STYLE_TEMPLATE)
    if p < 0:
        return main_view_style, main_view_dnames, main_view_length, main_view_info_str

    main_view_info_str = dashboard_str[p:]     # Get str starting with Main-View-Template-Style to end
    p = main_view_info_str.find(' ')           # Get pos at end of Main-View-Template-Style
    main_view_info_str = main_view_info_str[p+1:]  # Drop Main-View-Template-Style
    p = main_view_info_str.find("'")           # Get  end pos of main_view_info
    main_view_info_str = main_view_info_str[:p]    # Extract it

    if instr(main_view_info_str, ';'):
        main_view_info = f"{main_view_info_str};;".split(';')
        main_view_style      = main_view_info[0]
        main_view_dnames     = main_view_info[1].split(',')
        main_view_length     = main_view_info[2]


    if main_view_style not in DASHBOARD_MAIN_VIEW_STYLES: main_view_style  = RESULT_SUMMARY
    if is_empty(main_view_dnames): main_view_dnames = [ALL_DEVICES]
    main_view_length = int(main_view_length) if is_number(main_view_length) else 0

    return main_view_style, main_view_dnames, main_view_length, main_view_info_str

#............................................................................................
def _insert_main_view_style_str(self, dashboard_str):
    '''
    Save the main view style on the Event Log card to be used to update the dashboard
    after adding a device. Clear all possible styles before setting it to the current one
    The Main view Styles are iphone-first-2, iphone-all, result-summary
    '''
    new_mv_info_str = (
                f"{MAIN_VIEW_STYLE_TEMPLATE}"
                f"{self.ui_main_view_style};"
                f"{list_to_str(self.ui_main_view_dnames, ',')};"
                f"{self.main_view_created_length_by_dbname[self.dbname]}")

    main_view_layout_info = _extract_saved_main_view_layout_info(str(dashboard_str))
    main_view_style    = main_view_layout_info[0]
    main_view_dnames   = main_view_layout_info[1]
    main_view_length   = main_view_layout_info[2]
    main_view_info_str = main_view_layout_info[3]
    replace_main_view_info_str = f"{MAIN_VIEW_STYLE_TEMPLATE}{main_view_info_str}"

    dashboard_str = dashboard_str.replace(replace_main_view_info_str, new_mv_info_str)

    return dashboard_str

#............................................................................................
def _build_devices_str_other_view(self, devicenames_main):
    '''
        'iphone-first-2': 'Display the first 2 iPhones',
        'iphone-all': 'Display all iPhones',
        'result-summary': 'Display the Tracking Result Summary for all Devices'}
        devicename

    '''
    # if instr(self.main_view_style_str, RESULT_SUMMARY):
    if self.ui_main_view_style == RESULT_SUMMARY:
        devicenames = list(self.conf_fnames_by_devicename().keys())

    else:
        devicenames = [devicename
                        for devicename in self.conf_fnames_by_devicename().keys()
                        if devicename not in devicenames_main]

    template_name = 'template-device-block'
    devices_str   = _build_devices_str(self, template_name, devicenames)

    return devicenames, devices_str

#............................................................................................
def _build_devices_str(self, template_name, devicenames):
    '''
    Cycle through the template and insert the devicename and fname.

    If a Device is None and a Group template is being built, insert a blank template instead of
    the one being built. The template_name for the blank one will be built from the actual
    template name.
        'template-device-group-trk-results' --> 'filler-group-trk-results'
    '''

    template = self.db_templates[template_name]

    devices_str = ''
    for devicename in devicenames:
        if devicename == '':
            trailer_template_name = template_name.replace('template-device', 'filler')
            device_template = self.db_templates[trailer_template_name]

        else:
            device_template = template.replace('^devicename', devicename)
            fname           = self.conf_fnames_by_devicename()[devicename]
            fname           = fname.replace("'", "`").replace('"', '`')
            device_template = device_template.replace('^fname', fname)

        devices_str += f"{device_template},"

    if devices_str.endswith(','): devices_str = devices_str[:-1]

    return devices_str

#-------------------------------------------------------------------------------------------
async def _update_lovelace_dashboard_layout_ha_data(self, dbname, dashboard_dict):
    '''
    Update the Lovelace Dashboard data in the HA LovelaceData collection in the lovelace
    component.

    - Update the dashboard layout
    - Add the dashboard to the HA panel if creating a new dashboard
    '''

    # If dashboard_dict is actual a json_str, convert it to a dict
    try:
        if type(dashboard_dict) is str:
            dashboard_dict = file_io.json_str_to_dict(dashboard_dict)

        if dashboard_dict == {} or dashboard_dict is None:
            return

        Dashboard       = self.ic3db_Dashboards_by_dbname[dbname]
        dashboard_data  = dashboard_dict[DATA][CONFIG]
        Dashboard._data = {CONFIG: dashboard_data}

        await Dashboard.async_save(dashboard_data)

        Dashboard._config_updated()

        self.errors['base'] = 'dashboard_updated'

    except Exception as err:
        log_exception(err)
        return
    return

#............................................................................................
def _replace_json_text_items(self, dashboard_str):
    '''
    A heading item can be used to define a replaceable text field defined in the
    text-content.json file.
    '''
    json_text_dict = file_io.json_str_to_dict(self.db_templates.get('text-content', {}))
    if is_empty(json_text_dict):
        return

    for keyword, text in json_text_dict.items():
        dashboard_str = dashboard_str.replace(keyword, text)

    return dashboard_str

#-------------------------------------------------------------------------------------------
#       TEMPLATE FUNCTIONS
#-------------------------------------------------------------------------------------------
async def _load_templates(self):
    '''
    Load each template file (json file), remove all the spaces and build
    the dbs_template dictionary

    The template file is the dashboard json code that will replace the Device_#_templatename
    if the actual dashboard. the template itself is in the ["template"] entry.

    Builds:
        - self.db_templates[template_name] dictionary
    '''
    directory = f"{Gb.icloud3_directory}{CONFIGURE_DASHBOARD_TEMPLATES_DIR}"
    template_filenames = await _get_template_filenames(self, directory)

    for template_filename in template_filenames:
        filename      = f"{directory}/{template_filename}"
        template_json = await file_io.async_read_json_file(filename)

        template_name = template_filename.split('.')[0]

        if template_name == 'master-dashboard':
            self.master_dashboard = template_json

        # If the file name ends with json, store it in its json format instead of
        # converting it to a compressed string. It will be converted directory into
        # a dictionary when it is needed
        if template_name.startswith('json'):
            self.db_templates[template_name] = template_json
            continue

        template_str = str(template_json)
        template_str = template_str.replace('  ', '')

        # Drop [ & ]  at front and back of template string
        if template_str.startswith("["):
            template_str = template_str[1:-1]

        self.db_templates[template_name] = template_str

    master_dashboard = self.db_templates['master-dashboard']
    self.db_templates_used = {template_name: template
                                    for template_name, template in self.db_templates.items()
                                    if (template_name.startswith('template')
                                        and instr(master_dashboard, template_name.title()))}

#-------------------------------------------------------------------------------------------
async def _get_template_filenames(self, directory):
    '''
    Get all of the filenamess in the .../dashboard_builder directory starting with 'templates'
    or 'master'
    '''

    files = await file_io.async_get_directory_files(directory)
    return [file for file in files]


#-------------------------------------------------------------------------------------------
#       DASHBOARD FORM SELECTION LIST FUNCTIONS
#-------------------------------------------------------------------------------------------
async def build_existing_dashboards_selection_list(self):
    '''
    Load all of the ic3db dashboard layout files (view item) into the HA.Dashboard._data object
    in case that object was not previously loaded. This only is done once. Then cycle thru those Lovelace dashboard views and build a list existing dashboards.

    dashboards = {
        'home-master': <custom_components.lovelace-trace-code.dashboard.LovelaceStorage object at 0x7f8ae87b10>,
        'icloud3-yaml': <custom_components.lovelace-trace-code.dashboard.LovelaceStorage object at 0x7f8b0556e0>,
        'ic3db-icloud3-2': <custom_components.lovelace-trace-code.dashboard.LovelaceStorage object at 0x7f8b057ce0>},
        'ic3db-icloud3-4': <custom_components.lovelace-trace-code.dashboard.LovelaceStorage object at 0x7f8b057ce0>
        }

    ic3db_db_configs=[
        {'id': 'ic3db_icloud3_2', 'icon': 'mdi:cloud-alert-outline', TITLE: 'iCloud3-2', 'url_path': 'ic3db-icloud3-2', 'show_in_sidebar': True, 'require_admin': False, 'mode': 'storage'},
        {'id': 'ic3db_icloud3_4', 'icon': 'mdi:cloud-alert-outline', TITLE: 'iCloud3-4', 'url_path': 'ic3db-icloud3-4', 'show_in_sidebar': True, 'require_admin': False, 'mode': 'storage'}
        ]
    '''

    load_ic3db_dashboards_from_ha_data(self)

    self.dbf_dashboard_key_text  = {}
    if is_empty(self.ic3db_Dashboards_by_dbname):
        self.dbf_dashboard_key_text[ADD] = (f"➤ CREATE A NEW ICLOUD3 DASHBOARD")
        return


    ll_dashboards_file_configs = await _read_lovelace_dashboards_file()
    ll_dashboards_file_configs_str = str(ll_dashboards_file_configs)

    await _load_dashboard_layout_files(self)

    for _dbname, _Dashboard in self.ic3db_Dashboards_by_dbname.items():
        if instr(ll_dashboards_file_configs_str, _dbname) is False:
            continue

        self.AllDashboards_by_dbname[_dbname] = _Dashboard

        await _get_main_view_devicenames(self, _dbname, _Dashboard)

        main_view_devices  = self.main_view_extracted_fnames_by_dbname[_dbname]
        main_view_devices  = _strip_device_type(main_view_devices)

        if is_empty(main_view_devices):
            main_view_devices_msg = 'None'
        else:
            main_view_devices_msg = list_to_str(main_view_devices)

        main_view_style = self.main_view_info_style_by_dbname[_dbname]
        main_view_style_msg = DASHBOARD_MAIN_VIEW_STYLES[main_view_style]

        dashboard_msg =(f"{_Dashboard.config[TITLE]} > "
                        f"{main_view_style_msg} "
                        f"({main_view_devices_msg})")


        self.dbf_dashboard_key_text[_dbname] = dashboard_msg

    self.dbf_dashboard_key_text[ADD] = (f"➤ CREATE A NEW ICLOUD3 DASHBOARD")

#-------------------------------------------------------------------------------------------
def select_available_dashboard(self):
    '''
    Get the first item in the dashboard list(dashboard #1 or 'add')
    '''
    if is_empty(self.dbf_dashboard_key_text):
        self.ui_selected_dbname = ADD
    elif self.dbname == '':
        self.ui_selected_dbname = list(self.dbf_dashboard_key_text.keys())[0]

    return

#-------------------------------------------------------------------------------------------
#       DEVICES USED IN DASHBOARDS FUNCTIONS
#-------------------------------------------------------------------------------------------
async def _get_main_view_devicenames(self, dbname, _Dashboard):
    '''
    Cycle through the tracked devices and see if it is used in the Dashboard's Main view.
    If it is, list those devices on the dashboard selection list.

    Sets the following dictionary for the dashboard being reviewed:
    - self.main_view_extracted_fnames_by_dbname - Devices used msg

    '''

    # dashboard_data_dict = await _read_dashboard_layout_file(dbname)
    dashboard_view_dict = _dashboard_layout_views(dbname)

    main_view  = dashboard_view_dict[0]

    try:
        main_view_str     = str(main_view)
        devices_cards_str = str(main_view['sections'][0]['cards'])

    except Exception as err:
        log_exception(err)
        main_view_str     = ''
        devices_cards_str = ''

    _build_main_view_dicts(self, dbname, devices_cards_str)

    # Extract template style and main view length that was saved on the evlog_view tab when db was created
    main_view_layout_info = _extract_saved_main_view_layout_info(str(dashboard_view_dict))
    self.main_view_info_style_by_dbname[dbname]  = main_view_layout_info[0]
    self.main_view_info_dnames_by_dbname[dbname] = main_view_layout_info[1]
    self.main_view_infomsg_length_by_dbname[dbname] = main_view_layout_info[2]
    main_view_info_str = main_view_layout_info[3]

    return

#............................................................................................
def _build_main_view_dicts(self, dbname, devices_cards_str):
    # Build device info msg for any devices found in the Dashboard
    main_view_device_fnames  = []
    main_view_devicenames    = []

    # for devicename, fname in self.conf_fnames_by_devicename().items():
    for devicename, fname in lists.devices_selection_list().items():
        if instr(devices_cards_str, f"device_tracker.{devicename}"):
            list_add(main_view_devicenames, devicename)
            list_add(main_view_device_fnames, fname)

    self.main_view_extracted_fnames_by_dbname[dbname] = main_view_device_fnames
    self.main_view_extracted_dnames_by_dbname[dbname] = main_view_devicenames
    self.main_view_dbfile_length_by_dbname[dbname] = len(devices_cards_str.replace(' ', '')) - 2

#............................................................................................
def _strip_device_type(view_devices_msg):
    '''
    Cycle through the device names selection list and remove the device type text for each item.
    From: ['Gary (iPhone)', 'Lillian (iPhone)', 'Gary-iPad (iPad)']
    To:   ['Gary', 'Lillian', 'Gary-iPad']
    '''
    view_devices_fname = []
    for view_device_msg in view_devices_msg:
        for device_type in DEVICE_TYPES:
            device_type_text = f" ({device_type})"
            found = instr(view_device_msg, device_type_text)
            if found:
                view_device_fname = view_device_msg.replace(device_type_text, "")
                list_add(view_devices_fname, view_device_fname)
                break

    return view_devices_fname


#-------------------------------------------------------------------------------------------
#       .STORAGE/LOVELACE.DBNAME LAYOUT FILE FUNCTIONS
#-------------------------------------------------------------------------------------------
def _dashboard_layout_views(dbname):

    # _Dashboard = Gb.hass.data[LOVELACE_DATA][dbname]

    try:
        return Gb.hass.data[LOVELACE_DATA].dashboards[dbname]._data[CONFIG][VIEWS]
    except:
        return {}

#-------------------------------------------------------------------------------------------
async def _load_dashboard_layout_files(self):
    '''
    Initialize the hass.lovelace.Dashboard._data item (view element)
    with the ic3db dashboard files layout view
    '''

    for _dbname, _Dashboard in self.ic3db_Dashboards_by_dbname.items():
        if _Dashboard._data is None:
            dashboard_layout_dict = await _read_dashboard_layout_file(_dbname)
            _Dashboard._data = {}
            _Dashboard._data[CONFIG] = dashboard_layout_dict[DATA][CONFIG]
            await _Dashboard.async_load(force=True)

    return

#-------------------------------------------------------------------------------------------
async def _read_dashboard_layout_file(dbname):
    '''
    Get the actual dashboard layout data from the lovelace.dashboardname file

    We have to look in the actual file since HA does not include that in the config
    items it loads into memory.  However, HA does keep  the "source" when the the
    dashboard is changed.
    '''
    try:
        dashboard_file = f"{Gb.ha_storage_directory}/lovelace.{dbname.replace('-', '_')}"
        dashboard_layout_dict = await file_io.async_read_json_file(dashboard_file)

        return dashboard_layout_dict

    except Exception as err:
        log_exception(err)

    return {}

#-------------------------------------------------------------------------------------------
async def _write_lovelace_dashboard_layout_file(self, dbname, dashboard_dict_or_json_str):
    '''
    Write the dashboard data to the .storage directory. The record to be written can
    be a json_str or a dictionary item, which will be converted to a json_str.

    When adding a new Dashboard, dashboard_json will start with '{"view":'
    When updating a Dashboard, dashboard_json will start with '{"config":'
    '''
    if type(dashboard_dict_or_json_str) is dict:
        dashboard_dict_or_json_str = file_io.dict_to_json_str(dashboard_dict_or_json_str)
        if dashboard_dict_or_json_str == '':
            self.errors['base'] = 'dashboard_error'
            return

    filename = f"{Gb.ha_storage_directory}/lovelace.{dbname.replace('-', '_')}"
    await file_io.async_write_file(filename, dashboard_dict_or_json_str)

    log_debug_msg(f"Updating {filename}")


#-------------------------------------------------------------------------------------------
def load_ic3db_dashboards_from_ha_data(self):
    '''
    Cycle through the Gb.hass.data[LOVELACE_DATA].dashboards extract the ic3db dashboards

    Returns:
        dictionary of {_dbname: _Dashboard object}
    '''

    self.ic3db_Dashboards_by_dbname = {_dbname: _Dashboard
                    for _dbname, _Dashboard in Gb.hass.data[LOVELACE_DATA].dashboards.items()
                    if (_dbname is not None
                        and _dbname.startswith(IC3DB)
                        and _Dashboard is not None
                        and _Dashboard.config['url_path'].startswith(IC3DB))}

#-------------------------------------------------------------------------------------------
#       .STORAGE/LOVELACE_DASHBOARDS CONFIG FILE FUNCTIONS
#-------------------------------------------------------------------------------------------

async def _add_dashboard_to_lovelace_dashboards(self, dbname):
    '''
    Add the dashboard to the Lovelace dashboard collection,
    Register it as a new panel with the front_end,
    Create a new dashboard object and add it to the internal Lovelace tables
    Send the dashboard config to the front_end
    '''
    if dbname in self.ic3db_Dashboards_by_dbname:
        return

    url_path = dbname
    title    = dbname.replace(IC3DB, '').replace('icloud3', 'iCloud3')
    icon     = _icon(dbname)

    dashboard_config = {
        "id": dbname.replace('-', '_'),
        "show_in_sidebar": True,
        "icon": icon,
        "title": title,
        "require_admin": False,
        "mode": "storage",
        "url_path": url_path
        }

    db_collections_item = {
        'allow_single_word': True,
        'icon': icon,
        TITLE: title,
        'url_path': dbname,
        }

    # Add the new dashboard to the dashboard_collection
    dashboards_collection = dashboard.DashboardsCollection(Gb.hass)
    await dashboards_collection.async_load()

    # Add the new dashboard config to the '.storage/lovelace_dashboards' file. We also have to save the
    #   new config since the _create_item does a scheduled save and the dashboard selection screen
    #   is rebuilt before the lovelace_dashboards file save has actually been done.
    # Register the dashboard in the HA Sidebar as a new panel
    # Create a new dashboard object (LovelaceStorage)
    # Add the new dashboard object to the internal lovelace dashboard dictionary

    await dashboards_collection.async_create_item(db_collections_item)

    # Force lovelace_dashboards save since async_create_item does a delayed save. It will be updated
    # again in async_create_item
    await _add_dashboard_to_lovelace_dashboards_file(dbname, dashboard_config)

    _register_panel(Gb.hass, url_path, "storage", dashboard_config, True)
    Dashboard = dashboard.LovelaceStorage(Gb.hass, dashboard_config)
    Gb.hass.data[LOVELACE_DATA].dashboards[dbname] = Dashboard

    self.Dashboard = Dashboard
    self.ic3db_Dashboards_by_dbname[dbname]    = Dashboard
    self.AllDashboards_by_dbname[dbname] = Dashboard

    await dashboards_collection.async_load()

    # Send new dashboard_collection item to the frontend
    dashboard_collection_ws = dashboard.DashboardsCollectionWebSocket(
                                        dashboards_collection,
                                        "lovelace/dashboards",
                                        "dashboard",
                                        STORAGE_DASHBOARD_CREATE_FIELDS,
                                        STORAGE_DASHBOARD_UPDATE_FIELDS,
                                        )
    dashboard_collection_ws.async_setup(Gb.hass)

    log_debug_msg(f"Added Dashboard to Lovelace > {title}/{dbname}")

#............................................................................................
def _icon(dbname):
    if dbname == 'ic3db-icloud3':
        return "mdi:cloud-outline"

    number_suffix = dbname.split('-')[-1]
    number_suffix = int(number_suffix) if is_number(number_suffix) else 0
    number_suffix = number_suffix % 7

    return DASHBOARD_ICONS[number_suffix]

#-------------------------------------------------------------------------------------------
async def _read_lovelace_dashboards_file():
    '''
    Get the .storage/lovelace_dashboards data with the current dashboards. This is used to display
    the existing dashbords instead of using the hass.data['lovelace'].dashboards dictionary
    because the hass.data can contain deleted dashboards and is not reset until the next restart.

    Returned:
        {
            "id": "ic3db_icloud3_4",
            "icon": "mdi:cloud-alert-outline",
            "title": "iCloud3-4",
            "url_path": "ic3db-icloud3-4",
            "show_in_sidebar": true,
            "require_admin": false,
            "mode": "storage"
        }
    '''
    try:
        dashboards_file = f"{Gb.ha_storage_directory}/lovelace_dashboards"
        dashboards_config = await file_io.async_read_json_file(dashboards_file)

        if is_empty(dashboards_config):
            return []

        ic3db_db_configs = [config for config in dashboards_config[DATA][ITEMS]
                                if config['url_path'].startswith(IC3DB)]

        return ic3db_db_configs

    except Exception as err:
        log_exception(err)

    return []


#............................................................................................
async def _add_dashboard_to_lovelace_dashboards_file(dbname, dashboard_config):
    '''
    Add the dashboard_config to the /core/.storage/lovelace_dashboards file
    '''
    try:
        lovelace_dashboards_file = f"{Gb.ha_storage_directory}/lovelace_dashboards"
        lovelace_dashboards = await file_io.async_read_json_file(lovelace_dashboards_file)

        log_debug_msg(f"Updating {lovelace_dashboards_file}, URL-{dashboard_config['url_path']}")
        for item in lovelace_dashboards[DATA][ITEMS]:
            if item['url_path'] == dbname:
                return False

        lovelace_dashboards[DATA][ITEMS].append(dashboard_config)

        await file_io.async_save_json_file(lovelace_dashboards_file, lovelace_dashboards)

    except Exception as err:
        log_exception(err)

    return True
