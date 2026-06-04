import time
import random
from panel.bot_logic.settings_helper import get_setting

def random_wait():
    try:
        min_wait = float(get_setting("wait_range_min", 2))
        max_wait = float(get_setting("wait_range_max", 6))
    except (ValueError, TypeError):
        min_wait, max_wait = 2.0, 6.0
    
    delay = random.uniform(min_wait, max_wait)
    print(f"[WAIT] Sleeping for {delay:.2f} seconds...")
    time.sleep(delay)

def simulate_typing(page, selector, text, delay_min=0.05, delay_max=0.25):
    """
    Simulates human typing inside a field by keying characters with random delays.
    """
    page.click(selector)
    time.sleep(0.1)
    for char in text:
        page.type(selector, char)
        time.sleep(random.uniform(delay_min, delay_max))
    time.sleep(0.2)
