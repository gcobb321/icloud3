

from ..global_variables  import GlobalVariables as Gb
from ..const             import (DOMAIN, DEVICE_TYPE_DN, )
from ..const_config      import (CONF_UNIT_OF_MEASUREMENT, CONF_AADEV_NAME, CONF_MOBILE_APP_DEVICE, CONF_PARAMETER_TIME_STR,
                                 CONF_PARAMETER_FLOAT, CF_PROFILE, CF_TRACKING, CF_GENERAL,
                                 CONF_PASSWORD, )

from ..utils.utils     import (instr, is_number, is_empty, isnot_empty,
                                encode_password, decode_password, )
from ..utils.messaging import (log_exception, log_debug_msg, log_info_msg, add_log_file_filter,
                                _log, _evlog, log_stack, )

from .const_form_lists   import (SECTION_SUFFIX, FORM_ACTION, FORM_ACTION_SAVES_DATA,
                                DATA_ENTRY_ALERT, DATA_ENTRY_ALERT_CHAR, )
from homeassistant.helpers import translation, selector
import voluptuous as vol
import re
import json
from homeassistant.data_entry_flow import section

VALID_ERROR_MSG = [ 'conf_updated',
                    'internet_error',
                    'internet_error_no_change']

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                      CONFIGURE TEXT (strings.json)
#
#   HA translates the labels of the strings.json keys. The text the Configure screens
#   build (menu rows, option lists with names, messages with values) uses the strings.json
#   selector.cf_text.options.[key] texts. They are loaded once in the HA language when a
#   Configure, Repairs or Reauth flow starts. The flow context does not include the user
#   so the language of the user's profile is not known.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
_cf_texts = {'language': None, 'texts': {}}

async def async_load_texts():
    '''
    Load the selector and options strings of the HA language, English is used for the
    strings that are not translated
    '''
    language = Gb.hass.config.language
    if _cf_texts['language'] == language:
        return

    texts = {}
    for lang in dict.fromkeys(['en', language]):
        for category in ['selector', 'options']:
            texts.update(await translation.async_get_translations(
                                    Gb.hass, lang, category, [DOMAIN]))

    _cf_texts['texts']    = texts
    _cf_texts['language'] = language

def tr_path(path, **placeholders):
    '''
    The text of the strings.json path ('options.error.not_numeric') with the {placeholders}
    replaced. The path is returned when it is not found.
    '''
    text = _cf_texts['texts'].get(f"component.{DOMAIN}.{path}")
    if text is None:
        return path
    for placeholder, value in placeholders.items():
        text = text.replace(f"{{{placeholder}}}", str(value))
    return text

def tr(key, **placeholders):
    '''
    The selector.cf_text.options.[key] text
    '''
    return tr_path(f"selector.cf_text.options.{key}", **placeholders)

def tr_cnt(key, cnt, **placeholders):
    '''
    The [key]_one text when cnt is 1, otherwise [key]_other ({cnt} is the count)
    '''
    return tr(f"{key}_{'one' if cnt == 1 else 'other'}", cnt=cnt, **placeholders)

def has_tr(key):
    return f"component.{DOMAIN}.selector.cf_text.options.{key}" in _cf_texts['texts']

def tr_option(translation_key, value):
    '''
    The label of an option of a SelectSelector with a translation_key
    '''
    return tr_path(f"selector.{translation_key}.options.{value}")

def option_value(key):
    '''
    The SelectSelector value of an option key. A translated option's value is its
    strings.json key, which can only have a-z, 0-9, _ and - (.25 --> 0_25,
    'iCloud,MobApp' --> icloud_mobapp). It can not start or end with _ or - or have
    __ (hassfest), '.cn,GCJ02' --> cn_gcj02.
    '''
    value = re.sub(r'[^a-z0-9_-]', '_', str(key).lower())
    return re.sub(r'_{2,}', '_', value).strip('_-')

def select(options, translation_key=None, mode='dropdown', multiple=False):
    '''
    A SelectSelector of the options:
        [key] - The labels are the strings.json selector.[translation_key].options.[value]
                texts, HA translates them. The values are option_value(key).
        {value: label} - The labels are displayed as they are (names, built text)
    The values are strings, select_value converts one back to its key.
    '''
    if isinstance(options, dict):
        options = [{'value': str(value), 'label': label} for value, label in options.items()]
    else:
        options = [option_value(value) for value in options]

    config = {'options': options, 'mode': mode, 'multiple': multiple}
    if translation_key:
        config['translation_key'] = translation_key

    return selector.SelectSelector(selector.SelectSelectorConfig(**config))

# {pname: (first option value, stored value)} of the option_parm_key fields whose stored
# value is not one of the options
_unknown_option_values = {}

def select_value(user_input, pname, keys):
    '''
    Change the selected value (str) of the pname field back to its key (float, int)
    '''
    if user_input is None or pname not in user_input:
        return user_input

    # An unknown stored value that was displayed as the first option and not changed
    first_value, stored_value = _unknown_option_values.pop(pname, (None, None))
    if first_value is not None and user_input[pname] == first_value:
        user_input[pname] = stored_value
        return user_input

    keys_by_value = {option_value(key): key for key in keys}
    keys_by_value.update({str(key): key for key in keys})
    pvalue = user_input[pname]
    if isinstance(pvalue, list):
        user_input[pname] = [keys_by_value.get(value, value) for value in pvalue]
    else:
        user_input[pname] = keys_by_value.get(pvalue, pvalue)

    return user_input

def json_code_block(data):
    return f"\n```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```\n"

def version_downloads_msg():
    '''
    The GitHub release download counts and, when there is a newer beta, the beta's
    download counts displayed on the Analytics screens
    '''
    from ..support import analytics

    if Gb.github_version == '':
        return tr('downloads_not_available')

    # The analytics users are a portion of the release downloads, it is not displayed when
    # it rounds to 0%
    users = f"{Gb.analytics_installs:,}"
    if Gb.github_icloud3_downloads > 0:
        analytics_pct = round(100.0 * Gb.analytics_installs / Gb.github_icloud3_downloads)
        users += f" ({analytics_pct}%)" if analytics_pct >= 1 else ''

    downloads_msg = tr('downloads_msg',
                version=Gb.github_version,
                date=analytics._format_release_date(Gb.github_published_date),
                downloads=f"{Gb.github_icloud3_downloads:,}",
                users=users)

    if Gb.github_beta_version:
        downloads_msg += '\n' + tr('downloads_beta_msg',
                version=Gb.github_beta_version,
                date=analytics._format_release_date(Gb.github_beta_published_date),
                downloads=f"{Gb.github_beta_downloads:,}")

    return downloads_msg

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                      MISCELLANEOUS UTILITY FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def any_errors(self):
    return (isnot_empty(self.errors)
                and self.errors.get('base') not in VALID_ERROR_MSG)

def no_errors(self):
    return not any_errors(self)

#--------------------------------------------------------------------
# UNUSED (10/31/2026) - not called anywhere. Commented out, delete after v3.8.0
# def menu_text_to_item(self, user_input, selection_list):
#     '''
#     Convert the text of the menu item selected to it's key name.

#     selection_list - Field name in user_input to use:
#         ''menu_item' 'menu_action_item'
#     '''

#     if user_input is None:
#         return None, None

#     selected_text = None
#     if selection_list in user_input:
#         selected_text = user_input[selection_list]
#         selected_text_len = 35 if len(selected_text) > 35 else len(selected_text)

#         # selected_text contains the 'exit_xxx key', not the displayed menu text
#         if selected_text.startswith('exit_'):
#             user_input['menu_items'] = selected_text
#             return user_input, selected_text

#         # selected_text contains the displayed menu text
#         elif selected_text.startswith('EXIT'):
#             user_input['menu_items'] = 'exit'
#             return user_input, 'exit'

#         elif selected_text.startswith('MENU'):
#             user_input['menu_items'] = 'menu'
#             return user_input, 'menu'

#         menu_items = MENU_0_ITEMS if self.menu_page_no == 0 else MENU_1_ITEMS
#         menu_item = [k  for k, v in menu_items.items()
#                         if v.startswith(selected_text[:selected_text_len])][0]

#         user_input.pop(selection_list)
#     else:
#         menu_item = self.menu_item_selected

#     user_input['menu_items'] = menu_item

#     return user_input, menu_item

#--------------------------------------------------------------------
def set_header_msg(self):
    '''
    See if any header messages need to be displayed. If so set the self.errors['base']
    '''
    if self.header_msg:
        if self.errors is None: self.errors = {}
        self.errors = {'base': self.header_msg}
        self.header_msg = None

        return self.errors

    return {}

#--------------------------------------------------------------------
async def async_options_error_msgs(msg_keys):
    '''
    Return the options.error messages (strings.json) of the msg_keys in the HA language
    '''
    if is_empty(msg_keys):
        return []

    await async_load_texts()

    return [tr_path(f"options.error.{msg_key}") if f"component.{DOMAIN}.options.error.{msg_key}"
                    in _cf_texts['texts'] else msg_key
                for msg_key in msg_keys]

#--------------------------------------------------------------------
async def async_header_msgs(self, msg_keys):
    '''
    Return the messages displayed at the top of a menu. The 'conf_updated' message names
    the item that was saved (self.saved_item, a selector.cf_text.options.saved_[key] key or
    a name) when it is known and says when the changes are applied if iCloud3 is restarted
    when Configure closes. self.header_placeholders are inserted into the messages.
    '''
    saved_item = getattr(self, 'saved_item', '')
    if has_tr(f"saved_{saved_item}"):
        saved_item = tr(f"saved_{saved_item}")
    if 'conf_updated' in msg_keys:
        conf_updated_key = 'conf_updated_item' if saved_item else 'conf_updated'
        if 'restart' in getattr(self, 'config_parms_update_control', []):
            conf_updated_key += '_restart'
        msg_keys = [conf_updated_key if msg_key == 'conf_updated' else msg_key
                        for msg_key in msg_keys]

    placeholders = {'saved_item': saved_item, **(getattr(self, 'header_placeholders', None) or {})}
    msgs = []
    for msg in await async_options_error_msgs(msg_keys):
        for placeholder, value in placeholders.items():
            msg = msg.replace(f"{{{placeholder}}}", str(value))
        msgs.append(msg)
    self.saved_item = ''
    self.header_placeholders = {}

    return msgs

#--------------------------------------------------------------------
async def async_show_list_menu(self, step_id, menu_options, header_msg='', placeholders=None):
    '''
    Display a menu with rows that are built from the configuration (devices, Apple Accts).
    HA only translates a menu when all labels come from strings.json, so the static
    labels are looked up here.

    Parameters:
        menu_options - {option: label}. A label of None uses the strings.json
                options.step.<step_id>.menu_options.<option> label.
        header_msg - Text displayed above the rows. The self.errors['base'] message
                is added to it.
        placeholders - {placeholder: text} inserted into the strings.json labels here and
                into the description and menu_option_descriptions by HA
    '''
    placeholders = placeholders or {}
    await async_load_texts()

    menu_labels = {}
    for option, label in menu_options.items():
        if label is None:
            label = tr_path(f"options.step.{step_id}.menu_options.{option}", **placeholders)
        menu_labels[option] = label

    header_msgs = [header_msg] if header_msg else []
    header_msgs.extend(await async_header_msgs(self,
                    [self.errors['base']] if self.errors.get('base') else []))

    return self.async_show_menu(step_id=step_id,
                                menu_options=menu_labels,
                                description_placeholders={
                                        **placeholders,
                                        'header_msg': '\n\n'.join(header_msgs)})

#--------------------------------------------------------------------
def strip_spaces(user_input, parm_list=[]):
    '''
    Remove leading or trailing spaces from items in the parameter list

    '''
    if user_input is None: return None

    parm_list = [pname  for pname, pvalue in user_input.items()
                            if type(pvalue) is str and pvalue != '']

    for parm in parm_list:
        if parm in user_input:
            user_input[parm] = user_input[parm].strip()

    return user_input


#-------------------------------------------------------------------------------------------
def strip_special_text_from_user_input(user_input, pname):
    '''
    The user_input options may contain a special message after the actual parameter
    value. If so, strip it off so the field can be updated in the configuration file.

    Special message types:
        - '(Example: exampletext)'
        - '>'

    Returns:
        user_input  - user_input without the example text
    '''
    if user_input is None: return

    if pname not in user_input or type(pname) is not str:
        return user_input

    pvalue = user_input[pname]
    try:
        if instr(pvalue, DATA_ENTRY_ALERT_CHAR):
            pvalue = pvalue.split(DATA_ENTRY_ALERT_CHAR)[0]
        elif instr(pvalue, '(Example:'):
            pvalue = pvalue.split('(Example:')[0]

    except Exception as err:
        log_exception(err)
        pass

    user_input[pname] = pvalue.strip()

    return user_input

#--------------------------------------------------------------------
def action_text_to_item(self, user_input):
    '''
    Return the user_input without the form's Action field (FORM_ACTION) and the
    action_item selected in it, None if the form has no Action field.
    '''
    if user_input is None:
        return None, None

    if FORM_ACTION not in user_input:
        return user_input, None

    form_action = user_input.pop(FORM_ACTION)
    if form_action == 'back':
        return user_input, self.form_back_action
    if form_action == 'submit':
        return user_input, self.form_submit_action
    return user_input, form_action

#-------------------------------------------------------------------------------------------
def parm_or_error_msg(self, pname, conf_group=CF_GENERAL, conf_dict_variable=None):
    '''
    Determine the value that should be displayed in the config_flow parameter entry screen based
    on whether it was entered incorrectly and has an error message.

    Input:
        conf_group
    Return:
        Value in errors if it is in errors
        Value in Gb.conf_general[CONF_pname] if it is valid
    '''
    # pname is in the 'Profile' data fields
    # Example: [profile][version
    if conf_group == CF_PROFILE:
        return self.errors_user_input.get(pname) or Gb.conf_profile[pname]

    # pname is in the 'Tracking' data fields
    # Example: [data][general][tracking][apple_id]
    # Example: [data][general][tracking][devices]
    elif conf_group == CF_TRACKING:
        return self.errors_user_input.get(pname) or Gb.conf_tracking[pname]

    # pname is in a dictionary variable in the 'General Data' data fields grupo. It is a dictionary variable.
    # Example: [data][general][inzone_intervals][phone]
    elif conf_dict_variable is not None:
        pvalue = self.errors_user_input.get(pname) or Gb.conf_data[conf_group][conf_dict_variable][pname]

    # pname is in a dictionary variable in the 'General Data' data fields group. It is a non-dictionary variable.
    # Example: [data][general][unit_of_measurement]
    else:
        pvalue = self.errors_user_input.get(pname) or Gb.conf_data[conf_group][pname]
        if pname in CONF_PARAMETER_FLOAT:
            pvalue = str(pvalue).replace('.0', '')

    return pvalue

#-------------------------------------------------------------------------------------------
def parm_or_device(self, pname, suggested_value=''):
    '''
    Get the default value from the various dictionaries to display on the input form
    '''
    try:
        parm_displayed = self.errors_user_input.get(pname) \
                            or self.multi_form_user_input.get(pname) \
                            or self.conf_device.get(pname) \
                            or suggested_value

        if pname == 'device_type':
            parm_displayed = DEVICE_TYPE_DN(parm_displayed)
        parm_displayed = ' ' if parm_displayed == '' else parm_displayed

    except Exception as err:
        log_exception(err)

    return parm_displayed

#-------------------------------------------------------------------------------------------
def option_parm_to_text(self, pname, option_list_key_text, conf_device=False):
    '''
    Returns the full text string displayed in the config_flow options list for the parameter
    value in the configuration parameter file for the parameter name.

    pname - The name of the config parameter
    option_list_key_text - The option list displayed
    conf_device - Resolves device & general with same parameter name

    Example:
        pname = unit_of_measure field in conf record = 'mi'
        um_key_text = {'mi': 'miles', 'km': 'kilometers'}
    Return:
        'miles'
    '''

    try:
        if pname in self.errors_user_input:
            return option_list_key_text[self.errors_user_input[pname]]

        pvalue_key = pname
        if pname in Gb.conf_profile:
            pvalue_key = Gb.conf_profile[pname]

        elif pname in Gb.conf_tracking:
            pvalue_key = Gb.conf_tracking[pname]

        elif pname in self.conf_apple_acct:
            pvalue_key = self.conf_apple_acct[pname]

        elif pname in Gb.conf_general and pname in self.conf_device:
            if conf_device:
                pvalue_key = self.conf_device[pname]
            else:
                pvalue_key = Gb.conf_general[pname]

        elif pname in self.conf_device:
            pvalue_key = self.conf_device[pname]

        elif pname in Gb.conf_general:
            pvalue_key = Gb.conf_general[pname]

        if type(pvalue_key) in [float, int, str]:
            return option_list_key_text.get(pvalue_key, '')

        elif type(pvalue_key) is list:
            return [option_list_key_text[pvalue_key_item] for pvalue_key_item in pvalue_key]

        return option_list_key_text.values()[0]

    except Exception as err:
        log_exception(err)
        # If the parameter value is already the key to the items dict, it is ok.
        if pvalue_key not in option_list_key_text:
            if pname == CONF_AADEV_NAME:
                self.errors[pname] = 'unknown_icloud'
            elif pname == CONF_MOBILE_APP_DEVICE:
                self.errors[pname] = 'unknown_mobapp'
            else:
                self.errors[pname] = 'unknown_value'

        return f"{pvalue_key} {DATA_ENTRY_ALERT}Unknown Selection"

#-------------------------------------------------------------------------------------------
def option_parm_key(self, pname, keys, conf_device=False):
    '''
    The option_value of the parameter's current value, the default of a translated
    SelectSelector (select(keys, translation_key)). The first key if the value is
    not one of the keys, select_value keeps the stored value if the first key is not
    changed.
    '''
    keys = list(keys)
    key_by_value = {**{option_value(key): key for key in keys}, **{key: key for key in keys}}
    pvalue = option_parm_to_text(self, pname, key_by_value, conf_device)
    _unknown_option_values.pop(pname, None)
    if isinstance(pvalue, list):
        return [option_value(value) for value in pvalue if value in keys]
    if pvalue not in keys:
        stored_value = _stored_parm_value(self, pname, conf_device)
        if stored_value not in [None, '']:
            _unknown_option_values[pname] = (option_value(keys[0]), stored_value)
        pvalue = keys[0]
    return option_value(pvalue)

def _stored_parm_value(self, pname, conf_device):
    '''
    The stored value of the parameter, looked up like option_parm_to_text
    '''
    conf_apple_acct = getattr(self, 'conf_apple_acct', None) or {}
    conf_device_parms = getattr(self, 'conf_device', None) or {}
    if pname in getattr(self, 'errors_user_input', {}):
        return None
    if pname in Gb.conf_profile:
        return Gb.conf_profile[pname]
    if pname in Gb.conf_tracking:
        return Gb.conf_tracking[pname]
    if pname in conf_apple_acct:
        return conf_apple_acct[pname]
    if pname in Gb.conf_general and pname in conf_device_parms:
        return conf_device_parms[pname] if conf_device else Gb.conf_general[pname]
    if pname in conf_device_parms:
        return conf_device_parms[pname]
    return Gb.conf_general.get(pname)

#-------------------------------------------------------------------------------------------
# UNUSED (10/31/2026) - not called anywhere. Commented out, delete after v3.8.0
# def key_text_to_text_list(key_text):
#     return [text for text in key_text.values()]

#-------------------------------------------------------------------------------------------
def option_text_to_parm(user_input, pname, option_list_key_text):
    '''
    user_input contains the full text of the option list item selected. Replace it with
    the actual parameter value for the item selected.
    '''

    pvalue_text = '_'
    if user_input is None:
        return None
    if pname not in user_input:
        return user_input

    pvalue_text = user_input[pname]
    pvalue_key = [k for  k, v in option_list_key_text.items() if v == pvalue_text]
    pvalue_key = pvalue_key[0] if pvalue_key else pvalue_text

    user_input[pname] = pvalue_key

    return  user_input

#-------------------------------------------------------------------------------------------
#   Zones are stored without the 'zone.' domain and selected with the HA zone picker
def _selectable_zones(self):
    '''
    The zones of the old zone lists (zone_name_key_text), the Stationary zones and the
    zones iCloud3 does not use are not offered
    '''
    return [zone for zone in getattr(self, 'zone_name_key_text', {}) if zone not in ['', '.']
                    and zone.startswith('.') is False]

def zone_selector(self, multiple=False):
    return selector.EntitySelector(selector.EntitySelectorConfig(domain='zone', multiple=multiple,
                    include_entities=zone_entity_ids(_selectable_zones(self))))

def zone_entity_ids(zones):
    if isinstance(zones, str):
        return f"zone.{zones.strip()}" if zones.strip() not in ['', '.'] else None
    return [f"zone.{zone}" for zone in zones if zone.strip() not in ['', '.']]

def zones_from_ui(self, user_input, pnames, conf):
    '''
    Remove the 'zone.' domain from the selected zones. A newly selected zone that is not
    one of the selectable zones is a field error, the stored zones are kept as they are.

    Parameters:
        conf - The stored parameters (Gb.conf_general, self.conf_device)
    '''
    if user_input is None:
        return user_input
    selectable_zones = _selectable_zones(self)
    for pname in pnames:
        zones = user_input.get(pname)
        if isinstance(zones, str):
            user_input[pname] = zones = zones.removeprefix('zone.')
            new_zones = [zones] if zones != conf.get(pname) else []
        elif isinstance(zones, list):
            user_input[pname] = zones = [zone.removeprefix('zone.') for zone in zones]
            new_zones = [zone for zone in zones if zone not in (conf.get(pname) or [])]
        else:
            continue
        if [zone for zone in new_zones if zone not in selectable_zones]:
            self.errors[pname] = 'zone_not_selectable'
    return user_input

#-------------------------------------------------------------------------------------------
#   Distances are stored in km. They are displayed in mi when the unit of measurement that
#   is saved is mi. Gb.um_km_mi_factor is the factor of the unit iCloud3 is running with,
#   it is not changed until Configure is closed.
KM_TO_MI = .62137

def _is_um_mi():
    return Gb.conf_general.get(CONF_UNIT_OF_MEASUREMENT) == 'mi'

def km_field_default(pname):
    km = Gb.conf_general[pname]
    return round(km * KM_TO_MI, 1) if _is_um_mi() else km

def km_field_selector(pname, min_km, max_km, step=1):
    if _is_um_mi():
        return selector.NumberSelector(selector.NumberSelectorConfig(
                    min=round(min_km * KM_TO_MI, 1), max=round(max_km * KM_TO_MI, 1),
                    step=.1, unit_of_measurement='mi'))
    # A km value entered in mi has a decimal, the slider would change it when touched
    if Gb.conf_general[pname] != int(Gb.conf_general[pname]):
        step = .1
    return selector.NumberSelector(selector.NumberSelectorConfig(
                    min=min_km, max=max_km, step=step, unit_of_measurement='km'))

def km_fields_from_ui(user_input, pnames):
    '''
    Change the distances entered in mi back to km. A distance that was not changed keeps
    its stored km value. An entered distance is displayed with the same value when the
    screen is opened again.
    '''
    if user_input is None or _is_um_mi() is False:
        return user_input
    for pname in pnames:
        if pname not in user_input:
            continue
        if user_input[pname] == km_field_default(pname):
            user_input[pname] = Gb.conf_general[pname]
        else:
            # A whole km value is used when it is displayed as the entered mi value (1 decimal)
            km = user_input[pname] / KM_TO_MI
            user_input[pname] = round(km) if abs(km - round(km)) <= .05 / KM_TO_MI + 1e-9 else round(km, 1)
    return user_input

#-------------------------------------------------------------------------------------------
# UNUSED (10/31/2026) - not called anywhere. Commented out, delete after v3.8.0
# def convert_field_str_to_numeric(user_input):
#     '''
#     Config_flow chokes with malformed input errors when a field is numeric. To avoid this,
#     the field's default value is always a string. This converts it back to a float.
#     '''
#     for pname, pvalue in user_input.items():
#         if pname in CONF_PARAMETER_FLOAT:
#             user_input[pname] = float(pvalue)

#     return user_input

#-------------------------------------------------------------------------------------------
def validate_numeric_field(self, user_input):
    '''
    Cycle through the user_input fields and, if numeric, validate it
    '''
    for pname, pvalue in user_input.items():
        if pname not in CONF_PARAMETER_FLOAT:
            continue

        if is_number(pvalue) is False:
            pvalue = pvalue.strip()
            if pvalue == '':
                self.errors[pname] = "required_field"
            else:
                self.errors[pname] = "not_numeric"

        if pname in self.errors:
            self.errors_user_input[pname] = pvalue

    return user_input

#--------------------------------------------------------------------
def submit_back_field(self, submit_action, back_action, destination, submit_destination=None,
                        other_actions=None, default_action='submit'):
    '''
    Forms do not display an action list. The last field on the form selects the
    submit_action (default) or the back_action. action_text_to_item returns the
    action_item of the one selected.

    Parameters:
        destination - The screen displayed after the back_action, a dest_[key] text
                key (selector.cf_text) or a name
        submit_destination - The screen displayed after the submit_action when it is
                not the destination
        other_actions - {action_item: label} listed between the submit and back actions.
                action_text_to_item returns the action_item when one is selected.
        default_action - 'submit' or 'back' (a form whose Submit deletes something)

    Labels (selector.cf_text):
        submit_[submit_action] - The Submit label
        back_[submit_action] - The Back label of a form whose Submit stays on the form,
                otherwise back_discard (the Submit saves the entered data) or back
    Return:
        The Submit/Back schema item to be added to the end of the form's schema
    '''
    self.form_submit_action = submit_action
    self.form_back_action   = back_action

    dest        = destination_name(destination)
    submit_dest = destination_name(submit_destination) if submit_destination else dest
    submit_label = tr(f"submit_{submit_action}", dest=submit_dest)
    if has_tr(f"back_{submit_action}"):
        back_label = tr(f"back_{submit_action}", dest=dest)
    elif submit_action in FORM_ACTION_SAVES_DATA:
        back_label = tr('back_discard', dest=dest)
    else:
        back_label = tr('back', dest=dest)

    form_action_options = [{'value': 'submit', 'label': submit_label}]
    form_action_options.extend([{'value': action_item, 'label': label}
                                    for action_item, label in (other_actions or {}).items()])
    form_action_options.append({'value': 'back', 'label': back_label})

    return {vol.Required(FORM_ACTION, default=default_action):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=form_action_options, mode='list'))}

def form_action_field(self, actions, default_action):
    '''
    The Action field of a form whose actions are not a Submit/Back pair. The values
    are the action_items, action_text_to_item returns the one selected.

    Parameters:
        actions - {action_item: label}, the last one should leave the form
        default_action - The action_item selected when the form is displayed
    '''
    self.form_submit_action = default_action
    self.form_back_action   = list(actions)[-1]

    return {vol.Required(FORM_ACTION, default=default_action):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=[{'value': action_item, 'label': label}
                                for action_item, label in actions.items()],
                    mode='list'))}

def destination_name(destination):
    return tr(f"dest_{destination}") if has_tr(f"dest_{destination}") else destination

#--------------------------------------------------------------------
def sectioned_schema(self, schema, sections, form_action=None):
    '''
    Build a form with collapsible sections (data_entry_flow.section) from the flat
    schema of all of its fields. The step flattens the section-nested user_input
    with flatten_sections before using it.

    Parameters:
        schema - {vol marker: selector} of the fields
        sections - [(section_key, [field names], expanded)]. The section_key ends with
                SECTION_SUFFIX. The fields that are not in a section are displayed above
                the sections, a field that is not in the schema is skipped.
        form_action - The Submit/Back field (submit_back_field), displayed last

    HA displays the errors of the top level fields only. The error of a field in a
    section is displayed at the top of the section and the section is expanded.
    The section default holds its field defaults. HA fills in a section that was not
    submitted with them.

    self.section_redisplay_input - {field name: value} of the section fields that were
            submitted when the form is displayed again after an error. They are displayed
            instead of the defaults this time.
    '''
    errors = self.errors if isinstance(self.errors, dict) else {}
    redisplay_input = self.__dict__.pop('section_redisplay_input', None) or {}
    schema = {(type(marker)(str(marker), default=redisplay_input[str(marker)])
                    if str(marker) in redisplay_input else marker): value
                for marker, value in schema.items()}
    markers_by_name = {str(marker): marker for marker in schema}
    section_field_names = [name for _key, names, _expanded in sections for name in names]

    form_schema = {marker: value for marker, value in schema.items()
                                 if str(marker) not in section_field_names}

    for section_key, names, expanded in sections:
        section_schema = {markers_by_name[name]: schema[markers_by_name[name]]
                                for name in names if name in markers_by_name}
        if is_empty(section_schema):
            continue

        section_errors = [(name, errors.pop(name)) for name in names if name in errors]
        if section_errors:
            errors.setdefault(section_key, _section_error(self, section_key, section_errors))
            expanded = True

        section_defaults = {str(marker): marker.default()
                                for marker in section_schema
                                if marker.default is not vol.UNDEFINED}
        section_schema = {marker: (_RangeNumberSelector(value.config)
                                        if type(value) is selector.NumberSelector else value)
                                for marker, value in section_schema.items()}
        form_schema[vol.Optional(section_key, default=section_defaults)] = \
                section(vol.Schema(section_schema), {'collapsed': not expanded})

    form_schema.update(form_action or {})

    return vol.Schema(form_schema)

#.....................................................................
def _section_error(self, section_key, section_errors):
    '''
    HA displays one error at the top of a section. It names the fields with an error:
    'Fixed interval: Enter a number'. The text is a description placeholder of the
    section_error_[n] error key (async_show_form adds self.form_placeholders).
    '''
    step_id = getattr(self, 'step_id', '')
    field_errors = []
    for name, error_key in section_errors:
        field_label = tr_path(f"options.step.{step_id}.sections.{section_key}.data.{name}")
        if field_label.startswith('options.'):
            field_label = name
        error_text = tr_path(f"options.error.{error_key}", **(getattr(self, 'errors_info_msg', None) or {}))
        field_errors.append(f"{field_label}: {error_key if error_text.startswith('options.') else error_text}")

    if not hasattr(self, 'form_placeholders') or self.form_placeholders is None:
        self.form_placeholders = {}
    error_no = len([key for key in self.form_placeholders if key.startswith('section_error_')]) + 1
    self.form_placeholders[f"section_error_{error_no}"] = ' · '.join(field_errors)

    return f"section_error_{error_no}"

#.....................................................................
class _RangeNumberSelector(selector.NumberSelector):
    '''
    HA can not map a validation error of a field in a section to the field and displays
    the raw validation message. A number outside the field's range is set to the
    minimum or maximum instead.
    '''
    def __call__(self, data):
        try:
            value = float(data)
        except (TypeError, ValueError):
            return super().__call__(data)

        if self.config.get('min') is not None and value < self.config['min']:
            value = float(self.config['min'])
        if self.config.get('max') is not None and value > self.config['max']:
            value = float(self.config['max'])

        return super().__call__(value)

#--------------------------------------------------------------------
def show_form_placeholders(self, description_placeholders):
    '''
    The description_placeholders of a form with the self.form_placeholders (section
    error texts) and the self.header_placeholders (header message) added. They are used once.
    '''
    form_placeholders = {**(self.__dict__.pop('header_placeholders', None) or {}),
                         **(self.__dict__.pop('form_placeholders', None) or {})}
    if not form_placeholders:
        return description_placeholders
    return {**form_placeholders, **(description_placeholders or {})}

#--------------------------------------------------------------------
def flatten_sections(user_input):
    '''
    Move the fields of the sections (sectioned_schema) to the top level of the user_input.
    The number fields (NumberSelector) return a float, a whole number is changed to an int.
    '''
    if not user_input:
        return user_input

    for section_key in [key for key, value in user_input.items()
                            if key.endswith(SECTION_SUFFIX) and isinstance(value, dict)]:
        user_input.update(user_input.pop(section_key))

    for pname, pvalue in user_input.items():
        if isinstance(pvalue, float) and pvalue.is_integer():
            user_input[pname] = int(pvalue)

    return user_input

#--------------------------------------------------------------------
def section_fields_input(user_input):
    '''
    The {field name: value} of the section fields in the section-nested user_input
    '''
    return {pname: (pvalue.copy() if isinstance(pvalue, list) else pvalue)
                for key, section_input in (user_input or {}).items()
                if key.endswith(SECTION_SUFFIX) and isinstance(section_input, dict)
                for pname, pvalue in section_input.items()}

#--------------------------------------------------------------------
def menu_name(self):
    '''
    The dest_[key] text key (submit_back_field) of the menu the configure screen was
    opened from and returns to
    '''
    menu_id = getattr(self, 'menu_id', '') or 'menu'
    return menu_id if has_tr(f"dest_{menu_id}") else 'menu'

#-------------------------------------------------------------------------------------------
# UNUSED (10/31/2026) - not called anywhere. Commented out, delete after v3.8.0
# def validate_time_str(self, user_input):
#     '''
#     Cycle through the each of the parameters. If it is a time string, check it's
#     value and sec/min/hrs entry
#     '''
#     new_user_input = {}

#     for pname, pvalue in user_input.items():
#         if pname in CONF_PARAMETER_TIME_STR:
#             time_parts  = (f"{pvalue} mins").split(' ')

#             if time_parts[0].strip() == '':
#                 self.errors[pname] = "required_field"
#                 self.errors_user_input[pname] = ''
#                 continue
#             elif is_number(str(time_parts[0])) is False:
#                 self.errors[pname] = "not_numeric"
#                 self.errors_user_input[pname] = user_input[pname]
#                 continue

#             if instr(time_parts[1], 'm'):
#                 pvalue = f"{time_parts[0]} mins"
#             elif instr(time_parts[1], 'h'):
#                 pvalue = f"{time_parts[0]} hrs"
#             elif instr(time_parts[1], 's'):
#                 pvalue = f"{time_parts[0]} secs"
#             else:
#                 pvalue = f"{time_parts[0]} mins"

#             if not self.errors.get(pname):
#                 try:
#                     if float(time_parts[0]) == 1:
#                         pvalue = pvalue.replace('s', '')
#                     new_user_input[pname] = pvalue

#                 except ValueError:
#                     self.errors[pname] = "not_numeric"
#                     self.errors_user_input[pname] = user_input[pname]

#         else:
#             new_user_input[pname] = pvalue

#     return new_user_input

#-------------------------------------------------------------------------------------------
# UNUSED (10/31/2026) - not called anywhere. Commented out, delete after v3.8.0
# def parm_with_example_text(config_parameter, input_select_list_KEY_TEXT):
#     '''
#     The input_select_list for the parameter has an example text '(Example: exampletext)'
#     as part of list of options display for user selection. The exampletext is not part
#     of the configuration parameter. Dydle through the input_select_list and determine which
#     one should be the default value.

#     Return:
#         default - The input_select item to be used for the default value
#     '''
#     for isli_with_example in input_select_list_KEY_TEXT:
#         if isli_with_example.startswith(Gb.conf_general[config_parameter]):
#             return isli_with_example

#     return input_select_list_KEY_TEXT[0]

#--------------------------------------------------------------------

#--------------------------------------------------------------------
# UNUSED (10/31/2026) - not called anywhere. Commented out, delete after v3.8.0
# def discard_changes(user_input):
#     '''
#     See if user_input 'action_item' item has a 'discard_change' option
#     selected. Discard changes is the last item in the list.
#     '''
#     if user_input:
#         return (user_input.get('action_item') == default_action_text('cancel_goto_menu'))
#     else:
#         return False

#--------------------------------------------------------------------
def log_step_info(self, user_input, action_item=None, subtitle=''):


    log_stack_pgm, log_stack_fct = _get_log_stack_info()

    # The password is logged before the step adds it to the log file filter
    if isinstance(user_input, dict) and user_input.get(CONF_PASSWORD):
        user_input = {**user_input, CONF_PASSWORD: '********'}

    info_msg =( f"⭐ {self.step_id.upper()} {subtitle.upper()} "
                f"({action_item}/{self.menu_item}) {log_stack_fct}> "
                f"UserInput-{user_input}, Errors-{self.errors}")

    if Gb.is_log_level_debug:
        log_debug_msg(info_msg, log_stack_pgm=log_stack_pgm)
    else:
        log_info_msg(info_msg)

#.................................................................................
def _get_log_stack_info():
    '''
    Review the log_stack and return the calling program and function:line
    '''

    if Gb.is_log_level_debug is False:
        return '', ''

    # log_stack_data=configure/screens/step_icloud3_device.py, 98, async_step_device_list'
    log_stack_data = log_stack(return_cnt=1)
    log_stack_data = log_stack_data.replace(' ', '')

    filename, line_no, fct = log_stack_data.split(',')
    line_no = int(line_no)
    filename = filename.split('/')[-1][:-3]
    filename = filename.replace('step_', 'cf:')
    filename = filename.replace('form_', 'cf:')
    filename = filename.replace('icloud3', 'ic3')
    # filename = filename.replace('apple_acct', 'aa')
    if len(filename) < 14: filename += '…'*14
    log_stack_pgm = f"[{filename[:14]}:{line_no:04d}] "

    fct      = fct.replace('async_step_', '')
    log_stack_fct = f"[{fct[:12]}:{line_no:04d}] "

    return log_stack_pgm, log_stack_fct