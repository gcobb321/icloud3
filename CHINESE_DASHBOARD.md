# Simplified Chinese dashboard preview

This branch includes configuration translations and dashboard presentation localization.

## Installation and preview

1. Back up the installed `custom_components/icloud3` directory and the existing dashboard configuration.
2. Install the complete integration directory from this branch, keeping existing `.storage` account/device configuration.
3. Restart Home Assistant.
4. Set the Home Assistant server language to Simplified Chinese for generated dashboard templates. The Event Log card follows the current frontend user's language (`zh-Hans`).
5. Use the iCloud3 Dashboard Builder to recreate the dashboard. Recreating stores the previous main view as a backup; customized existing views are not silently rewritten.
6. Refresh the browser (hard refresh if necessary). The Event Log card version is 3.7.1 to allow the integration's resource update mechanism to recognize the changed card. If your deployment uses a custom resource path, verify that the served JavaScript is the updated file.

Built-in tabs, summary headings, explanatory template text, Event Log title, action menu and logging indicators are translated. Common Event Log field prefixes and configuration headings are translated in text nodes only. Device names, email addresses, coordinates, entity IDs, paths, command values, and the sensor's original log records are preserved.

Detailed backend diagnostic messages and third-party errors are not exhaustively translated. Generated dashboards use the server language at generation time; changing a user's frontend language alone does not regenerate them.

## Validation

Run `python -m unittest discover -s tests -p 'test_dashboard_localization.py'`.
The card has also been syntax-checked and tested with a lightweight DOM stub for Chinese/English control switching, idempotence and preservation of device/account/coordinate text. Live Home Assistant visual validation is still required.
