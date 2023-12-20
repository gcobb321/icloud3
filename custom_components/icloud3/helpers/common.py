

from ..global_variables import GlobalVariables as Gb
from ..const            import (NOT_HOME, STATIONARY, CIRCLE_LETTERS_DARK, UNKNOWN, CRLF_DOT, CRLF, )
from collections        import OrderedDict
import os

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DATA VERIFICATION FUNCTIONS
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
    separator_str = separator if separator else ', '
    list_str = separator_str.join(list_value)

    if separator_str.startswith(CRLF):
        return f"{separator_str}{list_str}"
    else:
        return list_str

#--------------------------------------------------------------------
def list_add(list_value, add_value):
    if add_value not in list_value:
        list_value.append(add_value)
    return list_value

#--------------------------------------------------------------------
def list_del(list_value, del_value):
    if del_value in list_value:
        list_value.remove(del_value)
    return list_value

#--------------------------------------------------------------------
def str_to_list(str_value):
    '''
    Create a list of a comma separated strings
    str_value   - ('icloud,iosapp')
    Return      - ['icloud','iosapp']
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
def instr(string, substring):
    '''
    Fine a substring or a list of substrings strings in a string
    '''
    if string is None or substring is None:
        return False

    if type(substring) is str:
        substring = [substring]

    for substring_str in substring:
        if str(string).find(substring_str) >= 0:
            return True
    return False

#--------------------------------------------------------------------
def is_statzone(zone):
    return instr(zone, STATIONARY)

#--------------------------------------------------------------------
def isnot_statzone(zone):
    return instr(zone, STATIONARY) is False

#--------------------------------------------------------------------
def isnumber(string):

    try:
        test_number = float(string)

        return True

    except:
        return False

#--------------------------------------------------------------------
def isbetween(number, greater_than, less_than_equal):
    return (less_than_equal > number > greater_than)

#--------------------------------------------------------------------
def inlist(string, list_items):
    for item in list_items:
        if str(string).find(item) >= 0:
            return True

    return False

#--------------------------------------------------------------------
def round_to_zero(value):
    if abs(value) < .0001: value = 0
    return round(value, 8)
#-------------------------------------------------------------------------------------------
def set_precision(value, um=None):
    '''
    Return the distance value as an integer or float value
    '''
    try:
        um = um if um else Gb.um
        precision = 5 if um in ['km', 'mi'] else 2 if um in ['m', 'ft'] else 4
        value = round(float(value), precision)
        if value == int(value):
            return int(value)

    except Exception as err:
        pass

    return value

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
    return CIRCLE_LETTERS_DARK.get(first_letter, '✪')

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
def zone_display_as(zone):
    if is_statzone(zone) and zone not in Gb.zone_display_as:
        return 'StatZone'
    return Gb.zone_display_as.get(zone, zone.title())

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
def format_cnt(desc, n):
    return f", {desc}(#{n})" if n > 1 else ''

#--------------------------------------------------------------------
def delete_file(file_desc, directory, filename, backup_extn=None, delete_old_sv_file=False):
    '''
    Delete a file.
    Parameters:
        directory   - directory containing the file to be deleted
        filename    - file to be deleted
        backup_extn - rename the filename to this extension before deleting
        delete_old_sv_file - Some files were previously renamed to .sv before deleting
                    They should be deleted if they exist.
    '''
    try:
        file_msg = ""
        directory_filename = (f"{directory}/{filename}")

        if backup_extn:
            filename_bu = f"{filename.split('.')[0]}.{backup_extn}"
            directory_filename_bu = (f"{directory}/{filename_bu}")

            if os.path.isfile(directory_filename_bu):
                os.remove(directory_filename_bu)
                file_msg += (f"{CRLF_DOT}Deleted backup file (...{filename_bu})")

            os.rename(directory_filename, directory_filename_bu)
            file_msg += (f"{CRLF_DOT}Rename current file to ...{filename}.{backup_extn})")

        if os.path.isfile(directory_filename):
            os.remove(directory_filename)
            file_msg += (f"{CRLF_DOT}Deleted file (...{filename})")

        if delete_old_sv_file:
            filename = f"{filename.split('.')[0]}.sv"
            directory_filename = f"{directory_filename.split('.')[0]}.sv"
            if os.path.isfile(directory_filename):
                os.remove(directory_filename)
                file_msg += (f"{CRLF_DOT}Deleted file (...{filename})")

        if file_msg != "":
            if instr(directory, 'config'):
                directory = f"config{directory.split('config')[1]}"
            file_msg = f"{file_desc} file > ({directory}) {file_msg}"
            # Gb.EvLog.post_event(event_msg)

        return file_msg

    except Exception as err:
        Gb.HALogger.exception(err)
        return "Delete error"
