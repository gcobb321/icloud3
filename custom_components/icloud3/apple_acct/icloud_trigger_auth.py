#!/usr/bin/env python3
"""
icloud_trigger_2fa.py

Triggers iCloud 2FA by automating login on iCloud.com.
Auto-detects the system default browser on Windows and macOS.
iPhone/iPad access via built-in web server mode.

Supported browsers: Chrome, Edge, Firefox, Safari (macOS), Brave
Usage:
    # Uses system default browser automatically
    python icloud_trigger_2fa.py --username you@example.com --password yourpass

    # Force a specific browser
    python icloud_trigger_2fa.py --browser edge
    python icloud_trigger_2fa.py --browser firefox
    python icloud_trigger_2fa.py --browser safari   # macOS only

    # Web server mode (iPhone / iPad / any device on your LAN)
    python icloud_trigger_2fa.py --server
    python icloud_trigger_2fa.py --server --port 8080

Requirements:
    pip install selenium webdriver-manager flask

    Safari (macOS) — one-time setup:
        Safari → Settings → Advanced → enable "Show features for web developers"
        Then: Develop → Allow Remote Automation
"""

import argparse
import getpass
import os
import platform
import plistlib
import subprocess
import sys
import threading
import time
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# ── Timeouts ─────────────────────────────────────────────────────────────────
PAGE_LOAD_TIMEOUT = 30
ELEMENT_TIMEOUT   = 20
POST_ACTION_DELAY = 1.5
SIGNOUT_WAIT      = 3

# ── Selectors ─────────────────────────────────────────────────────────────────
SEL_APPLE_ID_FIELD = (By.ID, "account_name_text_field")
SEL_CONTINUE_BTN   = (By.ID, "sign-in")
SEL_PASSWORD_FIELD = (By.ID, "password_text_field")
SEL_SIGNIN_BTN     = (By.ID, "sign-in")
SEL_2FA_SCREEN     = (By.CSS_SELECTOR,
                        "#stepEl .si-container, "
                        "#two-factor-authentication-enter-code, "
                        "[data-testid='two-factor']")

# ── Active web-server sessions ────────────────────────────────────────────────
_sessions: dict = {}


# ═════════════════════════════════════════════════════════════════════════════
# Default browser detection
# ═════════════════════════════════════════════════════════════════════════════

def detect_default_browser() -> str:
    """
    Returns one of: chrome | edge | firefox | safari | brave | opera
    Falls back to 'chrome' on Windows/Linux, 'safari' on macOS if detection fails.
    """
    os_name = platform.system()
    if os_name == "Windows":
        return _detect_default_windows()
    elif os_name == "Darwin":
        return _detect_default_mac()
    else:
        return "chrome"   # Linux fallback


def _detect_default_windows() -> str:
    """Read default browser from the Windows registry."""
    try:
        import winreg
        key_path = (r"Software\Microsoft\Windows\Shell\Associations"
                    r"\UrlAssociations\http\UserChoice")
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            prog_id = winreg.QueryValueEx(key, "ProgId")[0].lower()

        if "chrome"  in prog_id: return "chrome"
        if "edge"    in prog_id: return "edge"
        if "firefox" in prog_id: return "firefox"
        if "brave"   in prog_id: return "brave"
        if "opera"   in prog_id: return "opera"
        return "chrome"
    except Exception as e:
        print(f"  ⚠ Could not read default browser from registry: {e}")
        return "chrome"


def _detect_default_mac() -> str:
    """
    Read default browser from macOS LaunchServices plist.
    Falls back to Safari if anything goes wrong.
    """
    plist_path = os.path.expanduser(
        "~/Library/Preferences/com.apple.LaunchServices/"
        "com.apple.launchservices.secure.plist"
    )
    try:
        # Convert binary plist → XML so plistlib can parse it
        result = subprocess.run(
            ["plutil", "-convert", "xml1", "-o", "-", plist_path],
            capture_output=True, check=True
        )
        plist = plistlib.loads(result.stdout)

        for handler in plist.get("LSHandlers", []):
            if handler.get("LSHandlerURLScheme") == "http":
                bundle = handler.get("LSHandlerRoleAll", "").lower()
                if "chrome"           in bundle: return "chrome"
                if "firefox"          in bundle: return "firefox"
                if "microsoft.edge"   in bundle: return "edge"
                if "brave"            in bundle: return "brave"
                if "opera"            in bundle: return "opera"
                # empty bundle → Safari is the default
                return "safari"

        return "safari"
    except Exception as e:
        print(f"  ⚠ Could not read default browser from LaunchServices: {e}")
        return "safari"


# ═════════════════════════════════════════════════════════════════════════════
# WebDriver factory — one builder per browser
# ═════════════════════════════════════════════════════════════════════════════

def build_driver(browser: str = "default") -> webdriver.Remote:
    """
    Build and return a WebDriver for the requested browser.
    Pass browser='default' to auto-detect the system default.
    """
    if browser in ("default", "auto"):
        browser = detect_default_browser()

    print(f"  Browser : {browser}")

    builders = {
        "chrome":  _build_chrome_driver,
        "edge":    _build_edge_driver,
        "firefox": _build_firefox_driver,
        "safari":  _build_safari_driver,
        "brave":   _build_brave_driver,
        "opera":   _build_opera_driver,
    }

    builder = builders.get(browser)
    if not builder:
        print(f"  ⚠ Unknown browser '{browser}' — falling back to Chrome.")
        builder = _build_chrome_driver

    return builder()


# ── Chrome ────────────────────────────────────────────────────────────────────
def _build_chrome_driver() -> webdriver.Chrome:
    from selenium.webdriver.chrome.options  import Options
    from selenium.webdriver.chrome.service  import Service
    from webdriver_manager.chrome           import ChromeDriverManager

    options = _chromium_options(Options())
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    _mask_webdriver(driver)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# ── Microsoft Edge ────────────────────────────────────────────────────────────
def _build_edge_driver() -> webdriver.Edge:
    from selenium.webdriver.edge.options    import Options
    from selenium.webdriver.edge.service    import Service
    from webdriver_manager.microsoft        import EdgeChromiumDriverManager

    options = _chromium_options(Options())
    service = Service(EdgeChromiumDriverManager().install())
    driver  = webdriver.Edge(service=service, options=options)
    _mask_webdriver(driver)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# ── Firefox ───────────────────────────────────────────────────────────────────
def _build_firefox_driver() -> webdriver.Firefox:
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service
    from webdriver_manager.firefox          import GeckoDriverManager

    options = Options()
    # Suppress automation flags for Firefox
    options.set_preference("dom.webdriver.enabled",   False)
    options.set_preference("useAutomationExtension",  False)
    options.set_preference("general.useragent.override",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    )

    service = Service(GeckoDriverManager().install())
    driver  = webdriver.Firefox(service=service, options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# ── Safari (macOS only) ───────────────────────────────────────────────────────
def _build_safari_driver() -> webdriver.Safari:
    if platform.system() != "Darwin":
        raise RuntimeError(
            "Safari WebDriver is only available on macOS.\n"
            "Enable it in: Safari → Develop → Allow Remote Automation"
        )
    from selenium.webdriver.safari.options  import Options
    from selenium.webdriver.safari.service  import Service

    driver = webdriver.Safari(service=Service(), options=Options())
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# ── Brave ─────────────────────────────────────────────────────────────────────
def _build_brave_driver() -> webdriver.Chrome:
    from selenium.webdriver.chrome.options  import Options
    from selenium.webdriver.chrome.service  import Service
    from webdriver_manager.chrome          import ChromeDriverManager
    from webdriver_manager.core.os_manager import ChromeType

    # Locate Brave binary
    brave_candidates = [
        # Windows
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        # macOS
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        # Linux
        "/usr/bin/brave-browser",
        "/usr/bin/brave",
    ]
    options = _chromium_options(Options())
    for path in brave_candidates:
        if os.path.exists(path):
            options.binary_location = path
            break

    service = Service(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install())
    driver  = webdriver.Chrome(service=service, options=options)
    _mask_webdriver(driver)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# ── Opera ─────────────────────────────────────────────────────────────────────
def _build_opera_driver() -> webdriver.Chrome:
    from selenium.webdriver.chrome.options  import Options
    from selenium.webdriver.chrome.service  import Service
    from webdriver_manager.opera            import OperaDriverManager

    opera_candidates = [
        r"C:\Program Files\Opera\opera.exe",
        r"C:\Program Files (x86)\Opera\opera.exe",
        "/Applications/Opera.app/Contents/MacOS/Opera",
        "/usr/bin/opera",
    ]
    options = _chromium_options(Options())
    options.add_experimental_option("w3c", True)
    for path in opera_candidates:
        if os.path.exists(path):
            options.binary_location = path
            break

    service = Service(OperaDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    _mask_webdriver(driver)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# ── Shared Chromium helpers ───────────────────────────────────────────────────
def _chromium_options(options):
    """Apply common anti-detection flags to any Chromium-based Options object."""
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,900")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return options


def _mask_webdriver(driver):
    """Remove navigator.webdriver flag that Apple checks for."""
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"}
    )


# ═════════════════════════════════════════════════════════════════════════════
# Core automation steps
# ═════════════════════════════════════════════════════════════════════════════

def fill_field(wait, locator, value, field_name, log_fn=print):
    log_fn(f"  → Filling {field_name}...")
    field = wait.until(EC.element_to_be_clickable(locator))
    field.clear()
    field.send_keys(value)
    time.sleep(POST_ACTION_DELAY)


def click_element(wait, locator, label, log_fn=print):
    log_fn(f"  → Clicking '{label}'...")
    btn = wait.until(EC.element_to_be_clickable(locator))
    btn.click()
    time.sleep(POST_ACTION_DELAY)


def wait_for_2fa(wait, log_fn=print):
    log_fn("  → Waiting for 2FA screen...")
    try:
        wait.until(EC.presence_of_element_located(SEL_2FA_SCREEN))
        return True
    except Exception:
        return False


def sign_out(driver, log_fn=print):
    log_fn("  → Signing out...")
    try:
        account_btns = driver.find_elements(
            By.CSS_SELECTOR,
            "button.account-icon, [aria-label='Account'], #settings-btn"
        )
        if account_btns:
            account_btns[0].click()
            time.sleep(1)

        signout_btns = driver.find_elements(
            By.CSS_SELECTOR,
            "a[href*='signout'], button[aria-label*='Sign Out'], [data-testid='signout-btn']"
        )
        if signout_btns:
            signout_btns[0].click()
        else:
            driver.get("https://www.icloud.com/authentication/logout")

        time.sleep(SIGNOUT_WAIT)
        log_fn("  ✓ Signed out.")
    except Exception as e:
        log_fn(f"  ⚠ Sign-out step failed (non-critical): {e}")


def run_automation( username: str, password: str,
                    browser: str = "default",
                    log_fn=print) -> bool:
    """Full automation flow. Returns True if 2FA screen was confirmed."""
    driver  = build_driver(browser)
    wait    = WebDriverWait(driver, ELEMENT_TIMEOUT)
    success = False

    try:
        log_fn("[1] Opening iCloud.com...")
        driver.get("https://www.icloud.com")
        time.sleep(2)

        log_fn("[2] Entering Apple ID...")
        fill_field(wait, SEL_APPLE_ID_FIELD, username, "Apple ID", log_fn)
        click_element(wait, SEL_CONTINUE_BTN, "Continue", log_fn)

        log_fn("[3] Entering password...")
        fill_field(wait, SEL_PASSWORD_FIELD, password, "Password", log_fn)
        click_element(wait, SEL_SIGNIN_BTN, "Sign In", log_fn)

        log_fn("[4] Waiting for Apple to send 2FA code to your trusted device...")
        success = wait_for_2fa(wait, log_fn)

        if success:
            log_fn("DONE: 2FA code has been sent to your trusted Apple device.")
        else:
            log_fn("WARNING: Could not confirm 2FA screen — code may still have been sent.")

        time.sleep(SIGNOUT_WAIT)
        sign_out(driver, log_fn)

    except Exception as e:
        log_fn(f"ERROR: {e}")
    finally:
        time.sleep(2)
        driver.quit()
        log_fn("[Done] Browser closed.")

    return success


# ═════════════════════════════════════════════════════════════════════════════
# Flask web-server mode  (iPhone / iPad / any browser on your LAN)
# ═════════════════════════════════════════════════════════════════════════════

WEB_UI = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>iCloud 2FA Trigger</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f2f2f7;
      display: flex;
      justify-content: center;
      padding: 40px 16px;
      min-height: 100vh;
    }
    .card {
      background: white;
      border-radius: 16px;
      padding: 32px 28px;
      width: 100%;
      max-width: 420px;
      box-shadow: 0 4px 24px rgba(0,0,0,.08);
      height: fit-content;
    }
    h1   { font-size: 22px; font-weight: 700; color: #1c1c1e; margin-bottom: 6px; }
    p.sub { font-size: 14px; color: #6e6e73; margin-bottom: 28px; line-height: 1.5; }
    label { display: block; font-size: 13px; font-weight: 600; color: #3a3a3c; margin-bottom: 6px; }
    input[type=text], input[type=password] {
      width: 100%; padding: 12px 14px; font-size: 16px;
      border: 1.5px solid #d1d1d6; border-radius: 10px;
      margin-bottom: 18px; outline: none; transition: border-color .2s;
    }
    input:focus { border-color: #0071e3; }
    select {
      width: 100%; padding: 12px 14px; font-size: 15px;
      border: 1.5px solid #d1d1d6; border-radius: 10px;
      margin-bottom: 24px; background: white; outline: none;
    }
    button {
      width: 100%; padding: 14px; background: #0071e3; color: white;
      font-size: 16px; font-weight: 600; border: none; border-radius: 12px;
      cursor: pointer; transition: background .2s;
    }
    button:hover    { background: #0064c8; }
    button:disabled { background: #a0a0a5; cursor: default; }
    #log-box {
      margin-top: 28px; background: #1c1c1e; border-radius: 12px;
      padding: 16px; font-family: "SF Mono", Menlo, monospace;
      font-size: 13px; color: #e5e5ea; min-height: 120px;
      max-height: 320px; overflow-y: auto; display: none;
      white-space: pre-wrap; line-height: 1.6;
    }
    #status-badge {
      display: none; margin-top: 18px; padding: 14px 18px;
      border-radius: 12px; font-size: 15px; font-weight: 600; text-align: center;
    }
    .badge-ok   { background:#d1fae5; color:#065f46; }
    .badge-warn { background:#fef3c7; color:#92400e; }
    .badge-err  { background:#fee2e2; color:#991b1b; }
    .detected   { font-size:12px; color:#6e6e73; margin-top:-14px; margin-bottom:18px; }
  </style>
</head>
<body>
<div class="card">
  <h1>☁️ iCloud 2FA Trigger</h1>
  <p class="sub">Logs in to iCloud.com to make Apple send the 2FA code to your trusted device, then signs out.</p>

  <label for="username">Apple ID</label>
  <input type="text" id="username" placeholder="you@icloud.com"
         value="{{ prefill_user }}" autocomplete="username" autocapitalize="none">

  <label for="password">Password</label>
  <input type="password" id="password" placeholder="Apple ID password"
         autocomplete="current-password">

  <label for="browser">Browser (on host machine)</label>
  <select id="browser">
    <option value="default">Default — {{ detected_browser }} (auto-detected)</option>
    <option value="chrome">Chrome</option>
    <option value="edge">Microsoft Edge</option>
    <option value="firefox">Firefox</option>
    <option value="safari">Safari (macOS only)</option>
    <option value="brave">Brave</option>
    <option value="opera">Opera</option>
  </select>

  <button id="go-btn" onclick="startFlow()">Send 2FA Code to My Device</button>

  <div id="status-badge"></div>
  <div id="log-box"></div>
</div>

<script>
let sessionId = null;
let pollTimer = null;

async function startFlow() {
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  const browser  = document.getElementById('browser').value;

  if (!username || !password) { alert('Please enter your Apple ID and password.'); return; }

  const btn    = document.getElementById('go-btn');
  const logBox = document.getElementById('log-box');
  const badge  = document.getElementById('status-badge');

  btn.disabled    = true;
  btn.textContent = 'Working…';
  logBox.style.display = 'block';
  logBox.textContent   = '';
  badge.style.display  = 'none';

  const res  = await fetch('/start', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ username, password, browser })
  });
  const data = await res.json();
  sessionId  = data.session_id;

  pollTimer = setInterval(() => pollStatus(btn, logBox, badge), 1000);
}

async function pollStatus(btn, logBox, badge) {
  const res  = await fetch('/status/' + sessionId);
  const data = await res.json();

  logBox.textContent = data.log.join('\\n');
  logBox.scrollTop   = logBox.scrollHeight;

  if (data.done) {
    clearInterval(pollTimer);
    btn.disabled    = false;
    btn.textContent = 'Send 2FA Code to My Device';

    badge.style.display = 'block';
    if (data.success) {
      badge.className   = 'status-badge badge-ok';
      badge.textContent = '✅ 2FA code sent — check your Apple device and enter it into iCloud3.';
    } else if (data.warning) {
      badge.className   = 'status-badge badge-warn';
      badge.textContent = '⚠️ Could not confirm 2FA screen. The code may still have been sent.';
    } else {
      badge.className   = 'status-badge badge-err';
      badge.textContent = '❌ An error occurred. See the log above.';
    }
  }
}
</script>
</body>
</html>
"""


def start_flask_server( host: str, port: int,
                        prefill_user: str = "",
                        browser: str = "default"):
    try:
        from flask import Flask, jsonify, render_template_string, request
    except ImportError:
        print("Flask not installed. Run:  pip install flask")
        sys.exit(1)

    app = Flask(__name__)
    detected = detect_default_browser()

    @app.route("/")
    def index():
        return render_template_string(
            WEB_UI,
            prefill_user=prefill_user,
            detected_browser=detected.capitalize()
        )

    @app.route("/start", methods=["POST"])
    def start():
        data     = request.get_json()
        username = data.get("username", "")
        password = data.get("password", "")
        br       = data.get("browser", browser)
        sid      = str(uuid.uuid4())

        session = {"log": [], "done": False, "success": False, "warning": False}
        _sessions[sid] = session

        def log_fn(msg):
            session["log"].append(msg)
            print(msg)

        def run():
            try:
                ok = run_automation(username, password, browser=br, log_fn=log_fn)
                session["success"] = ok
                session["warning"] = not ok
            except Exception as e:
                session["log"].append(f"ERROR: {e}")
            finally:
                session["done"] = True

        threading.Thread(target=run, daemon=True).start()
        return jsonify({"session_id": sid})

    @app.route("/status/<sid>")
    def status(sid):
        s = _sessions.get(sid, {"log": ["Session not found."], "done": True,
                                "success": False, "warning": False})
        return jsonify(s)

    print("\n" + "═" * 58)
    print("  iCloud 2FA Trigger — Web Server Mode")
    print("═" * 58)
    print(f"  Detected default browser : {detected}")
    print(f"  Local URL  : http://localhost:{port}")
    print(f"  Network URL: http://<this-machine-IP>:{port}")
    print("  iPhone/iPad: open Network URL in Safari (same Wi-Fi)")
    print("═" * 58 + "\n")

    app.run(host=host, port=port, debug=False)


# ═════════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═════════════════════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="Trigger iCloud 2FA — auto-detects default browser on Windows & macOS."
    )
    parser.add_argument("--username",  "-u", default="",
                        help="Apple ID (email)")
    parser.add_argument("--password",  "-p", default="",
                        help="Apple ID password")
    parser.add_argument("--browser",   "-b", default="default",
                        choices=["default", "chrome", "edge",
                                "firefox", "safari", "brave", "opera"],
                        help="Browser to use (default: auto-detect system default)")
    parser.add_argument("--server",    "-s", action="store_true",
                        help="Start web server for iPhone/iPad access")
    parser.add_argument("--host",      default="0.0.0.0",
                        help="Server bind address (default: 0.0.0.0)")
    parser.add_argument("--port",      type=int, default=5150,
                        help="Server port (default: 5150)")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.server:
        start_flask_server(
            host=args.host,
            port=args.port,
            prefill_user=args.username,
            browser=args.browser
        )
        return

    username = args.username or input("Apple ID (email): ").strip()
    password = args.password or getpass.getpass("Password: ")

    if not username or not password:
        print("ERROR: Username and password are required.")
        sys.exit(1)

    print(f"\n  OS      : {platform.system()}")
    print(f"  Apple ID: {username}\n")

    success = run_automation(username, password, browser=args.browser)

    if success:
        print("\n✅ 2FA code sent — enter it into iCloud3 now.\n")
    else:
        print("\n⚠️  Check your device — code may still have been sent.\n")


if __name__ == "__main__":
    main()
l