

from ..global_variables import GlobalVariables as Gb
from ..const            import (NOT_HOME, STATIONARY,
                                CIRCLE_LETTERS_DARK, CIRCLE_LETTERS_LITE,
                                UNKNOWN, CRLF_DOT, CRLF,
                                CONF_USERNAME, CONF_PASSWORD, )
from collections        import OrderedDict
# from homeassistant.util import json as json_util
# from homeassistant.helpers import json as json_helpers
# import os
# import json
import base64
import logging
_LOGGER = logging.getLogger(__name__)
#_LOGGER = logging.getLogger(f"icloud3")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DICTION & LIST UTILITY FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def combine_lists(parm_lists):
    '''
    Take a list of lists and return a single list of all of the items.
        [['a,b,c'],['d,e,f']] --> ['a','b','c','d','e','f']
    '''
    new_list = []
    for lists in parm_lists:
        lists_items = lists.split(',')
        for lists_item in lists_items:
            new_list.append(lists_item)

    return new_list

#--------------------------------------------------------------------
def list_to_str(list_value, separator=None):
    '''
    Convert list values into a string

    list_valt - list to be converted
    separator - Strig valut that separates each item (default = ', ')
    '''
    if list_value == [] or list_value is None: return ''

    separator_str = separator if separator else ', '
    list_value = [lv.strip() for lv in list_value if lv is not None and lv != '']

    list_str = separator_str.join(list_value) if list_value else 'None'

    if separator_str.startswith(CRLF):
        return f"{separator_str}{list_str}"
    else:
        return list_str

#--------------------------------------------------------------------
def list_add(list_value, add_value):
    if add_value is None:
        return list_value

    if type(add_value) is list:
        for add_item in add_value:
            if add_item not in list_value:
                list_value.append(add_item)
        return list_value

    if add_value not in list_value:
        list_value.append(add_value)
    return list_value

#--------------------------------------------------------------------
def list_del(list_value, del_value):
    if del_value in list_value:
        list_value.remove(del_value)
    return list_value

#--------------------------------------------------------------------
def list_keys(list_value):
    return list(list_value.keys())

#--------------------------------------------------------------------
def str_to_list(str_value):
    '''
    Create a list of a comma separated strings
    str_value   - ('icloud,mobapp')
    Return      - ['icloud','mobapp']
    '''

    while instr(str_value,', '):
        str_value = str_value.replace( ', ', ',')

    return str_value.split(',')

#--------------------------------------------------------------------
def delete_from_list(list_value, item):
    if item in list_value:
        list_value.remove(item)

    return list_value

#--------------------------------------------------------------------
def sort_dict_by_values(dict_value):
    '''
    Return a dictionary sorted by the item values
    '''
    if (type(dict_value) is not dict
            or dict_value == {}):
        return {}

    dict_value_lower        = {k: v.lower() for k, v in dict_value.items()}
    sorted_dict_value_lower = sorted(dict_value_lower.items(), key=lambda x:x[1])
    keys_sorted_dict_value_lower = dict(sorted_dict_value_lower).keys()
    sorted_dict_value       = {k: dict_value[k] for k in keys_sorted_dict_value_lower}

    return sorted_dict_value

#-----------------------------------------------------------------------------------------
def dict_value_to_list(key_value_dict):
    """ Make a list from a dictionary's values  """

    if type(key_value_dict) is dict:
        value_list = [v for v in key_value_dict.values()]
    else:
        value_list = list(key_value_dict)

    return value_list


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DATA VERIFICATION FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def instr(string, substring):
    '''
    Find a substring or a list of substrings strings in a string
    '''
    if type(substring) is str:
        try:
            return substring in string
        except:
            return False

    if string is None or substring is None:
        return False

    # Is a list of substrings in the string
    if type(substring) is list:
        for substring_item in substring:
            if substring_item in string:
                return True

    return False

#--------------------------------------------------------------------
def is_statzone(zone):
    return instr(zone, STATIONARY)

#--------------------------------------------------------------------
def isnot_statzone(zone):
    return (instr(zone, STATIONARY) is False)

#--------------------------------------------------------------------
def is_number(string):

    try:
        test_number = float(string)

        return True

    except:
        return False

#--------------------------------------------------------------------
def yes_no(true_false):
    if true_false:
        return 'Yes'
    else:
        return 'No'

#--------------------------------------------------------------------
def isbetween(number, min_value, max_value):
    '''
    Return True if the the number is between the other two numbers
    including the min_value and max_value number)
    '''
    return (max_value+1 > number > min_value-1)

#--------------------------------------------------------------------
def inlist(string, list_items):
    for item in list_items:
        if str(string).find(item) >= 0:
            return True

    return False

#--------------------------------------------------------------------
def is_empty(list_dict_str):
    if list_dict_str is None:
        return True
    return not list_dict_str

def isnot_empty(list_dict_str):
    return not is_empty(list_dict_str)

#--------------------------------------------------------------------
def round_to_zero(number):
    if is_number(number) is False:
        return number

    int_number = int(number*100000000)
    if int(int_number) == 0:
        return 0.0

    return int_number/100000000

#--------------------------------------------------------------------
def is_zone(zone):
    return (zone != NOT_HOME)

#--------------------------------------------------------------------
def isnot_zone(zone):
    return (zone == NOT_HOME)

#--------------------------------------------------------------------
def ordereddict_to_dict(odict_item):
    if isinstance(odict_item, OrderedDict):
        dict_item = dict(odict_item)
    else:
        dict_item = odict_item
    try:
        for key, value in dict_item.items():
            dict_item[key] = ordereddict_to_dict(value)
            if isinstance(value, list):
                new_value = []
                for item in value:
                    if isinstance(item, OrderedDict):
                        item = ordereddict_to_dict(item)
                    new_value.append(item)
                dict_item[key] = new_value
    except AttributeError:
        pass

    return dict_item

#--------------------------------------------------------------------
def circle_letter(field):
    first_letter = field[:1].lower()
    # return CIRCLE_LETTERS_DARK.get(first_letter, '✪')
    return CIRCLE_LETTERS_LITE.get(first_letter, '✪')

#--------------------------------------------------------------------
def obscure_field(field):
    '''
    An obscured field is one where the first and last 2-characters are kept and the others
    are replaced by a string of periods to hide it's actual value. This is used for usernames
    and passwords. (geekstergary@gmail.com --> ge..........ry@gm.....om))

    Input:
        Field to be obscurred

    Return:
        The obscured field
    '''
    if field == '' or field is None:
        return ''

    if instr(field, '@'):
        # 12/19/2022 (beta 3)-An error was generated if there was more than 1 @-sign in the email field
        field_parts   = field.split('@')
        email_name    = field_parts[0]
        email_domain  = field_parts[1]
        obscure_field = (   f"{email_name[0:2]}{'.'*(len(email_name)-2)}@"
                            f"{email_domain[0:2]}{'.'*(len(email_domain)-2)}")
        return obscure_field

    obscure_field = (f"{field[0:2]}{'.'*(len(field)-2)}")
    return obscure_field

#--------------------------------------------------------------------
def zone_dname(zone):
    try:
        return Gb.zones_dname[zone]
    except:
        if zone in Gb.Zones_by_zone:
            Zone = Gb.Zones_by_zone[zone]
            Gb.zones_dname[zone] = Zone.dname
        elif is_statzone(zone):
            Gb.zones_dname[zone] = f"StatZone{zone[-1]}"
        else:
            Gb.zones_dname[zone] = zone.title()
        return Gb.zones_dname[zone]

#--------------------------------------------------------------------
def zone_display_as(zone):
    if is_statzone(zone) and zone not in Gb.zones_dname:
        return 'StatZone'
    return Gb.zones_dname.get(zone, zone.title())

#--------------------------------------------------------------------
def format_gps(latitude, longitude, accuracy, latitude_to=None, longitude_to=None):
    '''Format the GPS string for logs & messages'''

    if longitude is None or latitude is None:
        gps_text = UNKNOWN

    # elif Gb.display_gps_lat_long_flag is False:
    #     gps_text     = f"/±{accuracy:.0f}m"

    else:
        accuracy_text = (f"/±{accuracy:.0f}m)") if accuracy > 0 else ")"
        gps_to_text   = (f" to {latitude_to:.5f}, {longitude_to:.5f})") if latitude_to else ""
        gps_text      = f"({latitude:.5f}, {longitude:.5f}{accuracy_text}{gps_to_text}"

    return gps_text

#--------------------------------------------------------------------
def format_list(arg_list):
    formatted_list = str(arg_list)
    formatted_list = formatted_list.replace("[", "").replace("]", "")
    formatted_list = formatted_list.replace("{", "").replace("}", "")
    formatted_list = formatted_list.replace("'", "").replace(",", f"{CRLF_DOT}")

    return (f"{CRLF_DOT}{formatted_list}")

#--------------------------------------------------------------------
def strip_lead_comma(text):
    '''
    Strip a leading special character from a text string
    '''
    if text[:1] in [',', '+']:
        return text[1:].strip()
    else:
        return text.strip()

#--------------------------------------------------------------------
def username_id(username):
    username_base = f"{username}@".split('@')[0]

    if username_base in Gb.upw_filter_items:
        return Gb.upw_filter_items[username_base]
    else:
        return f"{username_base}@"

#--------------------------------------------------------------------
def format_cnt(desc, n):
    return f", {desc}(#{n})" if n > 1 else ''


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            PASSWORD ENCODE/DECODE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def encode_password(password):
    '''
    Determine if the password is encoded.

    Return:
        Decoded password
    '''
    try:
        if (password == '' or Gb.encode_password_flag is False):
            return password

        return f"««{base64_encode(password)}»»"

    except Exception as err:
        #log_exception(err)
        password = password.replace('«', '').replace('»', '')
        return password

def base64_encode(string):
    """
    Encode the string via base64 encoder
    """
    # encoded = base64.urlsafe_b64encode(string)
    # return encoded.rstrip("=")

    try:
        string_bytes = string.encode('ascii')
        base64_bytes = base64.b64encode(string_bytes)
        return base64_bytes.decode('ascii')

    except Exception as err:
        #log_exception(err)
        password = password.replace('«', '').replace('»', '')
        return password


#--------------------------------------------------------------------
def decode_password(password):
    '''
    Determine if the password is encoded.

    Return:
        Decoded password
    '''
    try:
        # If the password in the configuration file is not encoded (no '««' or '»»')
        # and it should be encoded, save the configuration file which will encode it
        if (Gb.encode_password_flag
                and password != ''
                and (password.startswith('««') is False
                    or password.endswith('»»') is False)):
            password = password.replace('«', '').replace('»', '')
            Gb.conf_tracking[CONF_PASSWORD] = password
            #write_icloud3_configuration_file()

        # Decode password if it is encoded and has the '««password»»' format
        if (password.startswith('««') or password.endswith('»»')):
            password = password.replace('«', '').replace('»', '')
            return base64_decode(password)

    except Exception as err:
        _LOGGER.exception(err)
        password = password.replace('«', '').replace('»', '')

    return password

def base64_decode(string):
    """
    Decode the string via base64 decoder
    """

    base64_bytes = string.encode('ascii')
    string_bytes = base64.b64decode(base64_bytes)
    return string_bytes.decode('ascii')

#--------------------------------------------------------------------
def is_running_in_event_loop():
    """
    Checks if the current function is being executed within an asyncio event loop.
    """
    import asyncio
    try:
        asyncio.get_running_loop()
        return True
    except: # RuntimeError:
        return False

    return False
    
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            CONFIG_FLOW FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def six_item_list(list_item):
    if len(list_item) >= 6: return list_item

    for i in range(6 - len(list_item)):
        list_item.append('.')

    return list_item

#-----------------------------------------------------------------------------------------
def six_item_dict(dict_item):
    if len(dict_item) >= 6: return dict_item

    dummy_key = ''
    for i in range(6 - len(dict_item)):
        dummy_key += '.'
        dict_item[dummy_key] = '.'

    return dict_item
