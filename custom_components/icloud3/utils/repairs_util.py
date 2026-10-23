from ..global_variables import GlobalVariables as Gb
from ..const            import (DOMAIN,
                                CRLF, CRLF_DOT, NBSP, NBSP2, NBSP3, NBSP4, NBSP5, NBSP6)

from homeassistant.helpers import issue_registry as ir
from homeassistant.util    import slugify

import re
import threading
from functools import partial

# The Home Assistant Repairs helpers live here so this module has no iCloud3
# messaging dependency at import time. messaging re-exports them, so callers
# keep importing from .messaging. Messaging routines used at call time are
# imported inside the function to avoid a circular import.
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   HA REPAIRS ISSUE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# iCloud3 issues use these translation keys. The title and message are passed as
# placeholders ('issues' in strings.json & translations/en.json).
#   icloud3_alert  - Issue with a change that is made when Submit is selected
#   icloud3_notice - Notice (fix_action='acknowledge'), Submit only removes it
REPAIR_ISSUE_TRANSLATION_KEY        = 'icloud3_alert'
REPAIR_NOTICE_TRANSLATION_KEY       = 'icloud3_notice'

# Fix handlers run by repairs.py when Submit is selected on a fixable issue.
#   {fix_action: handler(fix_data) -> bool}, see register_repair_fix_handler
repair_fix_handlers = {}

# Added to the device's sensor.icloud3_alerts entry (keyed by the device's fname) when
# a Repairs issue is posted. An entry with this text is removed after Submit.
REPAIR_ISSUED_ALERT_MSG = 'HA Repair issue created'

#--------------------------------------------------------------------
def post_repair_issue(  issue_id, alert_key, title, alert_msg,
                        fix_action=None, fix_data=None, severity='warning'):
    '''
    Add an iCloud3 notification to HA Settings > Repairs. It is also added to the
    sensor.icloud3_alerts attribute for the alert_key (Event Log greenbar).

    issue_id:
        Stable id of the condition, e.g. f"device_replaced_{devicename}_{device_id8}".
        Posting the same id again updates the issue instead of adding another one.
        HA keeps the issue's 'Ignore' state by id, so an ignored issue stays ignored
        when it is posted again on the next restart. A notice (fix_action='acknowledge')
        is deleted and created again so it is always displayed.
    alert_key:
        What the issue is for, used as the sensor.icloud3_alerts key:
            - devicename - The Device's fname is used
            - Apple acct username - The AppleAcct's username_id is used
            - Other text - Used as is
        The issue data has the alert_key and the devicename ('' if it is not a
        device) for the fix handler.
    title, alert_msg:
        Repairs title and message. Event Log formatting (CRLF, CRLF_DOT) is converted
        to markdown for the Repairs dialog.
    fix_action:
        Name of a handler registered with register_repair_fix_handler. The issue
        is fixable and the handler runs when Submit is selected in Repairs.
        None - Informational issue, it can only be ignored
    fix_data:
        dict of str/int/float/None values passed to the fix handler
    severity:
        'warning', 'error' or 'critical'

    Return:
        issue_id used for the Repairs issue (slugified)
    '''
    from .messaging import log_exception, update_alert_sensor
    try:
        issue_id = slugify(issue_id)
        devicename = ''
        if Device := Gb.Devices_by_devicename.get(alert_key):
            devicename = alert_key
            alert_key  = Device.fname
        elif AppleAcct := Gb.AppleAcct_by_username.get(alert_key):
            alert_key  = AppleAcct.username_id

        if fix_action is None:
            fix_action = 'acknowledge'

        data = {'devicename': devicename,
                'alert_key': alert_key,
                'fix_action': fix_action}
        data.update(fix_data or {})

        # A notice reports a new event. Delete the one from an earlier post first so
        # it is displayed even if it was ignored ('Ignore' is kept by issue_id).
        if fix_action == 'acknowledge':
            _run_in_event_loop(ir.async_delete_issue, Gb.hass, DOMAIN, issue_id)

        _run_in_event_loop(ir.async_create_issue,
                                Gb.hass, DOMAIN, issue_id,
                                is_fixable     = fix_action is not None,
                                is_persistent  = False,
                                severity       = ir.IssueSeverity(severity),
                                translation_key= REPAIR_NOTICE_TRANSLATION_KEY
                                                    if fix_action == 'acknowledge'
                                                    else REPAIR_ISSUE_TRANSLATION_KEY,
                                translation_placeholders = {
                                        'title': _evlog_msg_to_markdown(title),
                                        'message': _evlog_msg_to_markdown(alert_msg)},
                                data          = data)

        update_alert_sensor(alert_key, f"{title}, {REPAIR_ISSUED_ALERT_MSG}")

    except Exception as err:
        log_exception(err)

    return issue_id

#--------------------------------------------------------------------
def clear_repair_issue(issue_id, devicename_or_Device=None):
    '''
    Remove the Repairs issue and its sensor.icloud3_alerts message. Only call this
    when the condition no longer exists. Deleting the issue also deletes its
    'Ignore' state, so it is displayed again if it is posted later.
    '''
    from .messaging import _resolve_devicename_log_msg, log_exception
    devicename, _ = _resolve_devicename_log_msg(devicename_or_Device, '')
    issue_id = slugify(issue_id)

    try:
        _run_in_event_loop(ir.async_delete_issue, Gb.hass, DOMAIN, issue_id)
    except Exception as err:
        log_exception(err)

    if Device := Gb.Devices_by_devicename.get(devicename):
        clear_repair_issue_alert_msg(Device.fname)

#--------------------------------------------------------------------
def clear_repair_issues(issue_id_prefix, keep_issue_ids=None):
    '''
    Remove the Repairs issues with an id starting with issue_id_prefix except the
    ones in keep_issue_ids. Used to remove issues whose condition no longer exists
    while keeping the ones that were posted again (and their 'Ignore' state).

    issue_id_prefix:
        Leading words of the issue_id, 'device_replaced_gary_iphone' removes
        'device_replaced_gary_iphone_...' but not 'device_replaced_gary_iphone2_...'

    The device's sensor.icloud3_alerts entry is not cleared. It is shared by all of
    the device's issues (keyed by fname) and this runs right after a new issue for
    the device may have been posted. The alerts sensor is reset when iCloud3 starts.
    '''
    from .messaging import log_exception
    issue_id_prefix = f"{slugify(issue_id_prefix)}_"
    keep_issue_ids  = [slugify(issue_id) for issue_id in (keep_issue_ids or []) if issue_id]

    def _async_delete_issues():
        issue_registry = ir.async_get(Gb.hass)
        for domain, issue_id in list(issue_registry.issues):
            if (domain == DOMAIN
                    and issue_id.startswith(issue_id_prefix)
                    and issue_id not in keep_issue_ids):
                ir.async_delete_issue(Gb.hass, DOMAIN, issue_id)

    try:
        _run_in_event_loop(_async_delete_issues)
    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def clear_repair_issue_alert_msg(alert_key):
    '''
    Remove the sensor.icloud3_alerts entry for the alert_key (from the issue's data,
    a device's fname, Apple acct username_id or other text) if it is a Repairs issue
    notification (has REPAIR_ISSUED_ALERT_MSG). Another alert that replaced it is
    left. Called by repairs.py after Submit.
    '''
    from .messaging import update_alert_sensor
    if REPAIR_ISSUED_ALERT_MSG in Gb.alerts_sensor_attrs.get(alert_key, ''):
        update_alert_sensor(alert_key, '')

#--------------------------------------------------------------------
def register_repair_fix_handler(fix_action, handler):
    '''
    Register the function run when Submit is selected on a fixable Repairs issue.

    handler(fix_data) -> bool:
        fix_data - the issue's data (devicename, fix_action and the fix_data values)
        Return True if fixed (the issue is removed), False if it failed (the issue
        stays in Repairs). It runs in an executor thread so it can use the iCloud3
        routines and write the configuration file.
    '''
    repair_fix_handlers[fix_action] = handler

# 'acknowledge' - The issue is a notice. Submit removes it and its alerts sensor message.
register_repair_fix_handler('acknowledge', lambda fix_data: True)

#--------------------------------------------------------------------
def _run_in_event_loop(func, *args, **kwargs):
    '''
    Run an HA @callback function in the event loop. iCloud3 startup and tracking
    run in executor threads, so the call is scheduled without waiting for it
    (waiting from the event loop thread would deadlock).
    '''
    if Gb.hass is None:
        return

    if threading.get_ident() == Gb.hass.loop_thread_id:
        func(*args, **kwargs)
    else:
        Gb.hass.loop.call_soon_threadsafe(partial(func, *args, **kwargs))

#--------------------------------------------------------------------
def _evlog_msg_to_markdown(msg):
    '''
    Convert Event Log formatting to markdown for the Repairs dialog
    '''
    msg = re.sub(r'\^\w\^', '', str(msg))
    msg = msg.replace(CRLF_DOT, '\n- ')
    msg = msg.replace(CRLF, '  \n')
    for nbsp in (NBSP6, NBSP5, NBSP4, NBSP3, NBSP2, NBSP):
        msg = msg.replace(nbsp, ' ')

    return msg.strip()

