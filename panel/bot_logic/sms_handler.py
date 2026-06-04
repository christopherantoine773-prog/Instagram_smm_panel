import time
import requests
from panel.bot_logic.settings_helper import get_setting

class SMSHandler:
    def __init__(self, logger=None):
        self.logger = logger or print
        
    def get_api_key(self):
        return get_setting("sms_api_key", "")

    def get_number(self):
        api_key = self.get_api_key()
        if not api_key or api_key == "YOUR_5SIM_API_KEY":
            self.logger("[SMS] API Key not configured. Failing SMS fetch.")
            raise ValueError("5sim SMS API Key is missing or invalid.")
            
        base_url = "https://5sim.net/v1/user"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        try:
            self.logger("[SMS] Requesting phone number from 5sim for Instagram...")
            response = requests.get(
                f"{base_url}/buy/activation/instagram/any",
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            phone = data['phone']
            request_id = data['id']
            self.logger(f"[SMS] Successfully acquired phone: {phone} (ID: {request_id})")
            return phone, request_id
        except Exception as e:
            self.logger(f"[SMS] Failed to get SMS number: {e}")
            raise

    def wait_for_code(self, request_id, timeout=120):
        api_key = self.get_api_key()
        base_url = "https://5sim.net/v1/user"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        self.logger(f"[SMS] Polling for SMS confirmation code on ID: {request_id}...")
        elapsed = 0
        poll_interval = 5

        while elapsed < timeout:
            try:
                resp = requests.get(
                    f"{base_url}/check/{request_id}",
                    headers=headers,
                    timeout=10
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get('sms') and len(data['sms']) > 0:
                    code = data['sms'][0]['code']
                    self.logger(f"[SMS] Received confirmation code: {code}")
                    return code
            except Exception as e:
                self.logger(f"[SMS] Error checking for SMS code: {e}")

            time.sleep(poll_interval)
            elapsed += poll_interval

        self.logger("[SMS] Timed out waiting for SMS activation code.")
        raise TimeoutError("SMS verification code timed out.")
