

from ..global_variables  import GlobalVariables as Gb
from ..const             import (DEVICE_TYPE_FNAME, CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE,
                                CONF_PARAMETER_TIME_STR, CONF_PARAMETER_FLOAT,
                                CF_PROFILE, CF_TRACKING, CF_GENERAL,
                                )

from ..utils.utils     import (instr, is_number, is_empty, isnot_empty,
                                encode_password, decode_password, )
from ..utils.messaging import (log_exception, log_debug_msg, log_info_msg, add_log_file_filter,
                                _log, _evlog, )

from .const_form_lists   import (MENU_KEY_TEXT, ACTION_LIST_ITEMS_KEY_BY_TEXT, ACTION_LIST_OPTIONS,
                                UNKNOWN_DEVICE_TEXT, DATA_ENTRY_ALERT, DATA_ENTRY_ALERT_CHAR, )

VALID_ERROR_MSG = [ 'conf_updated',
                    'internet_error',
                    'internet_error_no_change']

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                      MISCELLANEOUS UTILITY FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def any_errors(self):
    return (isnot_empty(self.errors)
                and self.errors.get('base') not in VALID_ERROR_MSG)

#--------------------------------------------------------------------
def menu_text_to_item(self, user_input, selection_list):
    '''
    Convert the text of the menu item selected to it's key name.

    selection_list - Field name in user_input to use:
        ''menu_item' 'menu_action_item'
    '''

    if user_input is None:
        return None, None

    selected_text = None
    if selection_list in user_input:
        selected_text = user_input[selection_list]
        selected_text_len = 35 if len(selected_text) > 35 else len(selected_text)
        menu_item = [k for k, v in MENU_KEY_TEXT.items() if v.startswith(selected_text[:selected_text_len])][0]

        user_input.pop(selection_list)
    else:
        menu_item = self.menu_item_selected

    return user_input, menu_item

#--------------------------------------------------------------------
def set_header_msg(self):
    '''
    See if any header messages need to be displayed. If so set the self.errors['base']
    '''
    if self.header_msg:
        if self.errors is None: self.errors = {}
        self.errors['base'] = self.header_msg
        self.header_msg = None

#--------------------------------------------------------------------
def strip_spaces(user_input, parm_list=[]):
    '''
    Remove leading or trailing spaces from items in the parameter list

    '''
    parm_list = [pname  for pname, pvalue in user_input.items()
                            if type(pvalue) is str and pvalue != '']

    for parm in parm_list:
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
    Convert the text of the item selected to it's key name.
    '''

    if user_input is None:
        return None, None

    action_text = None
    if 'action_item' in user_input:
        action_item = user_input['action_item']
        user_input.pop('action_item')

    elif 'action_items' in user_input:
        action_text = user_input['action_items']
        user_input.pop('action_items')

    else:
        return user_input, None

    action_item = ACTION_LIST_ITEMS_KEY_BY_TEXT.get(action_text)

    # Action item was not found in the list of action items and may include
    # special text updated at run time. The special text iss inserted by replacing
    # a text string starting with a ^. Cycle back through the action items looking
    # for one that starts with the text before the ^.
    if action_item is None:
        action_item = [action_item_key
                        for action_item_key, action_item_text in ACTION_LIST_OPTIONS.items()
                        if action_text.startswith(action_item_text[:action_item_text.find('^')])]

        if isnot_empty(action_item):
            action_item = action_item[0]
        else:
            action_item = 'cancel_goto_menu'
            self.base = 'unknown_action'

    if action_item == 'cancel_goto_menu':
        self.header_msg = None

    return user_input, action_item

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
    # Example: [data][general][tracking][username]
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
            parm_displayed = DEVICE_TYPE_FNAME(parm_displayed)
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

        else:
            pvalue_key = Gb.conf_general[pname]

        if type(pvalue_key) in [float, int, str]:
            return option_list_key_text[pvalue_key]

        elif type(pvalue_key) is list:
            return [option_list_key_text[pvalue_key_item] for pvalue_key_item in pvalue_key]

        return option_list_key_text.values()[0]

    except Exception as err:
        log_exception(err)
        # If the parameter value is already the key to the items dict, it is ok.
        if pvalue_key not in option_list_key_text:
            if pname == CONF_FAMSHR_DEVICENAME:
                self.errors[pname] = 'unknown_icloud'
            elif pname == CONF_MOBILE_APP_DEVICE:
                self.errors[pname] = 'unknown_mobapp'
            else:
                self.errors[pname] = 'unknown_value'

        return f"{pvalue_key} {DATA_ENTRY_ALERT}Unknown Selection"

#-------------------------------------------------------------------------------------------
def key_text_to_text_list(key_text):
    return [text for text in key_text.values()]

#-------------------------------------------------------------------------------------------
def option_text_to_parm(user_input, pname, option_list_key_text):
    '''
    user_input contains the full text of the option list item selected. Replace it with
    the actual parameter value for the item selected.
    '''
    try:
        pvalue_text = '_'
        if user_input is None:
            return None
        if pname not in user_input:
            return user_input

        pvalue_text = user_input[pname]

        # Handle special text added to the end of the key_list
        pvalue_text = pvalue_text.replace(UNKNOWN_DEVICE_TEXT, '')

        # if pvalue_text in ['', '.']:
        #     self.errors[pname] = 'required_field'

        pvalue_key = [k for  k, v in option_list_key_text.items() if v == pvalue_text]
        pvalue_key = pvalue_key[0] if pvalue_key else pvalue_text

        user_input[pname] = pvalue_key

    except:
        pass
        # If the parameter value is already the key to the items dict, it is ok.
        # if pvalue_text not in option_list_key_text:
        #     self.errors[pname] = 'invalid_value'

    return  user_input

#-------------------------------------------------------------------------------------------
def convert_field_str_to_numeric(user_input):
    '''
    Config_flow chokes with malformed input errors when a field is numeric. To avoid this,
    the field's default value is always a string. This converts it back to a float.
    '''
    for pname, pvalue in user_input.items():
        if pname in CONF_PARAMETER_FLOAT:
            user_input[pname] = float(pvalue)

    return user_input

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

#-------------------------------------------------------------------------------------------
def validate_time_str(self, user_input):
    '''
    Cycle through the each of the parameters. If it is a time string, check it's
    value and sec/min/hrs entry
    '''
    new_user_input = {}

    for pname, pvalue in user_input.items():
        if pname in CONF_PARAMETER_TIME_STR:
            time_parts  = (f"{pvalue} mins").split(' ')

            if time_parts[0].strip() == '':
                self.errors[pname] = "required_field"
                self.errors_user_input[pname] = ''
                continue
            elif is_number(str(time_parts[0])) is False:
                self.errors[pname] = "not_numeric"
                self.errors_user_input[pname] = user_input[pname]
                continue

            if instr(time_parts[1], 'm'):
                pvalue = f"{time_parts[0]} mins"
            elif instr(time_parts[1], 'h'):
                pvalue = f"{time_parts[0]} hrs"
            elif instr(time_parts[1], 's'):
                pvalue = f"{time_parts[0]} secs"
            else:
                pvalue = f"{time_parts[0]} mins"

            if not self.errors.get(pname):
                try:
                    if float(time_parts[0]) == 1:
                        pvalue = pvalue.replace('s', '')
                    new_user_input[pname] = pvalue

                except ValueError:
                    self.errors[pname] = "not_numeric"
                    self.errors_user_input[pname] = user_input[pname]

        else:
            new_user_input[pname] = pvalue

    return new_user_input

#-------------------------------------------------------------------------------------------
def parm_with_example_text(config_parameter, input_select_list_KEY_TEXT):
    '''
    The input_select_list for the parameter has an example text '(Example: exampletext)'
    as part of list of options display for user selection. The exampletext is not part
    of the configuration parameter. Dydle through the input_select_list and determine which
    one should be the default value.

    Return:
        default - The input_select item to be used for the default value
    '''
    for isli_with_example in input_select_list_KEY_TEXT:
        if isli_with_example.startswith(Gb.conf_general[config_parameter]):
            return isli_with_example

    return input_select_list_KEY_TEXT[0]

#--------------------------------------------------------------------
def action_default_text(action_item, action_OPTIONS=None):
    if action_OPTIONS:
        return action_OPTIONS.get(action_item, 'UNKNOWN ACTION > Unknown Action')
    else:
        return ACTION_LIST_OPTIONS.get(action_item, 'UNKNOWN ACTION - Unknown Action')

#--------------------------------------------------------------------
def discard_changes(user_input):
    '''
    See if user_input 'action_item' item has a 'discard_change' option
    selected. Discard changes is the last item in the list.
    '''
    if user_input:
        return (user_input.get('action_item') == action_default_text('cancel_goto_menu'))
    else:
        return False

#--------------------------------------------------------------------
def log_step_info(self, user_input, action_item=None):

    log_info_msg(  f"🔸{self.step_id.upper()} ({action_item}) > "
                    f"UserInput-{user_input}, Errors-{self.errors}")
