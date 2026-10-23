'''
Library exceptions for the Apple Account authentication code.

This module has no imports on purpose. The exception hierarchy is shared by
apple_acct.py and icloud_session.py (both used to define their own copy) and
must stay importable without Home Assistant so the tests can load it directly.
'''

class AppleAcctException(Exception):
    '''Generic iCloud exception.'''
    pass

#----------------------------------------------------------------------------
class AppleAcctAPIResponseException(AppleAcctException):
    '''iCloud response exception.'''
    def __init__(self, reason, code=None, retry=False):

        self.reason = reason
        self.code = code
        message = reason or "Could not connect to iCloud Location Servers"
        if code:
            message += (f" (Error Code {code})")
        if retry:
            message += ". Retrying ..."

        super(AppleAcctAPIResponseException, self).__init__(message)

#----------------------------------------------------------------------------
class AppleAcctManagerNotActivatedException(AppleAcctAPIResponseException):
    '''iCloud service not activated exception.'''
    pass

#----------------------------------------------------------------------------
class AppleAcctFailedLoginException(AppleAcctException):
    '''iCloud failed login exception.'''
    pass

#----------------------------------------------------------------------------
class AppleAcct2FARequiredException(AppleAcctException):
    '''iCloud 2SA required exception.'''
    pass

#----------------------------------------------------------------------------
class AppleAcct2SARequiredException(AppleAcctException):
    """iCloud 2SA required exception."""
    def __init__(self, apple_id):
        message = f"Two-step authentication required for account: {apple_id}"
        super().__init__(message)

#----------------------------------------------------------------------------
class AppleAcctNoStoredPasswordAvailableException(AppleAcctException):
    '''iCloud no stored password exception.'''
    pass

#----------------------------------------------------------------------------
class AppleAcctNoDevicesException(AppleAcctException):
    '''iCloud no device exception.'''
    pass
