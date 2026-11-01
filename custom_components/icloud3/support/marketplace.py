'''
iCloud3 version information from the HACS / HA Marketplace update entities and the
switch from the iCloud3 Beta repository (gcobb321/icloud3_v3) to the iCloud3
repository (gcobb321/icloud3).

HA 2026.11 replaced HACS with the Marketplace integration. The HACS update entities
were moved to the Marketplace with the same entity_id and unique_id. The unique_id
is the GitHub repository id, it is the same for every installation. The entity_id
is not, it was created from the HACS name when the repository was downloaded.

    gcobb321/icloud3     - 222292912 - iCloud3 (catalog repository)
    gcobb321/icloud3_v3  - 394419578 - iCloud3 Beta (custom repository)

The update entity is only available for the repository that is installed. Both use
the 'icloud3' custom_components directory. The Marketplace will not install one
while the other one is installed (integration_owned), HACS did.
'''

from ..global_variables     import GlobalVariables as Gb
from ..const                import (DOMAIN, )
from ..const_char           import (CRLF_DOT, )

from ..utils.messaging      import (log_info_msg, log_exception, post_event, post_config_error, )

from homeassistant.config_entries   import ConfigEntryState
from homeassistant.helpers          import entity_registry as er
from homeassistant.const            import (MAJOR_VERSION, MINOR_VERSION, )

import re
import logging
_LOGGER = logging.getLogger(f"icloud3")

# The beta part of a version, -beta.3, -b.3, -b3 (and -beta.3.1)
BETA_VERSION_RE = re.compile(r'-(?:beta|b)\.?(\d+(?:\.\d+)?)$')

IC3_REPO_ID      = '222292912'      # gcobb321/icloud3
IC3_BETA_REPO_ID = '394419578'      # gcobb321/icloud3_v3

# The integrations with the update entities, checked in this order. 'hacs' is used
# before HA 2026.11 and during the first startup after the update until the
# Marketplace has moved the HACS entities.
MARKETPLACE = 'marketplace'
HACS        = 'hacs'
STORE_DOMAINS = (MARKETPLACE, HACS)
STORE_FNAME   = {MARKETPLACE: 'Marketplace', HACS: 'HACS'}

IS_HA_MARKETPLACE_VERSION = (MAJOR_VERSION, MINOR_VERSION) >= (2026, 11)

BETA_MOVING_ALERT_MSG = f"iCloud3 was installed from the iCloud3 Beta GitHub "\
                        f"repository. This repo is longer updated, future "\
                        f"betas will be available as pre-releases versions in the "\
                        f"iCloud3 repository. Run the following Repair Action "\
                        f"to reset your HACS/Markerplace configuration."\
                        f"{CRLF_DOT}Select HA Settings > Repairs > "\
                        f"Beta Versions are moving to the iCloud3 Repo"\


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE ENTITY ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def repo_update_entity(repo_id):
    '''
    Find the HACS or Marketplace update entity for the repository in the HA Entity
    Registry. The registry is loaded before the integrations are set up so it is
    available during startup.

    Return:
        (store_domain, entity_id) - ('marketplace', 'update.icloud3')
        (None, None)              - The repository is not installed from either one
    '''
    try:
        entity_reg = er.async_get(Gb.hass)
        for store_domain in STORE_DOMAINS:
            if entity_id := entity_reg.async_get_entity_id('update', store_domain, repo_id):
                return store_domain, entity_id

    except Exception as err:
        log_exception(err)

    return None, None

#--------------------------------------------------------------------
def repo_versions(repo_id):
    '''
    Get the installed and available versions from the repository's update entity.

    Return:
        (installed_version, latest_version), (None, None) if the entity does not exist
        or is not available (startup, no GitHub connection for a custom repository)
    '''
    store_domain, entity_id = repo_update_entity(repo_id)
    if entity_id is None:
        return None, None

    State = Gb.hass.states.get(entity_id)
    if State is None:
        return None, None

    return (State.attributes.get('installed_version'),
            State.attributes.get('latest_version'))


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 UPDATE AVAILABLE CHECK
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def check_hacs_icloud3_update_available():
    check_icloud3_update_available()

#--------------------------------------------------------------------
def check_icloud3_update_available():
    '''
    Set Gb.version_hacs to the newer iCloud3 version available on the HACS or
    Marketplace update entity of the iCloud3 or iCloud3 Beta repository, '' if there
    is not one. Only the installed repository has an update entity. The iCloud3
    entity offers a beta version when its Pre-release switch is on.

    It reads the entity registry and states and can be run in the event loop or an
    executor thread (hourly timer).
    '''
    if Gb.version_hacs == '0.0.0':
        return

    try:
        ic3_installed,  ic3_latest  = repo_versions(IC3_REPO_ID)
        beta_installed, beta_latest = repo_versions(IC3_BETA_REPO_ID)

        if ic3_latest is None and beta_latest is None:
            Gb.version_hacs = ''
            return

        ic3_newer  = _is_2nd_version_newer(Gb.version, ic3_latest)
        beta_newer = _is_2nd_version_newer(Gb.version, beta_latest)

        Gb.version_hacs = ''
        if beta_newer:
            Gb.version_hacs = beta_latest
        elif ic3_newer:
            Gb.version_hacs = ic3_latest

        store_domain, _entity_id = repo_update_entity(IC3_REPO_ID if ic3_latest else IC3_BETA_REPO_ID)
        store_fname   = STORE_FNAME.get(store_domain, 'HACS')
        update_avail_msg = f", {store_fname} Update Available-{Gb.version_hacs}" if Gb.version_hacs else ""

        post_event( f"Checking {store_fname} for new iCloud3 Version"
                    f"{update_avail_msg}, "
                    f"Running-v{Gb.version}"
                    f"{_version_msg('iCloud3', ic3_latest, ic3_newer)}"
                    f"{_version_msg('iCloud3 Beta', beta_latest, beta_newer)}")

    except Exception as err:
        log_exception(err)
        Gb.version_hacs = ''

#...................................................................
def _version_msg(repo_fname, latest_version, is_newer):
    if latest_version is None:
        return ''
    return f", {repo_fname}-{latest_version}{' (Newer)' if is_newer else ''}"

#--------------------------------------------------------------------
def _is_2nd_version_newer(version_1, version_2):
    '''
    Compare the version_1 and _2 values for the newest one.
    Return:
        True - version_2 is newer than version_1
        False - version_1 is newer than version_2

    version_1   version_2   Result
    v3.0.2      v3.0.23      True
    v3.0.3      v3.0.3       False
    v3.0.3b1    v3.0.3       True
    v3.0.3      v3.0a        False
    v3.0.4      v3.0.3.1     True
    '''

    if version_1 is None or version_2 is None:
        return False

    v1_value, v1_beta = _get_version_value(version_1)
    v2_value, v2_beta = _get_version_value(version_2)

    # version_2 is newer
    if  (v2_value > v1_value):
        return True

    # version_2 is the same as version_1 but not beta or beta is newer. A beta is
    # never newer than the release with the same version.
    elif v2_value == v1_value and v1_beta > 0:
        if (v2_beta == 0
                or v2_beta > v1_beta):
            return True

    return False

#--------------------------------------------------------------------
def _get_version_value(version):
    '''
    Return the release and beta number values of the version. The beta can be
    -beta.N, -b.N or -bN, 0 is a release.
        v3.8.0          - (3080000, 0)
        v3.8.1-beta.3   - (3080100, 300)
        v3.8.1-b.12     - (3080100, 1200)
        v3.7.4.1        - (3070410, 0)
    '''
    version = version.strip().lstrip('vV')
    v_base, v_beta = version, '0'
    if beta_match := BETA_VERSION_RE.search(version):
        v_base, v_beta = version[:beta_match.start()], beta_match.group(1)

    v_parts = (f"{v_base}.0.0.0.0").split('.')
    b_parts = (f"{v_beta}.0.0.0.0").split('.')

    r_version = 0
    b_version = 0

    try:
        b_version = int(b_parts[0])*100
        b_version += int(b_parts[1])

        r_version += int(v_parts[0])*1000000
        r_version += int(v_parts[1])*10000
        r_version += int(v_parts[2])*100
        r_version += int(v_parts[3])*10
        r_version += int(v_parts[4])
    except:
        pass

    return r_version, b_version


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SWITCH FROM THE ICLOUD3 BETA REPOSITORY TO THE ICLOUD3 REPOSITORY
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def check_icloud3_beta_repository():
    '''
    The iCloud3 beta versions are released as pre-releases in the iCloud3 repository.
    The iCloud3 Beta repository (gcobb321/icloud3_v3) is no longer updated. Add the
    'switch_repository' issue to HA Repairs if iCloud3 was installed from it. Submit
    runs async_switch_to_icloud3_repository (repairs.iCloud3SwitchRepositoryRepairFlow).

    It is posted on every startup until the switch is done and is removed with the
    other configuration errors when the iCloud3 Beta update entity no longer exists.
    '''
    try:
        store_domain, entity_id = repo_update_entity(IC3_BETA_REPO_ID)
        if store_domain is None:
            return

        store_fname = STORE_FNAME[store_domain]
        post_config_error(
                source      = 'icloud3_beta_to_prerelease',
                source_name = 'iCloud3',
                error       = 'Beta versions are now iCloud3 Prereleases',
                #error_item  = store_fname,
                message     = BETA_MOVING_ALERT_MSG,
                details     = f"",
                repair_step = 'switch_repository',
                translation_placeholders = {'store': store_fname})

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def _store_manager(store_domain):
    '''
    Get the HACS or Marketplace object with the repositories and its config entry.
    These are not a public interface, they are the integration's own objects.

    Return:
        (manager, config_entry), (None, None) if it is not loaded
    '''
    config_entry = next((config_entry
                            for config_entry in Gb.hass.config_entries.async_entries(store_domain)
                            if config_entry.state is ConfigEntryState.LOADED), None)
    if config_entry is None:
        return None, None

    if store_domain == MARKETPLACE:
        manager = getattr(config_entry, 'runtime_data', None)
    else:
        manager = Gb.hass.data.get(HACS)

    return manager, config_entry

#--------------------------------------------------------------------
async def async_switch_to_icloud3_repository():
    '''
    Move the installation from the iCloud3 Beta repository to the iCloud3 repository
    in HACS or the Marketplace without changing the files or the iCloud3 config entry.
    Both repositories use the 'icloud3' custom_components directory so the files
    installed from the Beta repository are the iCloud3 repository's files. The same
    version must be released in both repositories (a pre-release in the iCloud3
    repository) so the iCloud3 update entity does not offer it as an update.

        - iCloud3 Beta - Not installed, its update entity and device are removed
        - iCloud3      - Installed with the Beta repository's version and the
                         Pre-release switch on so the beta versions are offered
        - The HACS/Marketplace data is saved and its config entry is reloaded to
          add the iCloud3 update and Pre-release switch entities

    The Marketplace's Uninstall can not be used, it deletes the icloud3 directory and
    is refused while an icloud3 config entry exists.

    Return:
        '' - The switch was done
        abort reason in the switch_repository fix_flow - It was not done, nothing
                was changed:
            'store_not_loaded'  - HACS/Marketplace is not loaded
            'repo_not_found'    - A repository is not in the HACS/Marketplace data or
                                  its objects are not the ones this was written for
            'fix_action_failed' - An error occurred, see the icloud3.log file
    '''
    store_domain, entity_id = repo_update_entity(IC3_BETA_REPO_ID)
    if store_domain is None:
        return ''

    store_fname = STORE_FNAME[store_domain]
    manager, config_entry = _store_manager(store_domain)
    if manager is None:
        post_event(f"Switch to iCloud3 Repository > {store_fname} is not loaded")
        return 'store_not_loaded'

    try:
        BetaRepo = manager.repositories.get_by_id(IC3_BETA_REPO_ID)
        Ic3Repo  = manager.repositories.get_by_id(IC3_REPO_ID)

        if (BetaRepo is None or Ic3Repo is None
                or BetaRepo.data.installed is False
                or Ic3Repo.data.domain not in (None, DOMAIN)
                or not hasattr(BetaRepo, 'async_remove_entity_device')
                or not hasattr(manager.data, 'async_write')):
            post_event(f"Switch to iCloud3 Repository > {store_fname}, "
                        f"The iCloud3 or iCloud3 Beta repository was not found")
            return 'repo_not_found'

    except Exception as err:
        log_exception(err)
        return 'repo_not_found'

    # The running version is the one in the icloud3 directory. HACS/Marketplace has
    # an old version if the files were not installed by it.
    installed_version = f"v{Gb.version}"
    data_fields = ('installed', 'installed_version', 'installed_commit', 'show_beta', 'domain')
    beta_repo_data = {field: getattr(BetaRepo.data, field) for field in data_fields}
    ic3_repo_data  = {field: getattr(Ic3Repo.data, field)  for field in data_fields}

    try:
        Ic3Repo.data.installed         = True
        Ic3Repo.data.installed_version = installed_version
        Ic3Repo.data.installed_commit  = BetaRepo.data.installed_commit
        Ic3Repo.data.show_beta         = True
        Ic3Repo.data.domain            = DOMAIN

        BetaRepo.data.installed         = False
        BetaRepo.data.installed_version = None
        BetaRepo.data.installed_commit  = None
        BetaRepo.data.show_beta         = False

        await manager.data.async_write(force=True)

    except Exception as err:
        log_exception(err)
        # Put the data back, it may or may not have been saved
        for field, value in beta_repo_data.items(): setattr(BetaRepo.data, field, value)
        for field, value in ic3_repo_data.items():  setattr(Ic3Repo.data,  field, value)
        try:
            await manager.data.async_write(force=True)
        except Exception as err:
            log_exception(err)
        return 'fix_action_failed'

    # The data was saved, the entities are updated when the config entry is reloaded.
    # The iCloud3 Pre-release switch is only enabled by default when it is added to
    # the entity registry. One added when the beta versions were off stays disabled.
    try:
        await BetaRepo.async_remove_entity_device()

        entity_reg = er.async_get(Gb.hass)
        switch_entity_id = entity_reg.async_get_entity_id('switch', store_domain, IC3_REPO_ID)
        if (switch_entity_id
                and entity_reg.async_get(switch_entity_id).disabled_by
                        is er.RegistryEntryDisabler.INTEGRATION):
            entity_reg.async_update_entity(switch_entity_id, disabled_by=None)

        await Gb.hass.config_entries.async_reload(config_entry.entry_id)
    except Exception as err:
        log_exception(err)

    post_event( f"Switch to iCloud3 Repository > {store_fname}, "
                f"Installed from gcobb321/icloud3, Version-{installed_version}, "
                f"Pre-release (beta) versions are offered")
    log_info_msg(f"iCloud3 switched from the iCloud3 Beta repository (gcobb321/icloud3_v3) to "
                f"the iCloud3 repository (gcobb321/icloud3) in {store_fname}, "
                f"Version-{installed_version}, Pre-release On")

    return ''

#--------------------------------------------------------------------
def icloud3_prerelease_switch_state():
    '''
    Get the state of the iCloud3 repository's Pre-release switch in HACS or the
    Marketplace.

    Return:
        True  - The switch is on, beta versions are offered
        False - The switch is off
        None  - The switch was not found, is disabled or is not available
    '''
    store_domain, update_entity_id = repo_update_entity(IC3_REPO_ID)
    if store_domain is None:
        return None

    try:
        entity_reg = er.async_get(Gb.hass)
        switch_entity_id = entity_reg.async_get_entity_id('switch', store_domain, IC3_REPO_ID)
        if switch_entity_id is None:
            return None

        State = Gb.hass.states.get(switch_entity_id)
        if State is None or State.state not in ('on', 'off'):
            return None

        return State.state == 'on'

    except Exception as err:
        log_exception(err)

    return None

#--------------------------------------------------------------------
async def async_set_icloud3_prerelease_switch(turn_on):
    '''
    Turn the iCloud3 repository's Pre-release switch in HACS or the Marketplace on or
    off so beta versions are or are not offered by the iCloud3 update entity. This is
    the same as changing the switch on the store's iCloud3 device screen.

    The switch is found by its unique_id (the repository id), its entity_id is the
    one created from the HACS name when the repository was downloaded. A disabled
    switch is not loaded and can not be changed. It is enabled and the store's config
    entry is reloaded to add it.

    Return:
        '' - The switch was changed
        'repo_not_installed'  - iCloud3 was not installed from HACS/Marketplace
        'switch_not_found'    - The repository does not have a Pre-release switch
        'fix_action_failed'   - An error occurred, see the icloud3.log file
    '''
    on_off = 'On' if turn_on else 'Off'

    store_domain, update_entity_id = repo_update_entity(IC3_REPO_ID)
    if store_domain is None:
        post_event(f"iCloud3 Pre-release Versions > Not changed, iCloud3 was not "
                    f"installed from HACS/Marketplace")
        return 'repo_not_installed'

    store_fname = STORE_FNAME[store_domain]

    try:
        entity_reg = er.async_get(Gb.hass)
        switch_entity_id = entity_reg.async_get_entity_id('switch', store_domain, IC3_REPO_ID)
        if switch_entity_id is None:
            post_event(f"iCloud3 Pre-release Versions > Not changed, The {store_fname} "
                        f"Pre-release switch was not found")
            return 'switch_not_found'

        if entity_reg.async_get(switch_entity_id).disabled_by is not None:
            entity_reg.async_update_entity(switch_entity_id, disabled_by=None)
            manager, config_entry = _store_manager(store_domain)
            if config_entry is not None:
                await Gb.hass.config_entries.async_reload(config_entry.entry_id)

        await Gb.hass.services.async_call('switch', 'turn_on' if turn_on else 'turn_off',
                                            {'entity_id': switch_entity_id}, blocking=True)

    except Exception as err:
        log_exception(err)
        return 'fix_action_failed'

    post_event( f"iCloud3 Pre-release Versions > {store_fname}, "
                f"Pre-release (beta) versions are {'offered' if turn_on else 'not offered'}, "
                f"Switch-{switch_entity_id}")
    log_info_msg(f"iCloud3 Pre-release switch turned {on_off} in {store_fname}, "
                f"Entity-{switch_entity_id}")

    return ''
