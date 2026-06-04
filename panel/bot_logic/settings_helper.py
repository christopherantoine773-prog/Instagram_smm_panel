from panel.models import GlobalSetting

DEFAULTS = {
    'captcha_service': 'capmonster',
    'captcha_api_key': 'YOUR_CAPMONSTER_API_KEY',
    'sms_service': '5sim',
    'sms_api_key': 'YOUR_5SIM_API_KEY',
    'email_service': '1secmail',
    'use_random_user_agent': 'True',
    'rotate_proxies': 'True',
    'wait_range_min': '2',
    'wait_range_max': '6',
    'browser_type': 'firefox',       # Defaulting to firefox since it is pre-installed on this host
    'browser_path': '/usr/bin/firefox', # Absolute path to firefox on host
    'headless_mode': 'True',
}

def get_setting(key, default=None):
    try:
        setting, created = GlobalSetting.objects.get_or_create(
            key=key,
            defaults={'value': DEFAULTS.get(key, '')}
        )
        return setting.value
    except Exception:
        # Fallback in case of database connectivity or migration issues during setup
        return default if default is not None else DEFAULTS.get(key, '')

def get_all_settings():
    settings = {}
    for key in DEFAULTS.keys():
        settings[key] = get_setting(key)
    return settings

def set_setting(key, value):
    GlobalSetting.objects.update_or_create(key=key, defaults={'value': str(value)})
