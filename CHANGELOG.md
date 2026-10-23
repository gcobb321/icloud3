# Changelog

User-facing changes per release. The detailed, developer-level notes for each
release live in [`custom_components/icloud3/release_notes/`](custom_components/icloud3/release_notes/).

## v3.7.8

Update from HACS, then restart Home Assistant. No configuration changes are
required; the existing configuration file is migrated automatically and a
backup copy is kept next to it.

### Fixed

- **Tracking no longer keeps requesting an iCloud location every 5 seconds**
  after a location update is rejected, so battery use and the Event Log return
  to their normal cadence.
- **Removing or reloading the integration now stops its timers and the 5-second
  polling loop.** A removed entry no longer keeps running in the background and
  repeated reloads no longer stack up extra loops.
- **Times are displayed correctly in time zones west of UTC.** The UTC offset
  was applied with the wrong sign, which shifted event and arrival times.
- **Mobile App tracking keeps working for sleeping iPads.** A device that
  reports `unknown` while asleep is no longer treated as gone after four
  minutes, and the verification retry actually runs again.
- **Devices show their full set of sensors after a restart or reload.**
  Registry entries whose entities had been deleted were mistaken for disabled
  ones, which left only the `device_tracker` available.
- **The Startup Events screen survives a reload** instead of switching to a
  different data shape and failing to display or export.
- **Configuration migration is all-or-nothing.** Every device is verified and a
  half-migrated file is never written.
- **Waze travel time is more reliable** on long-running systems: bounded retry
  waits, indexed history lookups, batched deletes and an idempotent database
  close.
- **Services report an unknown device name** instead of silently applying the
  action to every device.

### Improved
- `sensor.icloud3_health` with loop/Apple/Waze/config-write counters.
- Configuration schema versioning, five rolling backups and downgrade protection.
- Waze history WAL mode; Event Log display cache.

- **Download diagnostics** now produces a redacted report containing only
  counts, versions and non-identifying settings. Account names, tokens and
  locations are removed.
- **Settings > Repairs** now shows Apple Account reauthentication requests and
  stale Mobile App device mappings. A stale mapping can be cleared with
  **Submit**; iCloud3 then falls back to iCloud tracking for that device.
- **Startup is more resilient**: configuration writes triggered by entity
  registry events no longer block the event loop, and configuration writes fall
  back safely when atomic writes are unavailable.

### Behaviour changes

- A Mobile App device that is disabled, already reserved by another device, or
  renamed in the Home Assistant registry is no longer mapped silently. iCloud3
  reports the device instead of monitoring the wrong tracker.
- `fixed_interval: 0` still means "no fixed interval". Only an explicitly set
  value below 3 is raised to 3.

Full notes: [release_notes_v3.7.8.md](custom_components/icloud3/release_notes/release_notes_v3.7.8.md)

## Earlier releases

Detailed notes for the versions before v3.7.8:

- [v3.7.7](custom_components/icloud3/release_notes/release_notes_v3.7.7.md)
- [v3.7.6](custom_components/icloud3/release_notes/release_notes_v3.7.6.md)
- [v3.7.5](custom_components/icloud3/release_notes/release_notes_v3.7.5.md)
- [v3.7.4 (base)](custom_components/icloud3/release_notes/release_notes_v3.7.4-base.md)

Beta and prerelease notes are kept in the same folder.
