
from ..global_variables     import GlobalVariables as Gb
from ..const                import (CRLF_DOT,  )
from .common                import (instr, )
from .messaging             import (log_exception, _trace, _traceha, )

from collections            import OrderedDict
from homeassistant.util     import json as json_util
from homeassistant.helpers  import json as json_helpers
import os
import asyncio
import aiofiles.ospath
import logging
_LOGGER = logging.getLogger(__name__)
#_LOGGER = logging.getLogger(f"icloud3")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            JSON FILE UTILITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_load_json_file(filename):

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
def load_json_file(filename):

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
        if Gb.initial_icloud3_loading_flag:
            json_helpers.save_json(filename, data)
        else:

            Gb.hass.async_add_executor_job(
                            json_helpers.save_json,
                            filename,
                            data)
        return True

    except RuntimeError as err:
        if err == 'no running event loop':
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
    return _os(os.path.isfile, filename)
    # return _os(aiofiles.ospath.isfile, filename)
def remove_file(filename):
    return _os(os.remove, filename)
    # return _os(aiofiles.ospath.remove, filename)

def directory_exists(dir_name):
    return _os(os.path.exists, dir_name)
    # return _os(aiofiles.ospath.exists, dir_name)
def make_directory(dir_name):
    if directory_exists(dir_name):
        return True
    return _os(os.makedirs, dir_name)
    # return _os(aiofiles.ospath.makedirs, dir_name)

def extract_filename(directory_filename):
    return _os(os.path.basename, directory_filename)
    # return _os(aiofiles.ospath.basename, directory_filename)

#--------------------------------------------------------------------
def _os(os_module, filename, on_error=None):
    try:
        # if Gb.ha_started:
        if True is False:
            results = asyncio.run_coroutine_threadsafe(
                    async_os(os_module, filename), Gb.hass.loop).result()
        else:
            results = os_module(filename)

        return results

    except RuntimeError as err:
        if err == 'no running event loop':
            return os_module(filename)

    except Exception as err:
        log_exception(err)
        pass

    return on_error or False
#...................................................................
async def async_os(os_module, filename):
    return await Gb.hass.async_add_executor_job(os_module, filename)

#--------------------------------------------------------------------
def rename_file(from_filename, to_filename):
    try:
        if file_exists(from_filename) is False:
            return False
        if file_exists(to_filename):
            remove_file(to_filename)

        if Gb.initial_icloud3_loading_flag:
            os.rename(from_filename, to_filename)
            return True
        else:
            asyncio.run_coroutine_threadsafe(
                    async_rename_file(from_filename, to_filename), Gb.hass.loop)
        return True

    except RuntimeError as err:
        if err == 'no running event loop':
            os.rename(from_filename, to_filename)
            return True

    except Exception as err:
        log_exception(err)
        pass

    return False
#...................................................................
async def async_rename_file(from_filename, to_filename):
    return await Gb.hass.async_add_executor_job(os.rename, from_filename, to_filename)

#--------------------------------------------------------------------
# def x_extract_filename(directory_filename):
#     try:
#         if file_exists(directory_filename) is False:
#             return '???.???'
#         elif Gb.initial_icloud3_loading_flag:
#             filename = os.path.basename(directory_filename)
#         else:
#             filename = asyncio.run_coroutine_threadsafe(
#                     async_extract_filename(directory_filename), Gb.hass.loop).result()
#         return filename

#     except RuntimeError as err:
#         if err == 'no running event loop':
#             filename = os.path.basename(directory_filename)
#             return filename

#     except Exception as err:
#         log_exception(err)
#         pass

#     return '???.???'
# #...................................................................
# async def async_extract_filename(directory_filename):
#     return await Gb.hass.async_add_executor_job(os.path.basename, directory_filename)

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

            if file_exists(directory_filename_bu):
                remove_file(directory_filename_bu)
                file_msg += (f"{CRLF_DOT}Deleted backup file (...{filename_bu})")

            rename_file(directory_filename, directory_filename_bu)
            file_msg += (f"{CRLF_DOT}Rename current file to ...{filename}.{backup_extn})")

        if file_exists(directory_filename):
            remove_file(directory_filename)
            file_msg += (f"{CRLF_DOT}Deleted file (...{filename})")

        if delete_old_sv_file:
            filename = f"{filename.split('.')[0]}.sv"
            directory_filename = f"{directory_filename.split('.')[0]}.sv"
            if file_exists(directory_filename):
                remove_file(directory_filename)
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
def get_file_list(start_dir=None,  file_extn_filter=[]):
    return get_file_or_directory_list(  directory_list=False,
                                        start_dir=start_dir,
                                        file_extn_filter=file_extn_filter)

def get_directory_list(start_dir=None):
    return get_file_or_directory_list(  directory_list=True,
                                        start_dir=start_dir,
                                        file_extn_filter=[])

#--------------------------------------------------------------------
def get_file_or_directory_list(directory_list=False, start_dir=None,  file_extn_filter=[]):
    '''
    Return a list of directories or files in a given path

    Parameters:
        - directory_list = True (List of directories), False (List of files)
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

    directory_filter      = ['/.', 'deleted', '/x-']
    filename_or_directory_list = []
    path_config_base = f"{Gb.ha_config_directory}/"
    back_slash       = '\\'
    if start_dir is None: start_dir = ''

    for path, dirs, files in os.walk(f"{path_config_base}{start_dir}"):
        www_sub_directory = path.replace(path_config_base, '')
        in_filter_cnt = len([filter for filter in directory_filter if instr(www_sub_directory, filter)])
        if in_filter_cnt > 0 or www_sub_directory.count('/') > 4 or www_sub_directory.count(back_slash):
            continue

        if directory_list:
            filename_or_directory_list.append(www_sub_directory)
            continue

        # Filter unwanted directories - std dirs are www/icloud3, www/cummunity, www/images
        if Gb.picture_www_dirs:
            valid_dir = [dir for dir in Gb.picture_www_dirs if www_sub_directory.startswith(dir)]
            if valid_dir == []:
                continue

        dir_filenames = [f"{www_sub_directory}/{file}"
                                for file in files
                                if (file_extn_filter
                                    and file.rsplit('.', 1)[-1] in file_extn_filter)]

        filename_or_directory_list.extend(dir_filenames[:25])
        if len(dir_filenames) > 25:
            filename_or_directory_list.append(
                        f"⛔ {www_sub_directory} > The first 25 files out of "
                        f"{len(dir_filenames)} are listed")

    return filename_or_directory_list