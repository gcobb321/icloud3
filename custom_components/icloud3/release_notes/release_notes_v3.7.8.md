## 🍎 iCloud3 v3.7.8
### 🐞 Bug Fixes
1. **Update cycle** - A rejected/old location no longer aborts the interval calculation and leaves `is_force_icloud_update` set (which produced an iCloud request on every 5-second cycle).
2. **Reload / remove** - The 5-second polling loop, restore-state timer and internet-status timer are now cancelled on unload. Previously a removed entry kept polling and every reload added another loop.
3. **Timezone** - The UTC offset was inverted twice for negative offsets (America, etc.), shifting displayed times in the wrong direction.
4. **Mobile App** - Fixed two guard expressions that never matched (new StatZone entry and "no location change").
5. **Mobile App** - A sleeping iPad reporting `unknown` no longer disables Mobile App monitoring after four minutes.
6. **Mobile App** - The verification retry handler was named `x_...` and raised `AttributeError`, so unverified devices were never retried.
7. **Startup Events** - Reloading no longer replaces the startup record list with a dict and breaks the Startup Events screen/export.
8. **Configuration** - All devices are verified, migration steps are isolated, and a partially migrated file is not written.
9. **Waze** - Bounded retry waits, indexed history queries, write-only commits, batched deletes and an idempotent database close.
10. **Services** - An unknown `device_name` is reported instead of silently applying the action to every device.
11. **Device sensors** - Deleted entity-registry entries were classified as disabled, so device sensors were skipped at startup (only the device_tracker remained). Reload also kept stale sensor links. Both are fixed; a device now shows its full sensor set again.

### 🎉 New and Improved Items
1. **Diagnostics** - `Download diagnostics` now produces a redacted report (counts and versions only; no account names, tokens or locations).
2. **Repairs** - Apple reauthentication and stale Mobile App mappings are now visible in Settings > Repairs. A stale mapping can be cleared with Submit.
3. **Startup reliability** - Config writes triggered by entity-registry events move off the event loop, and config JSON writes fall back when `atomic_writes` is unavailable.
4. **Tests / CI** - Added Home-Assistant-free tests for the timezone/validator helpers, regression contracts for the fixed bugs, and a CI gate (ruff, strict mypy on the pure modules, 90% coverage of the pure module).

### ⚠️ Behaviour Changes
- A Mobile App device that is disabled, reserved by another device, or renamed in the HA registry is no longer silently mapped. iCloud3 reports the device instead of monitoring the wrong tracker.
- `fixed_interval: 0` (the default, meaning "no fixed interval") is preserved. Only an explicitly set value below 3 is raised to 3.
