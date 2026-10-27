
from ..global_variables import GlobalVariables as Gb
from ..const            import (LATITUDE,  LONGITUDE, LOCATION_SOURCE,
                                INTO_ZONE_DATETIME,
                                TIMESTAMP, TIMESTAMP_SECS, TIMESTAMP_TIME, LOCATION_TIME, DATETIME, AGE,
                                BATTERY_LEVEL,
                                DEVICE_STATUS, LOW_POWER_MODE, ICLOUD_LOST_MODE_CAPABLE,
                                AUTHENTICATED,
                                LAST_UPDATE_TIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_TIME, LAST_LOCATED_DATETIME, LAST_LOCATED_TIME,
                                GPS, POLL_COUNT, VERT_ACCURACY, )
from ..const_config     import (CONF_IC3_DEVICENAME, ZONE, ZONE_DATETIME, LAST_ZONE, TRIGGER,
                                BATTERY, BATTERY_STATUS, INTERVAL, ZONE_DISTANCE, CALC_DISTANCE,
                                WAZE_DISTANCE, TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL,
                                MOVED_DISTANCE, INFO, GPS_ACCURACY, ALTITUDE, BADGE, )
from ..const_char       import (NL3_DATA, )
from .utils             import (instr, is_empty, isnot_empty, )
from .messaging         import (log_info_msg, log_exception, _called_from, )


DO_NOT_SHRINK     = ['url', 'accountName', 'deviceDisplayName', 'name', 'rawDeviceModel',
                    'deviceModel', 'message']
FILTER_DATA_DICTS = ['items', 'userInfo', 'dsid', 'dsInfo', 'webservices', 'locations','location',
                    'params', 'headers', 'kwargs', 'clientContext', 'identifiers', 'labels',
                    'securityCode', 'trustedPhoneNumber', 'devices']
FILTER_DATA_LISTS = ['devices', 'content', 'followers', 'following', 'contactDetails', 'protocols', 'trustTokens',
                    'keyNames', 'trustedPhoneNumbers', ]
FILTER_FIELDS = [
        AUTHENTICATED,
        LATITUDE,  LONGITUDE, LOCATION_SOURCE,
        ZONE, ZONE_DATETIME, INTO_ZONE_DATETIME, LAST_ZONE,
        TIMESTAMP, TIMESTAMP_SECS, TIMESTAMP_TIME, LOCATION_TIME, DATETIME, AGE,
        TRIGGER, BATTERY, BATTERY_LEVEL, BATTERY_STATUS,
        INTERVAL, ZONE_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
        TRAVEL_TIME, TRAVEL_TIME_MIN, DIR_OF_TRAVEL, MOVED_DISTANCE,
        DEVICE_STATUS, LOW_POWER_MODE, BADGE,
        LAST_UPDATE_TIME, LAST_UPDATE_DATETIME,
        NEXT_UPDATE_TIME, NEXT_UPDATE_TIME,
        LAST_LOCATED_TIME, LAST_LOCATED_DATETIME,
        INFO, GPS_ACCURACY, GPS, POLL_COUNT, VERT_ACCURACY, ALTITUDE, ICLOUD_LOST_MODE_CAPABLE,
        'ResponseCode', 'reason',
        'id', 'firstName', 'lastName', 'name', 'fullName', CONF_IC3_DEVICENAME,
        'appleId', 'emails', 'phones', 'locked',
        'deviceStatus', 'batteryStatus', 'batteryLevel', 'membersInfo',
        'deviceModel', 'rawDeviceModel', 'deviceDisplayName', 'modelDisplayName', 'deviceClass',
        # Retired/replaced device indicators. An unpaired watch or an iPhone erased
        # for trade-in drops Activation Lock, and a removed device is pendingRemove.
        'activationLocked', 'wipedTimestamp', 'wipeInProgress',
        'pendingRemove', 'pendingRemoveUntilTS', 'fmlyShare', 'deviceDiscoveryId',
        'isOld', 'isInaccurate', 'timeStamp', 'altitude', 'location', 'latitude', 'longitude',
        'horizontalAccuracy', 'verticalAccuracy', 'positionType',
        'hsaVersion', 'hsaEnabled', 'hsaTrustedBrowser', 'hsaChallengeRequired',
        'locale', 'appleIdEntries', 'statusCode',
        'familyEligible', 'findme', 'requestInfo',
        'termsUpdateNeeded', 'iCloudTerms', 'version',
        'invitationSentToEmail', 'invitationAcceptedByEmail', 'invitationFromHandles',
        'invitationFromEmail', 'invitationAcceptedHandles',
        'items', 'userInfo', 'prsId', 'dsid', 'dsInfo', 'webservices', 'locations', 'dslang',
        'devices', 'content', 'followers', 'following', 'contactDetails', 'countryCode',
        'dsWebAuthToken', 'accountCountryCode', 'extended_login', 'trustToken', 'trustTokens',
        'data', 'json', 'headers', 'params', 'url', 'retry_cnt', 'retried', 'retry', '#',
        'code', 'ok', 'method', 'fmly', 'shouldLocate', 'selectedDevice', 'membersInfo',
        'X-Apple-OAuth-State', 'X-Apple-ID-Session-Id', 'Accept', 'Authorization',
        # scnt pairs with X-Apple-ID-Session-Id to identify the idmsa signin
        # session. Logged so a rejected /appleauth/auth request can be checked
        # for whether the session headers were actually attached to it.
        'scnt', 'Content-Type', 'X-Apple-Widget-Key',
        'identifiers', 'labels', 'model', 'name_by_user', 'area_id', 'manufacturer', 'sw_version',
        'keyNames', 'securityCode', 'trustedPhoneNumbers', 'trustedPhoneNumber',
        'deviceType', 'areaCode', 'phoneNumber', 'deviceId',
        'authenticationType', 'pushSupported',
        # Apple's 2fa error/status fields. Without these, a rejected auth code
        # request (verify/phone 423) logs only the trusted phone numbers and the
        # reason Apple gives for the rejection is filtered out of the log.
        'service_errors', 'serviceErrors', 'hasError', 'message', 'title',
        'restrictedAccount', 'authType', 'mode', 'pushMode',
        'tooManyCodesSent', 'tooManyCodesValidated',
        'securityCodeLocked', 'securityCodeCooldown',
        'apple_id', 'password', 'accountName', 'salt', 'protocols', 'protocol', 'iteration',
        'a', 'A', 'b', 'B', 'c', 'm1', 'M1', 'm2', 'M2', 'g', 'K', 'N', 'u', 'v',
        ]
FILTER_OUT = [
    'features', 'BTR', 'LLC', 'CLK', 'TEU', 'SND', 'ALS', 'CLT', 'PRM', 'SVP', 'SPN', 'XRM', 'NWF', 'CWP',
    'MSG', 'LOC', 'LME', 'LMG', 'LYU', 'LKL', 'LST', 'LKM', 'WMG', 'SCA', 'PSS', 'EAL', 'LAE', 'PIN',
    'LCK', 'REM', 'MCS', 'REP', 'KEY', 'KPD', 'WIP', 'scd',
    'rm2State', 'pendingRemoveUntilTS', 'repairReadyExpireTS', 'repairReady', 'lostModeCapable', 'wipedTimestamp',
    'encodedDeviceId', 'scdPh', 'locationCapable', 'trackingInfo', 'nwd', 'remoteWipe', 'canWipeAfterLock', 'baUUID',
    'snd', 'continueButtonTitle', 'alertText', 'cancelButtonTitle', 'createTimestamp',  'alertTitle', ]


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   RAWDATA LOGGING ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def log_data_unfiltered(_hdr, rawdata, data_source=None, filter_id=None):
    try:
        rawdata_copy = rawdata['raw'].copy() if 'raw' in rawdata else rawdata.copy()
        rawdata_copy = _set_validpw_invalidpw_text(rawdata_copy)

    except:
        log_info_msg(f"{_hdr.upper()}{NL3_DATA}{rawdata}")
        return

    devices_data = {}

    if 'content' in rawdata_copy:
        for device_data in rawdata_copy['content']:
            devices_data[device_data['name']] = device_data

        rawdata_copy['content'] = 'DeviceData……'

    # Cycle thru rawdata items and create log line for each dict item
    # Add dict items to rawdata_items list, save others and add at end
    if type(rawdata_copy) is dict:
        rawdata_items = ''
        rawdata_non_dict_items = {}
        for k, v in rawdata_copy.items():
            if type(k) is dict:
                d = {k: v}
                rawdata_items += f"{NL3_DATA}{d}"
            else:
                rawdata_non_dict_items[k] = v
        rawdata_items += f"{NL3_DATA}{rawdata_non_dict_items}"

    else:
        rawdata_items = f"{NL3_DATA}{rawdata_copy}"

    log_info_msg(f"{_hdr.upper()}{rawdata_items}")


    for device_data in devices_data:
        log_msg = ( f"iCloud AppleAcct Data (unfiltered -- "
                    f"{device_data}")
        log_info_msg(log_msg)

#--------------------------------------------------------------------
def log_request_data(request_response_text, method, url, kwargs, AppleAcct=None, response=None):

        is_log_level_rawdata = False if response is None else (response.status_code != 200)

        is_log_level_rawdata = is_log_level_rawdata or (url.endswith('refreshClient') is False)
        if Gb.is_log_level_rawdata or is_log_level_rawdata or Gb.is_icloud3_initial_startup:
            pass
        else:
            return

        try:
            if AppleAcct in Gb.AppleAcct_by_apple_id.values():
                apple_id = AppleAcct.apple_user
            else:
                apple_id = AppleAcct
            _hdr = (f"{apple_id}, {method}, {request_response_text}-{url.split('/')[-2:]}")

            if request_response_text.startswith('Request'):
                _data = {'url': url[8:], 'retry': kwargs.get("retry_cnt", 0)}
                _data.update(kwargs)

            elif request_response_text.startswith('Response'):
                if response is None:
                    _data = kwargs
                else:
                    try:
                        data = response.json()
                    except:
                        data = {}
                    _data = {'code': response.status_code, 'ok': response.ok, 'data': data}
                    if Gb.is_log_level_rawdata_unfiltered:
                        _data['headers'] = response.headers


            log_data(_hdr, _data, is_log_level_rawdata=is_log_level_rawdata)

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
def log_data(_hdr, rawdata, is_log_level_rawdata=False, data_source=None, filter_id=None):
    '''
    Add raw data records to the HA log file for debugging purposes.

    This is used in Pyicloud_ic3 to log all data requests and responses,
    and in other routines in iCloud3 when device_tracker or other entities
    are read from or updated in HA.

    A filter is applied to the raw data and dictionaries and lists in the
    data to eliminate displaying uninteresting fields. The fields, dictionaries,
    and list are defined in the FILTER_FIELDS, FILTER_DATA_DICTS and
    FILTER_DATA_LISTS.
    '''

    if rawdata is None:
        return False
    elif Gb.is_log_level_rawdata is False and is_log_level_rawdata is False:
        return False

    if (Gb.is_icloud3_startup_inprocess
            or 'all' in Gb.log_level_devices
            or Gb.log_level_devices == []):
        pass

    elif instr(_hdr,'iCloud Data'):
        log_level_devices = [devicename for devicename in Gb.log_level_devices
                                        if instr(_hdr, devicename)]
        if log_level_devices == []:
            return

    rawdata_data   = {}
    log_msg        = ''

    try:
        if type(rawdata) is not dict:
            log_info_msg(f"{_hdr.upper()}{NL3_DATA}{rawdata}")
            return

        rawdata_data = rawdata.pop('data', None)
        log_msg += _create_log_msg_from_data(rawdata)
        log_msg += _create_log_msg_from_data(rawdata_data, data=True)

        if log_msg:
            log_info_msg(f"{_hdr.upper()} {_called_from(show_fct_name=True)}{log_msg}")

        return

    except Exception as err:
        log_exception(err)
        log_info_msg(f"{_hdr.upper()} *** Data could not be filtered ***{NL3_DATA}{rawdata}")
        return

#..........................................................................................
def _create_log_msg_from_data(rawdata, data=None):
    '''
    Extract lists and dictionaries from the rawdata dictionary

    Returns a new rawdata dictionary:
        log_items_data[listitem]               - lists by the list item name
        log_items_data[listitem.sublist]       - sublists of the list
        log_items_data[dictitem]               - dictionaries by the dict item name
        log_items_data[dictietm.subdictitem]   - dicts within that dict
        log_items_data[items]                  - non-list & non_dict items
    '''
    if is_empty(rawdata):
        return ''

    log_items_data = {}
    try:
        filtered_rawdata = {k: v for k, v in rawdata.items() if k in FILTER_FIELDS}
    except Exception as err:
        log_exception(err)

    if Gb.log_level_devices == 'all':
        filtered_names = []
    else:
        filtered_names = [name  for name, devicename in Gb.devicenames_by_aadev_dname.items()
                                if devicename in Gb.log_level_devices]

    for k, v in filtered_rawdata.copy().items():
        if type(v) is list:
            if is_empty(v): continue

            # The list contains a dict item Format it as a sub dict
            if type(v[0]) is dict:
                idx = -1
                filtered = []
                for vsd in v:
                    idx += 1
                    if k == 'content':
                        ksd = vsd.get('name', idx)
                        if ksd in filtered_names or Gb.is_icloud3_startup_inprocess:
                            log_items_data[f"{k}.{ksd}"] = _filter_rawdata_items(vsd)
                        else:
                            filtered.append(ksd)
                    else:
                        log_items_data[f"{k}.{idx}"] = _filter_rawdata_items(vsd, shrink_only=True)
                if isnot_empty(filtered):
                    log_items_data[f"{k}.Filtered"] = f'{filtered}'
            else:
                log_items_data[f"{k}"] = _filter_rawdata_items(v)
            filtered_rawdata.pop(k)

        elif type(v) is dict:
            if is_empty(v): continue

            # The dict contains another dict item Format it as a sub dict
            try:
                # ksd_0 = v.keys()[0]
                for ksd, vsd in v.items():
                    if ksd not in FILTER_FIELDS: continue
                    if type(vsd) is dict:
                        vsd_data = v.pop(ksd)
                        shrink_only = ksd in ['membersInfo']
                        log_items_data[f"{k}.{ksd}"] = _filter_rawdata_items(vsd_data, shrink_only)
            except:
                pass

            log_items_data[f"{k}"] = _filter_rawdata_items(v)

            filtered_rawdata.pop(k)

    filtered_rawdata = {k: shrink_item(v, k) for k, v in filtered_rawdata.items()}
    log_items_data['items'] = filtered_rawdata

    log_msg = ''
    data_text = 'data.' if data else '_.'
    for k, v in log_items_data.items():
        if isnot_empty(v):
            log_msg += f"{NL3_DATA}{data_text}{k}={v}"

    return log_msg

#..........................................................................................
def _is_device_filtered(aadev_name):
    devicename = Gb.devicenames_by_aadev_dname.get(aadev_name, '')
    return not (devicename in Gb.log_level_devices or 'all' in Gb.log_level_devices)

#..........................................................................................
def _filter_rawdata_items(item_value_dict, shrink_only=None):
    '''
    Cycle thru the items dict, filter and shrink the value items
    '''
    if (Gb.is_log_level_rawdata_unfiltered
            or type(item_value_dict) is not dict):
        return item_value_dict

    _filtered_rawdata_items = {}
    for k, v in item_value_dict.items():
        if k not in FILTER_FIELDS and shrink_only is None:
            continue

        _filtered_rawdata_items[k] = shrink_item(v, k)

    return _filtered_rawdata_items

#..........................................................................................
def shrink_item(v, k=None):
    '''
    Reduce the size of str fields longer than 20-chars
    '''
    if k in DO_NOT_SHRINK:
        return v

    # Shrink each item of a list (e.g. trustTokens) so it is not logged in full
    if type(v) is list:
        return [shrink_item(x, k) for x in v]

    if (type(v) is str
            and len(v) > 20
            and v.startswith('http') is False):
        v = f"{v[:6]}……{v[-6:]}"

    return v

#--------------------------------------------------------------------
def _set_validpw_invalidpw_text(rawdata):

    rawdata_items = rawdata['data'] if 'data' in rawdata else rawdata

    try:
        if 'code' in rawdata_items:
            if rawdata_items['code'] == 409:
                rawdata_items['ok'] = 'ValidPW'
            elif rawdata_items['code'] == 401:
                rawdata_items['ok'] = 'InvalidPW'

    except:
        pass

    return rawdata
