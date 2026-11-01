"""Normal Chrome login, followed by an explicit local DevTools connection.

No automation, debugging, certificate, or stealth flags are used in login mode.
Only the dedicated Jarvis profile is ever opened or connected.
"""
from pathlib import Path
import json
import os
import subprocess
import time

import httpx
import psutil

DATA=Path(os.environ['LOCALAPPDATA'])/'OpenJarvis'
PROFILE=DATA/'browser-profile-normal'
MODE_FILE=DATA/'browser-mode.json'
CONTROLLER_FILE=DATA/'browser-controller.json'
PORT=8767


def executable():
    for candidate in [r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                      r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe']:
        if Path(candidate).is_file():
            return candidate
    raise RuntimeError('Chrome or Edge was not found on this computer.')


def mode():
    try:
        value=json.loads(MODE_FILE.read_text())['mode']
        return value if value in ('login','control') else 'login'
    except (OSError,ValueError,KeyError):
        return 'login'


def save_mode(value):
    DATA.mkdir(parents=True,exist_ok=True)
    MODE_FILE.write_text(json.dumps({'mode':value}),encoding='utf-8')


def profile_processes():
    """Match an exact profile argument; never touch the normal personal profile."""
    expected=os.path.normcase(str(PROFILE.resolve()))
    matches=[]
    for process in psutil.process_iter(['pid','name','cmdline']):
        try:
            if (process.info['name'] or '').lower() not in ('chrome.exe','msedge.exe'):
                continue
            arguments=process.info['cmdline'] or []
            if any(x.startswith('--type=') for x in arguments):
                continue
            for argument in arguments:
                if argument.startswith('--user-data-dir='):
                    actual=argument.split('=',1)[1].strip('"')
                    if os.path.normcase(str(Path(actual).resolve()))==expected:
                        matches.append((process,arguments))
        except (psutil.Error,OSError):
            continue
    return matches


def open_login(urls):
    if mode()!='login':
        raise RuntimeError('Switch to sign-in mode first.')
    if any(any(x.startswith('--remote-debugging-') or x=='--enable-automation' for x in args) for _,args in profile_processes()):
        raise RuntimeError('The controlled browser must close before normal sign-in can start.')
    # Launch a normal supported browser. There is deliberately no debug port.
    PROFILE.mkdir(parents=True,exist_ok=True)
    arguments=[executable(),f'--user-data-dir={PROFILE}','--no-first-run','--new-window',*urls]
    subprocess.Popen(arguments,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


def finish_login():
    if profile_processes():
        raise RuntimeError('First close all tabs in the separate Jarvis sign-in browser. Then click Finish sign-in again. This saves your sessions before Jarvis reconnects.')
    save_mode('control')


def controller_endpoint():
    if mode()!='control':
        raise RuntimeError('Jarvis is paused for sign-in. Sign in using the normal browser, close that browser, then click Finish sign-in in Jarvis.')
    roots=profile_processes()
    if roots:
        # Never attach to a browser opened without explicit control mode.
        if not any(f'--remote-debugging-port={PORT}' in args for _,args in roots):
            raise RuntimeError('Close the separate sign-in browser, then click Finish sign-in.')
    try:
        response=httpx.get(f'http://127.0.0.1:{PORT}/json/version',timeout=1)
        if response.status_code==200:
            if not owns_port(roots):
                raise RuntimeError('The browser control port belongs to another app. Jarvis will not attach to it.')
            return f'http://127.0.0.1:{PORT}'
    except httpx.HTTPError:
        pass
    if not roots:
        arguments=[executable(),f'--user-data-dir={PROFILE}',
                   f'--remote-debugging-port={PORT}','--remote-debugging-address=127.0.0.1',
                   '--no-first-run','--new-window','about:blank']
        process=subprocess.Popen(arguments,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        CONTROLLER_FILE.write_text(json.dumps({'pid':process.pid,'profile':str(PROFILE),'port':PORT}),encoding='utf-8')
    for _ in range(50):
        try:
            response=httpx.get(f'http://127.0.0.1:{PORT}/json/version',timeout=1)
            if response.status_code==200 and owns_port(profile_processes()):
                return f'http://127.0.0.1:{PORT}'
        except httpx.HTTPError:
            pass
        time.sleep(.2)
    raise RuntimeError('Chrome did not start its local control connection. Return to sign-in mode and try again.')


def owns_port(roots):
    expected={process.pid for process,_ in roots}
    try:
        # A listening socket has no remote peer. Some Windows/psutil builds
        # report its state as NONE, so do not rely on the state label alone.
        return any(connection.pid in expected and not connection.raddr
                   and connection.laddr.port==PORT and connection.laddr.ip in ('127.0.0.1','::1')
                   for connection in psutil.net_connections(kind='tcp'))
    except psutil.Error:
        return False


def prepare_login():
    """Disconnect only a verified Jarvis-controlled browser, including an orphan after restart."""
    roots=profile_processes()
    controlled=[(process,args) for process,args in roots if f'--remote-debugging-port={PORT}' in args]
    if controlled:
        if not owns_port(controlled):
            raise RuntimeError('Close the separate Jarvis browser before starting sign-in mode.')
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser=pw.chromium.connect_over_cdp(f'http://127.0.0.1:{PORT}')
            # Closing a connected Playwright handle can merely detach.
            # Ask Chrome itself to exit so the profile is saved and unlocked.
            try:
                browser.new_browser_cdp_session().send('Browser.close')
            except Exception:
                if any(process.is_running() for process,_ in controlled):
                    time.sleep(.5)
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        if not any(any(x.startswith('--remote-debugging-') for x in args) for _,args in profile_processes()):
            return
        time.sleep(.2)
    raise RuntimeError('The controlled browser is still closing. Please try again.')
