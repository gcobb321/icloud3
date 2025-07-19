
from ..global_variables     import GlobalVariables as Gb
from ..const                import (CRLF_DOT,  )
from .utils                 import (instr, is_empty, isnot_empty, list_to_str, )
from .messaging             import (log_exception, _evlog, _log, log_error_msg, )

from collections            import OrderedDict
import asyncio
import json
import logging
import os
import requests
import shutil

from homeassistant.util     import json as json_util
from homeassistant.helpers  import json as json_helpers
from homeassistant.helpers  import httpx_client
from httpx                  import (ConnectTimeout, HTTPError, RequestError,
                                    HTTPStatusError, InvalidURL, )

_LOGGER = logging.getLogger(__name__)
#_LOGGER = logging.getLogger(f"icloud3")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            HTTPX & REQUESTS URL UTILITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_httpx_request_url_data(url, headers=None):
    '''
    Set up and request data from a url using the httpx requests process.

    Returns:
        - data dictionary with the returned json data, the url and status_code
        - error dictionary with the url, error and status_code if a connection or other error
            occurred
    '''
    try:
        error_type = ''
        error_code = -99
        try:
            if headers is None:
                # Use HA httpx client
                httpx = httpx_client.get_async_client(Gb.hass, verify_ssl=False)

            else:
                httpx = create_async_httpx_client(headers=headers)


            error_type = 'InternetError-'

            # response = await Gb.httpx.get(url)
            response = await httpx.get(url)
            response.raise_for_status()

            data = response.json()

            data['url'] = url
            data['status_code'] = response.status_code

            return data

        except HTTPStatusError:
            error_type = 'ClientError'
        except (ConnectTimeout) as err:
            error_type += 'ConnectTimeout'
        except (ConnectionError) as err:
            error_type += 'ConnectionError'
        except (HTTPError) as err:
            error_type += 'HTTPError'
        except Exception as err:
            log_exception(err)
            error_type += 'General'

        try:
            error_code = response.status_code
        except:
            if error_type == 'InternetError-':
                error_code = 104
            else:
                error_code = -999

        data = {'url': url, 'error': error_type, 'status_code': error_code}

        return data

    except Exception as err:
        log_exception(err)
        error_type = 'OverAll'

    data = {'url': url, 'error': error_type, 'status_code': error_code}

    return data

#----------------------------------------------------------------------------
def httpx_request_url_data(url, headers=None):
    '''
    Set up and request data from a url using the httpx requests process.

    Returns:
        - data dictionary with the returned json data, the url and status_code
        - error dictionary with the url, error and status_code if a connection or other error
            occurred
    '''
    try:
        error_type = ''
        error_code = -99
        try:
            # if Gb.httpx is None and headers is None:
            #     # Use HA httpx client
            #     # Gb.httpx = httpx_client.get_async_client(Gb.hass, verify_ssl=False)

            #     # Create a new HA httpx client
            #     Gb.httpx = create_async_httpx_client(headers=headers)
            if headers is None:
                # Use HA httpx client
                httpx = httpx_client.get_async_client(Gb.hass, verify_ssl=False)

            else:
                httpx = create_async_httpx_client(headers=headers)

            httpx = create_async_httpx_client(headers=headers)

            error_type = 'InternetError-'

            # response = await Gb.httpx.get(url)
            response = httpx.get(url)
            response.raise_for_status()

            data = response.json()

            data['url'] = url
            data['status_code'] = response.status_code

            return data

        except HTTPStatusError:
            error_type = 'ClientError'
        except (ConnectTimeout) as err:
            error_type += 'ConnectTimeout'
        except (ConnectionError) as err:
            error_type += 'ConnectionError'
        except (HTTPError) as err:
            error_type += 'HTTPError'
        except Exception as err:
            log_exception(err)
            error_type += 'General'

        try:
            error_code = response.status_code
        except:
            if error_type == 'InternetError-':
                error_code = 104
            else:
                error_code = -999

        data = {'url': url, 'error': error_type, 'status_code': error_code}

        return data

    except Exception as err:
        log_exception(err)
        error_type = 'OverAll'

    data = {'url': url, 'error': error_type, 'status_code': error_code}

    return data

#............................................................................
def create_async_httpx_client(headers=None):
    """Create a new httpx.AsyncClient with kwargs, i.e. for cookies.

    If auto_cleanup is False, the client will be
    automatically closed on homeassistant_stop.

    This method must be run in the event loop.
    """
    client = httpx_client.HassHttpXAsyncClient(
                    verify=False,
                    headers=headers,
                    limits=httpx_client.DEFAULT_LIMITS,
    )

    original_aclose = client.aclose

    httpx_client._async_register_async_client_shutdown(Gb.hass, client, original_aclose)

    return client

#----------------------------------------------------------------------------
def request_url_data(url):
    try:
        response = requests.get(url, timeout=3)

    except requests.RequestException as err:
        data = {'url': url, 'error': err, 'status_code': -2}

        return data

    except Exception as err:
        log_exception(err)
        data = {'url': url, 'error': err, 'status_code': -1}

        return data

    data = response.json()
    data['url'] = url
    data['status_code'] = response.status_code


    return data

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            JSON FILE UTILITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def async_read_json_file(filename):

    if file_exists(filename) is False:
        return {}

    try:
        data = Gb.hass.async_add_executor_job(
                            read_json_file,
                            filename)
        return data

    except Exception as err:
        # _LOGGER.exception(err)
        log_exception(err)
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

#--------------------------------------------------------------------
async def async_read_file(filename):

    file_exists_= await async_file_exists(filename)
    if file_exists is False:
        return None

    # return await Gb.hass.async_add_executor_job(read_file, filename)
    file_data = await Gb.hass.async_add_executor_job(read_file, filename)
    return file_data

#--------------------------------------------------------------------
def read_file(filename):
    with open(filename, 'r') as f:
        file_data = f.read()

    return file_data

#--------------------------------------------------------------------
def async_write_file(filename, data):

    success = Gb.hass.async_add_executor_job(write_file, filename, data)
    return success

#--------------------------------------------------------------------
def write_file(filename, data):
    try:
        with open(filename, 'w') as f:
            f.write(data)

        return True

    except Exception as err:
        log_exception(err)

    return False

#--------------------------------------------------------------------
def is_valid_json_str(json_str):
    '''
    Validate a json string
    '''
    try:
        json.loads(json_str)
    except ValueError as err:
        return False
    except Exception as err:
        log_exception(err)
        return False
    return True

#--------------------------------------------------------------------
def json_str_to_dict(json_str):
    '''
    Returna Python dictionary from a json string
    '''
    try:
        json_str = json_str.replace("'", '"')
        json_str = json_str.replace('True', 'true')
        json_str = json_str.replace('False', 'false')
        # json_str = json_str.replace(' ', '')
        return json.loads(json_str)

    except Exception as err:
        pass

    return {}

#--------------------------------------------------------------------
def dict_to_json_str(dict):
    '''
    Returna Python json string from a dictionary
    '''
    try:
        return json.dumps(dict)

    except Exception as err:
        pass

    return ''

#-------------------------------------------------------------------------------------------
def str_to_json_str(self, from_str):
    '''
    Convert the dashboard_str to json format for the lovelace.icloud3-XXX dashboard file
    '''
    from_str = from_str.replace("'", '"')
    from_str = from_str.replace('True', 'true')
    from_str = from_str.replace('False', 'false')
    # from_str = from_str.replace(' ', '')
    json_str = from_str

    return json_str



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            PYTHON OS. FILE I/O AND OTHER UTILITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def file_exists(filename):
    return _os(os.path.exists, filename)

def set_write_permission(filename):
    '''
    Set the file permissions to Read/Write
    '''
    try:
        if os.access(filename, os.W_OK):
            os.chmod(filename, 0o777)

        return True
    except FileNotFoundError:
        pass
    except Exception as err:
        # log_exception(err)
        pass

    return False


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
    try:
        results = os_module(filename)
        return results

    except PermissionError:
        file_info = os.stat(filename)
        mode = file_info.st_mode
        os.chmod(filename, 0o777)
        file_info = os.stat(filename)
        mode = file_info.st_mode

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


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            DIRECTORIES AND FILES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_get_directory_files(directory):
    files = await Gb.hass.async_add_executor_job(get_directory_files, directory)
    return files

#--------------------------------------------------------------------
def get_directory_files(directory):
    dir_names, files = get_directory(directory)
    return files

#--------------------------------------------------------------------
def get_directory(directory):
    if directory_exists(directory) is False:
        return [], []

    f = []
    for (dir_path, dir_names, files) in os.walk(directory):
        f.extend(files)
        break

    return dir_names, files


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