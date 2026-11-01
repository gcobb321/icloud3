

from ...global_variables    import GlobalVariables as Gb
from ...const               import (HOME, NONE,
                                    DEVICE_TYPE_DN, DEVICE_TYPE_DNS, DEVICE_TYPES_TRACK_MONITOR, INACTIVE,
                                    PICTURE_WWW_STANDARD_DIRS, )
from ...const_config        import (CONF_PICTURE_WWW_DIRS, CONF_APPLE_ACCT, CONF_APPLE_ACCT,
                                    CONF_TRACK_FROM_ZONES, CONF_LOG_ZONES,
                                    CONF_TRACK_FROM_BASE_ZONE, CONF_PICTURE, CONF_ICON,
                                    CONF_DEVICE_TYPE, CONF_IC3_DEVICENAME, CONF_FNAME,
                                    CONF_AADEV_NAME, CONF_MOBILE_APP_DEVICE, CONF_TRACKING_MODE,
                                    CONF_INZONE_INTERVAL, CONF_FIXED_INTERVAL, )
from ...const_char          import (LINK, RARROW, )

from ...utils.utils         import (list_to_str, list_add, isnot_empty,
                                    apple_user, apple_user_dev, apple_id_dev,
                                    zone_dname, dict_value_to_list, six_item_dict, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..const_form_lists     import *

from ...startup             import config_file
from ..                     import utils_cf
from ..                     import selection_lists as lists

from homeassistant.util     import slugify
from homeassistant.helpers  import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#     ICLOUD3 DEVICE FORMS
#
#           - form_device_list
#           - form_add_device
#           - form_update_device
#           - form_update_other_device_parameters
#           - form_change_device_order
#           - form_picture_dir_filter
#           - form_review_inactive_devices
#           - form_import_apple_devices
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DEVICE LIST
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#................................................................................................



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DEVICE LIST
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def device_list_menu_options(self):
    '''
    Build the Devices menu. Each device on the current page is a menu row that opens the
    device menu. The device's information is displayed below its name. The actions that
    are not for a device are listed below the devices.

    Return:
        {option: label}, label=None uses the strings.json label
        placeholders for the strings.json labels and descriptions
    '''
    device_cnt, inactive_device_cnt, inactive_pct = config_file.device_cnts()
    # Inactive devices that can't be tracked (AirPods, iPods) are not on the Review
    # inactive devices screen
    inactive_device_cnt = len([conf_device  for conf_device in Gb.conf_devices
                                            if (conf_device[CONF_TRACKING_MODE] == INACTIVE
                                                and conf_device[CONF_DEVICE_TYPE] in DEVICE_TYPES_TRACK_MONITOR)])
    devicenames = devicenames_by_apple_acct(list(self.device_items_by_devicename.keys()))

    page_cnt = max(1, -(-len(devicenames) // DEVICE_LIST_PAGE_SIZE))
    if self.dev_page_no >= page_cnt:
        self.dev_page_no = 0
    from_idx = self.dev_page_no * DEVICE_LIST_PAGE_SIZE
    self.device_items_displayed = devicenames[from_idx:from_idx + DEVICE_LIST_PAGE_SIZE]

    menu_options = {}
    placeholders = {}
    if inactive_device_cnt > 0 and inactive_pct > .5:
        menu_options['device_list_review_inactive'] = None

    for slot, devicename in enumerate(self.device_items_displayed):
        device_name, device_info = _split_list_item(self.device_items_by_devicename[devicename])
        menu_options[f"device_list_device_{slot}"], placeholders[f"device_{slot}"] = \
                        _row_label_and_description(device_name, device_info)

    if page_cnt > 1:
        next_page_from_idx = (from_idx + DEVICE_LIST_PAGE_SIZE) % (page_cnt * DEVICE_LIST_PAGE_SIZE)
        next_page_devicenames = devicenames[next_page_from_idx:next_page_from_idx + DEVICE_LIST_PAGE_SIZE]
        menu_options['device_list_next_page'] = None
        placeholders['devices'] = list_to_str(
                    [_device_item_fname(self.device_items_by_devicename[devicename])
                        for devicename in next_page_devicenames])

    menu_options['device_list_add'] = None
    if Gb.use_data_source_ICLOUD:
        try:
            lists.build_import_apple_devices_selection_list(self)
        except Exception as err:
            log_exception(err)
            self.imported_aadevices_sel_list = []
        menu_options['device_list_import'] = (None if self.imported_aadevices_sel_list else
                                                utils_cf.tr('device_list_import_none_new'))
    if device_cnt > 1:
        menu_options['device_list_change_order'] = None
    if inactive_device_cnt > 0 and inactive_pct <= .5:
        menu_options['device_list_review_inactive'] = None
    menu_options['device_list_back'] = None
    placeholders.update({'inactive_cnt': inactive_device_cnt, 'device_cnt': device_cnt})

    return menu_options, placeholders


#................................................................................................
def devicenames_by_apple_acct(devicenames):
    '''
    The devices grouped by their Apple Account (the Apple Accounts order), the Mobile App
    only devices last. The device order is kept within a group.
    '''
    apple_ids = [conf_apple_acct[CONF_APPLE_ACCT] for conf_apple_acct in Gb.conf_apple_accounts]
    conf_device_by_devicename = {conf_device[CONF_IC3_DEVICENAME]: conf_device
                                    for conf_device in Gb.conf_devices}

    def _apple_acct_idx(devicename):
        conf_device = conf_device_by_devicename.get(devicename, {})
        apple_id = (conf_device.get(CONF_APPLE_ACCT, '')
                        if conf_device.get(CONF_AADEV_NAME, 'None') != 'None' else '')
        return apple_ids.index(apple_id) if apple_id in apple_ids else len(apple_ids)

    if len({_apple_acct_idx(devicename) for devicename in devicenames}) <= 1:
        return devicenames
    return sorted(devicenames, key=_apple_acct_idx)

#................................................................................................
def _row_label_and_description(device_name, device_info):
    '''
    HA before 2025.10 does not display the row descriptions, the Monitored/Inactive status
    and the alert symbol are in the row label (⚠︎ Gary (gary_iphone) · Inactive). The status
    is removed from the description so it is only displayed once.

    Return:
        row label, row description
    '''
    label = f"{CF_ALERT}{device_name}" if CF_ALERT in device_info else device_name
    status, _, other_info = device_info.partition(' · ')
    if status in [utils_cf.tr('dev_status_monitored'), utils_cf.tr('dev_status_inactive'),
                    utils_cf.tr('dev_status_disabled')]:
        return f"{label} · {status}", other_info
    return label, device_info

#................................................................................................
def _split_list_item(list_item):
    '''
    Split a devices or Apple Accounts list item into the name displayed on the menu row
    and the information displayed below it (Gary (gary_iphone) → iPhone 16 · Apple: Gary-iPhone)
    '''
    name, _, info = list_item.partition(RARROW)
    return name.strip(), info.strip()

#................................................................................................
def _device_item_fname(device_item):
    '''
    The fname and the Monitored/Inactive status of the devices list item
    (Gary (gary_iphone) → Monitored · ... returns Gary (Monitored))
    '''
    device_name, device_info = _split_list_item(device_item)
    status = device_info.split(' · ')[0]
    fname = device_name.split(' (')[0]
    if status in [utils_cf.tr('dev_status_monitored'), utils_cf.tr('dev_status_inactive')]:
        return f"{fname} ({status})"
    return fname

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DEVICE HEADING
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def device_heading(self):
    '''
    The name and information of the device being updated (self.conf_device) displayed
    at the top of the device forms

    Return:
        description placeholders {form_title, device_name, device_info}
    '''
    if self.add_device_flag:
        return {'form_title': utils_cf.tr('title_add_device'),
                'device_name': utils_cf.tr('new_device'), 'device_info': ''}

    status, model, data_sources, zones = lists.device_info_parts(self, self.conf_device)
    live_status = lists.device_live_status(self.conf_device)
    device_info = f" · {status}{f' · {live_status}' if live_status else ''}{f' · {model}' if model else ''}"
    if data_sources:
        device_info += f"\n{' · '.join(data_sources)}"
    if zones:
        device_info += f"\n{' · '.join(zones)}"

    return {'form_title': utils_cf.tr('title_device'),
            'device_name': f"{self.conf_device[CONF_FNAME]} ({self.conf_device[CONF_IC3_DEVICENAME]})",
            'device_info': device_info}


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           CHANGE DEVICE ORDER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def change_device_order_menu_options(self):
    '''
    Build the Change Device Order menu. Each device is a menu row in the new order.
    Selecting a device moves it up one position (↑), the top device can not be moved.
    A row is opened by its async_step_change_device_order_device_[idx] function, they
    exist for the first DEVICE_ORDER_MAX_CNT devices. The devices after them keep
    their position.
    '''
    menu_options = {f"change_device_order_device_{cdo_idx}":
                            f"{'' if cdo_idx == 0 else '↑ '}{self.cdo_devicenames[cdo_idx]}"
                        for cdo_idx in range(min(len(self.cdo_devicenames), DEVICE_ORDER_MAX_CNT))}
    menu_options['change_device_order_save'] = None
    menu_options['change_device_order_back'] = None

    return menu_options



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def other_device_parameters_summary(self):
    '''
    The values of the Other Device Parameters displayed on the device menu and the
    Update Device screen opened from HA Repairs
    '''
    log_zones_fnames = [zone_dname(zone) for zone in self.conf_device[CONF_LOG_ZONES] if zone.startswith('name') is False]
    tfz_fnames = [zone_dname(zone) for zone in self.conf_device[CONF_TRACK_FROM_ZONES]]
    device_type_fname = DEVICE_TYPE_DN(utils_cf.parm_or_device(self, CONF_DEVICE_TYPE))
    tr = utils_cf.tr

    summary_parts = [device_type_fname,
                     tr('ods_inzone_interval', mins=self.conf_device[CONF_INZONE_INTERVAL])]
    if self.conf_device[CONF_FIXED_INTERVAL] > 0:
        summary_parts.append(tr('ods_fixed_interval', mins=self.conf_device[CONF_FIXED_INTERVAL]))
    if self.conf_device[CONF_LOG_ZONES] != [NONE]:
        summary_parts.append(tr('ods_log_zones', zones=list_to_str(log_zones_fnames)))
    if self.conf_device[CONF_TRACK_FROM_ZONES] != [HOME]:
        summary_parts.append(tr('dev_track_from', zones=list_to_str(tfz_fnames)))
    if self.conf_device[CONF_TRACK_FROM_BASE_ZONE] != HOME:
        summary_parts.append(tr('dev_home_override',
                                zone=zone_dname(self.conf_device[CONF_TRACK_FROM_BASE_ZONE])))

    return ' · '.join(summary_parts)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_update_device(self):
    self.errors = self.errors or {}

    devicename = utils_cf.parm_or_device(self, CONF_IC3_DEVICENAME)

    # iCloud Devices list default item
    apple_id   = utils_cf.parm_or_device(self, CONF_APPLE_ACCT)
    aadev_name = utils_cf.parm_or_device(self, CONF_AADEV_NAME)
    if aadev_name == 'None' or devicename == '':
        apple_devices_list_key = 'None'
    else:
        apple_devices_list_key, status_msg = \
                        lists.format_apple_acct_device_info(self, self.conf_device)

        if status_msg == '':
            apple_devices_list_key = apple_id_dev(apple_id, aadev_name)
        else:
            apple_devices_list_key = apple_id_dev(apple_id, devicename)

    apple_devices_list_text = self.icloud_list_text_by_fname.get(apple_devices_list_key)

    if apple_devices_list_text is None:
        apple_devices_list_text = self.icloud_list_text_by_fname['None']

    # Check the aadev_name and mobile app devicename for any errors
    self._validate_data_source_selections(self.conf_device)

    # Mobile App Devices list default item
    mobapp_device = utils_cf.parm_or_device(self, CONF_MOBILE_APP_DEVICE)
    mobapp_list_text_by_entity_id = self.mobapp_list_text_by_entity_id.copy()
    if '.unknown' in mobapp_list_text_by_entity_id:
        default_mobile_app_device = mobapp_list_text_by_entity_id['.unknown']
    else:
        default_mobile_app_device = mobapp_list_text_by_entity_id[mobapp_device]

    # Picture list setup
    _picture_by_filename = {}
    picture_filename = utils_cf.parm_or_device(self, CONF_PICTURE)
    default_picture_filename = self.picture_by_filename.get(picture_filename)
    if default_picture_filename is None:
        self.errors[CONF_PICTURE] = 'unknown_picture'
        default_picture_filename = (f"{CF_ALERT}{picture_filename}{RARROW}"
                                    f"{utils_cf.tr('picture_not_found')}")
        _picture_by_filename[picture_filename] = default_picture_filename

    _picture_by_filename.update(self.picture_by_filename)

    if Gb.internet_error:
            self.errors['base'] = 'internet_error'
    elif self.errors != {}:
        self.errors['base'] = 'unknown_value'

    if devicename in Gb.ha_disabled_by_by_devicename:
        self.errors['base'] = 'disabled_in_ha'
        self.errors[CONF_TRACKING_MODE] = 'disabled_in_ha'


    schema = {
        vol.Optional(CONF_FNAME,
                    default=utils_cf.parm_or_device(self, CONF_FNAME)):
                    selector.TextSelector(),
        vol.Optional(CONF_IC3_DEVICENAME,
                    default=utils_cf.parm_or_device(self, CONF_IC3_DEVICENAME)):
                    selector.TextSelector(),
        vol.Optional('apple_devices_list_key',
                    default=apple_devices_list_text):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.icloud_list_text_by_fname), mode='dropdown')),
        vol.Optional(CONF_MOBILE_APP_DEVICE,
                    default=default_mobile_app_device):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(mobapp_list_text_by_entity_id), mode='dropdown')),
        vol.Optional(CONF_PICTURE,
                    default=default_picture_filename):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(_picture_by_filename), mode='dropdown')),
        }
    if utils_cf.parm_or_device(self, CONF_PICTURE) == 'None':
        schema.update({
            vol.Required(CONF_ICON,
                    default=utils_cf.parm_or_device(self, CONF_ICON)):
                    selector.IconSelector(),
        })
    schema.update({
        vol.Optional(CONF_TRACKING_MODE,
                    default=utils_cf.option_parm_key(self, CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)):
                    utils_cf.select(TRACKING_MODE_OPTIONS, translation_key='tracking_mode', mode='dropdown'),
        })

    # The Update Device screen opened from HA Repairs has no sections, the Other
    # parameters are on their own screen
    if self.is_repair_flow:
        schema.update(utils_cf.form_action_field(self, {
                    'save':  utils_cf.tr('submit_save_repair'),
                    'update_other_device_parameters':
                            utils_cf.tr('action_update_other_device_parameters',
                                        summary=other_device_parameters_summary(self)),
                    'exit_repair': utils_cf.tr('back_exit_repair')},
                    'save'))
        return vol.Schema(schema)

    # A new device gets its Other Device Parameters from the device type, its entity ID
    # is entered at the top of the form
    if self.add_device_flag:
        advanced_fields = []
        form_action = utils_cf.submit_back_field(self, 'save', 'rtn_device_list', 'device_list')
    else:
        schema.update(_other_device_parameters_schema(self))
        advanced_fields = [CONF_IC3_DEVICENAME, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                            CONF_FIXED_INTERVAL]
        form_action = utils_cf.submit_back_field(self, 'save', 'rtn_device_list', 'device_list',
                            other_actions={'delete_device': utils_cf.tr('action_delete_device')})

    return utils_cf.sectioned_schema(self, schema, [
            ('data_sources_section', ['apple_devices_list_key', CONF_MOBILE_APP_DEVICE], True),
            ('appearance_section', [CONF_PICTURE, CONF_ICON], False),
            ('zones_section', [CONF_TRACK_FROM_ZONES, CONF_TRACK_FROM_BASE_ZONE, CONF_LOG_ZONES], False),
            (ADVANCED_SECTION, advanced_fields, False),
            ],
            form_action)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE OTHER DEVICE PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_update_other_device_parameters(self):
    '''
    The Other Device Parameters screen opened from the Update Device screen in HA Repairs
    '''
    return vol.Schema({
            vol.Optional(CONF_FNAME,
                    default=utils_cf.parm_or_device(self, CONF_FNAME)):
                    selector.TextSelector(),
            **_other_device_parameters_schema(self),

        **utils_cf.submit_back_field(self, 'save', 'rtn_update_device', 'the_device'),
        })

def _other_device_parameters_schema(self):
    '''
    The Other Device Parameters fields. They are in the Zones and Advanced sections of the
    Update Device screen and on the Other Device Parameters screen opened from HA Repairs.
    '''
    log_zones_key_text = {'none': utils_cf.tr('none')}
    zone_name_key_text = {k: v  for k, v in self.zone_name_key_text.items()
                                if k.startswith('.') is False}
    log_zones_key_text.update(zone_name_key_text)
    log_zones_key_text['.hdr'] = f"{utils_cf.tr('log_zones_hdr')}:"
    log_zones_key_text.update({key: utils_cf.tr(f"log_zones_{key.replace('-', '_')}")
                                    for key in LOG_ZONES_FILE_NAMES})

    return {
            vol.Optional(CONF_DEVICE_TYPE,
                    default=utils_cf.option_parm_key(self, CONF_DEVICE_TYPE, DEVICE_TYPE_DNS)):
                    utils_cf.select(DEVICE_TYPE_DNS, translation_key='device_type'),
            vol.Required(CONF_INZONE_INTERVAL,
                    default=self.conf_device[CONF_INZONE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='min')),
            vol.Required(CONF_FIXED_INTERVAL,
                    default=self.conf_device[CONF_FIXED_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=480, step=5, unit_of_measurement='min')),
            vol.Optional(CONF_LOG_ZONES,
                    default=utils_cf.parm_or_device(self, CONF_LOG_ZONES)):
                    cv.multi_select(six_item_dict(log_zones_key_text)),
            vol.Required(CONF_TRACK_FROM_ZONES,
                    default=utils_cf.zone_entity_ids(utils_cf.parm_or_device(self, CONF_TRACK_FROM_ZONES))):
                    utils_cf.zone_selector(self, multiple=True),
            vol.Optional(CONF_TRACK_FROM_BASE_ZONE,
                    default=utils_cf.zone_entity_ids(utils_cf.parm_or_device(self, CONF_TRACK_FROM_BASE_ZONE))):
                    utils_cf.zone_selector(self),
            }


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           PICTURE IMAGE FILTER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_picture_dir_filter(self):
    if PICTURE_WWW_STANDARD_DIRS in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
        Gb.conf_profile[CONF_PICTURE_WWW_DIRS] = []

    www_group_1 = {}
    www_group_2 = {}
    www_group_3 = {}
    www_group_4 = {}
    www_group_5 = {}
    conf_www_group_1 = []
    conf_www_group_2 = []
    conf_www_group_3 = []
    conf_www_group_4 = []
    conf_www_group_5 = []
    for dir in self.www_directory_list:
        if len(www_group_1) < 5:
            www_group_1[dir] = dir
            if dir in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                list_add(conf_www_group_1, dir)
        elif len(www_group_2) < 5:
            www_group_2[dir] = dir
            if dir in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                list_add(conf_www_group_2, dir)
        elif len(www_group_3) < 5:
            www_group_3[dir] = dir
            if dir in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                list_add(conf_www_group_3, dir)
        elif len(www_group_4) < 5:
            www_group_4[dir] = dir
            if dir in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                list_add(conf_www_group_4, dir)
        elif len(www_group_5) < 5:
            www_group_5[dir] = dir
            if dir in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                list_add(conf_www_group_5, dir)

    schema = {
        vol.Required('www_group_1',
                    default=conf_www_group_1):
                    cv.multi_select(www_group_1)}

    if isnot_empty(www_group_2):
        schema.update({
            vol.Required('www_group_2',
                    default=conf_www_group_2):
                    cv.multi_select(www_group_2),})
    if isnot_empty(www_group_3):
        schema.update({
            vol.Required('www_group_3',
                    default=conf_www_group_3):
                    cv.multi_select(www_group_3),})
    if isnot_empty(www_group_4):
        schema.update({
            vol.Required('www_group_4',
                    default=conf_www_group_4):
                    cv.multi_select(www_group_4),})
    if isnot_empty(www_group_5):
        schema.update({
            vol.Required('www_group_5',
                    default=conf_www_group_5):
                    cv.multi_select(www_group_5),})

    schema.update({
        **utils_cf.submit_back_field(self, 'save', 'goto_previous',
                        'add_device' if self.add_device_flag else 'the_device'),})

    return vol.Schema(schema)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           CHANGE DEVICE ORDER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              REVIEW INACTIVE DEVICES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_review_inactive_devices(self, start_cnt=None):
    self.inactive_devices_key_text = {'all': utils_cf.tr('review_inactive_all')}
    self.inactive_devices_key_text.update({
        conf_device[CONF_IC3_DEVICENAME]: lists.format_device_list_item(self, conf_device)
                                for conf_device in Gb.conf_devices
                                if (conf_device[CONF_TRACKING_MODE] == INACTIVE
                                        and conf_device[CONF_DEVICE_TYPE] in DEVICE_TYPES_TRACK_MONITOR)})

    return vol.Schema({
        vol.Optional('inactive_devices',
                    default=[]):
                    utils_cf.select(self.inactive_devices_key_text, mode='list', multiple=True),

        **utils_cf.submit_back_field(self, 'update_tracking_mode', 'rtn_device_list',
                                        'device_list'),
        })
