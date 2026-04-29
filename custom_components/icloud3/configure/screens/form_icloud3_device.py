

from ...global_variables    import GlobalVariables as Gb
from ...const               import (RED_ALERT, LINK, RARROW, HOME, NONE, INACTIVE_SYMB, MONITOR_SYMB,
                                    DEVICE_TYPE_FNAME, DEVICE_TYPE_FNAMES, INACTIVE,
                                    PICTURE_WWW_STANDARD_DIRS, CONF_PICTURE_WWW_DIRS,
                                    CONF_APPLE_ACCOUNT,
                                    CONF_TRACK_FROM_ZONES, CONF_LOG_ZONES,
                                    CONF_TRACK_FROM_BASE_ZONE,
                                    CONF_PICTURE, CONF_ICON, CONF_DEVICE_TYPE,
                                    CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE,
                                    CONF_TRACKING_MODE, CONF_INZONE_INTERVAL, CONF_FIXED_INTERVAL,
                                    )

from ...utils.utils         import (instr, list_to_str, list_add,
                                    is_empty, isnot_empty,
                                    zone_dname, dict_value_to_list, six_item_dict, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)
from ...utils.time_util     import (format_timer, )

from ..const_form_lists     import *

from ..                     import utils_cf
from ..                     import selection_lists as lists

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
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DEVICE LIST
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_device_list(self):
    default_action = 'update_device'
    self.actions_list = DEVICE_LIST_ACTIONS.copy()

    # Build list of all devices
    self.device_items_list = [device_item
                        for device_item in self.device_items_by_devicename.values()]

    if is_empty(self.device_items_list):
        pass
    elif len(self.device_items_list) <= 6:
        self.device_items_displayed = self.device_items_list
    else:
        _build_device_items_displayed_over_6(self)
    list_add(self.device_items_displayed, '➤ ADD A NEW DEVICE')

    default_key  = self.dev_page_last_selected_devicename[self.dev_page_no]
    default_item = self.device_items_by_devicename.get(default_key)
    if default_item not in self.device_items_displayed:
        default_item = self.device_items_displayed[0]

    return vol.Schema({
            vol.Required('devices',
                        default=default_item):
                        selector.SelectSelector(selector.SelectSelectorConfig(
                            options=self.device_items_displayed, mode='list')),
            vol.Required('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
    })

#................................................................................................
def _build_device_items_displayed_over_6(self):
    '''
    Build the display page and next page line for the devicrs list
    when more than 6 devices
    '''
    # Build the list of devices to display on this page
    if self.dev_page_no == 0:
        display_from_idx, display_to_idx = [0, 6]
        other_from_idx, other_to_idx     = [6, len(self.device_items_list)]
    else:
        display_from_idx, display_to_idx = [6, len(self.device_items_list)]
        other_from_idx, other_to_idx     = [0, 6]

    # Set displayed devicenames
    self.device_items_displayed = self.device_items_list[display_from_idx:display_to_idx]

    # Extract fname (devicename) from the devices list (Gary (gary_iphone) → ...))
    device_fnames = []
    for device_item in self.device_items_list:
        monitor_inactive_symb = (MONITOR_SYMB if instr(device_item, MONITOR_SYMB) else
                                INACTIVE_SYMB if instr(device_item, INACTIVE_SYMB) else
                                '')

        device_fname = f"{device_item.split(' (')[0]}{monitor_inactive_symb}"
        list_add(device_fnames, device_fname)


    other_item_fnames =(f"➤ OTHER DEVICES{RARROW}"
                        f"{list_to_str(device_fnames[other_from_idx:other_to_idx])}")
    # device_fnames = [device_item.split(' (')[0]
    #                             f"{list_to_str(device_fnames[other_from_idx:other_to_idx])}")
    # Set other devices item fnames (either the main page items (#1-#6) or the second page (#7 to the end))
    list_add(self.device_items_displayed, other_item_fnames)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            ADD DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_add_device(self):
    self.actions_list = DEVICE_ADD_ACTIONS.copy()

    devicename    = utils_cf.parm_or_device(self, CONF_IC3_DEVICENAME) or ' '
    icloud3_fname = utils_cf.parm_or_device(self, CONF_FNAME) or ' '

    # iCloud Devices list default item
    apple_acct    = utils_cf.parm_or_device(self, CONF_APPLE_ACCOUNT)
    icloud_dname  = utils_cf.parm_or_device(self, CONF_FAMSHR_DEVICENAME)
    if icloud_dname == 'None'  or devicename == '':
        device_list_item_key = 'None'
    else:
        device_list_item_key = f"{icloud_dname}{LINK}{apple_acct}"

    device_list_item_text = self.icloud_list_text_by_fname.get(device_list_item_key)
    if device_list_item_text is None:
        device_list_item_text = self.icloud_list_text_by_fname['None']

    # Mobile App Devices list setup
    mobapp_device = utils_cf.parm_or_device(self, CONF_MOBILE_APP_DEVICE)
    mobapp_list_text_by_entity_id = self.mobapp_list_text_by_entity_id.copy()
    if '.unknown' in mobapp_list_text_by_entity_id:
        default_mobile_app_device = mobapp_list_text_by_entity_id['.unknown']
    else:
        default_mobile_app_device = mobapp_list_text_by_entity_id[mobapp_device]

    # Picture list setup
    picture_filename = utils_cf.parm_or_device(self, CONF_PICTURE)
    default_picture_filename = self.picture_by_filename.get(picture_filename)
    if default_picture_filename is None:
        picture_filename = 'None'
        default_picture_filename = self.picture_by_filename['None']

    return vol.Schema({
        vol.Required(CONF_IC3_DEVICENAME,
                    default=devicename):
                    selector.TextSelector(),
        vol.Required(CONF_FNAME,
                    default=icloud3_fname):
                    selector.TextSelector(),
        vol.Required(CONF_FAMSHR_DEVICENAME,
                    default=device_list_item_text):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.icloud_list_text_by_fname), mode='dropdown')),
        vol.Required(CONF_MOBILE_APP_DEVICE,
                    default=default_mobile_app_device):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(mobapp_list_text_by_entity_id), mode='dropdown')),
        vol.Required(CONF_PICTURE,
                    default=default_picture_filename):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.picture_by_filename), mode='dropdown')),
        vol.Required(CONF_ICON,
                    default=utils_cf.parm_or_device(self, CONF_ICON)):
                    selector.IconSelector(),
        vol.Optional(CONF_TRACKING_MODE,
                    default=utils_cf.option_parm_to_text(self, CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(TRACKING_MODE_OPTIONS), mode='dropdown')),
        vol.Required('action_items',
                default=utils_cf.default_action_text('add_device')):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_update_device(self):

    # Build Other Tracking Parameters values text
    log_zones_fnames = [zone_dname(zone) for zone in self.conf_device[CONF_LOG_ZONES] if zone.startswith('name') is False]
    tfz_fnames = [zone_dname(zone) for zone in self.conf_device[CONF_TRACK_FROM_ZONES]]
    device_type_fname = DEVICE_TYPE_FNAME(utils_cf.parm_or_device(self, CONF_DEVICE_TYPE))
    otp_msg =  (f"Type ({device_type_fname}), "
                f"inZoneInterval ({format_timer(self.conf_device[CONF_INZONE_INTERVAL]*60)})")
    otp_msg += ", FixedInterval"
    if self.conf_device[CONF_FIXED_INTERVAL] > 0:
        otp_msg += f" ({format_timer(self.conf_device[CONF_FIXED_INTERVAL]*60)})"
    otp_msg += ", LogZones"
    if self.conf_device[CONF_LOG_ZONES] != [NONE]:
        otp_msg += f" ({list_to_str(log_zones_fnames)})"
    otp_msg += ", TrackFromZone"
    if self.conf_device[CONF_TRACK_FROM_ZONES] != [HOME]:
        otp_msg += f" ({list_to_str(tfz_fnames)})"
    otp_msg += ", PrimaryTrackFromZone"
    if self.conf_device[CONF_TRACK_FROM_BASE_ZONE] != HOME:
        otp_msg += f" ({zone_dname(self.conf_device[CONF_TRACK_FROM_BASE_ZONE])})"
    otp_action_item = ACTION_LIST_OPTIONS[
                'update_other_device_parameters'].replace('^otp_msg', otp_msg)

    error_key = ''
    self.errors = self.errors or {}
    self.actions_list = []
    self.actions_list.append(otp_action_item)
    self.actions_list.append(ACTION_LIST_OPTIONS['save'])
    self.actions_list.append(ACTION_LIST_OPTIONS['cancel_goto_menu'])
    self.actions_list.append(ACTION_LIST_OPTIONS['cancel_goto_select_device'])


    devicename    = utils_cf.parm_or_device(self, CONF_IC3_DEVICENAME)
    icloud3_fname = utils_cf.parm_or_device(self, CONF_FNAME) or ' '

    # iCloud Devices list default item
    apple_acct    = utils_cf.parm_or_device(self, CONF_APPLE_ACCOUNT)
    icloud_dname  = utils_cf.parm_or_device(self, CONF_FAMSHR_DEVICENAME)
    if icloud_dname == 'None' or devicename == '':
        device_list_item_key = 'None'
    else:
        icloud_dname_apple_acct, status_msg = \
                        lists.format_apple_acct_device_info(self, self.conf_device)

        if status_msg == '':
            device_list_item_key = f"{icloud_dname}{LINK}{apple_acct}"
        else:
            device_list_item_key = f"{devicename}{LINK}{apple_acct}"

    device_list_item_text = self.icloud_list_text_by_fname.get(device_list_item_key)
    if device_list_item_text is None:
        device_list_item_text = self.icloud_list_text_by_fname['None']

    # Check the icloud_dname and mobile app devicename for any errors
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
        default_picture_filename = (f"{RED_ALERT}{picture_filename}{RARROW}FILE NOT FOUND")
        _picture_by_filename[picture_filename] = default_picture_filename
        _picture_by_filename['.www_err'] = '═'*47

    _picture_by_filename.update(self.picture_by_filename)

    if Gb.internet_error:
            self.errors['base'] = 'internet_error'
    elif self.errors != {}:
        self.errors['base'] = 'unknown_value'

    if utils_cf.parm_or_device(self, CONF_TRACKING_MODE) == INACTIVE:
        self.errors[CONF_TRACKING_MODE] = 'inactive_device'

    log_zones_key_text = {'none': 'None'}
    zone_name_key_text = {k: v  for k, v in self.zone_name_key_text.items()
                                if k.startswith('.') is False}
    log_zones_key_text.update(zone_name_key_text)
    log_zones_key_text.update(LOG_ZONES_KEY_TEXT)

    schema = {
        vol.Required(CONF_IC3_DEVICENAME,
                    default=utils_cf.parm_or_device(self, CONF_IC3_DEVICENAME)):
                    selector.TextSelector(),
        vol.Required(CONF_FNAME,
                    default=utils_cf.parm_or_device(self, CONF_FNAME)):
                    selector.TextSelector(),
        vol.Required(CONF_FAMSHR_DEVICENAME,
                    default=device_list_item_text):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.icloud_list_text_by_fname), mode='dropdown')),
        vol.Required(CONF_MOBILE_APP_DEVICE,
                    default=default_mobile_app_device):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(mobapp_list_text_by_entity_id), mode='dropdown')),
        vol.Required(CONF_PICTURE,
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
                    default=utils_cf.option_parm_to_text(self, CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(TRACKING_MODE_OPTIONS), mode='dropdown')),
        })

    schema.update({
        vol.Required('action_items',
                default=utils_cf.default_action_text('save')):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=self.actions_list, mode='list')),
        })

    return vol.Schema(schema)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE OTHER DEVICE PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_update_other_device_parameters(self):

    self.actions_list = []
    self.actions_list.append(ACTION_LIST_OPTIONS['save'])
    self.actions_list.append(ACTION_LIST_OPTIONS['cancel_goto_previous'])

    log_zones_key_text = {'none': 'None'}
    zone_name_key_text = {k: v  for k, v in self.zone_name_key_text.items()
                                if k.startswith('.') is False}
    log_zones_key_text.update(zone_name_key_text)
    log_zones_key_text.update(LOG_ZONES_KEY_TEXT)

    device_type_fname = DEVICE_TYPE_FNAME(utils_cf.parm_or_device(self, CONF_DEVICE_TYPE))
    return vol.Schema({
            vol.Optional(CONF_DEVICE_TYPE,
                    default=utils_cf.option_parm_to_text(self, CONF_DEVICE_TYPE, DEVICE_TYPE_FNAMES)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(DEVICE_TYPE_FNAMES), mode='dropdown')),
            vol.Required(CONF_INZONE_INTERVAL,
                    default=self.conf_device[CONF_INZONE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
            vol.Required(CONF_FIXED_INTERVAL,
                    default=self.conf_device[CONF_FIXED_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=480, step=5, unit_of_measurement='minutes')),
            vol.Optional(CONF_LOG_ZONES,
                    default=utils_cf.parm_or_device(self, CONF_LOG_ZONES)):
                    cv.multi_select(six_item_dict(log_zones_key_text)),
            vol.Required(CONF_TRACK_FROM_ZONES,
                    default=utils_cf.parm_or_device(self, CONF_TRACK_FROM_ZONES)):
                    cv.multi_select(six_item_dict(self.zone_name_key_text)),
            vol.Optional(CONF_TRACK_FROM_BASE_ZONE,
                    default=utils_cf.option_parm_to_text(self, CONF_TRACK_FROM_BASE_ZONE,
                                                self.zone_name_key_text, conf_device=True)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.zone_name_key_text), mode='dropdown')),

        vol.Required('action_items',
                    default=utils_cf.default_action_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           PICTURE IMAGE FILTER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_picture_dir_filter(self):
    self.actions_list = [
            ACTION_LIST_OPTIONS['save'],
            ACTION_LIST_OPTIONS['goto_previous']]

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
        vol.Required('action_items',
                default=utils_cf.default_action_text('save')):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=self.actions_list, mode='list')),})

    return vol.Schema(schema)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           CHANGE DEVICE ORDER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_change_device_order(self):
    self.actions_list = [
            ACTION_LIST_OPTIONS['move_up'],
            ACTION_LIST_OPTIONS['move_down']]
    self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

    return vol.Schema({
        vol.Required('device_desc',
                    default=self.cdo_devicenames[self.cdo_curr_idx]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.cdo_devicenames, mode='list')),
        vol.Required('action_items',
                    default=utils_cf.default_action_text(self.actions_list_default)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              REVIEW INACTIVE DEVICES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_review_inactive_devices(self, start_cnt=None):

    self.actions_list = REVIEW_INACTIVES.copy()

    self.inactive_devices_key_text = {
        conf_device[CONF_IC3_DEVICENAME]: lists.format_device_list_item(self, conf_device)
                                for conf_device in Gb.conf_devices
                                if conf_device[CONF_TRACKING_MODE] == INACTIVE}
    return vol.Schema({
        vol.Required('inactive_devices',
                    default=[]):
                    cv.multi_select(self.inactive_devices_key_text),

        vol.Required('action_items',
                    default=utils_cf.default_action_text('goto_previous')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })
