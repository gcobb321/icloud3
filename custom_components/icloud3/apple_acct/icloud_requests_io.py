from ..global_variables     import GlobalVariables as Gb
from ..const                import (EVLOG_ALERT, CRLF_DOT, APPLE_SERVER_ENDPOINT, )
from ..utils.messaging      import (post_alert, log_exception, _evlog, _log, log_debug_msg,
                                    log_data_unfiltered, log_request_data, )
from ..utils.time_util      import (time_now,  time_now_secs, secs_to_time, format_time_age, )
from ..utils.utils          import (is_running_in_event_loop)
from .icloud_session        import iCloudSession

import datetime as dt
import http.cookiejar as cookielib
from os                     import path
import requests
from requests.exceptions    import ConnectionError

from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers  import httpx_client
from httpx                  import (ConnectTimeout, HTTPError, RequestError,
                                    HTTPStatusError, InvalidURL, )


REQUEST_TIMEOUT_TIME = dt.timedelta(seconds=60)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            ICLOUD SESSION REQUEST INTERFACE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''
All data request calls to icloud.com are routed through this central io handler.
'''

def post(AppleAcct, url, **kwargs):
    schedule_request_timeout_timer()
    try:
        data = AppleAcct.iCloudSession.post(url, **kwargs)
    except Exception as err:
        log_exception(err)
        data = {}

    cancel_request_timeout_timer()
    return data

#--------------------------------------------------------------------
def get(AppleAcct, url, **kwargs):
    schedule_request_timeout_timer()
    try:
        data = AppleAcct.iCloudSession.get(url, **kwargs)
    except Exception as err:
        log_exception(err)
        data = {}

    cancel_request_timeout_timer()
    return data

#--------------------------------------------------------------------
def update_headers(AppleAcct, **kwargs):
    return AppleAcct.iCloudSession.headers.update(kwargs)

#--------------------------------------------------------------------
def new_session(AppleAcct, **kwargs):
    _session = iCloudSession(AppleAcct)
    return _session

#--------------------------------------------------------------------
def cookies(AppleAcct, cookie_dir_filename):
    AppleAcct.iCloudSession.cookies = cookielib.LWPCookieJar(filename=cookie_dir_filename)

    if path.exists(AppleAcct.cookie_dir_filename):
        try:
            AppleAcct.iCloudSession.cookies.load(ignore_discard=True, ignore_expires=True)

        except:
            return False

    return True

#--------------------------------------------------------------------
async def async_request(url, **kwargs):
    return await Gb.hass.async_add_executor_job(request_url_data, url, kwargs)

#--------------------------------------------------------------------
def request(url, **kwargs):
    schedule_request_timeout_timer()
    data = request_get_post(url, **kwargs)
    cancel_request_timeout_timer()
    return data

#--------------------------------------------------------------------
def request_get_post(url, **kwargs):
    '''
    Set up and request data from a url. This handles non-session icloud.com calls

    Returns:
        - data dictionary with the returned json data, the url and status_code
        - error dictionary with the url, error and status_code if a connection or other error
            occurred
    '''

    try:
        error = 'InternetError-'
        code  = 104
        ok    = False

        data = {}
        data['code'] = code
        data['ok']   = ok

        try:
            if 'data' in kwargs:
                response = requests.post(url, **kwargs)
            else:
                response = requests.get(url, **kwargs)


            try:
                data = response.json()
            except Exception as err:
                pass


            code = response.status_code
            ok   = True
            error = ''

        except (requests.exceptions.ConnectTimeout) as err:
            error += 'ConnectTimeout'
            code   = 104
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout, ) as err:
            error += 'ConnectionError'
            code   = 105
        except (requests.exceptions.HTTPError) as err:
            error += 'HTTPError'
            code   = 500
        except Exception as err:
            log_exception(err)
            error += 'Other'
            code   = 500

    except Exception as err:
        log_exception(err)
        error = 'OverAll'
        code  = -99

    data['code']  = code
    data['ok']    = ok
    data['url']   = url
    data['error'] = error

    return data


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            REQUEST TIMEOUT HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''
A 1-min Timeout timer is set when post/get request is sent to detect Internet Connection
Errors in the underlying Python code that support the session/request modules. It is fired when
a data request is made and there is no response from Apple/iCloud.
'''

def schedule_request_timeout_timer():
    '''
    Set the timeout handler when a post/get call is made
    '''
    if Gb.internet_error or is_running_in_event_loop():
        cancel_request_timeout_timer()
        return

    if Gb.icloud_io_request_secs > 0:
        cancel_request_timeout_timer()

    Gb.icloud_io_request_secs = time_now_secs()
    # _log(f"🔺🔺 START TIMER {secs_to_time(Gb.icloud_io_request_secs)}")

    try:
        Gb.icloud_io_1_min_timer_fct = None
        Gb.icloud_io_1_min_timer_fct = track_time_interval(Gb.hass,
                                    request_timed_out,
                                    REQUEST_TIMEOUT_TIME,
                                    cancel_on_shutdown=True)

    except Exception as err:
        # if instr(err, 'RunTimeError'):
        #     log_error_msg('RuntimeError: Cannot be called from within the event loop')
        log_exception(err)

#------------------------------------------------------------------
def cancel_request_timeout_timer():

    # _log(f"🔻🔻 CANCEL TIMER {secs_to_time(Gb.icloud_io_request_secs)}")
    if Gb.icloud_io_request_secs > 0:
        Gb.icloud_io_request_secs = 0
    if Gb.icloud_io_1_min_timer_fct is not None:
        Gb.icloud_io_1_min_timer_fct()

#----------------------------------------------------------------------------
def request_timed_out():
    '''
    The 1-min timer timedout. This indicates an Internet Error occurred. Check to see if it is
    really available in case the timer was never canceled.
    '''

    cancel_request_timeout_timer()

    is_internet_available = Gb.InternetError.is_internet_available()
    if is_internet_available is False:
        Gb.internet_error = True
        post_alert(f"Internet Connection Error Detected (www.icloud.com) > "
                    "More than 1-min since last location request with no response. "
                    "Possible causes:"
                    f"{CRLF_DOT}An Internet Connection Error (Internet, WiFi, Router is down)"
                    f"{CRLF_DOT}Apple is not available (`www.icloud.com` is down)"
                    f"{CRLF_DOT}IPv6 is enabled and being used (IPv6 is not supported)")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            HTTPX & REQUESTS URL UTILITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_httpx_request(url, **kwargs): #headers=None):
    '''
    Set up and request data from a url using the httpx requests process.

    Returns:
        - data dictionary with the returned json data, the url and status_code
        - error dictionary with the url, error and status_code if a connection or other error
            occurred
    '''

    try:
        error = 'InternetError-'
        code  = 104
        ok    = False

        data = {}
        data['code'] = code
        data['ok']   = ok

        try:
            if 'headers' in kwargs:
                httpx = create_async_httpx_client(headers=kwargs['headers'])
            else:
                httpx = httpx_client.get_async_client(Gb.hass, verify_ssl=False)

            log_request_data('Request HTTPX', 'get', url, kwargs, '')

            if 'data' in kwargs:
                response = await httpx.post(url, **kwargs)
            else:
                response = await httpx.get(url, **kwargs)

            try:
                data = response.json()
            except Exception as err:
                pass

            log_request_data('Response HTTPX', 'get', url, kwargs, '')

            code = response.status_code
            ok   = True
            error = ''

        except HTTPStatusError:
            error = 'ClientError'
            code  = 400
        except (ConnectTimeout) as err:
            error += 'ConnectTimeout'
            code   = 104
        except (ConnectionError) as err:
            error += 'ConnectionError'
            code   = 105
        except (HTTPError) as err:
            error += 'HTTPError'
            code   = 500
        except Exception as err:
            log_exception(err)
            error += 'Other'
            code   = 500

    except Exception as err:
        log_exception(err)
        error = 'OverAll'
        code  = -99

    data['code']  = code
    data['ok']    = ok
    data['url']   = url
    data['error'] = error

    return data

#--------------------------------------------------------------------
def httpx_request(url, headers=None, **kwargs):
    '''
    Set up and request data from a url using the httpx requests process.

    Returns:
        - data dictionary with the returned json data, the url and status_code
        - error dictionary with the url, error and status_code if a connection or other error
            occurred
    '''

    try:
        error = 'InternetError-'
        code  = 104
        ok    = False

        data = {}
        data['code'] = code
        data['ok']   = ok

        try:
            if headers is None:
                httpx = httpx_client.get_async_client(Gb.hass, verify_ssl=False)

            else:
                httpx = create_async_httpx_client(headers=headers, **kwargs)

            response = httpx.get(url)

            try:
                data = response.json()
            except Exception as err:
                pass

            code = response.status_code
            ok   = True
            error = ''

        except HTTPStatusError:
            error = 'ClientError'
            code  = 400
        except (ConnectTimeout) as err:
            error += 'ConnectTimeout'
            code   = 104
        except (ConnectionError) as err:
            error += 'ConnectionError'
            code   = 105
        except (HTTPError) as err:
            error += 'HTTPError'
            code   = 500
        except Exception as err:
            log_exception(err)
            error += 'Other'
            code   = 500

    except Exception as err:
        log_exception(err)
        error = 'OverAll'
        code  = -99

    data['code']  = code
    data['ok']    = ok
    data['url']   = url
    data['error'] = error

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
