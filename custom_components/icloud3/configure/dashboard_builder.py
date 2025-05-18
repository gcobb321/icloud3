
# from ...lovelace import dashboard
from homeassistant.components.lovelace import dashboard
from homeassistant.components.lovelace import _register_panel
from homeassistant.components.lovelace.const import (LOVELACE_DATA,
                                                    STORAGE_DASHBOARD_CREATE_FIELDS,
                                                    STORAGE_DASHBOARD_UPDATE_FIELDS)

from ..global_variables  import GlobalVariables as Gb
from ..const             import (IPHONE_FNAME, DEVICE_TYPES,
                                CONF_IC3_DEVICENAME, CONF_TRACKING_MODE, TRACK_DEVICE)

from ..utils.utils     import (instr, isnumber, is_empty, isnot_empty, list_to_str, str_to_list,
                                list_add, dict_value_to_list, six_item_list, six_item_dict, )
from ..utils.messaging import (log_exception, log_debug_msg, log_info_msg, _log,  _evlog, )
from ..utils              import file_io

from .form_lists_def     import *
from .                   import utils
from .                   import selection_lists as lists

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
async def install_initial_icloud3_dashboard(self):
    '''
    This is run when iCloud3 is being installed
    '''
    await build_existing_dashboards_selection_list(self)
    if self.selected_dbname != 'add':
        return False

    dbname = self.dbname = 'ic3db-icloud3'
    await _load_templates(self)
    master_dashboard_str  = _build_master_dashboard(self)
    master_dashboard_str  = master_dashboard_str.replace('ic3db_template_master', dbname)
    master_dashboard_json = file_io.str_to_json_str(self, master_dashboard_str)
    master_dashboard_json = _replace_json_text_items(self, master_dashboard_json)

    if file_io.is_valid_json_str(master_dashboard_json) is False:
        log_debug_msg(f"Error Preparing Initial Dashboard, Invalid Json string > {master_dashboard_json}")
        return False

    await _add_dashboard_to_lovelace_dashboards(self, dbname)
    await _write_lovelace_dashboard_layout_file(self, dbname, master_dashboard_json)
    await _update_lovelace_dashboard_layout_ha_data(self, dbname, master_dashboard_json)
    log_debug_msg(f"Created Dashboard-{dbname}, Devices-{self.main_view_devices}")
    return True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           UPDATE IC3DB- VIEWS ON ALL DASHBOARDS WHEN DEVICES ARE ADDED OR DELETED
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def update_dashboard_ic3db_views_new_deleted_devices(self):
    '''
    This is run when devices are added or deleted on the add_device or update_device
    screens after all device_tracker entities have been processed.

    The *All Info, *Tracking Results and *Badge, Battery views are reset with the
    current devices.
    '''

    _load_ic3db_Dashboards_by_dbname(self)
    if is_empty(self.ic3db_Dashboards_by_dbname):
        return

    await _load_templates(self)
    master_dashboard_str    = _build_master_dashboard(self)
    master_dashboard_json   = file_io.str_to_json_str(self, master_dashboard_str)
    master_dashboard_layout = file_io.json_str_to_dict(master_dashboard_json)
    master_views            = master_dashboard_layout['data']['config']['views']

    if file_io.is_valid_json_str(master_dashboard_json) is False:
        log_debug_msg(f"Error Preparing Initial Dashboard, Invalid Json string > {master_dashboard_json}")
        return False

    for dbname, Dashboard in self.ic3db_Dashboards_by_dbname.items():
        selected_dashboard_dict = await _update_selected_views_from_master_dashboard(dbname, master_views)
        await _write_lovelace_dashboard_layout_file(self, dbname, selected_dashboard_dict)
        await _update_lovelace_dashboard_layout_ha_data(self, dbname, selected_dashboard_dict)
        log_debug_msg(f"Updated Dashboard-{dbname}")

    return True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           BUILD DASHBOARD
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def update_or_create_dashboard(self, user_input):

    if is_empty(self.db_templates):
        await _load_templates(self)

    master_dashboard_str  = _build_master_dashboard(self)
    master_dashboard_json = file_io.str_to_json_str(self, master_dashboard_str)
    master_dashboard_json = _replace_json_text_items(self, master_dashboard_json)

    if file_io.is_valid_json_str(master_dashboard_json) is False:
        self.errors['base'] = 'dashboard_json_error'
        log_debug_msg(f"Error Preparing Dashboard, Invalid Json string > {master_dashboard_json}")
        return

    action_item = user_input['action_item']

    if self.selected_dbname == 'add':
        dbname = self.dbname = get_next_dashboard_name(self)
        master_dashboard_str = master_dashboard_str.replace('ic3db_template_master', dbname)
        await _add_dashboard_to_lovelace_dashboards(self, dbname)
        await _write_lovelace_dashboard_layout_file(self, dbname, master_dashboard_json)
        await _update_lovelace_dashboard_layout_ha_data(self, dbname, master_dashboard_json)
        self.errors['base'] = 'dashboard_created'
        log_debug_msg(f"Created Dashboard-{dbname}, Devices-{self.main_view_devices}")
        return

    dbname = self.dbname = self.selected_dbname

    master_dashboard_layout = file_io.json_str_to_dict(master_dashboard_json)


    selected_dashboard_dict = await _prepare_selected_from_master_dashboard(
                                                dbname, action_item, master_dashboard_layout)

    await _write_lovelace_dashboard_layout_file(self, dbname, selected_dashboard_dict)
    await _update_lovelace_dashboard_layout_ha_data(self, dbname, selected_dashboard_dict)

    self.errors['base'] = 'dashboard_updated'
    return

#............................................................................................
def get_next_dashboard_name(self):
    number_suffix = len(self.AllDashboards_by_dashboard)
    url_path = f"ic3db-icloud3-{number_suffix}"

    while url_path in self.AllDashboards_by_dashboard:
        number_suffix += 1
        url_path = f"ic3db-icloud3-{number_suffix}"

        if number_suffix > 1000000:
            break

    return url_path

#-------------------------------------------------------------------------------------------
async def _prepare_selected_from_master_dashboard(dbname, action_item, master_dashboard_layout):
    '''
    The already built master_dashboard will become the created dashboard
    If recreating an existing dashboard, the current main view will be added to the
    end and serve as a backup view in case the user just meant to update it
    '''
    master_views = master_dashboard_layout['data']['config']['views']

    if action_item == 'update_dashboard':
        return await _update_selected_views_from_master_dashboard(dbname, master_views)

    selected_views = _dashboard_layout_views(dbname)

    selected_main_view = [selected_views[idx]
                                for idx in range(0, len(selected_views))
                                if selected_views[idx]['path'] == 'main']
    master_main_backup_view = [idx
                                for idx in range(0, len(master_views))
                                if master_views[idx]['path'] == 'main-backup']
    master_main_backup_idx = master_main_backup_view[0] if isnot_empty(master_main_backup_view) else -1

    # Backup the main view to main-backup view. Update it if it exists. Add it if it does not exist
    if isnot_empty(selected_main_view):
        selected_main_view = selected_main_view[0].copy()
        selected_main_view['title'] = 'Main (Backup)'
        selected_main_view['path']  = 'main-backup'
        if master_main_backup_idx < 0:
            master_views.append(selected_main_view)
        else:
            master_views[master_main_backup_idx] = selected_main_view

    return await _update_selected_views_from_master_dashboard(dbname, master_views, recreating_db=True)

#-------------------------------------------------------------------------------------------
async def _update_selected_views_from_master_dashboard(dbname, master_views, recreating_db=False):
    '''
    The master dashboards has 6-views - Main, Other Devices, *All Info, *Track Results (Summary),
    *Badge, Battery, Event Log.

    - Rrecreating a dashboard (recreating_db=True) - Each view on the master is copied to the
        appropriate view on the selected dashboard and the Main view becomes the Main (Backup) view.
    - Updating a dashboard - The *All Info, *Track Results (Summary), *Badge, Battery are copied from
        the master dashboard. The other Main and Other Devices are not changed.
    '''

    selected_dashboard_dict  = await _read_dashboard_layout_file(dbname)
    selected_views           = selected_dashboard_dict['data']['config']['views']

    # Get master views to copy to the selected dashboard
    copy_master_views_idx_by_path = {master_views[idx]['path']: idx
                                    for idx in range(0, len(master_views))
                                    if (recreating_db
                                        or master_views[idx]['path'].startswith('ic3db-'))}

    # Copy the master view tabs to the selected view tabs
    for selected_idx in range(0, len(selected_views)):
        selected_view_path = selected_views[selected_idx]['path']
        if selected_view_path in copy_master_views_idx_by_path:
            master_idx = copy_master_views_idx_by_path[selected_view_path]
            selected_views[selected_idx] = master_views[master_idx]
            del copy_master_views_idx_by_path[selected_view_path]

    # Add any master views that were deleted from the selected dashboard. The user needs
    # to delete them again
    for master_path in copy_master_views_idx_by_path:
        selected_views.append(master_views[copy_master_views_idx_by_path[master_path]])

    return selected_dashboard_dict

#-------------------------------------------------------------------------------------------
def _build_master_dashboard(self):
    '''
    Cycle through the various templates and insert the devicename & fname into them.
    Then update the dashboard 'Device_#-templatename' templates with the new template.

    Return:
        - Updated Dashboard data
    '''

    dashboard_str = self.db_templates['master-dashboard']
    dashboard_str = _build_main_other_view(self, dashboard_str)

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
def _build_main_other_view(self, dashboard_str):
    # Main dashboard is built based on the option type or devices selected

    template_fname = 'Template-Main-View'
    template_base  = self.db_templates['master-template-base']
    template_base  = template_base.replace('^template_name', template_fname)

    devicenames_main, devices_str = _build_devices_str_main_view(self)
    dashboard_str  = dashboard_str.replace(template_base, devices_str)

    dashboard_str = _set_main_view_template_style(self, dashboard_str)

    template_fname = 'Template-Other-View'
    template_base = self.db_templates['master-template-base']
    template_base  = template_base.replace('^template_name', template_fname)

    devicenames_other, devices_str = _build_devices_str_other_view(self, devicenames_main)
    found = instr(dashboard_str, template_base)
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
        'iphone-all': 'Display all iPhones',
        'result-summary': 'Display the Tracking Result Summary for all Devices'}
        devicename

    Return:
        - devicenames on the main view
        - devices string to be inserted into the main view on the Master Dashboard
    '''
    _main_view_template_style = ['']
    _main_view_template_style.extend([selected_template_style
                                for selected_template_style in self.main_view_devices
                                if selected_template_style in DASHBOARD_MAIN_VIEW_STYLE_BASE])

    self.main_view_template_style = _main_view_template_style[-1]
    idx = self.main_view_devices.index(self.main_view_template_style)
    self.main_view_devices = self.main_view_devices[idx:]

    if self.main_view_template_style in ['iphone-first-2', 'iphone-all']:
        devicenames = [devicename   for devicename, fname in lists.devices_selection_list().items()
                                    if instr(fname, f"({IPHONE_FNAME})")]

        if self.main_view_template_style == 'iphone-first-2':
            if len(devicenames) > 2:
                devicenames = devicenames[0:1]

        template_name = 'template-device-block'
        devices_str   = _build_devices_str(self, template_name, devicenames)

    elif self.main_view_template_style == 'result-summary':
        devicenames = [conf_device[CONF_IC3_DEVICENAME]
                                    for conf_device in Gb.conf_devices
                                    if (conf_device[CONF_TRACKING_MODE] == TRACK_DEVICE)]
        template_name = 'template-trk-results-group'
        devices_str   = _build_devices_str(self, template_name, devicenames)

        devicenames   = list(self.conf_fnames_by_devicename().keys())
        template_name = 'template-battery'
        devices_str  += ','
        devices_str  += _build_devices_str(self, template_name, devicenames)

    else:
        devicenames = [devicename
                        for devicename in self.main_view_devices
                        if devicename in self.conf_fnames_by_devicename()]

        template_name = 'template-device-block'
        devices_str   = _build_devices_str(self, template_name, devicenames)


    return devicenames, devices_str

#............................................................................................
def _get_main_view_template_style(dashboard_str):
    '''
    Save the main view style on the Event Log card to be used to update the dashboard
    after adding a device. Clear all possible styles before setting it to the current one
    The Main view Styles are iphone-first-2, iphone-all, result-summary
    '''
    for style_base_key in DASHBOARD_MAIN_VIEW_STYLE_BASE.keys():
        style_str = f"{MAIN_VIEW_STYLE_TEMPLATE}{style_base_key}"
        if instr(dashboard_str, style_str):
            style_str = style_str.replace(MAIN_VIEW_STYLE_TEMPLATE, '')
            return style_str

    return ''

#............................................................................................
def _set_main_view_template_style(self, dashboard_str):
    '''
    Save the main view style on the Event Log card to be used to update the dashboard
    after adding a device. Clear all possible styles before setting it to the current one
    The Main view Styles are iphone-first-2, iphone-all, result-summary
    '''
    style_str = _get_main_view_template_style(dashboard_str)
    if style_str != '':
        style_str = f"{MAIN_VIEW_STYLE_TEMPLATE}{style_str}"
        dashboard_str = dashboard_str.replace(style_str, MAIN_VIEW_STYLE_TEMPLATE)

    style_str = f"{MAIN_VIEW_STYLE_TEMPLATE}{self.main_view_template_style}"
    dashboard_str = dashboard_str.replace(MAIN_VIEW_STYLE_TEMPLATE, style_str)

    return dashboard_str

#............................................................................................
def _build_devices_str_other_view(self, devicenames_main):
    '''
        'iphone-first-2': 'Display the first 2 iPhones',
        'iphone-all': 'Display all iPhones',
        'result-summary': 'Display the Tracking Result Summary for all Devices'}
        devicename

    '''
    if self.main_view_template_style == 'result-summary':
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
    if type(dashboard_dict) is str:
        dashboard_dict = file_io.json_str_to_dict(dashboard_dict)

    Dashboard       = self.ic3db_Dashboards_by_dbname[dbname]
    dashboard_data  = dashboard_dict['data']['config']
    Dashboard._data = {'config': dashboard_data}

    await Dashboard.async_save(dashboard_data)

    Dashboard._config_updated()

    self.errors['base'] = 'dashboard_updated'

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
        template_json = await file_io.read_json_file(filename)
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
        {'id': 'ic3db_icloud3_2', 'icon': 'mdi:cloud-alert-outline', 'title': 'iCloud3-2', 'url_path': 'ic3db-icloud3-2', 'show_in_sidebar': True, 'require_admin': False, 'mode': 'storage'},
        {'id': 'ic3db_icloud3_4', 'icon': 'mdi:cloud-alert-outline', 'title': 'iCloud3-4', 'url_path': 'ic3db-icloud3-4', 'show_in_sidebar': True, 'require_admin': False, 'mode': 'storage'}
        ]
    '''

    self.dbf_dashboard_key_text  = {}

    ll_dashboards_file_configs = await _read_lovelace_dashboards_file()
    ll_dashboards_file_configs_str = str(ll_dashboards_file_configs)

    _load_ic3db_Dashboards_by_dbname(self)

    await _load_dashboard_layout_files(self)

    for _dbname, _Dashboard in self.ic3db_Dashboards_by_dbname.items():
        self.AllDashboards_by_dashboard[_dbname] = _Dashboard
        # self.ic3db_Dashboards_by_dbname[_dbname]    = _Dashboard

        await _get_main_other_views_devicenames(self, _dbname, _Dashboard)


        main_view_devices  = self.main_view_device_fnames_by_dashboard[_dbname]
        other_view_devices = self.other_view_device_fnames_by_dashboard[_dbname]
        main_view_devices  = _strip_device_type(main_view_devices)
        other_view_devices = _strip_device_type(other_view_devices)

        if is_empty(main_view_devices):
            main_view_devices_msg = 'None'
        else:
            main_view_devices_msg = list_to_str(main_view_devices)
        if is_empty(other_view_devices):
            other_view_devices_msg = 'None'
        else:
            other_view_devices_msg = list_to_str(other_view_devices)

        # If _dbname is in hass.data['lovelace'].dashboards and it is not in the
        # .storage/lovelace_dashboards, it was either deleted or the lovelace_dashboards
        # file has not been updated yet (hass.data['lovelace'].dashboards is not updated
        # until the next HA restart). If _dbname in in dbnames_just_added, it probably
        # is because the file was not updated. If it is not in _the file, it was probably
        # deleted. But maybe not if the icloud3 configure was exited and then reentered
        # and dbnames_just_added is empty.
        if (instr(ll_dashboards_file_configs_str, _dbname)
                or _dbname in self.dbnames_just_added):
            maybe_deleted_msg = ''
        else:
            maybe_deleted_msg = 'MAYBE DELETED(?), '

        dashboard_msg =(f"{_Dashboard.config['title']} > "
                        f"{maybe_deleted_msg}"
                        f"MainView-({main_view_devices_msg})")
        if self.main_view_template_style_by_dashboard[_dbname] == 'result-summary':
            dashboard_msg += ', Results Summary displayed'

        self.dbf_dashboard_key_text[_dbname] = dashboard_msg

    self.dbf_dashboard_key_text['add'] = (
                f"➤ CREATE A NEW ICLOUD3 DASHBOARD")

#-------------------------------------------------------------------------------------------
def select_available_dashboard(self):
    '''
    Get the first item in the dashboard list(dashboard #1 or 'add')
    '''
    if self.dbname == '':
        self.selected_dbname = list(self.dbf_dashboard_key_text.keys())[0]

    return

#-------------------------------------------------------------------------------------------
#       DEVICES USED IN DASHBOARDS FUNCTIONS
#-------------------------------------------------------------------------------------------
async def _get_main_other_views_devicenames(self, dbname, _Dashboard):
    '''
    Cycle through the tracked devices and see if it is used in the Dashboard's Main view.
    If it is, list those devices on the dashboard selection list.

    Sets the following dictionary for the dashboard being reviewed:
    - self.main_view_device_fnames_by_dashboard - Devices used msg

    '''

    # dashboard_data_dict = await _read_dashboard_layout_file(dbname)
    dashboard_view_dict = _dashboard_layout_views(dbname)

    main_view  = dashboard_view_dict[0]
    other_view = dashboard_view_dict[1]
    # main_view  = dashboard_data_dict['data']['config']['views'][0]
    # other_view = dashboard_data_dict['data']['config']['views'][1]

    try:
        main_view_str = str(main_view)
        other_view_str = str(other_view)
    except:
        main_view_str = ''
        view_otner_str = ''

    self.main_view_template_style_by_dashboard[dbname] = \
        _get_main_view_template_style(str(dashboard_view_dict))

    # Build device info msg for any devices found in the Dashboard
    main_view_device_fnames  = []
    main_view_devicenames    = []
    other_view_device_fnames = []

    # for devicename, fname in self.conf_fnames_by_devicename().items():
    for devicename, fname in lists.devices_selection_list().items():
        if instr(main_view_str, devicename):
            list_add(main_view_devicenames, devicename)
            list_add(main_view_device_fnames, fname)
        if instr(other_view_str, devicename):
            list_add(other_view_device_fnames, fname)

    self.main_view_device_fnames_by_dashboard[dbname]  = main_view_device_fnames
    self.main_view_devicenames_by_dashboard[dbname]    = main_view_devicenames
    self.other_view_device_fnames_by_dashboard[dbname] = other_view_device_fnames

    return

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

    return Gb.hass.data[LOVELACE_DATA].dashboards[dbname]._data['config']['views']

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
            _Dashboard._data['config'] = dashboard_layout_dict['data']['config']
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
        dashboard_layout_dict = await file_io.read_json_file(dashboard_file)

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
def _load_ic3db_Dashboards_by_dbname(self):
    '''
    Cycle through the Gb.hass.data[LOVELACE_DATA].dashboards extract the ic3db dashboards

    Returns:
        dictionary of {_dbname: _Dashboard object}
    '''

    self.ic3db_Dashboards_by_dbname = {_dbname: _Dashboard
                    for _dbname, _Dashboard in Gb.hass.data[LOVELACE_DATA].dashboards.items()
                    if (_dbname is not None
                        and _dbname.startswith('ic3db-')
                        and _Dashboard is not None
                        and _Dashboard.config['url_path'].startswith('ic3db-'))}


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

    url_path = dbname
    title    = dbname.replace('ic3db-', '').replace('icloud3', 'iCloud3')
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
        'title': title,
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

    # self.dashboard_config_just_added = dashboard_config
    # Force lovelace_dashboards save since async_create_item does a delayed save. It will be updated
    # again in async_create_item
    await _add_dashboard_to_lovelace_dashboards_file(dbname, dashboard_config)
    list_add(self.dbnames_just_added, dbname)

    _register_panel(Gb.hass, url_path, "storage", dashboard_config, True)
    Dashboard = dashboard.LovelaceStorage(Gb.hass, dashboard_config)
    Gb.hass.data[LOVELACE_DATA].dashboards[dbname] = Dashboard

    self.Dashboard = Dashboard
    self.ic3db_Dashboards_by_dbname[dbname]    = Dashboard
    self.AllDashboards_by_dashboard[dbname] = Dashboard

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
    number_suffix = int(number_suffix) if isnumber(number_suffix) else 0
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
        dashboards_config = await file_io.read_json_file(dashboards_file)
        if is_empty(dashboards_config):
            return []

        ic3db_db_configs = [config for config in dashboards_config['data']['items']
                                if config['url_path'].startswith('ic3db-')]

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
        for item in lovelace_dashboards['data']['items']:
            if item['url_path'] == dbname:
                return False

        lovelace_dashboards['data']['items'].append(dashboard_config)

        await file_io.async_save_json_file(lovelace_dashboards_file, lovelace_dashboards)

    except Exception as err:
        log_exception(err)

    return True
