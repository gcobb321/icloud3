
from ..global_variables     import GlobalVariables as Gb
from ..const                import (CRLF_DOT,  )
from .common                import (instr, is_empty, isnot_empty, list_to_str, )
from .messaging             import (log_exception, _evlog, _log, )

from collections            import OrderedDict
from homeassistant.util     import json as json_util
from homeassistant.helpers  import json as json_helpers
import os
import shutil
import asyncio
import logging
_LOGGER = logging.getLogger(__name__)
#_LOGGER = logging.getLogger(f"icloud3")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            JSON FILE UTILITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_read_json_file(filename):

    if file_exists(filename) is False:
        return {}

    try:
        data = await Gb.hass.async_add_executor_job(
                            json_util.load_json,
                            filename)
        return data

    except Exception as err:
        #_LOGGER.exception(err)
        pass

    return {}

#--------------------------------------------------------------------
def read_json_file(filename):

    if file_exists(filename) is False:
        return {}

    try:
        if Gb.initial_icloud3_loading_flag:
            data = json_util.load_json(filename)
        else:
            data = Gb.hass.async_add_executor_job(
                            json_util.load_json,
                            filename)
        return data

    except RuntimeError as err:
        if str(err) == 'no running event loop':
            data = json_util.load_json(filename)
            return data

    except Exception as err:
        _LOGGER.exception(err)
        pass

    return {}

#--------------------------------------------------------------------
async def async_save_json_file(filename, data):

    try:
        await Gb.hass.async_add_executor_job(
                            json_helpers.save_json,
                            filename,
                            data)
        return True

    except Exception as err:
        _LOGGER.exception(err)
        pass

    return False

#--------------------------------------------------------------------
def save_json_file(filename, data):
    try:
        # The HA event loop has not been set up yet during initialization
        json_helpers.save_json(filename, data)
        return True

    except Exception as err:
        _LOGGER.exception(err)
        pass

    return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            PYTHON OS. FILE I/O AND OTHER UTILITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def file_exists(filename):
    return _os(os.path.exists, filename)

def delete_file(filename):
    try:
        return _os(os.remove, filename)
    except FileNotFoundError:
        pass
    except Exception as err:
        log_exception(err)

def copy_file(from_dir_filename, to_directory):
    shutil.copy(from_dir_filename, to_directory)

def move_files(from_dir_filename, to_directory):
    shutil.move(from_dir_filename, to_directory)

def file_size(filename):
    try:
        return _os(os.path.getsize, filename)
    except FileNotFoundError:
        pass
    except Exception as err:
        log_exception(err)
    return 0

def extract_filename(directory_filename):
    return _os(os.path.basename, directory_filename)


def directory_exists(dir_name):
    return _os(os.path.exists, dir_name)

def make_directory(dir_name):
    if directory_exists(dir_name) is False:
        _os(os.makedirs, dir_name)

#--------------------------------------------------------------------
def rename_file(from_filename, to_filename):
    if file_exists(from_filename) is False:
        return
    if file_exists(to_filename):
        delete_file(to_filename)

    os.rename(from_filename, to_filename)

#--------------------------------------------------------------------
def _os(os_module, filename):
    results = os_module(filename)
    return results

#--------------------------------------------------------------------
def is_event_loop_running():
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False
    except Exception as err:
        log_exception(err)
    return False

def is_event_loop_running2():
    if asyncio.get_event_loop_policy()._local._loop:
        return True
    return False

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            PYTHON ASYNC OS. FILE I/O AND OTHER UTILITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

async def async_file_exists(filename):
    return await Gb.hass.async_add_executor_job(os.path.isfile, filename)

async def async_delete_file(filename):
    try:
        return await Gb.hass.async_add_executor_job(os.remove, filename)
    except FileNotFoundError:
        pass
    except Exception as err:
        log_exception(err)

async def async_copy_file(from_dir_filename, to_directory):
    return await Gb.hass.async_add_executor_job(shutil.copy, from_dir_filename, to_directory)

async def async_file_size(filename):
    return await Gb.hass.async_add_executor_job(os.path.getsize, filename)

async def async_extract_filename(directory_filename):
    return await Gb.hass.async_add_executor_job(os.path.basename, directory_filename)

async def async_rename_file(from_filename, to_filename):
    if await async_file_exists(from_filename) is False:
        return
    if await async_file_exists(to_filename):
        await async_delete_file(to_filename)
    return await Gb.hass.async_add_executor_job(os.rename, from_filename, to_filename)


async def async_directory_exists(dir_name):
    return await Gb.hass.async_add_executor_job(os.path.exists, dir_name)

async def async_make_directory(dir_name):
    _directory_exists = await async_directory_exists(dir_name)
    if _directory_exists is False:
        exist_ok = True
        await Gb.hass.async_add_executor_job(os.makedirs, dir_name, exist_ok)

async def async_delete_directory(dir_name):
    try:
        return await Gb.hass.async_add_executor_job(os.rmdir, dir_name)
    except FileNotFoundError:
        pass
    except Exception as err:
        log_exception(err)

#...................................................................
async def async_os(os_module, filename):
    return await Gb.hass.async_add_executor_job(os_module, filename)

#--------------------------------------------------------------------
async def async_delete_file_with_msg(file_desc, directory, filename, backup_extn=None, delete_old_sv_file=False):
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

            if file_exists(directory_filename_bu):
                delete_file(directory_filename_bu)
                file_msg += (f"{CRLF_DOT}Deleted backup file (...{filename_bu})")

            rename_file(directory_filename, directory_filename_bu)
            file_msg += (f"{CRLF_DOT}Rename current file to ...{filename}.{backup_extn})")

        if file_exists(directory_filename):
            delete_file(directory_filename)
            file_msg += (f"{CRLF_DOT}Deleted file (...{filename})")

        if delete_old_sv_file:
            filename = f"{filename.split('.')[0]}.sv"
            directory_filename = f"{directory_filename.split('.')[0]}.sv"
            if file_exists(directory_filename):
                delete_file(directory_filename)
                file_msg += (f"{CRLF_DOT}Deleted file (...{filename})")

        if file_msg != "":
            if instr(directory, 'config'):
                directory = f"config{directory.split('config')[1]}"
            file_msg = f"{file_desc} file > ({directory}) {file_msg}"

        return file_msg

    except Exception as err:
        Gb.HALogger.exception(err)
        return "Delete error"


#--------------------------------------------------------------------
def get_directory_filename_list(start_dir=None,  file_extn_filter=[]):
    return get_file_or_directory_list(  list_type=0,
                                        start_dir=start_dir,
                                        file_extn_filter=file_extn_filter)

def get_directory_list(start_dir=None):
    return get_file_or_directory_list(  list_type=1,
                                        start_dir=start_dir,
                                        file_extn_filter=[])

def get_file_list(list_type=None, start_dir=None,  file_extn_filter=[]):
    return get_file_or_directory_list(  list_type,
                                        start_dir=start_dir,
                                        file_extn_filter=file_extn_filter)

def get_filename_list(start_dir=None,  file_extn_filter=[]):
    return get_file_or_directory_list(  list_type=2,
                                        start_dir=start_dir,
                                        file_extn_filter=file_extn_filter)

#--------------------------------------------------------------------
def get_file_or_directory_list(list_type=None, start_dir=None,  file_extn_filter=[]):
    '''
    Return a list of directories or files in a given path

    Parameters:
        - list_type      = 0 - Directory/filename list (Default)
        - list_type      = 1 - Directory/subdirectory list
        - list_type      = 2 - Filename list
        - start_dir      = Top level directory to start searching from ('www')
        -file_extn_filter = List of files witn extensions to include (['png' 'jpg'], [])

        Can call from executor function:
        directory_list, start_dir, file_filter = [False, 'www', ['png', 'jpg', 'jpeg']]
        image_filenames = await Gb.hass.async_add_executor_job(
                                                    self.get_file_or_directory_list,
                                                    directory_list,
                                                    start_dir,
                                                    file_filter)
    '''
    if list_type is None: list_type = 0
    back_slash       = '\\'
    directory_filter      = ['/.', 'deleted', '/x-']
    filename_or_directory_list = []
    path_config_base = f"{Gb.ha_config_directory}/"
    start_dir = start_dir.replace(path_config_base, '')
    file_extn_filter_str = list_to_str(file_extn_filter, '.')
    if start_dir is None: start_dir = ''

    try:
        for path, dirs, files in os.walk(f"{path_config_base}{start_dir}"):
            sub_directory = path.replace(path_config_base, '')
            in_filter_cnt = len([filter for filter in directory_filter if instr(sub_directory, filter)])
            if in_filter_cnt > 0 or sub_directory.count('/') > 4 or sub_directory.count(back_slash):
                continue

            # list_type=1 - Directory/subdirectory list
            if list_type == 1:
                filename_or_directory_list.append(sub_directory)
                continue

            # Filter unwanted directories - std dirs are www/icloud3, www/community, www/images
            if start_dir.endswith('/event_log_card/'):
                pass
            elif start_dir == 'www' and Gb.picture_www_dirs:
                valid_dir = [dir for dir in Gb.picture_www_dirs if sub_directory.endswith(dir)]
                if valid_dir == []:
                    continue

            # list_type=2 - filename only, does not contain directory name
            dir_name =  '' if list_type == 2 else f"{sub_directory}/"
            dir_name = dir_name.replace('//', '/')
            dir_filenames = [f"{dir_name}{file}"
                                    for file in files
                                    if (is_empty(file_extn_filter)
                                        or file.rsplit('.', 1)[-1] in file_extn_filter)]
                                    # if (file_extn_filter_str == ''
                                    #     or instr(file.rsplit('.', 1)[-1], file_extn_filter))]

            filename_or_directory_list.extend(dir_filenames[:25])
            if len(dir_filenames) > 25:
                filename_or_directory_list.append(
                            f"⛔ {sub_directory} > The first 25 files out of "
                            f"{len(dir_filenames)} are listed")

        return filename_or_directory_list

    except Exception as err:
        Gb.HALogger.exception(err)