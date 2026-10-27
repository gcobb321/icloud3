Only the summaries are kept; the conversation itself isn't. Tomorrow, open with something like:

"Continue the iCloud3 Repairs work. Here's the list of errors start_ic3 / start_ic3_control can detect that should become repairs: …"

For each item, give the error type, whether it's a device or Apple account error, how it's detected (the alert-sensor text or the place in start_ic3), and which screen should fix it. That's enough to build the generic scan and the Apple account hook without re-reading everything.

Two loose ends from today that aren't repair work:

exit_configure_settings_final_tasks sets is_initialize_options_required = False. That may have been meant to be True (it's in memory).
common_form_handler in config_flow.py is dead code that calls six methods that don't exist.


Add to settings.json:
"commands.commands": {
    "⇥ Indent":  { "command": "editor.action.indentLines",  "statusBar": { "alignment": "left" } },
    "⇤ Outdent": { "command": "editor.action.outdentLines", "statusBar": { "alignment": "left" } }
}




## Task: Fix iCloud3 startup hang caused by Internet connectivity check

### Problem
iCloud3 runs an Internet availability test during startup using `requests` with
`timeout=30`. This appears to hang Home Assistant's startup. The timeout was
reduced to 5 as a stopgap, but the root cause is likely a blocking call running
on HA's event loop. Also, the `requests` timeout does not cover DNS resolution,
so with no network it can hang well past the timeout.

### Goal
The connectivity check must never block the HA event loop or delay HA startup.
If the Internet is unavailable, iCloud3 should keep retrying in the background
until it comes up.

### Steps
1. Find every place the Internet/connectivity test is called during startup.
   For each one, decide whether it runs on the event loop or in a worker thread
   (executor). Report this before changing anything.
2. If the code is on the event loop, replace the `requests` call with HA's shared
   aiohttp session:

   import aiohttp
   from homeassistant.helpers.aiohttp_client import async_get_clientsession

   async def internet_available(hass, url="https://www.apple.com") -> bool:
       session = async_get_clientsession(hass)
       timeout = aiohttp.ClientTimeout(total=5, connect=3)
       try:
           async with session.get(url, timeout=timeout, allow_redirects=False) as resp:
               return resp.status < 500
       except (aiohttp.ClientError, TimeoutError):
           return False

   - `total` includes DNS, which avoids the DNS hang.
   - Never close the shared session.
3. If the code runs in a worker thread and needs the result, call the async
   version with:

   future = asyncio.run_coroutine_threadsafe(internet_available(hass), hass.loop)
   is_online = future.result(timeout=8)   # wrap in try/except -> False

   NEVER call `future.result()` from the event loop thread (deadlock). Guard
   with `hass.loop_thread_id == threading.get_ident()` if unsure.
   Alternative: stay sync with `requests.get(url, timeout=(3, 5))`. This is
   acceptable only in a worker thread, and DNS is still not covered.
4. Don't make `async_setup_entry` wait on the check or the initial Apple
   Account login. Either:
   - start them with `hass.async_create_background_task(...)` so setup
     returns quickly, or
   - raise `ConfigEntryNotReady` on a connection failure and let HA retry
     with backoff.
   Pick whichever fits iCloud3's existing startup flow and explain the choice.

### Verify
- Start HA with the network disconnected. HA must finish startup promptly, and
  iCloud3 should log that the Internet is unavailable and keep retrying.
- Reconnect the network. iCloud3 should recover without an HA restart.
- Check the HA log for "Detected blocking call" warnings from iCloud3. There
  should be none.
