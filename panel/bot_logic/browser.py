import os
import random
from playwright.sync_api import sync_playwright
from panel.bot_logic.settings_helper import get_setting

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
]

def launch_browser(proxy=None, headless=None, playwright_instance=None):
    """
    Launches a browser instance based on database configurations.
    Returns: (playwright_instance, browser, context, page)
    """
    browser_type_name = get_setting('browser_type', 'firefox').lower()
    browser_path = get_setting('browser_path', '/usr/bin/firefox')
    
    if headless is None:
        headless = get_setting('headless_mode', 'True').lower() == 'true'

    use_random_ua = get_setting('use_random_user_agent', 'True').lower() == 'true'
    user_agent = random.choice(DEFAULT_USER_AGENTS) if use_random_ua else DEFAULT_USER_AGENTS[0]

    p = playwright_instance or sync_playwright().start()
    
    launch_kwargs = {
        "headless": headless,
    }
    
    # Point to the custom browser binary path if configured and exists
    if browser_path and os.path.exists(browser_path):
        launch_kwargs["executable_path"] = browser_path
        print(f"[BROWSER] Using local browser executable: {browser_path}")

    # Set proxy configurations
    if proxy:
        # Playwright supports proxy formatting: {"server": "http://ip:port", "username": "...", "password": "..."}
        # If proxy is a string, check if it contains credentials
        if isinstance(proxy, str):
            launch_kwargs["proxy"] = {"server": proxy}
        elif isinstance(proxy, dict):
            launch_kwargs["proxy"] = proxy

    # Launch browser according to config type
    print(f"[BROWSER] Launching {browser_type_name.upper()} (headless={headless})...")
    if browser_type_name == 'firefox':
        browser = p.firefox.launch(**launch_kwargs)
    else:
        browser = p.chromium.launch(**launch_kwargs)

    context = browser.new_context(
        user_agent=user_agent,
        viewport={"width": 375, "height": 667},
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
        locale="en-US"
    )

    page = context.new_page()
    page.set_default_timeout(45000)  # 45 seconds timeout

    return p, browser, context, page
